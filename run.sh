#!/bin/bash

source $(pipenv --venv)/bin/activate

FLASK_APP=main.py flask run -h 0.0.0.0