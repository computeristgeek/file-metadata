#!/bin/bash

# Do not use `set -x` here as then it displays the PYPIPW in logs
set -e

# Get environment variables, readily decrypted by rultor
source ../rultor_secrets.sh

# Ship it!
echo "Uploading file-metadata to pypi"
pip3 install twine wheel
python3 setup.py sdist bdist_wheel
twine upload dist/* -u "$PYPIUSER" -p "$PYPIPW"

sudo apt-get -qq -y install python3-dev

echo "Installing file-metadata from pypi"
pip3 install --pre file-metadata==`cat file_metadata/VERSION` --upgrade
pypi_version=`cd .. && python3 -c "import file_metadata; print(file_metadata.__version__)"`
repo_version=`cat file_metadata/VERSION`

echo versions: pip=$pypi_version repo=$repo_version
[ $pypi_version = $repo_version ]
