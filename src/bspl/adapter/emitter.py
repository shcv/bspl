import logging
import socket
import json
from threading import Thread
from cronus.beat import Beat
from collections import deque

logger = logging.getLogger('bungie')


class Bundle:
    def __init__(self, max_size):
        self.max_size = max_size
        self.contents = b''

    def add(self, message):
        """
        Add a message to contents, using ',' as the separator.
        """
        if type(message) is str:
            message = bytes(message, 'utf-8')

        if len(self.contents) > 0:
            self.contents += b',' + message
        else:
            self.contents = message

    def test(self, message):
        if len(self.contents) + len(message) + 2 <= self.max_size:
            return True
        return False

    def pack(self, queue):
        while len(queue) > 0:
            if self.test(queue[0]):
                self.add(queue.popleft())
            else:
                if self.contents:
                    break
                else:
                    raise Exception(
                        'Message is too long to fit in a single packet: {}'.format(queue[0]))

        return b'[' + self.contents + b']'


def bundle(mtu, queue):
    b = Bundle(mtu)
    return b.pack(queue)


def encode(msg):
    return json.dumps(msg.payload, separators=(',', ':'))


def simple_rate(frequency):
    def handler(callback):
        beat = Beat()
        beat.set_rate(frequency)
        while beat.true():
            callback()
            try:
                beat.sleep()
            except:
                pass
    return handler


class Emitter:
    """An Emitter just needs the send(message) method."""

    def __init__(self, transmitter, encoder=encode, bundler=bundle, controller=simple_rate(400), mtu=1500-48):
        """Each component is a function that """
        self.encode = encoder
        self.bundle = bundler
        self.transmit = transmitter
        self.controller = controller
        self.mtu = mtu

        self.channels = {}
        self.thread = Thread(target=self.controller, args=(self.process,))

    def start(self):
        """Start loop for transmitting messages in outgoing queue"""
        self.thread.start()

    def send(self, message):
        # Do mangling and encoding first; then bundler can process the queue directly
        m = self.encode(message)
        logger.info('send requested: {}'.format(m))
        if self.channels.get(message.dest):
            self.channels[message.dest].append(m)
        else:
            self.channels[message.dest] = deque()
            self.channels[message.dest].append(m)

    def process(self):
        for dest, queue in self.channels.items():
            if len(queue) > 0:
                logger.info('messages in queue for {}'.format(dest))
                bun = self.bundle(self.mtu, queue)
                self.transmit(bun, dest)


def udp_transmitter(bun, dest):
    """Send binary-encoded bun via UDP"""
    logger.info('Sending bun {} to {}'.format(bun, dest))
    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_DGRAM)  # UDP
    sock.sendto(bun, dest)
