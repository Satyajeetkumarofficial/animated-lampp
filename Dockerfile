FROM python:3.9-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 🔍 Verify ffmpeg & ffprobe at build time
RUN which ffprobe && ffprobe -version

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "bot"]
