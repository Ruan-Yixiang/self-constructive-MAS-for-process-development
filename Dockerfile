# ===== builder: build dependencies as wheels =====
FROM python:3.11.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1
WORKDIR /wheels

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /wheels/requirements.txt

RUN python -m pip install -U pip \
 && pip wheel --wheel-dir=/wheels -r /wheels/requirements.txt


# ===== runtime: final image =====
FROM python:3.11.13-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN python -m pip install -U pip \
 && python -m pip install --no-index --find-links=/wheels -r /wheels/requirements.txt

COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "Home.py"]
