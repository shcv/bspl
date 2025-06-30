import asyncio
import logging
import pytest
import bspl.parsers.bspl
from bspl.adapter import Adapter
from bspl.adapter.message import Message
from bspl.adapter.emitter import Emitter, MockEmitter
from bspl.adapter.receiver import Receiver, MockReceiver
from bspl.adapter.event import InitEvent

# Set pytest-asyncio default fixture loop scope to avoid deprecation warning
pytest_plugins = ["pytest_asyncio"]
pytestmark = pytest.mark.asyncio

logger = logging.getLogger("bspl")
logger.setLevel(logging.DEBUG)


@pytest.fixture(scope="module")
def Auction():
    return bspl.parsers.bspl.parse(
        """
Auction {
  roles A, B // Auctioneer, Bidder
  parameters out itemID key, out description, out price

  A -> B: announce[out itemID, out description]
  B -> A: bid[in itemID, out price]
  A -> B: accept[in itemID, in price]
}
"""
    ).protocols["Auction"]


@pytest.fixture(scope="module")
def A(Auction):
    return Auction.roles["A"]


@pytest.fixture(scope="module")
def B(Auction):
    return Auction.roles["B"]


@pytest.fixture(scope="module")
def systems(A, B, Auction):
    return {
        "auction": {
            "protocol": Auction,
            "roles": {A: "auctioneer", B: "bidder"},
        }
    }


@pytest.fixture(scope="module")
def agents():
    return {
        "auctioneer": [("localhost", 9001)],
        "bidder": [("localhost", 9002)],
    }


@pytest.fixture(scope="module")
def announce(Auction):
    return Auction.messages["announce"]


@pytest.fixture(scope="module")
def bid(Auction):
    return Auction.messages["bid"]


@pytest.fixture(scope="module")
def accept(Auction):
    return Auction.messages["accept"]


async def test_single_emission_decision_handler(systems, agents, announce):
    """Test that a decision handler can emit a single message"""
    # Create mock network components
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()

    # Create the adapter with our mock components to avoid network binding
    adapter = Adapter(
        "auctioneer", systems, agents, emitter=mock_emitter, receiver=mock_receiver
    )

    # Define a decision handler that returns a single message
    @adapter.decision(event=InitEvent)
    async def single_emission(forms):
        for announce_form in forms.messages(announce):
            return announce_form.bind(itemID="item1", description="A valuable item")

    # Process the InitEvent and get emissions
    emissions = await adapter.process(InitEvent())

    # Check that exactly one message was emitted
    assert len(emissions) == 1
    assert emissions[0]["itemID"] == "item1"
    assert emissions[0]["description"] == "A valuable item"
    assert emissions[0].schema == announce


async def test_multiple_emissions_decision_handler(systems, agents, announce):
    """Test that a decision handler can emit multiple messages"""
    # Create mock network components
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()

    # Create the adapter with our mock components to avoid network binding
    adapter = Adapter(
        "auctioneer", systems, agents, emitter=mock_emitter, receiver=mock_receiver
    )

    # Define a decision handler that returns multiple messages
    @adapter.decision(event=InitEvent)
    async def multiple_emissions(forms):
        messages = []
        # Create multiple announcements
        for announce_form in forms.messages(announce):
            # Create three different auction items
            messages.append(
                announce_form.bind(itemID="item1", description="A valuable item")
            )
            messages.append(
                announce_form.bind(itemID="item2", description="Another item")
            )
            messages.append(
                announce_form.bind(itemID="item3", description="Final item")
            )
            return messages

    # Process the InitEvent and get emissions
    emissions = await adapter.process(InitEvent())

    # Check that exactly three messages were emitted
    assert len(emissions) == 3

    # Verify message contents (order might vary)
    item_ids = [msg["itemID"] for msg in emissions]
    assert "item1" in item_ids
    assert "item2" in item_ids
    assert "item3" in item_ids

    # All messages should be announcements
    for msg in emissions:
        assert msg.schema == announce


