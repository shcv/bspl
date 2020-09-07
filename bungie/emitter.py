from threading import Thread
from cronus.beat import Beat
from collections import deque
import json


class Bundle:
    def __init__(self, max_size):
        self.max_size = max_size
        self.contents = b''

    def add(message):
        """
        Add a message to contents, using ',' as the separator.
        """
        if len(self.contents) > 0:
            self.contents += b',' + message
        else:
            self.contents = message

    def test(message):
        if len(self.contents + message + 2) <= max_size:
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
        beat.set_rate(2)
        while beat.true():
            callback()
            beat.sleep()
    return handler


class Emitter:
    """An Emitter just needs the send(message) method."""

    def __init__(self, transmitter, encoder=encode, bundler=bundle, controller=simple_rate(500), mtu=1500):
        """Each component is a function that """
        self.encode = encoder
        self.bundle = bundler
        self.transmit = transmitter
        self.queue = deque()
        self.thread = Thread(target=self.process)

    def start(self):
        """Start loop for transmitting messages in outgoing queue"""
        self.thread.start()

    def send(self, message):
        # Do mangling and encoding first; then bundler can process the queue directly
        m = self.encode(message)
        self.queue.append(m)

    def process(self):
        if len(queue) > 0:
            bun = self.bundle(self.mtu, self.queue)
            self.transmit(bun)


def udp_transmitter(message):
    data = json.dumops(message.payload).encode('utf-8')
    if len(data) > 1500-48:  # ethernet MTU - IPv6 + UDP header
        logger.info("Message too long: {}".format(data))

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.sendto(data, message.dest)
