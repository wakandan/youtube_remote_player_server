import bottle
from bottle import route, run, template, response
import subprocess
import shlex 
import os
from subprocess import Popen, PIPE

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


app = bottle.app()

p = None
download_pipe = None
mp3_pipe = None
playlist = []
current_song = None

@route('/stop', method=['OPTIONS', 'GET'])
def stop():
    '''just terminate all pipes'''
    global download_pipe 
    global mp3_pipe 


    if download_pipe is not None:
        download_pipe.terminate()

    if mp3_pipe is not None:
        mp3_pipe.terminate()

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
    return {'playlist': playlist}

@route('/play/<url>', method=['OPTIONS', 'GET'])
def play(url=''):
    '''do a pipe play'''
    global download_pipe 
    global mp3_pipe 
    
    print 'playing video id: '+url
    
    playlist.append(url)
    current_song = url 

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
    print 'playing...'
    return "playing..." 

app.install(EnableCors())
app.run(host='0.0.0.0', port=8080)


