# Dockerfile: nova-ci-rescue-sandbox
FROM python:3.11-slim

# Install project dependencies and test tools
# (Copy in requirements.txt from the project)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pytest pytest-json-report

# Copy the test runner helper script into the image
COPY run_python.py /usr/local/bin/run_python.py
RUN chmod +x /usr/local/bin/run_python.py

# Set working directory and default entrypoint for running tests
WORKDIR /workspace
ENTRYPOINT ["python", "/usr/local/bin/run_python.py"]
