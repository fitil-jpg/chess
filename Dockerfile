# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/python:3.10

# Avoid prompts from apt operations
ENV DEBIAN_FRONTEND=noninteractive

# Install Python dependencies
COPY requirements.txt /tmp/pip-tmp/
RUN pip install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && pip install --no-cache-dir pytest Flask==2.3.3 Flask-CORS==4.0.0 \
    && rm -rf /tmp/pip-tmp

# Install R and testthat
RUN apt-get update \
    && apt-get install -y r-base \
    && R -e 'install.packages("testthat", repos="https://cloud.r-project.org")' \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the default workdir
WORKDIR /workspace

CMD ["bash"]
