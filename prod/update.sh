#!/bin/sh
echo "--------------------------"
echo $(date '+%d/%m/%Y %H:%M:%S')
echo "Update GIT repository..."
git pull
echo "Prune unused Docker images..."
docker image prune -a -f
echo "Download new images..."
docker pull costigator/importer
docker pull costigator/web
docker pull mongo
echo "Updated the app..."
docker-compose up -d
echo "Update finished successfully."