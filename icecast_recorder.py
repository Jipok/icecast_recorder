#!/usr/bin/env python3
import os
import sys
import traceback
from urllib.request import Request, urlopen
from time import time
from datetime import timedelta

if len(sys.argv) != 2:
    print("Usage: icecast_recorder.py <url>")
    sys.exit(1)


# FROM: https://cast.readme.io/docs/icy
# If client sends Icy-MetaData:1 header this means client supports ICY-metadata
stream = urlopen(Request(sys.argv[1], headers={"Icy-MetaData": "1"}), timeout=8)
headers = dict((k.lower(), v) for k, v in stream.getheaders())

# FROM: https://cast.readme.io/docs/icy
# The server should respond icy-metaint: 8192. 8192 is the number
# of bytes between 2 metadata chunks. It is suggested to use this value as some
# players might have issues parsing other values. In these chunks
# StreamTitle='title of the song'; send the new song title. There also is a
# StreamURL field which should be able to also send album art links or more info.
if "icy-metaint" in headers:
    meta_interval = int(headers["icy-metaint"])
else:
    print("!ERROR!\n"
          "Server did not return Icy-Metaint\n"
          "Are you sure the server is Icecast compatible?")
    sys.exit(2)

# Print server information
if "icy-name" in headers:
    print(headers["icy-name"])
if "icy-url" in headers:
    print("URL: ", headers["icy-url"])
if "icy-genre" in headers:
    print("Genre: ", headers["icy-genre"])
if "icy-br" in headers:
    print("Bitrate: ", headers["icy-br"], "kb/s")
print("--------------------------------------------")

file = open("/dev/null", "wb")
start_time = time()
counter = 0

try:
    # Music download loop
    while True:
        metadata = None
        # See shoutcast-metadata.jpg for stream struct
        # Save music chunk
        file.write(stream.read(meta_interval))
        # Get number of blocks with meta information
        blocks = int.from_bytes(stream.read(1), byteorder='big')
        if blocks > 0:
            # Read meta information. Each block == 16 bytes
            raw_data = stream.read(blocks * 16).decode("UTF-8")
            try:
                metadata = {}
                # Parse Key1='Val1';Key2='Val2';
                for pair in raw_data.split(';'):
                    tmp = pair.split('=')
                    if len(tmp) > 1:
                        metadata[tmp[0]] = tmp[1].strip("'")
            except Exception as e:
                pass

        # Processing track change
        if metadata is not None:
            time_offset = timedelta(seconds = round(time() - start_time))
            if "StreamTitle" in metadata:
                stream_title = metadata["StreamTitle"].replace('/', '\\')
                file.close()
                #os.system("mp3check --add-tag --cut-junk-start --cut-junk-end '"+file.name+"' > /dev/null")
                print(str(time_offset) + "   " + stream_title)
                file = open(str(counter) + ". " + stream_title + ".mp3", "wb")
                counter += 1
            else:
                raise Exception("No StreamTitle in meta:", meta_data)

except Exception as e:
    print(traceback.format_exc())
    stream.close()
except KeyboardInterrupt: # Ctrl+C
    stream.close()
