#!/bin/bash
export FLASK_APP=main.py
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:8000 main:app