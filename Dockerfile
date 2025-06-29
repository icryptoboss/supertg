# Use a more compatible image (Alpine can break yt-dlp/mp4decrypt)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    aria2 \
    gcc \
    g++ \
    libffi-dev \
    make \
    cmake \
    unzip \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Build and install mp4decrypt
RUN wget https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-640.x86_64-unknown-linux.zip && \
    unzip Bento4-SDK-1-6-0-640.x86_64-unknown-linux.zip && \
    cp Bento4-SDK-1-6-0-640.x86_64-unknown-linux/bin/mp4decrypt /usr/local/bin/ && \
    chmod +x /usr/local/bin/mp4decrypt && \
    rm -rf Bento4-SDK-1-6-0-640.x86_64-unknown-linux.zip

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir yt-dlp

# Start bot and Flask app
CMD ["sh", "-c", "gunicorn app:app & python3 main.py"]
