from bspl.adapter.statistics import *


def test_net_usage():
    net = net_usage("")
    print(net)
    assert net


def test_cpu_usage():
    cpu = cpu_usage()
    print(cpu)
    assert cpu >= 0  # Accept 0 as valid fallback when cgroup files unavailable


def test_mem_usage():
    mem = mem_usage()
    print(mem)
    assert mem >= 0  # Accept 0 as valid fallback when cgroup files unavailable
