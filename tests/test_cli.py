#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import shutil

import pytest
import taggo


def test_noargs(capsys):
    with pytest.raises(SystemExit) as ex:
        taggo.main([])
    assert ex.value.code == 2

    out, err = capsys.readouterr()
    assert "usage: " in err
    assert "error: " in err

def test_help(capsys):
    with pytest.raises(SystemExit) as ex:
        taggo.main(["-h"])
    assert ex.value.code == 0

    out, err = capsys.readouterr()
    assert "show this help message and exit" in out


def test_run_non_existing(caplog):
    with pytest.raises(SystemExit) as ex:
        taggo.main(["run", "non-existing", "temp/test_run_non_existing"])
    assert ex.value.code == 2
    assert "Didnt find src-path" in caplog.text


def test_run_dry(caplog):
    taggo.main(["--debug", "run", "--dry", "tests/test_files/tagged/", "temp/test_run_dry"])
    assert "making tag-directory" in caplog.text
    assert "making symlink" in caplog.text
    assert "Checking directory" in caplog.text
    assert "to: ../../../tests/test_files/tagged/folders/pictures/2012 #Oslo tour/fishes/file #tag.jpg" in caplog.text


def test_nonexisting_dst(capsys):
    tmp = "temp/test_nonexisting_dst/{}".format(str(random.random()))
    taggo.main(["run", "tests/test_files/tagged/", tmp])
    assert os.path.isdir('{}/root'.format(tmp))


def test_existing_dst(caplog):
    if not os.path.isdir("temp/test_existing_dst"):
        os.mkdir("temp/test_existing_dst")
    taggo.main(["--debug", "run", "tests/test_files/tagged/", "temp/test_existing_dst"])
    assert "dst path exists and is a folder" in caplog.text


def test_existing_file_dst(capsys):
    with open("temp/test_existing_file_dst", "w") as fp:
        fp.write("")
    with pytest.raises(taggo.exceptions.FolderException, message="dst exist but is not a folder. Cant continue"):
        taggo.main(["--debug", "run", "tests/test_files/tagged/", "temp/test_existing_file_dst"], reraise=True)


def test_symlink_creation(capsys):
    taggo.main(["run", "tests/test_files/tagged/", "temp/test_symlink_creation"])

    for f in [
        "tagfolder/a #tagfolder - a #tagfolder/folder #with-a-deep-tag #multitag folder/a_file",
        "tagfolder/a #tagfolder - a #tagfolder/folder-inside-tagfolder/file",
        "with/a/deep/tag/a #tagfolder_folder #with-a-deep-tag #multitag folder - folder #with-a-deep-tag #multitag folder/a_file"
    ]:
        assert os.path.isfile("temp/test_symlink_creation/{}".format(f))


def test_via_python_command(capsys):
    import subprocess
    proc = subprocess.Popen(["python3", "-m", "taggo", "-h"], stdout=subprocess.PIPE)
    assert proc.wait() == 0
    assert b"show this help message and exit" in proc.stdout.read()


def test_cleanup_dst_err():
    with pytest.raises(taggo.exceptions.FolderException, match="Didnt find src directory: .*"):
        taggo.main(["cleanup", "nonexisting"], reraise=True)


def test_cleanup(capsys):
    tmp = "temp/test_cleanup/{}".format(str(random.random()))
    shutil.copytree("tests/test_files/cleanup_test", tmp, symlinks=True)

    assert os.path.isfile("{}/file".format(tmp))
    for f in [
        "existing-symlink-then-nonexist",
        "symlink-loop-a",
        "existing-symlink1",
        "existing-symlink3",
        "nonexisting-symlink"
    ]:
        assert os.path.islink("{}/a folder/{}".format(tmp, f))

    taggo.main(["cleanup", tmp])

    assert os.path.isfile("{}/file".format(tmp))
    for f in [
        "existing-symlink-then-nonexist",
        "symlink-loop-a",
        "nonexisting-symlink"
    ]:
        assert os.path.islink("{}/a folder/{}".format(tmp, f)) is False

    for f in [
        "existing-symlink1",
        "existing-symlink3"
    ]:
        assert os.path.islink("{}/a folder/{}".format(tmp, f))


def test_info(caplog):
    taggo.main(["info", "tests/test_files/"])

    for record in caplog.records:
        assert record.levelname == 'INFO'

    assert "  multitag" in caplog.text
    assert "  a-nested-tag" in caplog.text
    assert u"  øl" in caplog.text


def test_info_quiet(caplog):
    with pytest.raises(SystemExit) as ex:
        taggo.main(["--quiet", "info", "non-existing"])
    assert ex.value.code == 2

    assert caplog.text == ""


def test_rename(caplog):
    tmp = "temp/test_rename/{}".format(str(random.random()))
    shutil.copytree("tests/test_files/tagged", tmp, symlinks=True)

    assert os.path.isfile("{}/folder/tagged with #a-nested-tag.txt".format(tmp))
    taggo.main(["rename", tmp, "a-nested-tag", "new-nested-tag"])
    assert not os.path.exists("{}/folder/tagged with #a-nested-tag.txt".format(tmp))
    assert os.path.isfile("{}/folder/tagged with #new-nested-tag.txt".format(tmp))

    assert os.path.isdir("{}/folder/nesting folder/a #tagged folder".format(tmp))
    taggo.main(["rename", tmp, "tagged", "new-tagged"])
    assert not os.path.exists("{}/folder/nesting folder/a #tagged folder".format(tmp))
    assert os.path.isdir("{}/folder/nesting folder/a #new-tagged folder".format(tmp))

    with pytest.raises(SystemExit) as ex:
        taggo.main(["rename", "non-existing", "a-nested-tag", "new-nested-tag"])
    assert ex.value.code == 2

    with pytest.raises(SystemExit) as ex:
        taggo.main(["rename", tmp, "invalid tag", "new-nested-tag"])
    assert ex.value.code == 2

    with pytest.raises(SystemExit) as ex:
        taggo.main(["rename", tmp, "tag", "invalid tag"])
    assert ex.value.code == 2

    with pytest.raises(SystemExit) as ex:
        taggo.main(["rename", tmp, "tag", "tag"])
    assert ex.value.code == 2
