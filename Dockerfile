# Ghostline web console — runs as-is on Hugging Face Spaces (Docker SDK) or any container host.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    GHOSTLINE_MODE=replay

WORKDIR /app

COPY pyproject.toml README.md ./
COPY ghostline ./ghostline
COPY examples ./examples
COPY replay ./replay
# Editable install so REPO_ROOT resolves to /app (where examples/ and replay/ live).
RUN pip install --no-cache-dir -e .

# HF Spaces routes to port 7860 by default.
EXPOSE 7860
CMD ["uvicorn", "ghostline.console.app:app", "--host", "0.0.0.0", "--port", "7860"]
