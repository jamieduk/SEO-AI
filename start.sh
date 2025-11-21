#!/bin/bash
# (c) J~Net 2025
#
#
#
# ./start.sh https://jnetai.com
#
#
#
python -m venv venv
source venv/bin/activate
echo "Virtual Environment Setup and ready!"

if [ -z "$1" ]; then
    read -rp "Enter domain to crawl (example.com): " domain
else
    domain="$1"
fi

python run.py "$domain"

