from protocheck import bspl
from adapter import Adapter

specification = bspl.parse("""
Order {
  roles C, S // Customer, Seller
  parameters out item key, out done

  C -> S: Buy[out item]
  S -> C: Deliver[in item, out done]
}

With-Reject {
  roles C, S
  parameters out item key, out done

  Order(C, S, out item, out done)
  S -> C: Reject[in item, out done]
}
""")

with_reject = specification.protocols['With-Reject']

config = {
    with_reject.roles['C']: ('localhost', 8001),
    with_reject.roles['S']: ('localhost', 8002)
}


def test_receive_process():
    a = Adapter(with_reject.roles['S'], with_reject, config)
    a.process_receive({"item": "ball"})
    print(a.history.parameters)
    abort()


def test_send_process():
    a = Adapter(with_reject.roles['C'], with_reject, config)
    a.process_send((with_reject.roles['S'], {"item": "ball"}))
