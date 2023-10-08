from functools import partial
import websocket
import threading
import json
import time
from dylr.core import add_room_manager, config, record_manager
from dylr.util import logger

class Worker:
    def __init__(self, name, server_url, max_task_limit=10):
        self.name = name
        self.server_url = server_url
        self.tasks = [ {"id": room.room_id, "name": room.room_name} for room in record_manager.rooms]
        self.max_task_limit = max_task_limit
        self.heartbeat_interval = 35
        self.reconnect_interval = 10  # Reconnection interval in seconds
        self.max_reconnect_attempts = 5  # Maximum number of reconnection attempts
        self.ws = None
        self.reconnect_attempts = 0

    def on_open(self, ws):
        print(f'Connected to WebSocket server at {self.server_url}')
        # Register the worker with the manager
        registration_message = json.dumps({'type': 'register', 'name': self.name, 'tasks': self.tasks, 'work_load': len(self.tasks)/self.max_task_limit})

        ws.send(registration_message)

        # Reset the reconnect attempt counter on successful connection
        self.reconnect_attempts = 0

        # Start the heartbeat thread
        self.start_heartbeat()

    def on_message(self, ws, message):
        print(f'Received message from server: {message}')
        parsed_message = json.loads(message)
        message_type = parsed_message.get('type')

        if message_type == 'task':
            task = parsed_message.get('task')
            if task:
                self.add_task(task)
                # Handle the task here as needed
        if message_type == 'task_remove':
            task = parsed_message.get('task')
            if task:
                self.remove_task(task)

    def on_close(self, ws, close_status_code, close_msg):
        print(f'WebSocket connection closed with status code {close_status_code}: {close_msg}')
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            print(f'Reconnecting attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {self.reconnect_interval*self.reconnect_attempts} seconds...')
            time.sleep(self.reconnect_interval*self.reconnect_attempts)
            self.connect_to_manager()
        else:
            print(f'Exceeded maximum reconnection attempts. Worker will not reconnect.')

    def send_heartbeat(self):
        while True:
            if self.ws and self.ws.sock and self.ws.sock.connected:
                # tasks should be identical record_manager.rooms
                self.tasks = [ {"id": room.room_id, "name": room.room_name} for room in record_manager.rooms]
                # Prepare the heartbeat message with a task number (e.g., number of tasks in the worker's queue)
                heartbeat_message = json.dumps({'type': 'heartbeat', 'tasks': self.tasks, 'work_load': len(self.tasks)/self.max_task_limit})
                self.ws.send(heartbeat_message)
            time.sleep(self.heartbeat_interval)

    def start_heartbeat(self):
        # Start a separate thread to send heartbeat messages
        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

    def add_task(self, task):
        print('Adding task '+task.get('id'))
        if len(self.tasks) < self.max_task_limit:
            if task not in self.tasks:
                self.tasks.append(task)
                print('Add task b4 try_add_room ')
                add_room_manager.try_add_room(task.get('id'))
                print(f'Added task: {task}')
            else:
                print(f'Task "{task}" already exists in the queue.')
        else:
            print(f'Task queue is full. Task "{task}" not added.')

    def remove_task(self, task):
        print('Removing task '+task.get('id'))
        # self.tasks.remove(task)

        newTasks = [t for t in self.tasks if t.get('id')!=task.get('id')]
        self.tasks = newTasks
        for index, item in enumerate(record_manager.rooms):
            if item.room_id == task.get('id'):
                record_manager.rooms.remove(item)
                config.save_rooms()

    def on_task_started(self, task):
        # print(f'Task started: {task}')
        logger.info_and_print(f'Task started: {task}')
        if self.ws and self.ws.sock and self.ws.sock.connected:
            # Prepare the heartbeat message with a task number (e.g., number of tasks in the worker's queue)
            taskstart_message = json.dumps({'type': 'taskstart', 'task':task})
            self.ws.send(taskstart_message)
        else:
            logger.warning_and_print(f'send task start message failed: no sockets connected')

    def on_task_done(self, task):
        print('Task completed')
        logger.info_and_print(f'Task done: {task}')
        rid = task.get('id')
        url = task.get('url')
        key = task.get('key')
        title = task.get('title')
        if self.ws and self.ws.sock and self.ws.sock.connected:
            # Prepare the heartbeat message with a task number (e.g., number of tasks in the worker's queue)
            taskcomplete_message = json.dumps({'type': 'taskcomplete', 'task':{"id": rid, "url": url, "key":key, "title":title}})
            self.ws.send(taskcomplete_message)
        else:
            logger.warning_and_print(f'send task done message failed: no sockets connected')


    def connect_to_manager(self):
        while self.reconnect_attempts < self.max_reconnect_attempts:
            # Create a new WebSocket connection to the manager
            self.ws = websocket.WebSocketApp(self.server_url,
                                            on_open=self.on_open,
                                            on_message=self.on_message,
                                            on_close=self.on_close)
            # time.sleep(10)
            worker_thread = threading.Thread(target=self.ws.run_forever)
            worker_thread.daemon = True
            worker_thread.start()
            break
        # print(f'Attempting to reconnect to WebSocket server at {self.server_url}...{self.ws.getstatus()}  {teardown}')
        else:
            print(f'Exceeded maximum reconnection attempts. Worker will not reconnect.')

    def start(self):
        self.connect_to_manager()

# if __name__ == "__main__":
#     worker = Worker('Worker1', 'ws://localhost:8080')  # Replace with the WebSocket server URL
#     worker.start()

#     # Keep the program running to allow the WebSocket client to stay connected
#     input("Press Enter to exit...")
