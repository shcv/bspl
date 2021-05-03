from ..protocol import *
import re
import tatsu
import sys
from .build import build_parser, save_parser

debug = True

try:
    from .bspl_parser import BsplParser

    model = BsplParser()
except:
    model = build_parser()
    try:
        save_parser(model)
    except:
        # Couldn't save the file properly; eat the error and continue with dynamically loaded parser
        pass


def parse(definition):
    return from_ast(model.parse(definition, rule_name="document"))


def load(definition, path=None):
    try:
        return parse(definition)
    except:  # catch *all* exceptions
        if not debug:  # suppress traceback by default
            e = sys.exc_info()[1]
            if path:
                print("Error in: ", path, file=sys.stderr)
            print(e, file=sys.stderr)
            sys.exit(1)
        else:
            raise


def load_file(path):
    with open(path, "r", encoding="utf8") as file:
        raw = file.read()
        raw = strip_latex(raw)

        spec = load(raw, path)
        return spec


def strip_latex(spec):
    """Remove all instances of '\\mapsto' and '\\msf{}' from a latex listing, to make it proper BSPL"""
    spec = re.sub(r"\$\\msf{(\w+)}\$", r"\1", spec)
    spec = re.sub(r"\$\\mapsto\$", r"->", spec)

    spec = re.sub(r"\$\\role\$", r"roles", spec)
    spec = re.sub(r"\$\\param\$", r"parameters", spec)
    spec = re.sub(r"\$\\mo\$", r"->", spec)
    return spec


def ast_reference(ast, parent):
    r = Reference(ast["name"], parent=parent)
    r.parameters = [ast_parameter(p, r) for p in ast["params"]]
    return r


def ast_parameter(ast, parent):
    return Parameter(ast["name"], ast.get("adornment"), ast.get("key"), parent)


def ast_message(ast, parent):
    msg = Message(ast["name"], ast["sender"], ast["recipient"], parent=parent)
    parameters = [ast_parameter(p, msg) for p in ast.get("parameters") or []]
    msg.set_parameters(parameters)
    return msg


def ast_protocol(ast, parent):
    protocol = Protocol(ast["name"], parent=parent)
    roles = [Role(r["name"], protocol) for r in ast.get("roles", [])]
    protocol.configure(roles=roles)
    public_parameters = [ast_parameter(p, protocol) for p in ast["parameters"]]
    private_parameters = [ast_parameter(p, protocol) for p in ast.get("private") or []]

    references = []
    messages = {}
    acks = False
    for r in ast.get("references", []):
        type = r["type"]
        if type == "message":
            if r["name"][0] == "@":
                m = messages[r["name"][1:]]
                references.append(m.acknowledgment())
                acks = True
            else:
                m = ast_message(r, protocol)
                messages[m.raw_name] = m
                references.append(m)
        elif type == "protocol":
            references.append(ast_reference(r, protocol))
        else:
            raise Exception(f"Unknown type: {type}")

    if acks:
        private_parameters.append(Parameter("$ack", "out", key=True, parent=protocol))

    protocol.configure(roles, public_parameters, references, private_parameters)
    return protocol


def from_ast(ast):
    spec = Specification()
    protocols = []
    spec.add_protocols([ast_protocol(p.asjson(), spec) for p in ast])
    return spec


def load_protocols(paths, filter=".*"):
    for path in paths:
        spec = load_file(path)
        if not spec.protocols:
            print("No protocols parsed from file: ", path)
        for protocol in spec.protocols.values():
            protocol.path = spec.path
        yield from spec.protocols.values()
