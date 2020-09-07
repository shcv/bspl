from threading import Thread
from queue import Queue


def unbundle(bundle):
    return bundle


def decode(msg):
    return json.loads(msg)


class Receiver:
    """An Receiver just needs the send(message) method."""

    def __init__(self, listener, decoder=decode, unbundler=unbundle):
        """Each component is a function that """
        self.decode = decoder
        self.unbundle = unbundler
        self.listen = listener
        self.queue = Queue()
        self.listen_thread = Thread(target=self.listen, args=(self.queue,))
        self.process_thread = Thread(target=self.process)

    def start(self, adapter):
        """Start loop for transmitting messages in outgoing queue"""
        self.adapter = adapter
        self.listen_thread.start()
        self.process_thread.start()

    def process(self):
        while True:
            data = self.recv_q.get()
            bundle = self.decode(data)
            messages = self.unbundle(bundle)
            for m in messages:
                self.adapter.recv_q.put(m)


def udp_listener(IP, port):
    def listener(queue):
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind((IP, port))  # (IP, port)

        while True:
            data, addr = sock.recvfrom(1500)  # buffer size is 1500 bytes
            queue.put(data)
    return listener
