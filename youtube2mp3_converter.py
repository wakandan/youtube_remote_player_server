import urllib
import urllib2
import re
import sys

if len(sys.argv)<2:
    print "need video id"
    sys.exit(1)

video_id = sys.argv[1]
response = urllib2.urlopen("http://www.youtube-mp3.org/a/pushItem/?item=https://www.youtube.com/watch?v="+video_id)
data = response.read()
#ignore this reponse and send the second request
response = urllib2.urlopen("http://www.youtube-mp3.org/a/itemInfo/?video_id="+video_id)
data = response.read()
result = re.search("[\w\d]{32}", data)
hash_value = result.group(0)
final_download_link = "http://www.youtube-mp3.org/get?video_id=%s&h=%s" % (video_id, hash_value)
print final_download_link

class AppURLopener(urllib.FancyURLopener):
    version = "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101230 Mandriva Linux/1.9.2.13-0.2mdv2010.2 (2010.2) Firefox/3.6.13"

opener = AppURLopener()

fp = opener.open(final_download_link)
data = fp.read(1024)
while data:
  sys.stdout.write(data)
  data = fp.read(1024)
fp.close()


