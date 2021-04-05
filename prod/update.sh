#!/bin/sh
echo "Update GIT repository..."
git pull
echo "Download new images..."
sudo docker pull costigator/importer
sudo docker pull costigator/web
sudo docker pull mongo
