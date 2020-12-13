FROM python:slim

ENV PYTHONUNBUFFERED=0

WORKDIR /app

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

# Copy app
ADD ./app .

# Switching to a non-root user
RUN useradd appuser && chown -R appuser /app
USER appuser

# Entrypoint
CMD ["python", "importer.py"]
