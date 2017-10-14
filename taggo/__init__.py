import re
import os
import logging
import argparse

__author__ = """Lars Solberg"""
__email__ = 'lars.solberg@gmail.com'
__version__ = '0.5.0'

logger = logging.getLogger("taggo")
hashtag_re = re.compile(r'\B#([^ \.,]+)\b')

class Error(Exception):
    pass


class FolderException(Error):
    pass


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
                except FileExistsError:
                    pass


    def run(self):
        logger.debug("run()")

        src_path = os.path.abspath(self.args.src)
        dst_path = os.path.abspath(self.args.dst)
        logger.debug("Using src-path: {}".format(src_path))
        logger.debug("Using dst-path: {}".format(dst_path))

        if not os.path.isdir(src_path):
            raise FolderException("Didnt find src-path: {}".format(src_path))

        if os.path.exists(dst_path):
            if os.path.isdir(self.args.dst):
                logger.debug("dst path exists and is a folder")
            else:
                raise FolderException("dst exist but is not a folder. Cant continue")
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
                logger.debug("DIR  Found # in directory-name {}".format(current_folder))
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
        pass


def main(known_args=None, reraise=False):
    parser = argparse.ArgumentParser(
        description="Create symlinks to files/folders based on their names"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Set loglevel/verbosity. Higher == more output",
    )

    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    # rename
    # cleanup

    parser_run = subparsers.add_parser('run')
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

    parser_cleanup = subparsers.add_parser('cleanup')
    parser_cleanup.add_argument(
        "--dry",
        help="Dont actually do anything",
        action="store_true"
    )
    parser_cleanup.add_argument(
        "src",
        help="Source folder, the folder containing your symlinks"
    )

    args = parser.parse_args(known_args)

    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
    if args.debug or os.environ.get("DEBUG"):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    t = Taggo(args)

    try:
        getattr(t, args.cmd)()
    except Error as e:
        logger.error(e)
        if reraise:
            raise

if __name__ == "__main__":
    main()

