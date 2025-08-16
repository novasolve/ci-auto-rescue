# Dockerfile for nova-ci-rescue-sandbox
# ========================================
# Sandbox container for running tests in isolation

FROM python:3.11-slim

# Set working directory (tests will be run from /workspace)
WORKDIR /workspace

# Install pytest and the JSON report plugin
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-json-report==1.5.0 \
    pytest-timeout==2.2.0

# Copy the test runner helper script into the container
COPY run_python.py /usr/local/bin/run_python.py
RUN chmod +x /usr/local/bin/run_python.py

# Set up non-root user for security
RUN useradd -m -s /bin/bash testrunner && \
    chown -R testrunner:testrunner /workspace

# Switch to non-root user
USER testrunner

# Set Python to run in unbuffered mode for real-time output
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "/usr/local/bin/run_python.py", "--help"]
