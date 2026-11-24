# ambient: one small stdlib-only Python server. Multi-arch (amd64 + arm64) via the GitHub workflow.
FROM python:3.12-alpine
RUN apk add --no-cache tzdata && mkdir -p /data
COPY app /app
ENV AMBIENT_ROOT=/app DATA_DIR=/data PORT=8099 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8099
VOLUME /data
HEALTHCHECK --interval=60s --timeout=5s CMD wget -qO- http://127.0.0.1:8099/healthz >/dev/null || exit 1
CMD ["python3", "/app/server.py"]
