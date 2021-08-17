import asyncio
import logging
from bungie import Adapter

# from configuration import config, prescription, Patient, Complain, Filled
from bungie.policies import Remind
from configuration import config, treatment, Patient, Complaint, FilledRx

# from configuration_ack import config, prescription, Patient, Complain, Map, Filled

# logging.getLogger("bungie").setLevel(logging.DEBUG)

# adapter
adapter = Adapter(Patient, treatment, config)
adapter.load_asl("patient.asl")

if __name__ == "__main__":
    print("Starting Patient...")

    # remind policy
    # adapter.add_policies(
    #     Remind(Complain).With(Map).after(1).until.received(Filled), when="every 1s"
    # )

    # acknowledgment policy
    # adapter.add_policies(
    #     Remind(Complain).With(Map).after(1).until.acknowledged,
    #     when='every 1s')

    # start adapter
    adapter.start()