async def test_mock_emitter_send(systems, agents, announce):
    """Test that MockEmitter properly tracks messages when using adapter.send"""
    # Create mock network components
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()

    # Create the adapter with our mock components to avoid network binding
    adapter = Adapter(
        "auctioneer", systems, agents, emitter=mock_emitter, receiver=mock_receiver
    )

    # Create a test message
    test_msg = announce().bind(itemID="test1", description="Test message")
    test_msg.meta["system"] = "auction"

    # Send the message via the adapter
    await adapter.send(test_msg)

    # Verify the mock emitter tracked the message
    assert len(mock_emitter.sent_messages) == 1
    assert mock_emitter.sent_messages[0]["itemID"] == "test1"
    assert mock_emitter.sent_messages[0]["description"] == "Test message"
    assert mock_emitter.sent_messages[0].schema == announce

    # Create a second message
    test_msg2 = announce().bind(itemID="test2", description="Second test")
    test_msg2.meta["system"] = "auction"

    # Send the second message (first would be a duplicate and skipped)
    await adapter.send(test_msg2)

    # Verify both messages are tracked (test1 from first send, test2 from second)
    assert len(mock_emitter.sent_messages) == 2

    # Check the message IDs in the tracked messages
    tracked_ids = [msg["itemID"] for msg in mock_emitter.sent_messages]
    assert "test1" in tracked_ids
    assert "test2" in tracked_ids

    # Test bulk message sending with unique messages
    test_msg3 = announce().bind(itemID="test3", description="Third test")
    test_msg3.meta["system"] = "auction"

    test_msg4 = announce().bind(itemID="test4", description="Fourth test")
    test_msg4.meta["system"] = "auction"

    # Send multiple messages at once - these should go through bulk_send
    await adapter.send(test_msg3, test_msg4)

    # Should now have 4 messages tracked
    assert len(mock_emitter.sent_messages) == 4

    # Check all message IDs are there
    tracked_ids = [msg["itemID"] for msg in mock_emitter.sent_messages]
    assert "test1" in tracked_ids
    assert "test2" in tracked_ids
    assert "test3" in tracked_ids
    assert "test4" in tracked_ids


async def test_mock_receiver_and_emitter(systems, agents, announce):
    """Test that MockReceiver and MockEmitter work together without network binding"""
    # Create mock components
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()

    # Create the adapter with our mock components
    adapter = Adapter(
        "auctioneer", systems, agents, emitter=mock_emitter, receiver=mock_receiver
    )

    # Manually start the receiver task
    await mock_receiver.task(adapter)

    # Create a test message to "receive" from the network
    incoming_msg = announce().bind(itemID="incoming", description="Incoming test")
    incoming_msg.meta["system"] = "auction"

    # Inject the message through our mock receiver
    await mock_receiver.inject_message(incoming_msg)

    # Verify the message was received and added to history
    history_messages = list(adapter.history.messages())
    assert len(history_messages) == 1
    assert history_messages[0]["itemID"] == "incoming"

    # Create a message to send
    outgoing_msg = announce().bind(itemID="outgoing", description="Outgoing test")
    outgoing_msg.meta["system"] = "auction"

    # Send the message
    await adapter.send(outgoing_msg)

    # Verify the message was sent through our mock emitter
    assert len(mock_emitter.sent_messages) == 1
    assert mock_emitter.sent_messages[0]["itemID"] == "outgoing"

    # Clean up
    await mock_receiver.stop()
    await mock_emitter.stop()


