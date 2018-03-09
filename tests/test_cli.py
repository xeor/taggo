#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import random
import shutil
import textwrap

import pytest
import taggo

"""
# test files

There are a bunch of test-files under tests/test_files, here are some higlights.

./tests/test_files
  no_tags        # Files that are not tagged
  files_flat     # Empty files with different forms of tags
  files_meta     # Files to test meta plugins..
  folders        # Tagged folders with some empty files
  folders_depth  # Different depth folders, with empty files
"""

test_files = "tests/test_files/"

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


def test_run_dry(caplog, tmpdir):
    taggo.main(["--debug", "run", "--dry", test_files, str(tmpdir)])
    assert "making tag-directory" in caplog.text
    assert "making symlink" in caplog.text
    assert "Checking directory" in caplog.text
    assert re.search('to: .*/tests/test_files/files_flat/.*\.txt', caplog.text)
    assert not os.path.exists(f'{tmpdir}/tag1')


def test_nonexisting_dst(tmpdir):
    tmppath = f"{tmpdir}/non-existing"
    taggo.main(["run", test_files, tmppath])
    assert os.path.isdir(f'{tmppath}/tag1')


def test_existing_dst(caplog, tmpdir):
    taggo.main(["--debug", "run", test_files, str(tmpdir)])
    assert "dst path exists and is a folder" in caplog.text


def test_existing_file_dst(tmpdir):
    tmppath = f"{tmpdir}/existing-file"
    with open(tmppath, "w") as fp:
        fp.write("")
    with pytest.raises(taggo.exceptions.FolderException, message="dst exist but is not a folder. Cant continue"):
        taggo.main(["--debug", "run", test_files, tmppath], reraise=True)


def test_symlink_creation_1(tmpdir):
    taggo.main(["run", test_files, str(tmpdir), "--symlink-name", "{tag[as-folders]}/{basename}"])

    for filepath in [
        "tarball/#tarball.tar",
        "ѤѥѦѧѨ/ƂƃƄƅƆƇƈ #ѤѥѦѧѨ ƉƊƋƌƍƎƏƐƑ.txt",

        textwrap.dedent("""\
        tag1/#tag1 #tag2-a-b(c)

        #tag3

        .txt"""),

        # FIXME, this should pass
        #         textwrap.dedent("""\
        #         tag3/#tag1 #tag2-a-b(c)
        #
        #         #tag3
        #
        #         .txt""")
    ]:
        assert os.path.isfile(f"{tmpdir}/{filepath}")


def test_symlink_creation_2(caplog, tmpdir):
    os.symlink("non-existing-file", f"{tmpdir}/should-be-removed-but-arent")

    with pytest.raises(SystemExit) as ex:
        taggo.main([
            "--json-output",
            "run", test_files, str(tmpdir),
            "--metadata-addon", "stat",
            "--metadata-addon", "filetype",
            "--metadata-addon", "exif",
            "--metadata-addon", "md5",
            "--metadata-default", "a_key=value",
            "--filter-mode", "include", "--filter", "a_key__startswith=val",
            "--filter-query", 'contains(paths.*, `"files_flat"`) && "file-ext" == `txt`',
            "--symlink-name", "{paths[0]}/{md5}.{file-ext}",
            "--collision-handler", "bail-if-different",
            "--auto-cleanup"
        ])
    assert ex.value.code == 20

    for filepath in [
        "files_flat/d41d8cd98f00b204e9800998ecf8427e.txt"
    ]:
        assert os.path.islink(f"{tmpdir}/{filepath}")

    # Should be cleaned up, but arent, since the collision-handler didn't let us finish...
    assert os.path.islink(f"{tmpdir}/should-be-removed-but-arent")
    assert len(os.listdir(str(tmpdir))) == 2

    assert len(caplog.records) == 2
    for log in caplog.records:
        message = json.loads(log.message)
        if log.levelname == 'INFO':
            assert message.get('_type') == 'made-symlink'
            assert message.get('symlink_destination').endswith('files_flat/#tag1 #tag1-a-b(c).txt')
        if log.levelname == 'ERROR':
            assert message.get('_type') == 'collision'
            assert message.get('symlink_destination').endswith('.txt')


def test_via_python_command():
    import subprocess
    proc = subprocess.Popen(["python3", "-m", "taggo", "-h"], stdout=subprocess.PIPE)
    assert proc.wait() == 0
    assert b"show this help message and exit" in proc.stdout.read()


def test_cleanup_dst_err():
    with pytest.raises(taggo.exceptions.FolderException, match="Didnt find directory: .*"):
        taggo.main(["cleanup", "nonexisting"], reraise=True)


def test_cleanup(tmpdir):
    # Using a subfolder, since pytest is creating the folder, but shutil also wants that
    tmp = f"{tmpdir}/cleanup_files"

    shutil.copytree(f"{test_files}/cleanup_files", tmp, symlinks=True)

    assert os.path.isfile(f"{tmp}/file")
    for filepath in [
        "existing-symlink-then-nonexist",
        "symlink-loop-a",
        "existing-symlink1",
        "existing-symlink3",
        "nonexisting-symlink"
    ]:
        assert os.path.islink(f"{tmp}/a folder/{filepath}")

    taggo.main(["cleanup", str(tmp)])

    assert os.path.isfile(f"{tmp}/file")
    for filepath in [
        "existing-symlink-then-nonexist",
        "symlink-loop-a",
        "nonexisting-symlink"
    ]:
        assert not os.path.islink(f"{tmp}/a folder/{filepath}")

    for filepath in [
        "existing-symlink1",
        "existing-symlink3"
    ]:
        assert os.path.islink(f"{tmp}/a folder/{filepath}")


def test_info(caplog):
    taggo.main(["info", test_files])

    for record in caplog.records:
        assert record.levelname == 'INFO'

    assert "  tag1-a-b-c" in caplog.text
    assert "  ѤѥѦѧѨ" in caplog.text


def test_info_quiet_non_existing(caplog):
    with pytest.raises(SystemExit) as ex:
        taggo.main(["--quiet", "info", "non-existing"])
    assert ex.value.code == 2

    assert caplog.text == ""


def test_rename(caplog, tmpdir):
    tmp = f"{tmpdir}/test_rename"
    shutil.copytree("tests/test_files", tmp, symlinks=True)

    assert os.path.isfile(f"{tmp}/files_flat/a file #tag1-a-b-c.txt")
    taggo.main(["rename", tmp, "tag1-a-b-c", "new-nested-tag"])
    assert not os.path.exists(f"{tmp}/files_flat/a file #tag1-a-b-c.txt")
    assert os.path.isfile(f"{tmp}/files_flat/a file #new-nested-tag.txt")

    assert os.path.isfile(f"{tmp}/files_flat/ƂƃƄƅƆƇƈ #ѤѥѦѧѨ ƉƊƋƌƍƎƏƐƑ.txt")
    taggo.main(["rename", tmp, "ѤѥѦѧѨ", "normalized-tag"])
    assert not os.path.exists(f"{tmp}/files_flat/ƂƃƄƅƆƇƈ #ѤѥѦѧѨ ƉƊƋƌƍƎƏƐƑ.txt")
    assert os.path.isfile(f"{tmp}/files_flat/ƂƃƄƅƆƇƈ #normalized-tag ƉƊƋƌƍƎƏƐƑ.txt")

    assert os.path.isdir(f"{tmp}/folders/simple #tag4")
    taggo.main(["rename", tmp, "tag4", "newtag4"])
    assert not os.path.exists(f"{tmp}/folders/simple #tag4")
    assert os.path.isdir(f"{tmp}/folders/simple #newtag4")

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
