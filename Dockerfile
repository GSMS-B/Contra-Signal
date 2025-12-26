# Use official Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for PDF handling if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Hugging Face requirement)
# User ID 1000 is the standard for HF Spaces
RUN useradd -m -u 1000 user

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create critical directories and set permissions
# These must be writable by the non-root user for persistence/uploads to work
RUN mkdir -p chroma_db uploads && \
    chown -R user:user /app

# Switch to the non-root user
USER user

# Expose the standard Hugging Face port
EXPOSE 7860

# Command to run the application
# Note: HF expects port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
