#!/bin/sh
cd "$(dirname "$0")"
pip3 install -r requirements.txt --user
python3 ./downloader.py
