#!/usr/bin/env python3

from bspl.adapter.core import listify
import pytest


def test_listify():
    assert listify(1) == [1]
    assert listify([1]) == [1]
    assert listify(set([1])) == [1]
