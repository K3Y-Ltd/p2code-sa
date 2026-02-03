# 1st part: Use cruizba/ubuntu-dind as the base image
FROM cruizba/ubuntu-dind:latest AS p2code-sa-base

# Install Docker dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    ffmpeg \
    libsm6 \
    libxext6 \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3.10 python3.10-venv python3.10-distutils \
    && rm -rf /var/lib/apt/lists/*

# Create venv and ensure subsequent pip/python commands use it
ENV VENV_PATH=/opt/venv

RUN python3.10 -m venv $VENV_PATH \
    && $VENV_PATH/bin/python -m pip install --upgrade pip setuptools wheel
ENV PATH="$VENV_PATH/bin:$PATH"

# The working directory in the container
WORKDIR /usr/src/p2code
RUN chmod -R 777 /usr/src/p2code


# 2nd part: Use configured base image
FROM p2code-sa-base

# Copy the local directory contents to the container
COPY ./dist ./dist
COPY ./models ./models

# Create directory to hold config files
RUN mkdir -p ./cfgs

# Run pip install for `.whl` files & `.whl` file dependencies
RUN python3.10 -m pip install ./dist/*.whl --extra-index-url https://download.pytorch.org/whl/cpu

# CMD to run the application
CMD ["p2code-inference-pipeline", "--cfg_path", "./cfgs/config.yaml"]