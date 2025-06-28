FROM python:3.9-slim

WORKDIR /app
COPY . .

# Install system packages
RUN apt update && apt install -y \
    ffmpeg \
    aria2 \
    unzip \
    wget \
    gcc \
    g++ \
    libffi-dev \
    build-essential \
    supervisor \
    && wget -q https://www.bok.net/Bento4/binary/bento4-1-6-0-639.x86_64-unknown-linux.zip \
    && unzip bento4-1-6-0-639.x86_64-unknown-linux.zip -d /opt/bento4 \
    && cp /opt/bento4/bin/mp4decrypt /usr/local/bin/ \
    && chmod +x /usr/local/bin/mp4decrypt \
    && rm -rf /opt/bento4 bento4-1-6-0-639.x86_64-unknown-linux.zip

# Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -U yt-dlp

EXPOSE 8000

CMD ["python3", "run.py"]
