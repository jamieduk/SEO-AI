#!/bin/bash
# (c) J~Net 2025
#
python -m venv venv
source venv/bin/activate
echo "Virtual Environment Setup and ready!"

pip install -r requirements.txt
pip install --upgrade pip
pip install requests beautifulsoup4
