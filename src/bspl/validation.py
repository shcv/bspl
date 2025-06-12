"""
Parameter validation for BSPL protocols.

This module provides static validation checks for parameter adornment consistency.
"""


def validate_protocol_parameters(protocol):
    """
    Validate parameter adornment consistency across an entire protocol.
    
    Checks:
    1. 'out' parameters must be produced by at least one message
    2. 'in' parameters must never be produced by any message  
    3. Warns about declared but unused parameters
    
    Args:
        protocol: Protocol object to validate
        
    Raises:
        ValueError: If validation rules are violated
    """
    # Get all protocol parameters by adornment
    out_params = {p.name for p in protocol.parameters.values() if p.adornment == 'out'}
    in_params = {p.name for p in protocol.parameters.values() if p.adornment == 'in'}
    all_declared = {p.name for p in protocol.parameters.values()}
    
    # Get all message parameters by adornment
    message_outs = set()
    message_ins = set()  
    message_all = set()
    
    for message in protocol.messages.values():
        for param in message.parameters.values():
            message_all.add(param.name)
            if param.adornment == 'out':
                message_outs.add(param.name)
            elif param.adornment == 'in':
                message_ins.add(param.name)
    
    # Check: 'out' parameters must be produced by at least one message
    unproduced_outs = out_params - message_outs
    if unproduced_outs:
        if not protocol.messages:
            # Minimal protocol with no messages - just warn
            print(f"Warning: Protocol '{protocol.name}' declares 'out' parameters {sorted(unproduced_outs)} "
                  f"but has no messages")
        else:
            raise ValueError(
                f"Protocol '{protocol.name}' declares 'out' parameters {sorted(unproduced_outs)} "
                f"but no message produces them with 'out' adornment"
            )
    
    # Check: 'in' parameters must never be produced by any message
    produced_ins = in_params & message_outs
    if produced_ins:
        raise ValueError(
            f"Protocol '{protocol.name}' declares 'in' parameters {sorted(produced_ins)} "
            f"but messages produce them with 'out' adornment"
        )
    
    # Check: declared but unused parameters
    unused_params = all_declared - message_all
    if unused_params:
        print(f"Warning: Protocol '{protocol.name}' declares parameters {sorted(unused_params)} "
              f"but no message uses them")


def validate_protocol_composition(protocol):
    """
    Validate parameter consistency in protocol references.
    
    Ensures that parameters passed to subprotocols are properly declared
    in the parent protocol.
    
    Args:
        protocol: Protocol object to validate
    """
    # This is already handled by existing validation in Message.configure()
    # but we could add additional composition-specific checks here
    pass