# Development

If you want to contribute to this project you can run the app locally. Please check the following commands.

## Pull the latest images

These commands can also be used to update existing images.

```cmd
docker pull mongo
docker pull python:slim
```

Useful links:

- [MongoDB Release Notes](https://docs.mongodb.com/manual/release-notes/)
- [Python Docker Container](https://hub.docker.com/_/python)

## Build

Build and start the app with docker compose:

```cmd
docker-compose up --build --remove-orphans
```

## Python

### Install packages

```cmd
pip install -r requirements.txt
pip install libraries/Twisted-20.3.0-cp39-cp39-win_amd64.whl
```

## Delete DB

To delete all the data present in the DB just delete the content of this folder (except the .gitkeep file):

```cmd
./mongodb/data
```
