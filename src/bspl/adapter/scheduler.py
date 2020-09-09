import croniter
import uuid
from cronus.beat import Beat
from crontab import CronTab
from threading import Thread


class Scheduler:
    def __init__(self, schedule='* * * * *', policies=None, rate=None):
        self.schedule = schedule
        self.policies = policies or set()
        if rate:
            self.beat = Beat()
            self.beat.set_rate(rate)
        self.crontab = CronTab()
        self.ID = uuid.uuid4()
        job = self.crontab.new(command='echo '+str(self.ID))
        job.setall(schedule)  # assume cron syntax for now

    def add(self, policy):
        self.policies.add(policy)
        return self

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
                # put message directly onto send queue, bypassing protocol check (?)
                self.adapter.send_q.put(m)
