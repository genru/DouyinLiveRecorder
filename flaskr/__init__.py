import os
from flask import Flask, jsonify, request
from dylr.core import app as dylr_app, add_room_manager, transcode_manager
from flaskr import route
from flaskr.client import Worker
# from dylr.core import add_room_manager, record_manager

worker = None

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # app.cli.add_command(transcode_manager.ffmpeg_bin_exist)

    """ initialize routes """
    app = route.init(app)

    """ initialize dylr modules """
    dylr_app.init(False)

    """ start client """
    global worker;
    worker = Worker('client 1', 'ws://localhost:8080')
    worker.start()
    return app
