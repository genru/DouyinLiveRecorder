"""
:author: Lyzen
:date: 2023.04.23
:brief: 通过 Web_Rid、直播间地址、直播间短链、主播主页 获取主播房间信息
"""
import json
import random
import re
import time
import threading
import traceback
from functools import partial

try:
    from tkinter import messagebox
except:
    print('ignore')

import requests

# Web_Rid 纯数字
from dylr.core import record_manager, app, dy_api, config, monitor
from dylr.core.room import Room
from dylr.util import logger

re_num = re.compile(r'^\d*$')
# 使用 Web_Rid 的网址
re_live = re.compile(r'^(http:|https:)?(//)?live.douyin.com/\d*')
# 短链
re_short = re.compile(r'^(http:|https:)?(//)?v.douyin.com/')
# 用户主页
re_user = re.compile(r'^(http:|https:)?(//)?(www.)?douyin.com/user/')


def try_add_room(info):
    try:
        if re_num.match(info):
            find_by_web_rid(info)
            return
        elif re_live.match(info):
            find_live(info)
            return
        elif re_short.match(info):
            find_short(info)
            return
        elif re_user.match(info):
            find_user(info)
            return
    except Exception:
        logger.error_and_print("添加主播失败，请确认输入的内容是否符合要求\n如果符合要求，可能是接口失效，请换种方式。")
        logger.error_and_print(traceback.format_exc())


def find_live(info):
    """ live.douyin.com/xxx """
    info = info[info.index('.com/') + 5:]
    if '?' in info:
        info = info[:info.index('?')]
    find_by_web_rid(info)


def find_by_web_rid(web_rid):
    """ web_rid number """
    room = record_manager.get_room(web_rid)
    if room is not None:
        logger.error_and_print(f'重复获取主播房间: {room.room_name}({web_rid})')
        return

    api_url = dy_api.get_api_url(web_rid)
    req = requests.get(api_url, headers=dy_api.get_request_headers(), proxies=dy_api.get_proxies())
    json_info = json.loads(req.text)
    name = json_info['data']['user']['nickname']

    if name is None or len(name) == 0:
        raise Exception()
    room = Room(web_rid, name, True, False, False)
    record_manager.rooms.append(room)
    config.save_rooms()

    logger.info_and_print(f'成功获取到房间{name}({web_rid})')

    # 添加完房间立刻检查是否开播
    t = threading.Thread(target=partial(monitor.check_room, room))
    app.threads.append(t)
    t.start()


def find_short(info):
    """ v.douyin.com/xxx """
    find_by_web_rid(dy_api.get_web_rid_from_short_url(info))


def find_user(info: str):
    """ www.douyin.com/user/xxx """
    sec_user_id = info[info.rfind('/')+1:]
    nickname, web_rid = dy_api.get_user_info(sec_user_id)
    if nickname is None:
        return
    if web_rid is not None:
        find_by_web_rid(web_rid)
    else:
        room = Room(f"将会在开播时获取{random.randint(1, 100000000)}", nickname, True, False, False, sec_user_id)
        record_manager.rooms.append(room)
        config.save_rooms()
