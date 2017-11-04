import re
import os
import sys
import logging
import argparse

from . import (exceptions, utils)

__author__ = """Lars Solberg"""
__email__ = 'lars.solberg@gmail.com'
__version__ = '0.10.0'

logger = logging.getLogger("taggo")
hashtag_re = re.compile(r'\B#([^ \.,]+)\b')


class Taggo:
    # What should we name the file inside the folder belonging to a tag?
    # You should include enough data here so we wont get a name-conflict.
    # In case of conflicts, it will get overwritten, we do no check..
    symlink_name_template = "{rel_folders} - {basename}"

    def __init__(self, args):
        self.origin_cwd = os.getcwd()
        self.args = args
        logger.debug("Initializing using options: {}".format(args.__dict__))

    def __del__(self):
        # Try to get back to our original directory after we are done.
        # Not normally that important, but usefull in some cases, example for testing.
        os.chdir(self.origin_cwd)

    def _make_symlinks(self, basename, symlink_name_data, dirpath, dst_path, is_file=True):
        tags = set(hashtag_re.findall(basename))
        logger.debug("  {}({}) have tags({})".format(
            'file' if is_file else 'folder',
            basename,
            tags
        ))

        symlink_name_data['basename'] = basename

        # Filename is only set if we are making a symlink from a file
        if is_file:
            full_path = os.path.join(dirpath, basename)
        else:
            full_path = dirpath

        for tag in tags:
            # We replaces - with folder-separator so we can
            # use eg #tag-tag2 as a way of making tags in tags..
            # Inside nested folders..
            tag = tag.replace("-", os.path.sep)

            tag_folder = os.path.join(dst_path, tag)
            symlink_name = self.symlink_name_template.format(**symlink_name_data)
            logger.debug("Made symlink-name ({}) from symlink-name-data: {}".format(
                symlink_name, symlink_name_data
            ))

            # Find the related path to the file, from our symlink.
            # It is better to have a symlink pointing to our destination
            # via a relative path, than an absolute path.
            symlink_destination = os.path.relpath(full_path, tag_folder)

            full_symlink_path = os.path.join(tag_folder, symlink_name)

            if not os.path.isdir(tag_folder):
                logger.debug("    making tag-directory: {}".format(tag_folder))
                if not self.args.dry:
                    os.makedirs(tag_folder)

            logger.debug("    making symlink:")
            logger.debug("      in: {}".format(full_symlink_path))
            logger.debug("      to: {}".format(symlink_destination))

            if not self.args.dry:
                try:
                    os.symlink(symlink_destination, full_symlink_path)
                except OSError:
                    pass

    def run(self):
        logger.debug("run()")

        src_path = os.path.abspath(self.args.src)
        dst_path = os.path.abspath(self.args.dst)
        logger.debug("Using src-path: {}".format(src_path))
        logger.debug("Using dst-path: {}".format(dst_path))

        if not os.path.isdir(src_path):
            raise exceptions.FolderException("Didnt find src-path: {}".format(src_path))

        if os.path.exists(dst_path):
            if os.path.isdir(self.args.dst):
                logger.debug("dst path exists and is a folder")
            else:
                raise exceptions.FolderException("dst exist but is not a folder. Cant continue")
        else:
            logger.debug("dst folder not found, creating")
            if not self.args.dry:
                os.makedirs(self.args.dst)

        # Information we can use with symlink_name_template to decide what to name
        # the file inside the tagged folder.
        symlink_name_data = {
            'rel_folders': '',  # Folders where we found the file, / replaced with _
            'basename': '',  # Original filename
        }

        # Change the folder to make it easier for ourself when getting
        # names of paths to use in link-names
        os.chdir(src_path)

        logger.debug('Changing folder to {} to start the search'.format(src_path))
        for dirpath, dirnames, filenames in os.walk('.'):
            logger.debug("Checking directory: {}".format(dirpath))

            relative_path = dirpath.split(os.path.sep)
            current_folder = relative_path[-1]
            relative_path.pop(0)  # Remove the "." entry

            if relative_path:
                symlink_name_data['rel_folders'] = '_'.join(relative_path)
            else:
                symlink_name_data['rel_folders'] = 'root'

            if "#" in current_folder:
                self._make_symlinks(
                    os.path.basename(dirpath),
                    symlink_name_data,
                    dirpath,
                    dst_path,
                    is_file=False
                )

            for filename in filenames:
                if "#" not in filename:
                    continue

                self._make_symlinks(
                    filename,
                    symlink_name_data,
                    dirpath,
                    dst_path,
                    is_file=True
                )

    def cleanup(self):
        src_path = os.path.abspath(self.args.src)
        if not os.path.isdir(src_path):
            raise exceptions.FolderException("Didnt find src directory: {}".format(src_path))

        for root, dirs, files in os.walk(src_path):
            for f in files:
                full_path = os.path.join(root, f)
                if not os.path.islink(full_path):
                    continue

                link_path = os.path.join(root, os.readlink(full_path))
                exists = os.path.exists(link_path)
                logger.debug("Symlink: {}".format(full_path))
                logger.debug("  points to: {}".format(link_path))
                logger.debug("  destination exist: {}".format(exists))
                if not exists:
                    logger.info("Deleting symlink {}".format(full_path))
                    if not self.args.dry:
                        os.unlink(full_path)

        # This will eventually trigger another os.walk on what we just looped over.
        # But we might have just cleaned out a lot of old files, making folders empty after
        # our part1 cleanup. Doing it again is quick, and much less error prune than baking
        # in the logic in the loop above.
        utils.remove_empty_folders(src_path, remove_root=False)

    def rename(self):
        src_path = os.path.abspath(self.args.src)
        if not os.path.isdir(src_path):
            raise exceptions.FolderException("Didnt find src directory: {}".format(src_path))
        logger.debug("Will look in folder '{}' for tags to rename from '{}' to '{}'".format(
            src_path, self.args.original, self.args.new
        ))

        original_tag = "#{}".format(self.args.original)
        if not utils.fullmatch(hashtag_re, original_tag):
            raise exceptions.Error("Invalid hashtag: '{}'".format(original_tag))

        new_tag = "#{}".format(self.args.new)
        if not utils.fullmatch(hashtag_re, new_tag):
            raise exceptions.Error("Invalid hashtag: '{}'".format(new_tag))

        if original_tag == new_tag:
            raise exceptions.Error("There is no need to rename tag to the same...?")

        queue = []
        logger.debug("Starting collecting list of files/folders to rename:")
        for root, dirs, files in os.walk(src_path):
            if dirs:
                for d in dirs:
                    if self.args.original in hashtag_re.findall(d):
                        full_path = os.path.join(root, d)
                        logger.debug("  Found directory: {}".format(full_path))
                        queue.append(full_path)

            if files:
                for f in files:
                    if self.args.original in hashtag_re.findall(f):
                        full_path = os.path.join(root, f)
                        logger.debug("  Found file: {}".format(full_path))
                        queue.append(full_path)

        # Start with the longest path, so we can be sure that we are not renaming a
        # folder that contains another file or folder we also should rename.
        # We must sort, or be dirty in the os.walk loop. This is much cleaner.
        for e in sorted(queue, key=len, reverse=True):
            dirname = os.path.dirname(e)
            old_basename = os.path.basename(e)
            new_basename = old_basename.replace(original_tag, new_tag)
            logger.info("Renaming: {}{}{{{} -> {}}}".format(
                dirname,
                os.path.sep,
                old_basename,
                new_basename
            ))
            if not self.args.dry:
                os.rename(e, os.path.join(dirname, new_basename))

    def info(self):
        src_path = os.path.abspath(self.args.src)
        logger.debug("Using src-path: {}".format(src_path))

        if not os.path.isdir(src_path):
            raise exceptions.FolderException("Didnt find src-path: {}".format(src_path))

        folder_tags = []
        file_tags = []
        for root, dirs, files in os.walk(src_path):
            for d in dirs:
                folder_tags += hashtag_re.findall(d)
            for f in files:
                file_tags += hashtag_re.findall(f)

        folder_tags = sorted(set(folder_tags))
        file_tags = sorted(set(file_tags))

        logger.info("Folder tags:")
        for folder_tag in folder_tags:
            logger.info("  {}".format(folder_tag))

        logger.info("")
        logger.info("File tags:")
        for file_tag in file_tags:
            logger.info("  {}".format(file_tag))


