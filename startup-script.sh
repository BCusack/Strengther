#!/bin/bash
REGION="australia-southeast2"
REPOSITORY="server-repo"
IMAGE_NAME="strengther-app"
PROJECT_ID="binanceapp-333f1"

# Pull the latest Docker image
sudo docker pull ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest

# Stop and remove the existing container if it's running
sudo docker stop fastapi-app || true
sudo docker rm fastapi-app || true

# Run the new container
sudo docker run -d --name fastapi-app -p 80:8000 ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest
