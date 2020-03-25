from __future__ import unicode_literals

import glob
import json
import os
import subprocess
from collections import ChainMap
from pathlib import Path
from queue import Queue
from threading import Thread

import taglib
import youtube_dl
from bottle import Bottle, request, route, run, static_file

app = Bottle()


app_defaults = {
    'YDL_FORMAT': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    'YDL_EXTRACT_AUDIO_FORMAT': None,
    'YDL_EXTRACT_AUDIO_QUALITY': '192',
    'YDL_OUTPUT_TEMPLATE': '/music/%(title)s.%(ext)s',
    'YDL_ARCHIVE_FILE': None,
    'YDL_SERVER_HOST': '0.0.0.0',
    'YDL_SERVER_PORT': 8080
}


@app.route('/')
def dl_queue_list():
    return static_file('index.html', root='./')


@app.route('/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')


@app.route('/q', method='GET')
def q_size():
    return {"success": True, "size": json.dumps(list(dl_q.queue))}


@app.route('/q', method='POST')
def q_put():
    url = request.forms.get("url")
    options = {
        'format': request.forms.get("format"),
        'final_dir': request.forms.get("final_dir"),
        'fname': request.forms.get("fname"),
        'artist': request.forms.get("artist"),
        'title': request.forms.get("title"),
        'album': request.forms.get("album")
    }

    if not url:
        return {"success": False, "error": "/q called without a 'url' query param"}

    if not options.get('fname') or options.get('fname') == '':
        if 'artist' and 'title' in options and options.get('artist') != '' and options.get('title') != '':
            filename = f'{options.get("artist")} - {options.get("title")}'
            options['fname'] = filename
            print(f'Set filename to {filename} [src:artist/title]')

    if not options.get('final_dir').endswith('/'):
        options['final_dir'] = options.get('final_dir') + '/'

    dl_q.put((url, options))
    print("Added url " + url + " to the download queue")
    return {"success": True, "url": url, "options": options}

@app.route("/update", method="GET")
def update():
    command = ["pip", "install", "--upgrade", "youtube-dl"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = proc.communicate()
    return {
        "output": output.decode('ascii'),
        "error":  error.decode('ascii')
    }

def dl_worker():
    while not done:
        url, options = dl_q.get()
        download(url, options)
        fpath_noext = options.get('final_dir') + options.get('fname')
        fpath = [fp for fp in glob.glob(fpath_noext + '.*')]
        if fpath:
            tag(fpath[0], artist=options.get('artist'), title=options.get('title'), album=options.get('album'))
        else:
            print(f'File {fpath_noext} not found. Skipping tagging.')
        print('Done.')
        dl_q.task_done()


def get_ydl_options(request_options):
    request_vars = {
        'YDL_EXTRACT_AUDIO_FORMAT': None
    }

    requested_format = request_options.get('format', 'bestaudio')

    if requested_format in ['aac', 'flac', 'mp3', 'm4a', 'opus', 'vorbis', 'wav']:
        request_vars['YDL_EXTRACT_AUDIO_FORMAT'] = requested_format
    elif requested_format == 'bestaudio':
        request_vars['YDL_EXTRACT_AUDIO_FORMAT'] = 'best'

    final_dir = request_options.get('final_dir')
    if final_dir and final_dir != '':
        if not os.path.isdir(final_dir):
            os.makedirs(final_dir)
        if os.path.isdir(final_dir):
            request_vars['YDL_OUTPUT_TEMPLATE'] = final_dir + '%(title)s.%(ext)s'
            print(f'Set output directory to {final_dir} [src:final_dir].')
        else:
            print(f'Error: Output directory `{final_dir}` does not exist. Falling back to default.')
            request_vars['YDL_OUTPUT_TEMPLATE'] = app_defaults['YDL_OUTPUT_TEMPLATE']
    else:
        request_vars['YDL_OUTPUT_TEMPLATE'] = app_defaults['YDL_OUTPUT_TEMPLATE']
    
    filename = request_options.get('fname')
    if filename and filename != '':
        if not glob.glob(filename + '.*'):
            request_vars['YDL_OUTPUT_TEMPLATE'] = request_vars.get('YDL_OUTPUT_TEMPLATE').replace('%(title)s', filename)
            print(f'Set output file name to {filename} [src:filename]')
        else:
            print(f'Error: Output directory `{final_dir}` already contains a file named `{filename}`.')

    ydl_vars = ChainMap(request_vars, os.environ, app_defaults)

    postprocessors = []

    if (ydl_vars['YDL_EXTRACT_AUDIO_FORMAT']):
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': ydl_vars['YDL_EXTRACT_AUDIO_FORMAT'],
            'preferredquality': ydl_vars['YDL_EXTRACT_AUDIO_QUALITY'],
        })

    return {
        'format': ydl_vars['YDL_FORMAT'],
        'postprocessors': postprocessors,
        'outtmpl': ydl_vars['YDL_OUTPUT_TEMPLATE'],
        'download_archive': ydl_vars['YDL_ARCHIVE_FILE']
    }


def download(url, request_options):
    with youtube_dl.YoutubeDL(get_ydl_options(request_options)) as ydl:
        ydl.download([url])


def tag(filepath, artist=None, title=None, album=None):
    try:
        print('Tagging file.')
        song = taglib.File(filepath)
        if artist:
            song.tags['ARTIST'] = [artist]
            print('Added `artist` tag.')
        if title:
            song.tags['TITLE'] = [title]
            print('Added `title` tag.')
        if album:
            song.tags['ALBUM'] = [album]
            print('Added `album` tag.')
        song.save()
    except Exception as e:
        print(f'Error: Exception while tagging {filepath}.')
        print(e)
        pass



dl_q = Queue()
done = False
dl_thread = Thread(target=dl_worker)
dl_thread.start()

print("Updating youtube-dl to the newest version")
updateResult = update()
print(updateResult["output"])
print(updateResult["error"])

print("Started download thread")

app_vars = ChainMap(os.environ, app_defaults)

app.run(host=app_vars['YDL_SERVER_HOST'], port=app_vars['YDL_SERVER_PORT'], debug=True)
done = True
dl_thread.join()
