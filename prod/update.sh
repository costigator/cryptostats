#!/bin/sh
echo "Update GIT repository..."
git pull
echo "Prune unused Docker images..."
docker image prune -a -f
echo "Download new images..."
docker pull costigator/importer
docker pull costigator/web
docker pull mongo
echo "Stop & Start the app..."
docker-compose down
docker-compose up -d
