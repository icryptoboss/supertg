# Use a Python 3.9.6 Alpine base image
FROM python:3.9.6-alpine3.14

# Set the working directory
WORKDIR /app

# Copy all files from the current directory to the container's /app directory
COPY . .

# Install necessary dependencies
RUN apk add --no-cache \
    gcc \
    libffi-dev \
    musl-dev \
    ffmpeg \
    aria2 \
    make \
    g++ \
    cmake \
    unzip \
    wget && \
    wget -q https://www.bok.net/Bento4/binary/bento4-1-6-0-639.x86_64-unknown-linux.zip && \
    unzip bento4-1-6-0-639.x86_64-unknown-linux.zip -d /opt/bento4 && \
    cp /opt/bento4/bin/mp4decrypt /usr/local/bin/ && \
    chmod +x /usr/local/bin/mp4decrypt && \
    rm -rf /opt/bento4 bento4-1-6-0-639.x86_64-unknown-linux.zip

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir --upgrade -r requirements.txt \
    && python3 -m pip install -U yt-dlp

# Set the command to run the application
CMD ["sh", "-c", "gunicorn app:app & python3 main.py"]
