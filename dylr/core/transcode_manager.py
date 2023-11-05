# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.16
:brief: 转码
"""

import os
import subprocess
import sys
import threading
from threading import Thread

from dylr.core import config, app, room, room_info
from dylr.util import logger
from dylr.util.ffmpeg_utils import FFMpegUtils
from dylr.plugin import plugin



# 同时只能有一个项目在转码，防止资源占用过高
lock = threading.Lock()


def start_transcode(room: room.Room, filename: str, room_info: room_info.RoomInfo):
    logger.info_and_print(f'已将 {filename} 加入转码队列')
    t = Thread(target=transcode, args=(filename,room, room_info))
    app.threads.append(t)
    t.start()


def transcode(filename: str, room: room.Room, room_info:room_info.RoomInfo):
    lock.acquire()

    if not ffmpeg_bin_exist():
        logger.error_and_print(f'没有找到ffmpeg可执行文件，无法转码。')
        lock.release()
        return

    logger.info_and_print(f'开始对 {filename} 转码')
    if not os.path.exists(filename):
        logger.info_and_print(f'{filename} does not exist')
        lock.release()
        return

    ffmpeg = FFMpegUtils()
    ffmpeg.input_file(filename)
    output_name = filename[0:filename.rindex('.')] + '.aac'
    ffmpeg.set_no_video();
    ffmpeg.set_output_name(output_name)
    ffmpeg.force_override()
    ffmpeg.set_audio_codec('copy')
    command = ffmpeg.generate()
    if len(config.get_ffmpeg_path()) > 0:
        command = config.get_ffmpeg_path() + '/' + command
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    if config.is_auto_transcode_delete_origin():
        os.remove(filename)
    logger.info_and_print(f'{output_name} 转码完成')
    plugin.on_live_transcoded(room, output_name, room_info)
    lock.release()


def ffmpeg_bin_exist():
    if len(config.get_ffmpeg_path()) > 0:
        ffmpeg_cmd = config.get_ffmpeg_path() + "/ffmpeg -version"
    else:
        ffmpeg_cmd = "ffmpeg -version"
    if sys.version_info >= (3,7):
        r = subprocess.run(ffmpeg_cmd, capture_output=True, shell=True)
    else:
        r = subprocess.run(ffmpeg_cmd, stdout = subprocess.PIPE, shell=True)
    info = str(r.stdout, "UTF-8")
    return 'version' in info
