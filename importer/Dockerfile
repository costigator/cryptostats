FROM python:slim

ENV LOG_LEVEL INFO
ENV DB_URI mongodb://crypto:Cr7ptopa55@mongo:27017
ENV HISTORY_INITIAL_DELAY_S 60

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
