import pytest
from protocheck.bspl import load_file
from protocheck.protocol import *


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


def test_contents(Bid):
    id = Bid.parameters['id']
    bidID = Bid.parameters['bidID']
    bid = Bid.parameters['bid']
    assert Bid.contents == [id, bidID, bid]
