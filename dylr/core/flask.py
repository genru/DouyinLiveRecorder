from flask import Flask, request, jsonify
from threading import Thread
from dylr.util import logger
from dylr.core import add_room_manager, app, record_manager, config

web = Flask(__name__)
t = None

@web.route('/ping')
def ping():
    return ok("pong")

@web.route('/rooms', methods=['POST', 'GET'])
def rooms_handler():
    try:
        if request.method == 'POST':
            data = request.json
            # logger.debug(f'create room: {data["room"]}')
            create_room(data["room"])
            return ok(data)
        if request.method == 'GET':
            is_recording = request.args.get('recording', 'false')
            # logger.debug(f'get rooms, recording: {is_recording}')
            objarr = read_rooms(is_recording)
            return ok(objarr)
        else:
            return error(-2, "bad request")
    except Exception as e:
        logger.error(str(e))
        return error()

"""
get room info
"""
@web.route('/room/<room_id>', methods=['GET', 'DELETE', 'UPDATE'])
def room_handler(room_id):
    try:
        if request.method == 'GET':
            room = read_room(room_id)
            if room is None:
                return error(-404, "no room found")
            return ok(room)
        if request.method == 'DELETE':
            ret = remove_room(room_id)
            resp = ok(ret) if ret==0 else error(ret)
            return resp
        if request.method == 'UPDATE':
            room = request.get_json('room')
            room.id = room_id
            ret = update_room(room)
            resp = ok(ret) if ret==0 else error(ret)
            return resp
        else:
            return error(-400, "bad request")
    except Exception as e:
        return error(-1, str(e))

def create_room(room_data):
    return add_room_manager.try_add_room(room_data)

def read_rooms(is_recording):
    if is_recording == '1' or is_recording.lower() == "true":
        rooms = [row.room for row in record_manager.get_recordings()]
    else:
        rooms = record_manager.get_rooms()
    return [{"name":row.room_name, "id": row.room_id, "auto_record": row.auto_record} for row in rooms]

def read_room(id):
    room = record_manager.get_room(id)
    if room is None:
        return None
    b = record_manager.is_recording(room)
    return {"name": room.room_name, "id": room.room_id, "is_recording": b}

def remove_room(id):
    room = record_manager.get_room(id)
    if room is None:
        return -404
    record_manager.rooms.remove(room)
    config.save_rooms()
    return 0

def update_room(room):
    if room is None:
        return -1
    if 'id' not in room:
        return -2

    r = record_manager.get_room(room['id'])
    if r is None:
        return -404
    r.auto_record = room['auto_record']
    config.save_rooms()
    return 0

def ok(data=None):
    return jsonify({"code": 0, "message":"successful", "data":data})

def error(code=-1, message="unexpected error"):
    if code == -404:
        message = "not found"
    return jsonify({"code":code, "message":message})


def start_server():
    global t
    t = Thread(target=web.run, args=('0.0.0.0', 8000))
    t.setDaemon(True)
    t.start()
    # server = Process(target=web.run, args=('0.0.0.0', 8000))
    # server.start()
    # logger.info('start_server')
    # web.run(host="0.0.0.0", port=8000, debug=True)
    logger.info('start done')

def stop_server():
    global t
    # server.terminate()
    # server.join()
    # func = request.environ.get('werkzeug.server.shutdown')
    # if func is None:
        # raise RuntimeError('Not running with the Werkzeug Server')
    # func()
    return
