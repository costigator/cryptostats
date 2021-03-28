FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

WORKDIR /app

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

# Copy app
ADD ./app .