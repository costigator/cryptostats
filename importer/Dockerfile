FROM python:slim

ENV DB_URI mongodb://crypto:Cr7ptopa55@mongo:27017
ENV SCRAPE_INTERVAL 60

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
CMD ["python", "-u", "importer.py"]
