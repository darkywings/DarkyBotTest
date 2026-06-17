FROM python:3.10-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/api

WORKDIR /app/api/generator
RUN python setup.py build_ext --inplace

WORKDIR /app

EXPOSE 8000

CMD ["python", "-m", "api"]