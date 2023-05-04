import os
from ..parser import load_file
from ..verification import paths
from ..verification.paths import max_paths, UoD
from ..utils import abort, cap_first, camel_to_snake


def generate_asl(
    path,
    role=None,
    protocol: str = None,
    roles: list = None,
    dir: str = None,
    out: str = None,
    all: bool = None,
    stdout: bool = False,
    dry: bool = False,
):
    # dict of {role: [goals]}
    goals = {}

    if roles and out:
        abort("Can't specify filename for multiple roles")
    if all and out:
        abort("Can't specify filename for multiple roles")

    spec = load_file(path)
    if protocol:
        ps = [spec.protocols[protocol]]
    else:
        ps = spec.protocols.values()

    for p in ps:
        if role:
            # working with a single role
            roles = [p.roles[role]]
            out = out or role + ".asl"
        elif roles:
            # multiple specified roles
            roles = [p.roles[r] for r in roles]
        elif all:
            # all roles
            roles = [r for r in p.roles.values()]
        else:
            abort("You must identify some role(s) to generate code for, or use --all")
        for r in roles:
            if r not in goals:
                goals[r] = []
            covers = generate_covers(p, r)
            goals[r].extend(generate_goals(covers))

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
    u = UoD.from_protocol(protocol)
    ps = max_paths(u)
    covers = {}
    for e in role.emissions(protocol):
        covers[e] = []
        ins = set(e.ins)
        inclusive_ps = [p for p in ps if e in paths.emissions(p)]
        for p in inclusive_ps:
            cover = set()
            for ev in p:
                m = ev.msg
                intersection = ins.intersection(m.parameters.keys())
                if m in role.observations(protocol) and intersection:
                    cover.add(m)
                    for i in ins.intersection(m.parameters.keys()):
                        ins.discard(i)
                if not ins:
                    covers[e].append(cover)
                    break
    return covers


def msg_term(message):
    msg_params = ", ".join(
        [
            cap_first(message.sender.name),
            cap_first(message.recipient.name),
        ]
        + [cap_first(param) for param in message.parameters]
    )
    return f"{camel_to_snake(message.name)}({msg_params})"


def generate_goals(covers):
    goals = []
    for message, cover_sets in covers.items():
        msg_params = ", ".join(
            [cap_first(param) for param in message.parameters if param in message.ins]
        )
        msg_goal = f"!send_{camel_to_snake(message.name)}({msg_params})"
        msg_comment = f"// insert code to compute {message.name} out parameters {message.outs} here\n    "
        for cover in cover_sets:
            if len(cover) == 0:
                goals.append(
                    f"!send_{camel_to_snake(message.name)}\n  <- {msg_comment} .emit({msg_term(message)}).\n"
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
                    f"{msg_goal}\n  <- {msg_comment} .emit({msg_term(message)}).\n"
                )

    return goals
