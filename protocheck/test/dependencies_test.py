import pytest
from protocheck.bspl import load_file
from protocheck.analysis.dependencies import *


@pytest.fixture(scope="module")
def Auction():
    return load_file('samples/bspl/auction').protocols['Auction']


@pytest.fixture(scope="module")
def A(Auction):
    return Auction.roles['A']


@pytest.fixture(scope="module")
def B(Auction):
    return Auction.roles['B']


@pytest.fixture(scope="module")
def Bid(Auction):
    return Auction.messages['Bid']


def test_dependency_graph(Auction):
    result = dependency_graph(Auction)
    print(result)
    assert not result


def test_production_graph(Auction):
    result = production_graph(Auction)
    print(result)
    assert not result


def test_cycles(Auction):
    graph = production_graph(Auction)
    cycles = find_cycles(graph, Auction.entrypoints)
    print(cycles)
    assert cycles
