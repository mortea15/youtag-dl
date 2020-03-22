![Docker Stars Shield](https://img.shields.io/docker/stars/mortea15/youtag-dl.svg?style=flat-square)
![Docker Pulls Shield](https://img.shields.io/docker/pulls/mortea15/youtag-dl.svg?style=flat-square)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/mortea15/youtag-dl/master/LICENSE)

# youtag-dl
*Yet another fork of manbearwiz/youtube-dl-server, with tagging functionality*

Created to make your YouTube music-downloading tasks chiller. Specify (sub)directory, filename and tags (artist/title/album) per download.

![screenshot][1]

## Running

### Docker CLI

This example uses the docker run command to create the container to run the app. Here we also use host networking for simplicity. Also note the `-v` argument. This directory will be used to output the resulting videos

```shell
$ docker run -d --net="host" --name ytdl -v <music_directory>:/music mortea15/youtag-dl
```

### Docker Compose

This is an example service definition that could be put in `docker-compose.yml`.

```yml
version: 3
services:
  ytdl:
    image: "mortea15/youtag-dl"
    container_name: ytdl
    restart: always
    ports:
      - 8080:8080
    volumes:
      - /media/music:/music
```

### Python

If you have python ^3.3.0 installed in your PATH you can simply run like this, providing optional environment variable overrides inline.

```shell
$ YDL_SERVER_PORT=8123 python3 -u ./youtube-dl-server.py
```

## Usage

### Start a download remotely

Downloads can be triggered by supplying the `{{url}}` of the requested video through the Web UI or through the REST interface via curl, etc.

#### HTML

Just navigate to `http://{{host}}:8080` and enter the requested `{{url}}`.

Additionally, you can specify:
- Output directory
- Filename (without .ext)
- Artist, title and album tags

#### Curl

```shell
$ curl -X POST --data-urlencode "url={{url}}" http://{{host}}:8080/q
```

#### Fetch

```javascript
fetch(`http://${host}:8080/q`, {
  method: "POST",
  body: new URLSearchParams({
    url: url,
    format: "bestaudio",
    artist: artist,
    title: title,
    album: album
  }),
});
```

#### Bookmarklet

Add the following bookmarklet to your bookmark bar so you can conviently send the current page url to your youtube-dl-server instance.

```javascript
javascript:!function(){fetch("http://${host}:8080/q",{body:new URLSearchParams({url:window.location.href,format:"bestaudio"}),method:"POST"})}();
```

## Implementation
This is a fork of [`youtube-dl-server`](https://github.com/manbearwiz/youtube-dl-server) by *manbearwiz*.

The server uses [`bottle`](https://github.com/bottlepy/bottle) for the web framework and [`youtube-dl`](https://github.com/rg3/youtube-dl) to handle the downloading. The integration with youtube-dl makes use of their [python api](https://github.com/rg3/youtube-dl#embedding-youtube-dl).

This docker image is based on [`python:alpine`](https://registry.hub.docker.com/_/python/) and consequently [`alpine:3.8`](https://hub.docker.com/_/alpine/).

[1]:youtag-dl.png
