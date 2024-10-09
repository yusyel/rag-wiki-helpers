### Building Streamlit app
`creds.json` file is google cloud service account file. 

Must be with these roles:

    BigQuery Admin
    Cloud Run Admin
    Cloud Run Service Agent 

Sentence Transformers located to `./transformers` folder.

For saving model:
```python
load_model = SentenceTransformer("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")
load_model.encoder.("./transformers")
```

Building Docker image:

```bash
docker build -t app .
```

Running Docker images with envs:


```
docker run -it --rm -e SEARCH=$SEARCH -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8501:8501 app
```