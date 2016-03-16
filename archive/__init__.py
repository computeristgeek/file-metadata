"""
This file is a set of configurations required for compatibility to use
catimages.py for now. It is no way meant to be portable and will possibly
only work on the developer's computer.
"""
import os
import sys

# REPO_DIR is the path where the root directory of this repository
REPO_DIR = os.path.join(os.path.dirname(__file__), os.pardir)

# WIKI_DIR is the path above the repo. We assume all wiki related repos are
# in this directory.
WIKI_DIR = os.path.join(os.path.dirname(__file__), os.pardir)

# PYWIKIBOT_PATH is the pywikibot-core repository. We use the environment
# variable if that is defined.
PYWIKIBOT2_DIR = os.environ.get('PYWIKIBOT2_DIR',
                                os.path.join(REPO_DIR, os.pardir, 'pywikibot-core'))

PYWIKIBOT_SCRIPTS_DIR = os.path.join(PYWIKIBOT2_DIR, "scripts")

# Add the paths which are needed for catimages to function correctly.
for path in [PYWIKIBOT2_DIR, PYWIKIBOT_SCRIPTS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Binaries to install
# sudo apt-get install exiftool poppler-utils libav-tools imagemagick

# Python libs not in pypi
# sudo apt-get install libdmtx-dev libzbar-dev
