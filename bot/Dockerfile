FROM python:3.12.4-slim

RUN apt-get update && apt-get install -y fonts-liberation

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]