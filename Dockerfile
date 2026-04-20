# CUSTOMIZE: Replace this with your stack's base image and dependencies.
#
# Examples:
#   Elixir:  FROM elixir:1.19-slim
#   Node:    FROM node:22-slim
#   Python:  FROM python:3.13-slim
#   Rust:    FROM rust:1.82-slim

FROM ubuntu:24.04

# Install git (required for KEEL) + your stack's runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    # CUSTOMIZE: Add your stack's packages here
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CUSTOMIZE: Copy dependency files and install
# COPY package.json package-lock.json ./
# RUN npm install

# CUSTOMIZE: Copy source
COPY . .

# CUSTOMIZE: Set your app's start command
# CMD ["npm", "start"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["echo", "CUSTOMIZE: Set your start command in Dockerfile"]
