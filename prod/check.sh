#!/bin/bash

# Original script by Matthias Lohr
# Example usage:
# ./check.sh costigator/web update.sh

IMAGE="$1"
COMMAND="$2"

which jq
if [ "$?" != "0" ] ; then
	echo "'jq' command not found. Please install and ensure that it is available in PATH."
  exit 1
fi

echo "Fetching Docker Hub token..."
token=$(curl --silent "https://auth.docker.io/token?scope=repository:$IMAGE:pull&service=registry.docker.io" | jq -r '.token')

echo -n "Fetching remote digest... "
digest=$(curl --silent -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
	-H "Authorization: Bearer $token" \
	"https://registry.hub.docker.com/v2/$IMAGE/manifests/latest" | jq -r '.config.digest')
echo "$digest"
