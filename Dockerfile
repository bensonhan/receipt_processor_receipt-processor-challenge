# Base image
FROM python:3

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose a port (if needed)
EXPOSE 8000

# Define the command to run the application
CMD ["python3", "app.py"]
