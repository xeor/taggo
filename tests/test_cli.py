#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import contextlib

import pytest
import taggo


def runner(args, required_text, stderr=False):
    f = io.StringIO()
    redirector = contextlib.redirect_stderr if stderr else contextlib.redirect_stdout
    with redirector(f):
        try:
            taggo.main(args)
        except SystemExit:
            pass
    assert required_text in f.getvalue()


def test_noargs():
    runner([], 'the following arguments are required', stderr=True)


def test_help():
    runner(['-h'], 'show this help message and exit')


def test_run_non_existing():
    runner(['run', 'a', 'b'], '')
