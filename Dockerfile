# Use an official Python runtime as a parent image
FROM python

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port your app runs on
EXPOSE 5000

# CMD to run the Flask application
CMD ["python", "app.py"]
