FROM prefecthq/prefect:3.0.0-python3.11

RUN pip install --upgrade pip


WORKDIR /app

COPY ["transformers", "./transformers"]

COPY ["creds.json", "./"]

RUN pip3 install torch --index-url https://download.pytorch.org/whl/cpu

COPY ["requirements.txt", "./"]

RUN pip install -r requirements.txt

COPY ["docs_with_q_4o-mini.json", "app.py", "db.py", "retriever.py", "./"]

CMD ["streamlit", "run", "app.py"]


