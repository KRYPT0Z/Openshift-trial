# ============================================================
# Use the official Python 3.10.4 base image
# This ensures all students use the same Python environment
# ============================================================
FROM python:3.10.4-bullseye


# ============================================================
# Copy the requirements file into the container
# This file contains all Python dependencies needed for the app
# ============================================================
COPY requirements.txt ./


# ============================================================
# Install dependencies
# 1. Upgrade pip
# 2. Install all required libraries listed in requirements.txt
# ============================================================
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./requirements.txt


# ============================================================
# Copy the application code into the container
# The app folder should contain:
# - main Flask file (e.g. app.py / ListItems.py)
# - templates/
# - static/
# - instance/ (for SQLite database)
# ============================================================
COPY ./app /usr/src/app


# ============================================================
# Set the working directory inside the container
# All commands after this will run from this directory
# ============================================================
WORKDIR /usr/src/app


# ============================================================
# Allow write permissions for the instance folder
# This is required for SQLite database to work in OpenShift
# Note:
# - OpenShift runs the container with a random user
# - That user belongs to the root group
# ============================================================
RUN chmod -R g+w /usr/src/app/instance


# ============================================================
# Start the application
# We use Gunicorn instead of Flask's built-in server
# because it is suitable for production deployment
#
# IMPORTANT FOR STUDENTS:
# You MUST update this line depending on your project structure
#
# FORMAT:
# gunicorn --bind 0.0.0.0:5000 <filename>:<flask_app_variable>
#
# EXAMPLES:
#
# If your main file is app.py and contains:
# app = Flask(__name__)
# then use:
# CMD gunicorn --bind 0.0.0.0:5000 app:app
#
# If your file is ListItems.py:
# CMD gunicorn --bind 0.0.0.0:5000 ListItems:app
#
# Replace the values BELOW to match your own project
# ============================================================
CMD gunicorn --bind 0.0.0.0:5000 onlineshop:app