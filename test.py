from flask_opencv_streamer.streamer import Streamer
from time import sleep

s = Streamer(80, True, "logins.txt", ".login")
s.start_streaming()

while True:
    try:
        sleep(1 / 30)
    except KeyboardInterrupt:
        break
