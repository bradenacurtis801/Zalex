FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    transformers \
    datasets \
    accelerate \
    scikit-learn \
    pandas \
    numpy \
    matplotlib \
    seaborn

# Set working directory
WORKDIR /workspace

# Expose Jupyter port
EXPOSE 8888

# Start Jupyter
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]