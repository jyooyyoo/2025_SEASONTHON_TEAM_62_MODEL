# Use the official Python 3.11 base image for compatibility with Flask 3.x and click 8.2.1
FROM python:3.11-slim

# Set the working directory in the container.
WORKDIR /app

# Install system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies.
# You can later split model-heavy packages if needed.
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Set the FLASK_APP environment variable (optional for Gunicorn)
ENV FLASK_APP=src/app.py

# Expose the port your app runs on. Cloud Run expects it to be 8080.
EXPOSE 8080

# Run the application using Gunicorn, a production-ready WSGI server.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "src.app:app"]
