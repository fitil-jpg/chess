# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/python:3.10

# Avoid prompts from apt operations
ENV DEBIAN_FRONTEND=noninteractive

# Install Python dependencies
COPY requirements.txt /tmp/pip-tmp/
RUN pip install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && pip install --no-cache-dir pytest \
    && rm -rf /tmp/pip-tmp

# Set the default workdir
WORKDIR /workspace

CMD ["bash"]
