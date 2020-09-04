import logging
import json
import datetime
from threading import Thread
import sys
import os
import math
import socket
from queue import Queue
from collections import deque
from cronus.beat import Beat
from crontab import CronTab
import croniter
import uuid
import yaml

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger('bungie')


class History:
    def __init__(self):
        self.by_param = {}
        self.by_msg = {}
        self.all_bindings = {}

    def check_integrity(self, message):
        """
        Make sure payload can be received.

        Each message in enactment should have the same keys.
        Returns true if the parameters are consistent with all messages in the matching enactment.
        """
        # may not the most efficient algorithm for large histories
        # might be better to ask the database to find messages that don't match
        enactment = self.enactment(message)
        result = all(message.payload[p] == m[p]
                     for p in message.payload.keys()
                     for m in enactment
                     if p in m)
        if result:
            return enactment

    def check_outs(self, message):
        """
        Make sure none of the outs have been bound.
        Only use this check if the message is being sent.
        """
        enactment = [m for l in self.by_param.get(next(k for k in message.schema.keys), {}).values()
                     for m in l
                     if all(m.payload.get(p) == message.payload.get(p) for p in message.schema.keys)]
        return not any(m.payload.get(p)
                       for m in enactment
                       for p in message.schema.outs)

    def check_dependencies(self, message):
        """
        Make sure that all 'in' parameters are bound and matched by some message in the history
        """
        return not any(message.payload[p] not in self.all_bindings.get(p, {})
                       for p in message.schema.ins)

    def validate_send(self, message):
        if not self.check_outs(message):
            logger.info("Failed out check: {}".format(message.payload))
            return False

        if not self.check_integrity(message):
            logger.info("Failed integrity check: {}".format(message.payload))
            return False

        if not self.check_dependencies(message):
            logger.info("Failed dependency check: {}".format(message.payload))
            return False

        return True

    def observe(self, message):
        """Observe an instance of a given message specification.
           Check integrity, and add the message to the history."""

        # log by message type
        if message.schema in self.by_msg:
            self.by_msg[message.schema].add(message)
        else:
            self.by_msg[message.schema] = {message}

        # record all unique parameter bindings
        for p in message.payload:
            if p in self.all_bindings:
                self.all_bindings[p].add(message.payload[p])
            else:
                self.all_bindings[p] = set([message.payload[p]])

        # log message under each key
        for k in message.schema.keys:
            v = message.payload.get(k)
            if v and self.by_param.get(k):
                if self.by_param[k].get(v):
                    self.by_param[k][v].append(message)
                else:
                    self.by_param[k][v] = [message]
            else:
                self.by_param[k] = {v: [message]}

    def enactment(self, message):
        enactment = {'messages': set()}
        matches = {}
        for k in message.schema.keys:
            if message.payload.get(k):
                matches[k] = self.by_param.get(
                    k, {}).get(message.payload[k], [])
                enactment['messages'].update(matches[k])
                # may need to filter parameters
            else:
                matches[k] = []
        enactment['history'] = matches

        preds = None
        for k in message.schema.keys:
            preds = preds or matches[k]
            preds = filter(lambda m: m.payload.get(
                k) == message.payload.get(k), preds)

        enactment["bindings"] = {
            k: v for m in preds for k, v in m.payload.items()}
        return enactment

    def duplicate(self, message):
        """Return true if payload has been observed before"""
        for k, v in message.payload.items():
            if v in self.by_param.get(k, {}):
                log = self.by_param[k][v]
                if len(log) and all(message.payload.get(p) == m.payload.get(p)
                                    for p in message.payload
                                    for m in log):
                    return True


class Message:
    def __init__(self, schema, payload, enactment=None, duplicate=False):
        self.schema = schema
        self.payload = payload
        self.enactment = enactment
        self.duplicate = duplicate
        self.meta = {
            "ack": False
        }

    def __str__(self):
        if self.enactment and self.duplicate:
            return "Message({}, {}, {}, {})".format(
                self.schema.name, self.payload, self.enactment, self.duplicate)
        elif self.enactment:
            return "Message({}, {}, {})".format(
                self.schema.name, self.payload, self.enactment)
        elif self.duplicate:
            return "Message({}, {}, duplicate={})".format(
                self.schema.name, self.payload, self.duplicate)
        else:
            return "Message({}, {})".format(self.schema.name, self.payload)

    def keys_match(self, other):
        return all(self.payload[k] == other.payload[k]
                   for k in self.schema.keys
                   if k in other.schema.parameters)


