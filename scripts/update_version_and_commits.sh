#!/bin/bash

# Exit if any command fails
set -x

# Check if the version.txt file exists, and create it if it doesn't
if [ ! -f version.txt ]; then
    echo "Version: 000000-00000000" > version.txt
fi

# Get the last version number from the version.txt file
LAST_VERSION=$(cat version.txt | grep -oP '(?<=Version: ).*')

# Get the current date YYYYMMDD
DATE=$(date +%Y%m%d)

# Get the current commit hash
COMMIT=$(git rev-parse --short HEAD)

# Create the new version number
VERSION="$COMMIT-$DATE"

# Update the version.txt file with the new version number
echo "Version: $VERSION" > version.txt
# Add the version.txt file to the git index
git add version.txt

# Get the last version commit hash from the last version number
LAST_VERSION_SHORT_HASH=$(echo $LAST_VERSION | cut -d'-' -f1)
# Get the commit hash of the last version.
LAST_VERSION_COMMIT=$(git rev-list -n 1 $LAST_VERSION_SHORT_HASH 2>/dev/null || echo "")

# Check if the commits.md file exists, and create it if it doesn't
if [ ! -f commits.md ]; then
    touch commits.md
fi

if [ -z "$LAST_VERSION_COMMIT" ]; then
    # If the last version commit hash is empty, then this is the first version.
    # So, we'll just add the commit log since the beginning of the repo.
    git log --pretty=format:'## Version: $VERSION%n### %s%n%b' >> commits.md
else
    # Update the commits.md file with the commit log since the last version
    git log --pretty=format:'## Version: $VERSION%n### %s%n%b' $LAST_VERSION_COMMIT..HEAD >> commits.md
fi

# Add the commits.md file to the git index
git add commits.md