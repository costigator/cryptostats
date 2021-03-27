FROM python:slim

RUN apt-get update && apt-get -y install gcc

WORKDIR /app

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

# Copy app
ADD ./app .

# Set permissions
RUN chmod a+x run.sh

# Switching to a non-root user
RUN useradd appuser && chown -R appuser /app
USER appuser

# Entrypoint
CMD ["./run.sh"]
