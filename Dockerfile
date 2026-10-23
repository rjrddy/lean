FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
COPY sdk /sdk
RUN npm run build
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir pip==26.2.2 . && useradd --uid 10001 --create-home app
COPY assets ./assets
COPY docs/results/evaluation.json ./docs/results/evaluation.json
COPY --from=web /web/dist ./apps/web/dist
USER 10001
ENV LEAN_ROOT=/app HOST=0.0.0.0 PORT=8092
EXPOSE 8092
CMD ["python", "-m", "lean.server"]
