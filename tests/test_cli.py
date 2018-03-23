#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
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


def test_run_non_existing():
    with pytest.raises(SystemExit) as ex:
        taggo.main(["run", "non-existing", "temp/test_run_non_existing"])
    assert ex.value.code == 2


def test_run_dry(tmpdir):
    taggo.run(test_files, str(tmpdir), dry=True, nametemplate='{path.basename}')
    content = list(os.walk(tmpdir))
    assert len(content) == 1
    assert content[0][1] == []
    assert content[0][2] == []


def test_nonexisting_dst(tmpdir):
    tmppath = f"{tmpdir}/non-existing"
    taggo.main(["run", test_files, tmppath])
    assert os.path.isdir(f'{tmppath}/tag1')


def test_misc1(tmpdir):
    taggo.run(
        test_files, str(tmpdir),
        nametemplate='{tag.as-folders}/{path.md5}.{path.file-ext}',
        metadata={'md5': {}}
    )
    assert os.path.isfile(f'{tmpdir}/zip/f0a62d6347d930af50b4a0bbd948c401.zip')
    assert os.path.isfile(f'{tmpdir}/human/47ef693cfb45f0f9dc6f590a0f96d49b.jpg')
    assert os.path.isfile(f'{tmpdir}/ѤѥѦѧѨ/d41d8cd98f00b204e9800998ecf8427e.txt')
    assert os.readlink(
        f'{tmpdir}/ѤѥѦѧѨ/d41d8cd98f00b204e9800998ecf8427e.txt'
    ).endswith('tests/test_files/files_flat/ƂƃƄƅƆƇƈ #ѤѥѦѧѨ ƉƊƋƌƍƎƏƐƑ.txt')


def test_existing_file_dst(tmpdir):
    tmppath = f"{tmpdir}/existing-file"
    with open(tmppath, "w") as fp:
        fp.write("")
    with pytest.raises(SystemExit) as ex:
        taggo.main(["--debug", "run", test_files, tmppath])
    assert ex.value.code == 5


def test_symlink_creation_1(tmpdir):
    taggo.main(["run", test_files, str(tmpdir), "--nametemplate", "{tag.as-folders}/{path.basename}"])

    for filepath in [
        "tarball/#tarball.tar",
        "ѤѥѦѧѨ/ƂƃƄƅƆƇƈ #ѤѥѦѧѨ ƉƊƋƌƍƎƏƐƑ.txt",

        textwrap.dedent("""\
        tag1/#tag1 #tag2-a-b(c)

        #tag3

        .txt"""),
         textwrap.dedent("""\
         tag3/#tag1 #tag2-a-b(c)

         #tag3

         .txt""")
    ]:
        assert os.path.isfile(f"{tmpdir}/{filepath}")


def test_symlink_creation_2(tmpdir):
    # This should end up matching only one file..
    taggo.main([
        "--json-output",
        "run", test_files, str(tmpdir),
        "--metadata", "stat",
        "--metadata", "filetype",
        "--metadata", "exif",
        "--metadata", "md5",
        "--filter", 'contains(path.hierarcy, `files_flat`) && path."file-ext" == `txt` && tag.param[0] == `b`',
        "--nametemplate", "{tag.as-folders}/{path.md5}.{path.file-ext}"
    ])

    assert os.path.islink(f"{tmpdir}/tag1/a/b/0bee89b07a248e27c83fc3d5951213c1.txt")


def test_via_python_command():
    import subprocess
    proc = subprocess.Popen(["python3", "-m", "taggo", "-h"], stdout=subprocess.PIPE)
    assert proc.wait() == 0
    assert b"show this help message and exit" in proc.stdout.read()


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
