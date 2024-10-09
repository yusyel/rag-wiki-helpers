import os
import time
from haystack import Pipeline
from haystack.components.builders.answer_builder import AnswerBuilder
from haystack_integrations.document_stores.elasticsearch import (
    ElasticsearchDocumentStore,
)
from haystack_integrations.components.retrievers.elasticsearch import (
    ElasticsearchEmbeddingRetriever,
)
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.components.evaluators.ragas import (
    RagasEvaluator,
    RagasMetric,
)
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret
import google.auth
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession


SEARCH = os.environ["SEARCH"]


KEY = os.environ["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"]

SERVICE_ACCOUNT_FILE = "./creds.json"


def get_token():
    credentials = service_account.IDTokenCredentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, target_audience=SEARCH
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    token = credentials.token

    return token


def get_document_store(token):

    document_store = ElasticsearchDocumentStore(
        hosts=SEARCH,
        embedding_similarity_function="cosine",
        index="germany",
        request_timeout=3000,
        bearer_auth=token,
    )
    return document_store


def get_generator():

    template = """
    You're a FAQ database assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
    Use only the facts from the CONTEXT when answering the QUESTION.

    Context:
    {% for document in documents %}
        {{ document.content }}
    {% endfor %}

    Question: {{question}} Answer: """

    prompt_builder = PromptBuilder(template=template)
    generator = OpenAIGenerator(model="gpt-4o-mini", api_key=Secret.from_token(KEY))

    return prompt_builder, generator


def get_pipeline(document_store, prompt_builder, generator):

    rag_pipeline = Pipeline()
    rag_pipeline.add_component(
        "text_embedder",
        SentenceTransformersTextEmbedder(model="./transformers", progress_bar=False),
    )
    rag_pipeline.add_component(
        "retriever",
        ElasticsearchEmbeddingRetriever(document_store=document_store, top_k=1),
    )
    rag_pipeline.add_component("prompt_builder", prompt_builder)
    rag_pipeline.add_component("llm", generator)
    rag_pipeline.add_component(instance=AnswerBuilder(), name="answer_builder")
    rag_pipeline.connect("text_embedder", "retriever")
    rag_pipeline.connect("retriever", "prompt_builder.documents")
    rag_pipeline.connect("prompt_builder", "llm")
    rag_pipeline.connect("llm.replies", "answer_builder.replies")
    rag_pipeline.connect("llm.meta", "answer_builder.meta")
    rag_pipeline.connect("retriever", "answer_builder.documents")

    return rag_pipeline


def get_eval_pipeline():

    eval_pipeline = Pipeline()
    evaluator = RagasEvaluator(
        metric=RagasMetric.ASPECT_CRITIQUE,
        metric_params={
            "name": "eval",
            "definition": "Given question, context and generated response, how revelant is response?",
            "strictness": 2,
        },
    )
    eval_pipeline.add_component("evaluator", evaluator)

    return eval_pipeline


def get_response(question, rag_pipeline):
    start_time = time.time()

    response = rag_pipeline.run(
        {
            "text_embedder": {"text": question},
            "prompt_builder": {"question": question},
            "answer_builder": {"query": question},
        }
    )
    end_time = time.time()
    response_time = end_time - start_time
    return response, response_time


def get_eval_score(eval_pipeline, question, context, response):

    results = eval_pipeline.run(
        {
            "evaluator": {
                "questions": question,
                "contexts": [context],
                "responses": response,
            }
        }
    )
    return results["evaluator"]["results"][0][0]["score"]


def calculate_openai_cost(tokens):

    openai_cost = 0
    openai_cost = (
        tokens["prompt_tokens"] * 0.03 + tokens["completion_tokens"] * 0.06
    ) / 1000

    return openai_cost


def get_answer(question):

    token = get_token()

    document_store = get_document_store(token)

    prompt_builder, generator = get_generator()

    rag_pipeline = get_pipeline(document_store, prompt_builder, generator)

    response, response_time = get_response(question, rag_pipeline)
    eval_pipeline = get_eval_pipeline()

    context = response["answer_builder"]["answers"][0].documents[0].content
    answer = response["answer_builder"]["answers"][0].data
    model = response["answer_builder"]["answers"][0].meta["model"]
    tokens = response["answer_builder"]["answers"][0].meta["usage"]
    metas = response["answer_builder"]["answers"][0].documents[0].meta
    score = response["answer_builder"]["answers"][0].documents[0].score
    eval_score = get_eval_score(eval_pipeline, [question], [context], [answer])
    openai_cost = calculate_openai_cost(tokens)

    return {
        "context": context,
        "answer": answer,
        "model": model,
        "retriever_score": score,
        "eval_score": eval_score,
        "metas": metas,
        "response_time": response_time,
        "cost": openai_cost,
        "completion_tokens": tokens["completion_tokens"],
        "prompt_tokens": tokens["prompt_tokens"],
        "total_tokens": tokens["total_tokens"],
        "openai_cost": openai_cost,
    }
