# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Copy the Flask API folder files into "/app" in docker container
COPY ./flaskapi /app

# Set the working directory in the container
WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Install any needed packages specified in requirements.txt
RUN pip install --default-timeout=1000 --no-cache-dir -r ./requirements.txt

# Expose Container Port Number 5000
EXPOSE 5000

# Run the Flask API app
CMD ["python", "./run.py"]
