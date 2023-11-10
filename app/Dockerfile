# Use the official Python image
FROM python:3.9

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file to the container
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the application source code to the container
COPY ./service /code/
EXPOSE 8082
# Expose the port your Flask app runs on
CMD ["uvicorn", "courseregistrationservice:app", "--host", "0.0.0.0", "--port", "8082"]