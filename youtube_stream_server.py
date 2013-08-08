import bottle
from bottle import route, run, template, response
import subprocess
import shlex 
import os
from subprocess import Popen, PIPE
import pygst
pygst.require("0.10")
import gst
import urllib
import urllib2
import re
import sys

YOUTUBE2_MP3_LINK1 = "http://www.youtube-mp3.org/a/pushItem/?item=https://www.youtube.com/watch?v="
YOUTUBE2_MP3_LINK2 = "http://www.youtube-mp3.org/a/itemInfo/?video_id="
YOUTUBE2_MP3_LINK3 = "http://www.youtube-mp3.org/get?video_id=%s&h=%s"

#creates a playbin (plays media form an uri) 
PLAYER = gst.element_factory_make("playbin", "player")

#define global variables 
p = None
download_pipe = None
mp3_pipe = None
playlist = []
current_song = None

def play_mp3_link(mp3_link):
    '''stream the mp3 file'''
    global PLAYER
    #set the uri
    PLAYER.set_property('uri', mp3_link)

    #start playing
    PLAYER.set_state(gst.STATE_PLAYING)


def stop_playing_w_pipe():
    '''just terminate all pipes'''
    global download_pipe 
    global mp3_pipe 


    if download_pipe is not None:
        download_pipe.terminate()

    if mp3_pipe is not None:
        mp3_pipe.terminate()


def play_mp3_link_w_pipe(mp3_link):
    '''mp3 playing using pipeline'''
    if download_pipe is not None:
        download_pipe.terminate()
    print os.getcwd()+'/youtube2mp3_converter.py'
    download_pipe = Popen(['python', os.getcwd()+'/youtube2mp3_converter.py', url], stdout=PIPE) 

    if mp3_pipe is not None:
        mp3_pipe.terminate()
    mp3_pipe = Popen(shlex.split('mpg123 -'), stdin=download_pipe.stdout)   
    playing_check = mp3_pipe.poll()
    if playing_check is not None or playing_check!=0:
        print 'error while playing the file'
        return 'error while playing the file'


def get_mp3_link(video_id):
    '''get mp3 link from a youtube video id using youtube2mp3 service'''
    response = urllib2.urlopen(YOUTUBE2_MP3_LINK1+video_id)
    data = response.read()
    #ignore this reponse and send the second request
    response = urllib2.urlopen(YOUTUBE2_MP3_LINK2+video_id)
    data = response.read()
    result = re.search("[\w\d]{32}", data)
    hash_value = result.group(0)
    final_download_link =  YOUTUBE2_MP3_LINK3 % (video_id, hash_value)
    return final_download_link


class EnableCors(object):
    '''bottle plugin to enable cross-domain-access-control'''
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


@route('/stop', method=['OPTIONS', 'GET'])
def stop():
    PLAYER.set_state(gst.STATE_READY)


@route('/check', method=['OPTIONS', 'GET'])
def check():
    global mp3_pipe
    if mp3_pipe is not None:
        # sub process has not return, therefore there's no return code
        if mp3_pipe.poll() is None:
            return 'still playing...'
        else: 
            playlist.remove(current_song)
    return 'no file playing'


@route('/playlist', method=['OPTIONS', 'GET'])
def get_playlist():   
    print playlist
    return {'playlist': playlist}


@route('/play/<video_id>', method=['OPTIONS', 'GET'])
def play(video_id=''):
    print 'playing video id: '+video_id
    playlist.append(video_id)
    current_song = video_id 

    #get the mp3 link 
    mp3_link = get_mp3_link(video_id)
    play_mp3_link(mp3_link)
    return "playing..." 

app = bottle.app()
app.install(EnableCors())
app.run(host='0.0.0.0', port=8080)


