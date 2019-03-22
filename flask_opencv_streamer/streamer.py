"""Stores a Streamer class"""
import time
from functools import wraps
from threading import Thread
from cryptography.fernet import Fernet

import cv2
from flask import Flask, Response, render_template, request

from .login_manager import LoginManager


class Streamer:
    """A clean wrapper class for a Flask OpenCV Video Streamer"""

    def __init__(
        self,
        port,
        requires_auth,
        stream_res=(1280, 720),
        frame_rate=30,
        login_file="logins",
        login_key=".login",
    ):
        self.flask_name = "{}_{}".format(__name__, port)
        self.login_file = login_file
        self.login_key = login_key
        self.flask = Flask(self.flask_name)
        self.frame_to_stream = None
        self.guest_password = None
        self.password_create_time = None
        self.thread = None
        self.is_streaming = False
        self.port = port
        self.req_auth = requires_auth
        self.stream_res = stream_res
        self.frame_rate = frame_rate
        if requires_auth:
            self.generate_guest_password()
            self.login_manager = LoginManager(login_file, login_key)

    def __getstate__(self):
        """An override for loading this object's state from pickle"""
        ret = {
            "flask_name": self.flask_name,
            "port": self.port,
            "req_auth": self.req_auth,
            "stream_res": self.stream_res,
            "login_file": self.login_file,
            "login_key": self.login_key,
        }
        return ret

    def __setstate__(self, dict_in):
        """An override for pickling this object's state"""
        self.flask_name = dict_in["flask_name"]
        self.flask = Flask(self.flask_name)
        self.frame_to_stream = None
        self.guest_password = None
        self.password_create_time = None
        self.thread = None
        self.is_streaming = False
        self.port = dict_in["port"]
        self.req_auth = dict_in["req_auth"]
        self.stream_res = dict_in["stream_res"]
        if self.req_auth:
            self.generate_guest_password()
            self.login_manager = LoginManager(
                dict_in["login_file"], dict_in["login_key"]
            )

    def start_streaming(self):
        """Starts the video stream hosting process"""
        gen_function = self.gen

        @self.flask.route("/video_feed")
        @self.requires_auth
        def video_feed():
            """The response for <url>/video_feed"""
            return Response(
                gen_function(), mimetype="multipart/x-mixed-replace; boundary=frame"
            )

        @self.flask.route("/")
        @self.requires_auth
        def index():
            """The response for <url>"""
            return render_template("index.html")

        self.thread = Thread(
            daemon=True,
            target=self.flask.run,
            kwargs={
                "host": "0.0.0.0",
                "port": self.port,
                "debug": False,
                "threaded": True,
            },
        )
        self.thread.start()
        self.is_streaming = True

    def update_frame(self, frame):
        """Updates the frame for streaming"""
        self.frame_to_stream = self.get_frame(frame)

    def get_frame(self, frame):
        """Encodes the OpenCV image to a 1280x720 image"""
        _, jpeg = cv2.imencode(
            ".jpg",
            cv2.resize(frame, self.stream_res),
            params=(cv2.IMWRITE_JPEG_QUALITY, 70),
        )
        return jpeg.tobytes()

    def gen(self):
        """A generator for the image."""
        while True:
            frame = self.frame_to_stream
            time.sleep(1 / self.frame_rate)
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n"
            )

    def check_auth(self, username, password):
        """Dummy thing to check password"""
        # Generate a password if there is no password OR the one given is older than 24hrs
        if (
            self.guest_password is None
            or (time.time() - self.password_create_time) > 86400
        ) and self.req_auth:
            self.generate_guest_password()
        # Refresh the login manager's logins from the disk, in case a new login has been generated
        self.login_manager.logins = self.login_manager.load_logins()
        # Check the login manager for a match first
        if username in list(self.login_manager.logins.keys()):
            return password == self.login_manager.logins[username]

        # Otherwise check if it's the guest acct
        return username == "guest" and password == self.guest_password

    def authenticate(self):
        """Sends a 401 response that enables basic auth"""
        return Response(
            "Authentication Failed\nPlease reload to log in with proper credentials",
            401,
            {"WWW-Authenticate": 'Basic realm="Login Required"'},
        )

    def requires_auth(self, func):
        """A custom decorator for Flask streams"""

        @wraps(func)
        def decorated(*args, **kwargs):
            if self.req_auth:
                auth = request.authorization
                if not auth or not self.check_auth(auth.username, auth.password):
                    return self.authenticate()
                return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return decorated

    def generate_guest_password(self):
        """Generates and prints a random password on creation"""
        print("Generating Flask password")
        self.guest_password = str(Fernet.generate_key().decode())
        self.password_create_time = time.time()
        print(
            "Password for stream on Port: {} is\n    {}".format(
                self.port, self.guest_password
            )
        )
