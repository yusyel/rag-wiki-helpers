import os
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from google.oauth2 import service_account


SERVICE_ACCOUNT_FILE = "./creds.json"


credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
)

tz = ZoneInfo("Europe/Istanbul")


def save_conversation(conversation_id, question, output, timestamp=None):

    if timestamp is None:
        timestamp = datetime.now(tz)

    output["id"] = conversation_id
    output["question"] = question
    output["timestamp"] = timestamp

    table_schema = [
        {"name": "id", "type": "STRING"},
        {"name": "question", "type": "STRING"},
        {"name": "timestamp", "type": "TIMESTAMP"},
        {"name": "context", "type": "STRING"},
        {"name": "answer", "type": "STRING"},
        {"name": "model", "type": "STRING"},
        {"name": "retriever_score", "type": "FLOAT"},
        {"name": "eval_score", "type": "FLOAT"},
        {"name": "source", "type": "STRING"},
        {"name": "headline", "type": "STRING"},
        {"name": "ids", "type": "STRING"},
        {"name": "length", "type": "INTEGER"},
        {"name": "docs_question", "type": "STRING"},
        {"name": "response_time", "type": "FLOAT"},
        {"name": "cost", "type": "FLOAT"},
        {"name": "completion_tokens", "type": "INTEGER"},
        {"name": "prompt_tokens", "type": "INTEGER"},
        {"name": "total_tokens", "type": "INTEGER"},
    ]

    obs = {
        "id": output["id"],
        "question": output["question"],
        "timestamp": output["timestamp"],
        "context": output["context"],
        "answer": output["answer"],
        "model": output["model"],
        "retriever_score": output["retriever_score"],
        "eval_score": output["eval_score"],
        "source": output["metas"]["source"],
        "headline": output["metas"]["headline"],
        "ids": output["metas"]["ids"],
        "length": output["metas"]["length"],
        "docs_question": output["metas"]["question"],
        "response_time": output["response_time"],
        "cost": output["cost"],
        "completion_tokens": output["completion_tokens"],
        "prompt_tokens": output["prompt_tokens"],
        "total_tokens": output["total_tokens"],
    }

    df = pd.DataFrame(obs, index=[0])
    df.to_gbq(
        "wikis.conversation",
        "credible-glow-410419",
        credentials=credentials,
        if_exists="append",
        table_schema=table_schema,
    )


def save_feedback(conversation_id, feedback, timestamp=None):

    if timestamp is None:
        timestamp = datetime.now(tz)

    table_schema = [
        {"name": "id", "type": "STRING"},
        {"name": "feedback", "type": "INTEGER"},
        {"name": "timestamp", "type": "TIMESTAMP"},
    ]

    obs = {"id": conversation_id, "feedback": feedback, "timestamp": timestamp}

    df = pd.DataFrame(obs, index=[0])

    df.to_gbq(
        "wikis.feedback",
        "credible-glow-410419",
        credentials=credentials,
        if_exists="append",
        table_schema=table_schema,
    )
