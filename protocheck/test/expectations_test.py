import pytest
from protocheck.bspl import load_file
from protocheck.analysis.expectations import *


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


def test_rank_messages(Auction, Bid):
    result = rank_messages(Auction)
    assert result[Bid] is 1
    assert result[Auction.messages['Start']] is 0


def test_dependencies(Auction, Bid):
    start = Auction.messages['Start']
    result = dependencies(Bid)
    print(result)
    assert result['id'] == [start]
    assert dependencies(start) == {}
