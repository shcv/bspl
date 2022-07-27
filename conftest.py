#!/usr/bin/env python3
import pytest


def pytest_collection_modifyitems(items, config):
    for item in items:
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
    markexpr = config.getoption("markexpr")
    config.option.markexpr = markexpr or "(not performance)"
