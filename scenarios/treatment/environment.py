#!/usr/bin/env python3

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib

import os

rootdir = os.path.dirname(__file__) or "."
env = agentspeak.runtime.Environment()


def load_agent(path):
    print(path)
    with open(os.path.join(rootdir, path)) as source:
        env.build_agent(source, agentspeak.stdlib.actions)


for root, dirs, files in os.walk(rootdir):
    print(files)

agents = [
    load_agent(path)
    for (root, dirs, files) in os.walk(rootdir)
    for path in files
    if ".asl" in path
]

if __name__ == "__main__":
    env.run()
