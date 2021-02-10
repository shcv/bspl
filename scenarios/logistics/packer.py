import logging
from bungie import Adapter, Resend
from configuration import config, logistics
from bungie.performance import perf_logger

Labeled = logistics.messages['Labeled']
Wrapped = logistics.messages['Wrapped']
Packed = logistics.messages['Packed']

adapter = Adapter(logistics.roles['Packer'], logistics, config)

logger = logging.getLogger('bungie')
# logger.setLevel(logging.DEBUG)


@adapter.reaction(Labeled)
async def labeled(message):
    if message.duplicate:
        return

    orderID = message.payload['orderID']

    unpacked = [m for m in adapter.history.by_param['orderID'][orderID].get(Wrapped, [])
                if not m.meta.get('packed')]

    for m in unpacked:
        payload = {
            'orderID': orderID,
            'itemID': m.payload['itemID'],
            'wrapping': m.payload['wrapping'],
            'label': message.payload['label'],
            'status': 'packed'
        }
        adapter.send(payload, Packed)
        m.packed = True


@adapter.reaction(Wrapped)
async def wrapped(message):
    if message.duplicate:
        logger.debug(f'duplicate: {message}')
        return
    orderID = message.payload['orderID']
    label = adapter.history.bindings.get(f'orderID:{orderID}', {}).get('label')

    if label:
        payload = {
            'orderID': orderID,
            'itemID': message.payload['itemID'],
            'wrapping': message.payload['wrapping'],
            'label': label,
            'status': 'packed'
        }
        adapter.send(payload, Packed)
        message.meta['packed'] = True

if __name__ == '__main__':
    logger.info("Starting Packer...")
    adapter.load_policy_file('policies.yaml')
    adapter.start(perf_logger(3))