class Adapter:
    def __init__(self, role, protocol, configuration):
        """
        Initialize the PoS adapter.

        role: name of the role being implemented
        protocol: a protocol specification
          {name, keys, messages: [{name, from, to, parameters, keys, ins, outs, nils}]}
        configuration: a dictionary of roles to endpoint URLs
          {role: url}
        """
        self.role = role
        self.protocol = protocol
        self.configuration = configuration
        self.reactors = {}  # dict of message -> {handlers}
        self.history = History()
        self.send_q = Queue()
        self.recv_q = Queue()
        self.process_thread = Thread(target=self.process_loop)
        self.listen_thread = Thread(target=self.listen_loop)

    def process_receive(self, payload):
        if not isinstance(payload, dict):
            logger.warn(
                "Payload does not parse to a dictionary: {}".format(payload))
            return

        schema = self.protocol.find_schema(payload, to=self.role)
        if not schema:
            logger.warn("No schema matching payload: {}".format(payload))
            return
        message = Message(schema, payload)
        message.enactment = self.history.check_integrity(message)
        if message.enactment is not False:
            if self.history.duplicate(message):
                logger.debug("Duplicate message: {}".format(message))
                message.duplicate = True
            else:
                logger.debug("Observing message: {}".format(message))
                self.history.observe(message)

            self.react(message)

    def send(self, payload, schema=None, name=None, to=None):
        """
        Add a message to the outgoing queue
        """
        schema = schema or self.protocol.find_schema(payload, name=name, to=to)
        self.send_q.put(Message(schema, payload))

    def process_send(self, message):
        """
        Send a message by posting to the recipient's http endpoint,
        after checking for correctness, and storing the message.
        """
        enactment = self.history.enactment(message)
        dest = self.configuration[message.schema.recipient]

        if self.history.validate_send(message):
            self.history.observe(message)

            logger.debug("Sending message {} to {} at {}".format(
                message.payload, message.schema.recipient.name, dest))

            self.react(message)

            data = json.dumps(message.payload).encode('utf-8')
            if len(data) > 1500-48:  # ethernet MTU - IPv6 + UDP header
                logger.info("Message too long: {}".format(data))

            sock = socket.socket(socket.AF_INET,  # Internet
                                 socket.SOCK_DGRAM)  # UDP
            sock.sendto(data, dest)
            return True

    def reaction(self, schema):
        """
        Decorator for declaring reactor handler.

        Example:
        @adapter.react(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """
        def register_handler(handler):
            if self.reactors.get(schema):
                self.reactors[schema].add(handler)
            else:
                self.reactors[schema] = {handler}  # set
        return register_handler

    def react(self, message):
        """
        Handle emission/reception of message by invoking corresponding reactors.
        """
        reactors = self.reactors.get(message.schema)
        if reactors:
            for r in reactors:
                logger.info("Invoking reactor: {}".format(r))
                # run reactor in a thread
                threading.Thread(target=r, args=(message,)).start()

    def listen_loop(self):
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind(self.configuration[self.role])  # (IP, port)

        while True:
            data, addr = sock.recvfrom(1500)  # buffer size is 1500 bytes
            self.recv_q.put(json.loads(data))

    def process_loop(self):
        while True:
            # very busy waiting...
            if not self.send_q.empty():
                self.process_send(self.send_q.get())
            if not self.recv_q.empty():
                self.process_receive(self.recv_q.get())

    def start(self):
        self.process_thread.start()
        self.listen_thread.start()


class Resend:
    """
    A helper class for defining proactive resend policies.

    The following statement returns a function that returns a list of all Accept messages that do not have corresponding Deliver instances in the history.
      Resend(Accept).until(Deliver)
    """

    def __init__(self, *messages):
        """List of message schemas to try resending"""
        self.messages = messages

    def until(self, *expectations):
        """
        Conditions for resending the messages; another list of message schemas to wait for, resending until they arrive
        """
        def process(history):
            resend = {}
            # for each schema that needs resending
            for s in self.messages:
                # identify candidate instances in the log
                for candidate in history.by_msg[s]:
                    # go through each expected schema
                    for e in expectations:
                        # if there aren't any matching instances, add
                        # the candidate to the resend set
                        if not any(candidate.keys_match(m)
                                   for m in history.by_msg.get(e, [])):
                            resend.add(candidate)
            return resend
        return process


class Scheduler:
    def __init__(self, adapter, schedule='* * * * * *', policies=None):
        self.adapter = adapter
        self.schedule = schedule
        self.policies = policies or set()
        self.crontab = CronTab()
        self.ID = uuid.uuid4()
        job = self.crontab.new(command='echo '+self.ID)
        job.setall(schedule)  # assume cron syntax for now

    def add(self, policy):
        self.policies.add(policy)

    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.start()

    def cron(self):
        for result in self.crontab.run_scheduler():
            if result == self.ID:
                # only run on our schedule
                self.run()

    def run(self):
        for p in policies:
            # give policy access to full history for conditional evaluation
            if p.condition(self.adapter.history):
                for m in p.messages:
                    m = self.adapter.history.fill(m)
                    self.adapter.send(m)


def identity(arg):
    return arg


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
    return json.dumps(separators=(',', ':'))


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

    def __init__(self, transmitter, mangler=identity, encoder=encode, bundler=bundle, controller=simple_rate(500), mtu=1500):
        """Each component is a function that """
        self.mangle = mangler
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
        m = self.mangle(message)
        m = self.encode(message)
        self.queue.append(m)

    def process(self):
        if len(queue) > 0:
            bun = self.bundle(self.mtu, self.queue)
            self.transmit(bun)
