FROM python:3.9-buster

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 🔍 verify ffprobe exists (IMPORTANT)
RUN which ffprobe && ffprobe -version

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "bot"]
