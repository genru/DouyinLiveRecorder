# coding=utf-8
"""
:author: Lyzen
:date: 2023.04.03
:brief: app主文件
"""

import os
import signal
import sys
import logging
import platform
import threading
import atexit

from dylr.core import version, config, record_manager, monitor
from dylr.util import logger
from dylr.plugin import plugin
from flaskr.client import Worker

win_mode = False
win = None
# 处理 ctrl+c
stop_all_threads = False
threads = []
worker = None

def init(gui_mode: bool):
    global win_mode
    global threads

    win_mode = gui_mode
    # 处理 ctrl+c
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    # atexit.register(app_onexit)

    if not check_dependencies():
        return

    plugin.on_open(gui_mode)

    logger.info(f'software started. version: {version}. gui: {gui_mode}.')
    logger.info(f'platform: {platform.platform()}')
    logger.info(f'python version: {platform.python_version()}')

    print('=' * 80)
    print(f'Douyin Live Recorder v.{version} by Lyzen')
    print(f'软件仅供科研数据挖掘与学习交流，因错误使用而造成的危害由使用者负责。')
    print('=' * 80)

    config.read_configs()
    if config.debug():
        logger.instance.setLevel(logging.DEBUG)
    record_manager.rooms = config.read_rooms()

    plugin.on_loaded(gui_mode)

    """ start client """
    global worker;
    worker = Worker(config.get_worker_name(), config.get_worker_manager_url())
    worker.start()

    monitor.init()


def sigint_handler(signum, frame):
    global stop_all_threads
    global threads
    logger.info_and_print(f'sigint thread len={len(threads)}')
    if threads is None:
        threads = []
    stop_all_threads = True
    logger.fatal_and_print('catched SIGINT(Ctrl+C) signal')
    # for t in threads:
    #     t.join()
    plugin.on_close()

def app_onexit():
    global stop_all_threads
    global threads
    if threads is None: threads = []
    stop_all_threads = True
    logger.fatal_and_print(f'app exiting... threads: %s' %len(threads))
    # for t in threads:
        # t.join()
    plugin.on_close()


def check_dependencies():
    has_requests = True
    has_websocket = True
    has_protobuf = True
    has_flask = True
    try:
        import requests
    except:
        has_requests = False
    try:
        import websocket
    except:
        has_websocket = False
    try:
        import google.protobuf
    except:
        has_protobuf = False
    try:
        import Flask
    except:
        has_flask = False

    if has_requests and has_websocket and has_protobuf:
        return True
    res = []
    if not has_requests:
        res.append('requests')
    if not has_websocket:
        res.append('websocket-client')
    if not has_protobuf:
        res.append('protobuf')
    if not has_flask:
        res.append('flask')

    return False
