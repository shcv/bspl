import croniter
import uuid
import datetime
import random
import re
from cronus.beat import Beat
from crontab import CronTab, CronSlices
from threading import Thread
from . import policies


def exponential(interval=1):
    def inner(message):
        return interval * random.randint(0, 2 ** message.meta.get('retries', 0)-1)
    return inner


class Scheduler:
    def __init__(self, schedule='* * * * *', policies=None, backoff=None):
        self.ID = uuid.uuid4()

        if CronSlices.is_valid(schedule):
            self.schedule = schedule
            self.crontab = CronTab()
            job = self.crontab.new(command='echo '+str(self.ID))
            job.setall(schedule)  # assume cron syntax for now
        elif re.match(r'(?:every\s?)?(\d+\.?\d*)?\s?(?:s|seconds?)', schedule):
            match = re.match(
                r'(?:every\s?)?(\d+\.?\d*)?\s?(?:s|seconds?)', schedule).groups()
            if match[0] is not None:
                interval = float(match[0])
            else:
                interval = 1
            self.beat = Beat()
            self.beat.set_rate(1/interval)
        else:
            raise Exception("Unknown schedule format: {}".format(schedule))

        self.policies = policies or set()
        self._backoff = backoff

    def add(self, policy):
        self.policies.add(policy)
        return self

    def backoff(message):
        if 'last-retry' in message.meta:
            delta = datetime.datetime.now() - message.meta['last-retry']
            delay = self._backoff(message)
            return delta > datetime.timedelta(seconds=delay)
        else:
            return True

    def start(self, adapter):
        self.adapter = adapter
        self.thread = Thread(target=self.loop)
        self.thread.start()

    def loop(self):
        if self.beat:
            while self.beat.true():
                self.run()
                self.beat.sleep()
        else:
            for result in self.crontab.run_scheduler():
                if result == self.ID:
                    # only run on our schedule
                    self.run()

    def run(self):
        for p in self.policies:
            # give policy access to full history for conditional evaluation
            messages = p.run(self.adapter.history)
            for m in messages:
                # check backoff, if set, before sending
                if not self.backoff or self.backoff(m):
                    # put message directly onto send queue, bypassing protocol check (?)
                    self.adapter.send_q.put(m)
