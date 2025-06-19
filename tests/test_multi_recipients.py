#!/usr/bin/env python3

import pytest
from bspl.parsers.bspl import load
from bspl.protocol import Message, Role, Protocol, Parameter


def test_multi_recipient_parsing():
    """Test that multi-recipient syntax parses correctly"""
    spec_text = """
    protocol MultiRecipientTest {
      roles A, B, C, D
      parameters out id, out data, out result
      
      A -> B,C,D: broadcast[out id, out data]
      B -> A: response[in id, in data, out result] 
    }
    """
    
    spec = load(spec_text)
    protocol = spec.protocols['MultiRecipientTest']
    
    broadcast_msg = protocol.messages['broadcast']
    assert len(broadcast_msg.recipients) == 3
    assert broadcast_msg.recipients[0].name == 'B'
    assert broadcast_msg.recipients[1].name == 'C'
    assert broadcast_msg.recipients[2].name == 'D'
    
    response_msg = protocol.messages['response']
    assert len(response_msg.recipients) == 1
    assert response_msg.recipients[0].name == 'A'


def test_backwards_compatibility():
    """Test that single recipient still works and provides backwards compatibility"""
    spec_text = """
    protocol BackwardsCompatTest {
      roles A, B
      parameters out data
      
      A -> B: singleRecipient[out data]
    }
    """
    
    spec = load(spec_text)
    protocol = spec.protocols['BackwardsCompatTest']
    msg = protocol.messages['singleRecipient']
    
    # Test new multi-recipient interface
    assert len(msg.recipients) == 1
    assert msg.recipients[0].name == 'B'
    
    # Test backwards compatibility interface
    assert msg.recipient.name == 'B'


def test_multi_recipient_format():
    """Test that multi-recipient messages format correctly"""
    spec_text = """
    protocol FormatTest {
      roles A, B, C
      parameters out data
      
      A -> B,C: multi[out data]
      A -> B: single[out data]
    }
    """
    
    spec = load(spec_text)
    protocol = spec.protocols['FormatTest']
    
    multi_msg = protocol.messages['multi']
    single_msg = protocol.messages['single']
    
    assert "A -> B,C: multi[out data]" in multi_msg.format()
    assert "A -> B: single[out data]" in single_msg.format()


def test_multi_recipient_to_dict():
    """Test that multi-recipient messages serialize correctly"""
    spec_text = """
    protocol SerializationTest {
      roles A, B, C
      parameters out data
      
      A -> B,C: test[out data]
    }
    """
    
    spec = load(spec_text)
    protocol = spec.protocols['SerializationTest']
    msg = protocol.messages['test']
    
    data = msg.to_dict()
    assert data['to'] == ['B', 'C']
    assert data['from'] == 'A'


def test_role_methods_multi_recipient():
    """Test that Role methods work correctly with multi-recipient messages"""
    spec_text = """
    protocol RoleTest {
      roles A, B, C
      parameters out data
      
      A -> B,C: broadcast[out data]
      B -> A: response1[in data]
      C -> A: response2[in data]
    }
    """
    
    spec = load(spec_text)
    protocol = spec.protocols['RoleTest']
    
    role_a = protocol.roles['A']
    role_b = protocol.roles['B']
    role_c = protocol.roles['C']
    
    # Test role.messages() includes multi-recipient messages
    a_messages = role_a.messages(protocol)
    assert 'broadcast' in a_messages  # A is sender
    assert 'response1' in a_messages  # A is recipient
    assert 'response2' in a_messages  # A is recipient
    
    b_messages = role_b.messages(protocol)
    assert 'broadcast' in b_messages  # B is recipient
    assert 'response1' in b_messages  # B is sender
    
    c_messages = role_c.messages(protocol)
    assert 'broadcast' in c_messages  # C is recipient
    assert 'response2' in c_messages  # C is sender
    
    # Test role.receptions()
    b_receptions = role_b.receptions(protocol)
    assert any(m.name == 'broadcast' for m in b_receptions)
    
    c_receptions = role_c.receptions(protocol)
    assert any(m.name == 'broadcast' for m in c_receptions)
    
    # Test role.emissions()
    a_emissions = role_a.emissions(protocol)
    assert any(m.name == 'broadcast' for m in a_emissions)


def test_message_creation_with_multi_recipients():
    """Test programmatic creation of multi-recipient messages"""
    protocol = Protocol("TestProtocol")
    role_a = Role("A", protocol)
    role_b = Role("B", protocol)
    role_c = Role("C", protocol)
    
    protocol.configure(
        roles=[role_a, role_b, role_c],
        public_parameters=[Parameter("data", "out")],
        parent=None
    )
    
    # Create message with multiple recipients
    msg = Message(
        "testMsg",
        sender=role_a,
        recipients=[role_b, role_c],
        parameters=[Parameter("data", "out", parent=protocol)],
        parent=protocol
    )
    
    assert len(msg.recipients) == 2
    assert msg.recipients[0] == role_b
    assert msg.recipients[1] == role_c
    assert msg.recipient == role_b  # backwards compatibility


if __name__ == "__main__":
    test_multi_recipient_parsing()
    test_backwards_compatibility()
    test_multi_recipient_format()
    test_multi_recipient_to_dict()
    test_role_methods_multi_recipient()
    test_message_creation_with_multi_recipients()
    print("All multi-recipient tests passed!")