FROM python:3.10-slim

RUN mkdir /code

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY /out-chess ./out-chess
COPY main.py api_sample.py model.py .
COPY /data/chess/meta.pkl ./data/chess/meta.pkl

CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=80"]
