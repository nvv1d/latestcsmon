
FROM python:3.12-slim

# Install system dependencies including audio libraries
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    ffmpeg \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY Requirements.txt ./requirements.txt
# Install PyAudio separately first
RUN pip install --no-cache-dir PyAudio
# Then install the rest of the requirements
RUN pip install --no-cache-dir -r requirements.txt
# Install Flask explicitly (in case it wasn't installed from requirements)
RUN pip install --no-cache-dir flask

# Copy the rest of the application
COPY . .

# Install the local package in development mode
RUN pip install -e .

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "webapp.py"]
