import os
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
