#!/bin/sh
echo "Download new images..."
sudo docker pull costigator/importer
sudo docker pull costigator/web
sudo docker pull mongo
