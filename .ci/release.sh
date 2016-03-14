#!/bin/bash

set -x
set -e

# Abort if uncommitted things lie around
git diff HEAD --exit-code

# Release!
python3 .ci/adjust_version_number.py file_metadata/VERSION --release
bash .ci/deploy.pypi.sh

# Adjust version number to next release, script will check validity
python3 .ci/adjust_version_number.py file_metadata/VERSION --new-version ${tag} -b 0

# Commit it
git add file_metadata/VERSION
git commit -m "[GENERATED] Increment version to ${tag}"
