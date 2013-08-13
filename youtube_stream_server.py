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
import gobject

YOUTUBE2_MP3_LINK1 = "http://www.youtube-mp3.org/a/pushItem/?item=https://www.youtube.com/watch?v="
YOUTUBE2_MP3_LINK2 = "http://www.youtube-mp3.org/a/itemInfo/?video_id="
YOUTUBE2_MP3_LINK3 = "http://www.youtube-mp3.org/get?video_id=%s&h=%s"


class Player:
    '''player maintain a playlist.  '''
    def __init__(self):    
        self.playlist = []
        self.current_song = 0
                            
        #this only works with playbin2
        self.player = gst.element_factory_make("playbin2", "player")
        self.player.connect("about-to-finish", self.on_about_to_finish)

    def is_playing(self):
        return self.player.get_state()==gst.STATE_PLAYING

    def run(self):
        self.player.set_state(gst.STATE_PLAYING)

    def on_about_to_finish(self, player):
        '''The current song is about to finish, if we want to play another
        song after this, we have to do that now'''
        self.play_next()

    def stop(self):
        self.player.set_state(gst.STATE_READY)

    def play_next(self):
        '''play the next song if available'''
        if self.current_song<len(self.playlist):
            self.current_song += 1
            song_url = self.playlist[self.current_song]
            self.stop()
            self.player.set_property('uri', song_url)
            self.player.set_state(gst.STATE_PLAYING)
            
    def play_prev(self):
        '''play the previous song if there's any'''
        if self.current_song>0 and len(self.playlist)>0:
            self.current_song -= 1
            song_url = self.playlist[self.current_song]
            self.stop()
            self.player.set_property('uri', song_url)
            self.player.set_state(gst.STATE_PLAYING)

    def get_mp3_link(self, video_id):
        '''get mp3 link from a youtube video id using youtube2mp3 service'''
        response = urllib2.urlopen(YOUTUBE2_MP3_LINK1+video_id)
        data = response.read()
        #ignore this reponse and send the second request
        response = urllib2.urlopen(YOUTUBE2_MP3_LINK2+video_id)
        data = response.read()      
        result = re.search("[\w\d]{32}", data)
        #the video was converted
        if result is not None:
            hash_value = result.group(0)
            final_download_link =  YOUTUBE2_MP3_LINK3 % (video_id, hash_value)
            return final_download_link
        else:
            return None

    def add_song_id(self, song_id):         
        '''add a song into this playlist, return false if not possible'''

        song_url = self.get_mp3_link(song_id)
        print 'adding song id ',song_id
        if song_url == None:
            print 'unable to get mp3 link for song id', song_id
            return False
        else: 
            print 'appending song %s to playlist' % song_id
            self.playlist.append(song_url)
            if len(self.playlist)==1:
                print 'playing song ', song_id
                self.player.set_property('uri', song_url)
                self.run()
            else: 
                print 'adding, not playing'
                print 'current playlist', self.playlist
            return True


#creates a playbin (plays media form an uri) 
player = Player()

def stop_playing_w_pipe():
    '''@depreciated'''
    '''just terminate all pipes'''
    global download_pipe 
    global mp3_pipe 


    if download_pipe is not None:
        download_pipe.terminate()

    if mp3_pipe is not None:
        mp3_pipe.terminate()


def play_mp3_link_w_pipe(mp3_link):
    '''@depreciated'''
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
    player.stop()


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
    global player 
    return {'playlist': player.playlist}


@route('/play/<video_id>', method=['OPTIONS', 'GET'])
def play(video_id=''):
    global  player
    if video_id!=None:
        player.add_song_id(video_id)
    else: 
        player.run()
    return "playing..." 

@route('/next', method=['OPTIONS', 'GET'])
def next():
    global player
    player.play_next()

@route('/prev', method=['OPTIONS', 'GET'])
def next():
    global player
    player.play_prev()

app = bottle.app()
app.install(EnableCors())
app.run(host='0.0.0.0', port=8080)


