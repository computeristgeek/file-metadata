#!/bin/bash

set -x
set -e

source .ci/env_variables.sh

# Basics
sudo apt-get install gcc g++ build-essential autoconf autogen shtool libtool pkg-config python-dev python3-dev

# gi requirements
sudo apt-get install gobject-introspection libgirepository1.0-dev python-cairo-dev

# OpenCV requirements
sudo apt-get install build-essential cmake libgtk2.0-dev pkg-config python-dev libavcodec-dev libavformat-dev libswscale-dev 

# GI repositories: gtk
sudo apt-get install gir1.2-gtk-3.0 gir1.2-gtk-2.0 libgtk-3-dev libgtk2.0-dev
# GI repositories: gexiv2
sudo apt-get install libexiv2-dev gir1.2-gexiv2-0.10
# GI repositories: rsvg
sudo apt-get install librsvg2-dev gir1.2-rsvg-2.0


# If using the system's python:
# sudo apt-get install python-gi python-opencv
# OR
# If using pyenv or a virtualenv:
./.ci/install.python-gi.sh "$python_virtualenv"
./.ci/install.python-opencv.sh "$python_virtualenv"
