FROM python:3.12-slim

WORKDIR /srv/confluencr

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY piccolo_conf.py .

RUN useradd --system --uid 10001 --home /srv/confluencr confluencr \
    && chown -R confluencr:confluencr /srv/confluencr

USER confluencr

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
