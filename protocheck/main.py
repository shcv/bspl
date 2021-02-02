from protocheck.bspl import load_file, model, strip_latex
from protocheck.verification.sat import handle_enactability, handle_liveness, handle_safety, handle_atomicity
from protocheck.verification.paths import path_liveness, path_safety, all_paths, UoD
from protocheck.verification.refinement import handle_refinement
from protocheck.node_red import handle_node_flow
import configargparse
import sys
import re
import json


def handle_projection(args):
    role_name = args.input[0]
    spec = load_file(args.input[1])

    projections = []
    for protocol in spec.protocols.values():
        schema = protocol.schema
        if args.verbose:
            print(schema)

        role = protocol.roles.get(role_name)
        if not role:
            raise LookupError("Role not found", role_name)

        projections.append(protocol.projection(role))

    for p in projections:
        print(p.format())


def handle_json(protocol, args):
    print(json.dumps(protocol.to_dict(), indent=args.indent))


def handle_all(protocol, args, **kwargs):
    enactable = handle_enactability(protocol, args, **kwargs)
    if enactable:
        handle_liveness(protocol, args, **kwargs)
        handle_safety(protocol, args, **kwargs)
        handle_atomicity(protocol, args, **kwargs)


def handle_ast(args):
    with open(args.input[0]) as file:
        raw = file.read()
        raw = strip_latex(raw)

        spec = model.parse(raw, rule_name='document')

        def remove_parseinfo(d):
            if not isinstance(d, (dict, list)):
                return d
            if isinstance(d, list):
                return [remove_parseinfo(v) for v in d]
            return {k: remove_parseinfo(v) for k, v in d.items()
                    if k not in {'parseinfo'}}

        for p in spec:
            print(json.dumps(remove_parseinfo(p.asjson()), indent=2))


def check_syntax(*args):
    print("Syntax: correct")


def handle_all_paths(protocol, args):
    verbose = args.verbose
    U = UoD.from_protocol(protocol)
    all_paths(U, verbose)


# Actions that only take one argument, and therefore can be repeated for each input file
unary_actions = {
    'enactability': handle_enactability,
    'liveness': handle_liveness,
    'safety': handle_safety,
    'path-safety': path_safety,
    'path-liveness': path_liveness,
    'atomicity': handle_atomicity,
    'syntax': check_syntax,
    'all': handle_all,
    'json': handle_json,
    'all-paths': handle_all_paths,
}

# Actions with more complex argument schemes
actions = {
    'flow': handle_node_flow,
    'refinement': handle_refinement,
    'projection': handle_projection,
    'ast': handle_ast,
}


def main():

    parser = configargparse.get_argument_parser()
    parser.description = 'BSPL Protocol property checker'
    parser.add('-s', '--stats', action="store_true",
               help='Print statistics')
    parser.add('-v', '--verbose', action="store_true",
               help='Print additional details: spec, formulas, stats, etc.')
    parser.add('-q', '--quiet', action="store_true",
               help='Prevent printing of violation and formula output')
    parser.add('-f', '--filter', default='.*',
               help='Only process protocols matching regexp')
    parser.add('-i', '--indent', type=int, help='Amount to indent json')
    parser.add('--version', action="store_true", help='Print version number')
    parser.add('--debug', action="store_true", help='Debug mode')
    parser.add('action', help='Primary action to perform',
               choices=set(actions.keys()).union(unary_actions.keys()))
    parser.add('input', nargs='+',
               help='additional parameters or protocol description file(s)')

    if '--version' in sys.argv:
        print(__version__)
        sys.exit(0)
    else:
        args = parser.parse()
        global debug
        debug = args.debug

    if args.action in unary_actions:
        # unary actions only take one argument, and are therefore repeated for each argument
        for path in args.input:
            spec = load_file(path)
            for protocol in spec.protocols.values():
                if re.match(args.filter, protocol.name):
                    if args.action != 'json':
                        print("%s (%s): " % (protocol.name, path))
                    result = unary_actions[args.action](protocol, args)
                    if result:
                        print(result)
                    print()

            if not spec.protocols:
                print("No protocols parsed from file: ", args.input)
    else:
        actions[args.action](args)


if __name__ == "__main__":
    main()
