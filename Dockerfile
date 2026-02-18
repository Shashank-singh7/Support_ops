# Use an official lightweight Python image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Initialize the database and generate initial synthetic data
# This ensures the app is ready to use immediately on startup
RUN python generate_data.py && python ingestion.py

# Expose the port the app runs on
EXPOSE 5001

# Command to run the application
CMD ["python", "app.py"]
