# Use Alpine-based Python image
FROM python:3.9.6-alpine3.14

# Set working dir
WORKDIR /app

# Copy all files
COPY . .

# Install system deps
RUN apk add --no-cache \
    gcc \
    g++ \
    make \
    cmake \
    libffi-dev \
    musl-dev \
    ffmpeg \
    aria2 \
    unzip \
    wget \
    supervisor && \
    wget -q https://www.bok.net/Bento4/binary/bento4-1-6-0-639.x86_64-unknown-linux.zip && \
    unzip bento4-1-6-0-639.x86_64-unknown-linux.zip -d /opt/bento4 && \
    cp /opt/bento4/bin/mp4decrypt /usr/local/bin/ && \
    chmod +x /usr/local/bin/mp4decrypt && \
    rm -rf /opt/bento4 bento4-1-6-0-639.x86_64-unknown-linux.zip

# Install Python packages
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install -U yt-dlp

# Expose port (for Flask)
EXPOSE 8000

# Start both processes (Flask + Bot)
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
