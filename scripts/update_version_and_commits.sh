#!/bin/bash

# Get the last version number from the version.txt file
LAST_VERSION=$(cat version.txt | grep -oP '(?<=Version: ).*')

# Update the commits.md file with the commit log since the last version
LAST_VERSION_SHORT_HASH=$(echo $LAST_VERSION | cut -d'-' -f1)
LAST_VERSION_COMMIT=$(git rev-list -n 1 $LAST_VERSION_SHORT_HASH 2>/dev/null || echo "")
git log --pretty=format:'## Version: $VERSION%n### %s%n%b' $LAST_VERSION_COMMIT..HEAD >> commits.md

# Update the version.txt file with the new version number
echo "Version: $VERSION" > version.txt