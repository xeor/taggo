#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random

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
    taggo.main(["run", "non-existing", "temp/test_run_non_existing"])
    out, err = capsys.readouterr()
    assert "ERROR - Didnt find src-path" in err


def test_run_dry(capsys):
    taggo.main(["--debug", "run", "--dry", "tests/tagged_files/", "temp/test_run_dry"])
    out, err = capsys.readouterr()
    assert "making tag-directory" in err
    assert "making symlink" in err
    assert "Checking directory" in err
    assert "to: ../../../tests/tagged_files/folders/pictures/2012 #Oslo tour/fishes/file #tag.jpg" in err


def test_nonexisting_dst(capsys):
    tmp = "temp/test_nonexisting_dst/{}".format(str(random.random()))
    taggo.main(["run", "tests/tagged_files/", tmp])
    assert os.path.isdir('{}/root'.format(tmp))


def test_existing_dst(capsys):
    if not os.path.isdir("temp/test_existing_dst"):
        os.mkdir("temp/test_existing_dst")
    taggo.main(["--debug", "run", "tests/tagged_files/", "temp/test_existing_dst"])
    out, err = capsys.readouterr()
    assert "dst path exists and is a folder" in err


def test_existing_file_dst(capsys):
    with open("temp/test_existing_file_dst", "w") as fp:
        fp.write("")
    with pytest.raises(taggo.FolderException, message="dst exist but is not a folder. Cant continue"):
        taggo.main(["--debug", "run", "tests/tagged_files/", "temp/test_existing_file_dst"], reraise=True)

    #out, err = capsys.readouterr()
    #assert "dst path exists and is a folder" in err
