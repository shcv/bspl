import pytest
from bspl.parsers.bspl import load_file, load
from bspl.protocol import *


@pytest.fixture(scope="module")
def Auction():
    return load_file("samples/tests/auction").protocols["Auction"]


@pytest.fixture(scope="module")
def A(Auction):
    return Auction.roles["A"]


@pytest.fixture(scope="module")
def B(Auction):
    return Auction.roles["B"]


@pytest.fixture(scope="module")
def Bid(Auction):
    return Auction.messages["Bid"]


def test_contents(Bid):
    id = Bid.parameters["id"]
    bidID = Bid.parameters["bidID"]
    bid = Bid.parameters["bid"]
    assert Bid.contents == [id, bidID, bid]


def test_determines(Auction):
    assert Auction.determines("id", "bidID")
    assert Auction.determines("id", "done")
    assert not Auction.determines("done", "id")


def test_ordered_params(Auction, Bid):
    print(Auction.parameters.keys())
    print([p.name for p in Auction.ordered_params()])
    print([p.name for p in Bid.ordered_params()])
    # regression; assume stable sorting
    assert [p.name for p in Auction.ordered_params()] == ["id", "done", "bidID", "bid"]
    assert [p.name for p in Bid.ordered_params()] == ["id", "bidID", "bid", "done"]


def test_initiators(Auction):
    assert Auction.initiators() == {Auction.messages["Start"]}


def test_message_construct(Bid):
    # bind positional parameters
    assert Bid.construct("a", "b", "c") == {"id": "a", "bidID": "b", "bid": "c"}

    # should raise error when attempting to bind a nil
    with pytest.raises(Exception) as e:
        Bid.construct("a", "b", "c", "d")
    assert e

    # binding nil to None is fine
    assert Bid.construct("a", "b", "c", None) == {"id": "a", "bidID": "b", "bid": "c"}

    # should raise error when attempting to bind unknown key parameter
    with pytest.raises(Exception) as e:
        Bid.construct("a", "b", blah="c")
    assert e
    # binding known kwargs is fine
    assert Bid.construct("a", bidID="b", bid="c") == {
        "id": "a",
        "bidID": "b",
        "bid": "c",
    }


# Multi-recipient protocol tests


def test_multi_recipient_parsing():
    """Test multi-recipient syntax parsing and backwards compatibility"""
    spec = load(
        "MultiTest { roles A, B, C parameters out data A -> B,C: multi[out data] A -> B: single[out data] }"
    )
    protocol = spec.protocols["MultiTest"]

    # Multi-recipient message
    multi_msg = protocol.messages["multi"]
    assert len(multi_msg.recipients) == 2
    assert [r.name for r in multi_msg.recipients] == ["B", "C"]
    assert multi_msg.recipient.name == "B"  # backwards compatibility

    # Single-recipient message
    single_msg = protocol.messages["single"]
    assert len(single_msg.recipients) == 1
    assert single_msg.recipient.name == "B"


def test_multi_recipient_format():
    """Test multi-recipient message formatting"""
    spec = load(
        "FormatTest { roles A, B, C parameters out data A -> B,C: multi[out data] }"
    )
    msg = spec.protocols["FormatTest"].messages["multi"]
    assert "A -> B,C: multi[out data]" in msg.format()
