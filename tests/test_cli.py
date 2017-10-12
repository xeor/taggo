#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import taggo


def test_noargs(capsys):
    with pytest.raises(SystemExit) as ex:
        taggo.main([])
    assert ex.value.code == 2

    out, err = capsys.readouterr()
    assert "the following arguments are required" in err


def test_help(capsys):
    with pytest.raises(SystemExit) as ex:
        taggo.main(["-h"])
    assert ex.value.code == 0

    out, err = capsys.readouterr()
    assert "show this help message and exit" in out


def test_run_non_existing(capsys):
    taggo.main(["--debug", "run", "non-existing", "temp/test_run_non_existing"])
    out, err = capsys.readouterr()
    assert "ERROR - Didnt find src-path" in err


def test_run_dry(capsys):
    taggo.main(["--debug", "run", "--dry", "tests/tagged_files/", "temp/test_run_dry"])
    out, err = capsys.readouterr()
    assert "making tag-directory" in err
    assert "making symlink" in err
    assert "Checking directory" in err
    assert "to: ../../../tests/tagged_files/folders/pictures/2012 #Oslo tour/fishes/file #tag.jpg" in err
