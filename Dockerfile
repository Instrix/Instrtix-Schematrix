# Schematrix web edition: docker build -t schematrix . && docker run -p 8000:8000 -v schematrix-data:/data schematrix
FROM python:3.12-slim

# cairo for PNG/PDF export; the house fonts so server-rendered PNG/PDF match the editor
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcairo2 fonts-jetbrains-mono fonts-inter \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY schematrix ./schematrix
RUN pip install --no-cache-dir ".[export]" \
    && useradd --create-home --uid 1000 schematrix \
    && mkdir /data && chown schematrix /data

USER schematrix
ENV SCHEMATRIX_WORKSPACE=/data \
    SCHEMATRIX_HOST=0.0.0.0 \
    SCHEMATRIX_PORT=8000 \
    SCHEMATRIX_SCRIPTS=1 \
    PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/api/health'); " || exit 1
CMD ["schematrix", "serve"]
