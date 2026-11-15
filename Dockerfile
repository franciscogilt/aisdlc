FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home app && chown -R app /app
USER app
EXPOSE 8000
# TODO: ajusta el comando de arranque (modulo wsgi; agrega gunicorn a requirements, es necesario en produccion)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
