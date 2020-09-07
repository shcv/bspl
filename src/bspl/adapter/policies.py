import yaml
from .adapter import Message


class Resend:
    """
    A helper class for defining resend policies.

    The following statement returns a function that returns a list of all Accept messages that do not have corresponding Deliver instances in the history.
      Resend(Accept).until.received(Deliver)

    Other example policies:

      Resend(Accept).until.acknowledged(Accept)
      Resend(Shipment).upon.duplicate(Accept)
    """

    def __init__(self, *schemas):
        """List of message schemas to try resending"""
        self.schemas = schemas
        self.reactors = {}
        self.reactive = False
        self.disjunctive = True
        self.proactors = []

    def run(self, history):
        selected = set()
        for p in self.proactors:
            if self.disjunctive:
                selected.update(p(history))
            else:
                selected.intersection_update(p(history))
        return selected

    def action(self, adapter, schema, enactment):
        adapter.resend(schema, enactment)

    @property
    def until(self):
        self.reactive = True
        return self

    def received(self, *expectations):
        """
        Select messages for which not all of the listed expectations have been received.
        E.g.:
          Resend(A).until.received(B,C)
        will resend A until /both/ B and C are received.

        To handle a disjunction, use separate received() clauses at at least one Or.
        E.g.:
          Resend(A).until.received(B).Or.received(C)
        """

        if reactive:
            for s in expectations:
                def reactor(msg, adapter):
                    for r in self.schemas:
                        # resend message schema r in the same enactment as msg
                        self.action(adapter, r, msg.enactment)
                reactors[s] = reactor
        else:
            def process(history):
                messages = set()
                # for each schema that needs resending
                for s in self.schemas:
                    # identify candidate instances in the log
                    for candidate in history.by_msg[s]:
                        # go through each expected schema separately;
                        # if any expectation is not met, it will
                        # select the candidate
                        for e in expectations:
                            # if there aren't any matching instances,
                            # select the candidate
                            if not any(candidate.keys_match(m)
                                       for m in history.by_msg.get(e, [])):
                                messages.add(candidate)
                return messages
            self.proactors.append(process)
        return self

    @property
    def Or(self):
        self.disjunctive = True
        return self

    @property
    def And(self):
        self.disjunctive = False
        return self

    @property
    def acknowledged(self):
        """
        If proactive, add a process to the policy to resend the messages until they are acknowledged.
        Example:
          Resend(Accept).until.acknowledged
        """

        if self.reactive:
            pass
        else:
            def process(history):
                resend = set()
                # for each schema that needs resending
                for s in self.schemas:
                    # identify candidate instances in the log
                    for candidate in history.by_msg[s]:
                        # go through each expected schema
                        if not candidate.acknowledged:
                            resend.add(candidate)
                return resend
            self.proactors.append(process)
        return self

    @property
    def upon(self):
        self.reactive = True
        return self

    def duplicate(self, *schemas):
        """
        React to duplicate instances of any message in *messages
        """
        for s in schemas:
            def reactor(msg, adapter):
                if msg.duplicate:
                    for r in self.schemas:
                        # resend message schema r in the same enactment as msg
                        self.action(adapter, r, msg.enactment)
            reactors[s] = reactor
        return self


class Forward(Resend):
    """
    Forwarding policy; sends a message to a specified recipient.
    E.g.: Forward(Deliver).to(Seller).upon.duplicate(Shipment)
    """

    def __init__(self, *schemas):
        self.to = None
        super().__init__(*schemas)

    def to(self, recipient):
        self.to = recipient
        return self

    def action(self, adapter, schema, enactment):
        adapter.forward(schema, self.to or schema.recipient, enactment)


Send = Forward  # alias
