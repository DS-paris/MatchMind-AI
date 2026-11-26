FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
    TOKENIZERS_PARALLELISM=false MATCHMIND_PUBLIC=true \
    HOME=/home/user
RUN useradd --create-home --uid 1000 user
WORKDIR /home/user/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check
COPY --chown=user:user . .
RUN chown user:user /home/user/app
USER user
# Download public MiniLM weights during build. No credentials or resumes needed.
RUN python -c "from matcher import load_model; load_model()"
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8501/_stcore/health',timeout=4)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
