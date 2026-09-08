FROM python:3.10-slim

# Install system libraries for OpenCV and PyTorch CPU
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install lightweight CPU-only PyTorch first (~180MB instead of 2GB CUDA bloat)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install backend dependencies
COPY requirements-hf.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source directories and model weights
COPY api /app/api
COPY classifier /app/classifier
COPY image_quality /app/image_quality
COPY evidence /app/evidence
COPY explainability /app/explainability
COPY model /app/model

# Expose standard Hugging Face Space port
EXPOSE 7860

# Runtime environment settings
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV OMP_NUM_THREADS=1
ENV KMP_DUPLICATE_LIB_OK=TRUE

# Start FastAPI screening service
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
