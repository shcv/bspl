import asyncio
import logging
import socket
import json
import ijson
from asyncio.queues import Queue

logger = logging.getLogger('bungie')


def unbundle(bundle):
    return bundle


def decode(msg):
    return json.loads(msg)


class UDPReceiverProtocol:
    def __init__(self, queue):
        self.queue = queue

    def datagram_received(self, data, addr):
        self.queue.put_nowait(data)

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        logger.info(f"Connection lost: {exc}")


class Receiver:
    """An Receiver just needs the send(message) method."""

    def __init__(self, address, decoder=decode, unbundler=unbundle):
        self.address = address
        self.decode = decoder
        self.unbundle = unbundler

    async def task(self, adapter):
        """Start loop for transmitting messages in outgoing queue"""
        self.adapter = adapter
        self.queue = Queue()
        loop = asyncio.get_running_loop()
        print(f"Attempting to bind: {self.address}")
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UDPReceiverProtocol(self.queue),
            local_addr=('0.0.0.0', self.address[1]))
        logger.info(f"Listening on {self.address}")
        loop.create_task(self.process())

    async def process(self):
        while True:
            data = await self.queue.get()
            bundle = self.decode(data)
            messages = self.unbundle(bundle)
            for m in messages:
                await self.adapter.recv_q.put(m)


class TCPReceiver:
    def __init__(self, address, decoder=decode):
        self.address = address
        self.decode = decoder

    async def task(self, adapter):
        self.adapter = adapter
        self.queue = Queue()
        loop = asyncio.get_running_loop()
        loop.create_task(self.process())

        server = await asyncio.start_server(
            self.process,
            *self.address)

        addr = server.sockets[0].getsockname()
        logger.info(f'Listening on {addr}')

        async with server:
            await server.serve_forever()

    async def process(self, reader, writer):
        async for object in ijson.items(reader):
            await self.adapter.recv_q.put(object)
