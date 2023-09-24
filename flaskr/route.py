from flask import jsonify, request
from dylr.core import app as dylr_app, add_room_manager, record_manager, transcode_manager
from dylr.util import logger

def init(app):
    @app.route('/ping')
    def ping():
        return 'pong'

    @app.route('/test')
    def test():
        b = transcode_manager.transcode('download/杰哥哥🔥爱美食/20230924_010951.flv')
        logger.info(f'test %s' % b)
        return str(b)

    @app.route('/rooms', methods=['POST', 'GET'])
    def rooms_handler():
        try:
            if request.method == 'POST':
                data = request.json
                create_room(data["room"])
                return ok(data)
            if request.method == 'GET':
                is_recording = request.args.get('recording', 'false')
                objarr = read_rooms(is_recording)
                return ok(objarr)
            else:
                return error(-2, "bad request")
        except Exception as e:
            print(str(e))
            return error()

    return app

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