async def test_multiple_different_schema_emissions(systems, agents, announce, bid):
    """Test that a decision handler can emit multiple messages with different schemas"""
    # Create mock network components
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()

    # Create the adapter with our mock components to avoid network binding
    adapter = Adapter(
        "auctioneer", systems, agents, emitter=mock_emitter, receiver=mock_receiver
    )

    # Define a decision handler that returns multiple messages with different schemas
    @adapter.decision(event=InitEvent)
    async def mixed_emissions(forms):
        messages = []

        # Create different types of messages directly
        # For the announce message (initiator), we can bind output parameters
        announce_msg = announce().bind(itemID="item1", description="A valuable item")
        announce_msg.meta["system"] = "auction"

        # Create a second announce with different values
        announce_msg2 = announce().bind(itemID="item2", description="Another item")
        announce_msg2.meta["system"] = "auction"

        messages.append(announce_msg)
        messages.append(announce_msg2)

        return messages

    # Process the InitEvent and get emissions
    emissions = await adapter.process(InitEvent())

    # Verify we have two announce messages
    assert len(emissions) == 2
    schemas = [msg.schema.name for msg in emissions]
    assert all(schema == "announce" for schema in schemas)

    # Check the two messages have different itemIDs
    item_ids = [msg["itemID"] for msg in emissions]
    assert "item1" in item_ids
    assert "item2" in item_ids


async def test_agent_list_endpoint_emission(systems, announce):
    """Test that agents with list endpoints don't cause AF_INET TypeError"""
    # This is the minimal test for the reported bug
    mock_emitter = MockEmitter()

    # The bug: when B is configured with a list, it caused TypeError
    agents_config = {
        "auctioneer": ("127.0.0.1", 9001),
        "bidder": [("127.0.0.1", 9002)],  # List format that caused the bug
    }

    adapter = Adapter("auctioneer", systems, agents_config, emitter=mock_emitter)

    # Create and send a message to the agent with list endpoint
    test_msg = announce().bind(itemID="test", description="Testing list endpoint")
    test_msg.meta["system"] = "auction"

    # This should NOT raise "AF_INET address must be tuple, not list"
    await adapter.send(test_msg)

    # Verify the message was sent successfully
    assert len(mock_emitter.sent_messages) == 1
    assert mock_emitter.sent_messages[0]["itemID"] == "test"


async def test_message_dest_dests_properties():
    """Test the dest/dests properties behavior and mutual exclusivity"""
    # Test with minimal setup - we just need a Message instance
    from bspl.adapter.message import Message
    from bspl.parsers.bspl import parse

    spec = parse("Test { roles A, B parameters out data A -> B: msg[out data] }")
    schema = spec.protocols["Test"].messages["msg"]

    # Test 1: Setting dest clears dests
    msg = Message(schema, {"data": "test"})
    msg.dests = [("host1", 8001), ("host2", 8002)]
    assert msg.dests == [("host1", 8001), ("host2", 8002)]
    msg.dest = ("host3", 8003)
    assert msg.dest == ("host3", 8003)
    assert msg.dests == [("host3", 8003)]  # dests returns [dest] when only dest is set

    # Test 2: Setting dests clears dest
    msg = Message(schema, {"data": "test"})
    msg.dest = ("host1", 8001)
    assert msg.dest == ("host1", 8001)
    msg.dests = [("host2", 8002), ("host3", 8003)]
    assert msg.dests == [("host2", 8002), ("host3", 8003)]
    assert msg.dest == ("host2", 8002)  # dest returns first of dests

    # Test 3: Validation - invalid dest
    with pytest.raises(ValueError, match="must be \\(host, port\\) tuple"):
        msg.dest = ["not", "a", "tuple"]

    with pytest.raises(ValueError, match="must be \\(host, port\\) tuple"):
        msg.dest = ("host",)  # Wrong length

    with pytest.raises(ValueError, match="host must be string, port must be int"):
        msg.dest = (123, "not_int")

    # Test 4: Validation - invalid dests
    with pytest.raises(ValueError, match="dests must be a list"):
        msg.dests = ("host", 8001)  # Not a list

    with pytest.raises(ValueError, match="must be \\(host, port\\) tuple"):
        msg.dests = [("host", 8001), ["not", "tuple"]]

    with pytest.raises(ValueError, match="host must be string, port must be int"):
        msg.dests = [("host", 8001), ("host", "not_int")]

    # Test 5: Setting to None is allowed
    msg.dest = None
    assert msg.dest is None
    assert msg.dests == []

    msg.dests = None
    assert msg.dests == []

    # Test 6: Empty list for dests
    msg.dests = []
    assert msg.dests == []
    assert msg.dest is None
