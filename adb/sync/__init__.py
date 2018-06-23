import struct
import time
import os

from adb.protocol import Protocol
from adb.sync.stats import S_IFREG

import logging

logger = logging.getLogger(__name__)


class Sync:
    TEMP_PATH = '/data/local/tmp'
    DEFAULT_CHMOD = 0o644
    DATA_MAX_LENGTH = 65536

    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def temp(path):
        return "{}/{}".format(Sync.TEMP_PATH, os.path.basename(path))

    def push(self, src, dest, mode):
        stream = open(src, 'rb')
        timestamp = int(time.time())

        # SEND
        mode = mode | S_IFREG
        args = "{dest},{mode}".format(
            dest=dest,
            mode=mode
        )
        self._send_str(Protocol.SEND, args)

        # DATA
        while True:
            chunk = stream.read(self.DATA_MAX_LENGTH)
            if not chunk:
                break

            self._send_length(Protocol.DATA, len(chunk))
            self.connection.write(chunk)

        # DONE
        self._send_length(Protocol.DONE, timestamp)
        self.connection._check_status()

    def pull(self, src, dest):
        stream = open(dest, 'wb')
        error = None

        # RECV
        self._send_str(Protocol.RECV, src)

        # DATA
        while True:
            flag = self.connection.read(4).decode('utf-8')

            if flag == Protocol.DATA:
                data = self._read_data()
                stream.write(data)
            elif flag == Protocol.DONE:
                self.connection.read(4)
                break
            elif flag == Protocol.FAIL:
                error = self._read_data()

        return error

    def _integer(self, little_endian):
        return struct.unpack("<I", little_endian)

    def _little_endian(self, n):
        return struct.pack('<I', n)

    def _read_data(self):
        length = self._integer(self.connection.read(4))[0]
        return self.connection.read(length)

    def _send_length(self, cmd, length):
        le_len = self._little_endian(length)
        data = cmd.encode() + le_len

        logger.debug("Send length: {}".format(data))
        self.connection.write(data)

    def _send_str(self, cmd, args):
        """
        Format:
            {Command}{args length(little endian)}{str}
        Length:
            {4}{4}{str length}
        """
        logger.debug("{} {}".format(cmd, args))
        args = args.encode('utf-8')

        le_args_len = self._little_endian(len(args))
        data = cmd.encode() + le_args_len + args
        logger.debug("Send string: {}".format(data))
        self.connection.write(data)
