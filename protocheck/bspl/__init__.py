from ..protocol import *
import re
import tatsu
import sys
import os
debug = True


try:
    from .bspl_parser import BsplParser
    model = BsplParser()
except:
    grammar_path = os.path.join(os.path.dirname(__file__), "bspl.gr")
    with open(grammar_path, 'r', encoding='utf8') as grammar:
        model = tatsu.compile(grammar.read())
    try:
        parser_path = os.path.join(os.path.dirname(__file__), "bspl_parser.py")
        with open(grammar_path, 'r', encoding='utf8') as grammar:
            bspl_parser = tatsu.to_python_sourcecode(
                grammar.read(), 'Bspl', 'bspl_parser.py')
            print(bspl_parser)
            with open(parser_path, 'w', encoding='utf8') as parser_file:
                parser_file.write(bspl_parser)
    except:
        # Couldn't save the file properly; eat the error and continue with dynamically loaded parser
        pass


def parse(definition):
    return from_ast(model.parse(definition, rule_name='document'))


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
    with open(path, 'r', encoding='utf8') as file:
        raw = file.read()
        raw = strip_latex(raw)

        spec = load(raw, path)
        return spec


def strip_latex(spec):
    """Remove all instances of '\\mapsto' and '\\msf{}' from a latex listing, to make it proper BSPL"""
    spec = re.sub(r'\$\\msf{(\w+)}\$', r'\1', spec)
    spec = re.sub(r'\$\\mapsto\$', r'->', spec)

    spec = re.sub(r'\$\\role\$', r'roles', spec)
    spec = re.sub(r'\$\\param\$', r'parameters', spec)
    spec = re.sub(r'\$\\mo\$', r'->', spec)
    return spec


def reference(ast, parent):
    if ast["type"] == "message":
        return ast_message(ast, parent)
    elif ast["type"] == "protocol":
        return ast_reference(ast, parent)
    else:
        raise Exception("Unknown type: " + ast["type"])


def ast_reference(ast, parent):
    r = Reference(ast['name'], parent=parent)
    r.parameters = [ast_parameter(p, r) for p in ast['params']]
    return r


def ast_parameter(ast, parent):
    return Parameter(ast['name'], ast["adornment"], ast["key"], parent)


def ast_message(ast, parent):
    msg = Message(ast["name"], ast["sender"], ast["recipient"], parent=parent)
    parameters = [ast_parameter(p, msg) for p in ast['parameters']]
    msg.set_parameters(parameters)
    return msg


def ast_protocol(ast, parent):
    protocol = Protocol(ast["name"], parent=parent)
    roles = [Role(r['name'], protocol)
             for r in ast.get('roles', [])]
    protocol.configure(roles=roles)
    public_parameters = [ast_parameter(p, protocol)
                         for p in ast['parameters']]
    private_parameters = [ast_parameter(p, protocol)
                          for p in ast.get('private') or []]

    references = [reference(r, protocol)
                  for r in ast.get('references', [])]

    protocol.configure(roles, public_parameters, references,
                       private_parameters)
    return protocol


def from_ast(ast):
    spec = Specification()
    protocols = []
    spec.add_protocols([ast_protocol(p.asjson(), spec) for p in ast])
    return spec
