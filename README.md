youtube_remote_player_server
============================

The server part of my youtube remote player. It's build on 
- python's bottle as simple REST server
- in the back end, youtube video is played using shell command. I was trying 2 ways of playing a video 1)download the video directly using youtube-dl, an awesome cli command to extract video info from a youtube url and 2) download the video's mp3 part from a 3rd party server. The second one is better and faster for preserving bandwidth


client part is here https://github.com/wakandan/youtube_remote_player_client.git
