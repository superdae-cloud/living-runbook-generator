# Builds the React dashboard, then serves it + the FastAPI API from a
# single container — the same "one process, one URL" shape as
# `python3 serve.py` after a local `npm run build`, just containerized.

FROM node:20-slim AS web-build
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tickets/ ./tickets/
COPY runbooks/ ./runbooks/
COPY generate_runbooks.py ./
COPY --from=web-build /web/dist ./web/dist

ENV PYTHONPATH=/app/src
EXPOSE 8080

# $PORT is set by most PaaS platforms (Render, Railway, ...); defaults to
# 8080 for a plain `docker run` with no env var set.
CMD ["sh", "-c", "uvicorn lrg.api:app --host 0.0.0.0 --port ${PORT:-8080}"]
