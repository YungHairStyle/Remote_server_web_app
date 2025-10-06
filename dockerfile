# Use the official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files to the container
COPY . /app


# Install system dependencies (if needed for e.g., image preview)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories in container (these will be mounted)
RUN mkdir -p /app/media /app/files /app/data /app/guest

# Expose the port your app runs on
EXPOSE 4999

# Start the Flask app
RUN pip install gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]


