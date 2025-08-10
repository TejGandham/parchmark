# Stage 1: Builder stage to create wheel files for dependencies
FROM python:3.11 as builder

WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Create wheel files for all dependencies
# This allows for faster and offline installation in the final stage
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# Stage 2: Final stage to run the application
FROM python:3.11-slim

WORKDIR /app

# Copy the wheel files from the builder stage
COPY --from=builder /wheels /wheels

# Install the dependencies from the wheel files
# This is faster and doesn't require network access
RUN pip install --no-cache --no-index --find-links=/wheels /wheels/*

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Use run.py to ensure all environment variables and paths are set correctly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
