import re
import os
import logging
import argparse

__author__ = """Lars Solberg"""
__email__ = 'lars.solberg@gmail.com'
__version__ = '0.4.4'

logger = logging.getLogger("taggo")


class Error(Exception):
    pass


class NonExistingPath(Error):
    pass


def setup_log(debug=False):
    if debug or os.environ.get("DEBUG"):
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(
        level=loglevel,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


class Taggo:
    hashtag_re = re.compile(r'\B#([^ \.,]+)\b')

    # What should we name the file inside the folder belonging to a tag?
    # You should include enough data here so we wont get a name-conflict.
    # In case of conflicts, it will get overwritten, we do no check..
    tag_filename_template = "{rel_folders} - {basename}"

    def __init__(self, args):
        self.args = args
        logger.debug("Initializing using options: {}".format(args.__dict__))

    def run(self):
        logger.debug("run()")

        src_path = os.path.abspath(self.args.src)
        dst_path = os.path.abspath(self.args.dst)
        logger.debug("Using src-path: {}".format(src_path))
        logger.debug("Using dst-path: {}".format(dst_path))

        if not os.path.isdir(src_path):
            raise NonExistingPath("Didnt find src-path: {}".format(src_path))

        if os.path.exists(dst_path):
            if os.path.isdir(self.args.dst):
                logger.debug("dst path exists and is a folder")
            else:
                raise NonExistingPath("dst exist but is not a folder. Cant continue")
        else:
            logger.debug("dst folder not found, creating")
            if not self.args.dry:
                os.makedirs(self.args.dst)

        # Information we can use with tag_filename_template to decide what to name
        # the file inside the tagged folder.
        template_data = {
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
                template_data['rel_folders'] = '_'.join(relative_path)
            else:
                template_data['rel_folders'] = 'root'
            logger.debug("Relative path template-data is: {}".format(template_data['rel_folders']))

            if "#" in current_folder:
                logger.debug("  Found # in dirname, making symlink")

            for filename in filenames:
                if "#" not in filename:
                    continue

                template_data['basename'] = filename

                tags = set(self.hashtag_re.findall(filename))
                logger.debug("  file({}) have tags({})".format(filename, tags))

                full_file_path = os.path.join(dirpath, filename)

                for tag in tags:
                    tag = tag.replace("-", os.path.sep)

                    # Full folder where we will put our symlink. We replaces - with folder-separator
                    # so we can use the #tag-tag2 as a way of making tags in tags.. Nested
                    tag_folder = os.path.join(dst_path, tag.replace("-", os.path.sep))

                    tag_filename = self.tag_filename_template.format(**template_data)

                    # Find the related path to the file, from our symlink.
                    symlink_destination = os.path.relpath(full_file_path, tag_folder)

                    full_symlink_path = os.path.join(tag_folder, tag_filename)

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



    def cleanup(self):
        pass


def main(known_args=None):
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

    setup_log(args.debug)

    t = Taggo(args)

    try:
        getattr(t, args.cmd)()
    except Error as e:
        logger.error(e)

if __name__ == "__main__":
    main()

