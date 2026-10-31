"""Per-user/session single-instance handoff using Qt local sockets."""
import hashlib
import json
import os
from pathlib import Path
import time

from PySide6.QtCore import QObject, QLockFile, QStandardPaths, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    open_requested = Signal(str)

    def __init__(self, parent=None, identity=None):
        super().__init__(parent)
        session = os.environ.get('WAYLAND_DISPLAY', os.environ.get('DISPLAY', 'desktop'))
        key = hashlib.sha256((identity or f'{Path.home()}:{session}').encode()).hexdigest()[:20]
        runtime = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.RuntimeLocation))
        runtime.mkdir(parents=True, exist_ok=True)
        self.name = f'still-player-v1-{key}'
        self.lock = QLockFile(str(runtime / (self.name + '.lock')))
        self.lock.setStaleLockTime(0)
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.newConnection.connect(self.accept_connections)
        self._connections = {}
        self._owns_lock = False

    def forward(self, filename):
        socket = QLocalSocket()
        socket.connectToServer(self.name)
        if not socket.waitForConnected(100):
            return False
        payload = json.dumps({'open': filename}, ensure_ascii=False).encode('utf-8') + b'\n'
        socket.write(payload)
        socket.flush()
        reply = b''
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            reply += bytes(socket.readAll())
            if b'\n' in reply:
                socket.disconnectFromServer()
                if reply.split(b'\n')[0] != b'OK':
                    raise RuntimeError('The running Still window could not open this request.')
                return True
            socket.waitForReadyRead(100)
        socket.abort()
        raise RuntimeError('The running Still window did not respond. Close it and try again.')

    def start_or_forward(self, filename=''):
        if self.forward(filename):
            return True
        deadline = time.monotonic() + 5
        while not self.lock.tryLock(0):
            if self.forward(filename):
                return True
            if time.monotonic() >= deadline:
                raise RuntimeError('Still is starting or not responding. Please try again shortly.')
            time.sleep(0.025)
        self._owns_lock = True
        # Only the process holding the lock may remove a socket left by a crash.
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            self.close()
            raise RuntimeError(self.server.errorString())
        return False

    def accept_connections(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            timer_id = id(socket)
            self._connections[timer_id] = (socket, bytearray())
            socket.readyRead.connect(lambda key=timer_id: self.read_request(key))
            socket.disconnected.connect(lambda key=timer_id: self.drop_connection(key))
            self.read_request(timer_id)

    def read_request(self, key):
        entry = self._connections.get(key)
        if entry is None:
            return
        socket, data = entry
        data.extend(bytes(socket.readAll()))
        if len(data) > 32768:
            socket.abort()
            return
        if b'\n' not in data:
            return
        try:
            request = json.loads(bytes(data).split(b'\n', 1)[0])
            filename = request['open']
            if not isinstance(filename, str):
                raise ValueError('Invalid request')
            self.open_requested.emit(filename)
            socket.write(b'OK\n')
        except (ValueError, KeyError, TypeError):
            socket.write(b'ERROR\n')
        socket.flush()
        socket.disconnectFromServer()

    def drop_connection(self, key):
        entry = self._connections.pop(key, None)
        if entry:
            entry[0].deleteLater()

    def close(self):
        for socket, _ in list(self._connections.values()):
            socket.abort()
        self._connections.clear()
        self.server.close()
        if self._owns_lock:
            self.lock.unlock()
            self._owns_lock = False
