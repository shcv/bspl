import os
from ..parsers.bspl import load_file
from ..verification import paths
from ..verification.paths import max_paths, UoD, all_paths
from ..utils import abort, camel_to_snake, camel, upcamel


def generate_asl(
    path,
    role=None,
    protocol: str = None,
    roles: list = None,
    dir: str = None,
    out: str = None,
    all_roles: bool = None,
    stdout: bool = False,
    dry: bool = False,
):
    # dict of {role: [goals]}
    goals = {}

    if roles and out:
        abort("Can't specify filename for multiple roles")
    if all_roles and out:
        abort("Can't specify filename for multiple roles")

    spec = load_file(path)
    if protocol:
        ps = [spec.protocols[protocol]]
    else:
        ps = spec.protocols.values()

    for p in ps:
        if stdout:
            print(f"#----- Protocol {p.name} ({path}): -----#")
        if role:
            # working with a single role
            roles = [p.roles[role]]
            out = out or role + ".asl"
        elif all_roles:
            # all roles
            roles = [r for r in p.roles.values()]
        elif roles:
            # multiple specified roles
            roles = [p.roles[r] for r in roles]
        else:
            abort(
                "You must identify some role(s) to generate code for, or use --all_roles"
            )
        for r in roles:
            if r not in goals:
                goals[r] = []
            covers = generate_covers(p, r)
            covers = {m: [prune(m, c) for c in covers[m]] for m in covers}
            new_goals = generate_goals(covers)
            print(f"New goals for {r.name}: ", *new_goals, sep="\n")
            goals[r].extend(new_goals)

    for r in roles:
        if dir and out:
            fp = dir + "/" + out
        elif dir:
            fp = dir + "/" + r.name + ".asl"
        elif out:
            fp = "./" + out
        else:
            fp = "./" + r.name + ".asl"

        if stdout:
            print(f"  #----- Goals for {r.name}: -----#")
            for g in goals[r]:
                print(g)
            # go to the next role, without writing to a file
            continue

        if dry:
            # print where it *would* have been saved
            print(fp)
            # don't save it
            continue

        # Extract the directory path
        dir_path = os.path.dirname(fp)

        # Create the directory if it doesn't already exist
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(fp, "w") as f:
            print(f"Writing {r.name}'s goals to {fp}")
            for g in goals[r]:
                f.write(f"{g}\n")


def generate_covers(protocol, role):
    """For each emission by ROLE in PROTOCOL, generate a list of covers for that emission.
    Each cover is a set of messages that must be received before the emission can be sent."""
    u = UoD.from_protocol(protocol, external=True)
    ps = max_paths(u)
    covers = {}
    for e in role.emissions(protocol):
        covers[e] = []
        # the list of paths that include the target emission e
        inclusive_ps = [p for p in ps if e in paths.emissions(p)]
        for p in inclusive_ps:
            cover = set()
            ins = set(e.ins)  # need to track ins for current cover
            for ev in p:
                m = ev.msg
                if m != e:
                    intersection = ins.intersection(m.ins.union(m.outs))
                    if intersection and m in role.observations(protocol):
                        cover.add(m)
                        for i in ins.intersection(m.parameters.keys()):
                            ins.discard(i)
                if not ins and cover not in covers[e]:
                    covers[e].append(cover)
                    break
    return covers


def prune(emission, cover):
    """Prune a cover by removing messages whose portion of the emission's 'in' parameters are fully covered by other messages in the cover"""
    pruned = set()

    for m in cover:
        if not any(
            emission.ins.intersection(m.ins.union(m.outs))
            <= other.ins.union(other.outs)
            for other in cover
            if other != m
        ):
            pruned.add(m)
    return pruned


def msg_prefix(message):
    return [
        "MasID",
        message.sender.name.capitalize(),
        message.recipient.name.capitalize(),
    ]


def msg_term(message):
    msg_params = ", ".join(
        msg_prefix(message)
        + [
            upcamel(param)
            for param in message.parameters
            if message.public_parameters[param].adornment in ("in", "out")
        ]
    )
    return f"{camel_to_snake(message.name)}({msg_params})"


def generate_goals(covers):
    goals = []
    print(covers)
    for message, cover_sets in covers.items():
        msg_params = ", ".join(
            msg_prefix(message)
            + [upcamel(param) for param in message.parameters if param in message.ins]
        )
        msg_goal = f"!send_{camel_to_snake(message.name)}({msg_params})"
        msg_comment = f"// insert code to compute {message.name} out parameters {sorted(message.outs)} here\n    "
        for cover in cover_sets:
            if len(cover) == 0:
                goals.append(
                    f"+!send_{camel_to_snake(message.name)}\n  <- {msg_comment} .emit({msg_term(message)}).\n"
                )
            elif len(cover) == 1:
                dep_message = list(cover)[0]
                goals.append(
                    f"+{msg_term(dep_message)}\n  <- {msg_comment} .emit({msg_term(message)}).\n"
                )
            else:
                for dep_message in cover:
                    other_deps = [other for other in cover if other != dep_message]
                    context = "\n  & ".join([msg_term(other) for other in other_deps])
                    goals.append(
                        f"+{msg_term(dep_message)}\n  : {context}\n  <- {msg_goal}.\n"
                    )
                # Add the plan for the message goal
                goals.append(
                    f"+{msg_goal}\n  <- {msg_comment} .emit({msg_term(message)}).\n"
                )

    return goals
