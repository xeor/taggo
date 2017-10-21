import os
import re
import logging

logger = logging.getLogger("taggo")


# Original from https://gist.github.com/jacobtomlinson/9031697
def remove_empty_folders(path, remove_root=True):
    if not os.path.isdir(path):
        return

    # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                remove_empty_folders(fullpath)

    # if folder empty, delete it
    files = os.listdir(path)
    if len(files) == 0 and remove_root:
        logger.info("Removing empty folder: {}".format(path))
        os.rmdir(path)


# Original from https://stackoverflow.com/questions/30212413/backport-python-3-4s-regular-expression-fullmatch-to-python-2
def fullmatch(regex, string):
    if hasattr(re, 'fullmatch'):
        return regex.fullmatch(string)

    m = re.match(regex, string)
    if m and m.span()[1] == len(string):
        return m
