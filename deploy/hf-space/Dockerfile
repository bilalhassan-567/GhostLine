# Hugging Face Space container for the Ghostline console.
# Clones the GitHub repo at build time; a factory rebuild picks up the latest commit.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    GHOSTLINE_MODE=replay

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/bilalhassan-567/GhostLine.git /app
WORKDIR /app
RUN pip install -e .

EXPOSE 7860
CMD ["uvicorn", "ghostline.console.app:app", "--host", "0.0.0.0", "--port", "7860"]
