#!/bin/sh
echo "--------------------------"
echo $(date '+%d/%m/%Y %H:%M:%S')
echo "Update GIT repository..."
git pull
echo "Prune unused Docker images..."
/usr/local/bin/docker image prune -a -f
echo "Download new images..."
/usr/local/bin/docker pull costigator/importer
/usr/local/bin/docker pull costigator/web
/usr/local/bin/docker pull costigator/analyzer
/usr/local/bin/docker pull mongo
echo "Updated the app..."
/usr/local/bin/docker-compose up -d
echo "Update finished successfully."