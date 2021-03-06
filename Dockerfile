FROM python:alpine

LABEL maintainer="Morten Amundsen <me@mortenamundsen.me>"

ENV USER=abc
ENV PUID=1000
ENV PGID=985

RUN addgroup -g $PGID $USER
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/tmp/$USER" \
    --ingroup "$USER" \
    --no-create-home \
    --uid "$PUID" \
    "$USER"

RUN apk add --no-cache \
  ffmpeg \
  tzdata \
  gcc \
  build-base \
  taglib-dev
      
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip3 install -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080

USER $USER

CMD [ "python", "-u", "./youtag-dl.py" ]