def main(known_args=None, reraise=False):
    parser = argparse.ArgumentParser(
        description="Create symlinks to files/folders based on their names"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print extra info about what we are doing",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print no outputs to stdout/stderr",
    )

    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    # run
    parser_run = subparsers.add_parser("run", help="")
    parser_run.add_argument(
        "--dry",
        help="Dont actually do anything",
        action="store_true"
    )
    parser_run.add_argument(
        "src",
        help="Source folder"
    )
    parser_run.add_argument(
        "dst",
        help="Destination folder, folder to store the tags/symlinks"
    )

    # cleanup
    parser_cleanup = subparsers.add_parser("cleanup", help="Remove dead symlinks from src")
    parser_cleanup.add_argument(
        "--dry",
        help="Dont actually do anything",
        action="store_true"
    )
    parser_cleanup.add_argument(
        "src",
        help="Source folder, the folder containing your symlinks"
    )

    # rename
    parser_cleanup = subparsers.add_parser("rename", help="Rename an existing tag")
    parser_cleanup.add_argument(
        "--dry",
        help="Dont actually do anything",
        action="store_true"
    )
    parser_cleanup.add_argument(
        "src",
        help="Source folder, the folder containing your tagged files (not the symlinks)"
    )
    parser_cleanup.add_argument(
        "original",
        help="Original tag you want to replace (no #)"
    )
    parser_cleanup.add_argument(
        "new",
        help="New tag, without the #"
    )

    # info
    parser_cleanup = subparsers.add_parser("info", help="List existing tags and some info")
    parser_cleanup.add_argument(
        "src",
        help="Source folder, the folder containing your tagged files (not the symlinks)"
    )

    args = parser.parse_args(known_args)

    if args.debug or os.environ.get("DEBUG"):
        logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
        logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(format="%(message)s")
        logger.setLevel(logging.INFO)

    logger.disabled = args.quiet

    t = Taggo(args)

    try:
        getattr(t, args.cmd)()
    except exceptions.Error as e:
        logger.error(e)
        if reraise:
            raise
        sys.exit(2)


if __name__ == "__main__":  # pragma: no cover
    main()  # pragma: no cover
