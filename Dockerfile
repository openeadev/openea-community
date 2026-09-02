FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/openea

RUN addgroup --system openea && adduser --system --ingroup openea openea
COPY pyproject.toml README.md LICENSE ./
COPY app ./app
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
RUN python scripts/vendor_frontend_assets.py \
    && chmod -R a+rX app/static/vendor
RUN pip install --no-cache-dir .

USER openea
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
