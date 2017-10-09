import re
import os
import logging
import argparse

__author__ = """Lars Solberg"""
__email__ = 'lars.solberg@gmail.com'
__version__ = '0.4.4'

logger = logging.getLogger("taggo")


class TaggoException(Exception):
    pass


class ErrorInArgumentException(TaggoException):
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

def _verify_path_exist(path, name):
    if not os.path.isdir(path):
        raise ErrorInArgumentException("Unable to find {} {} ({})".format(
            name,
            path,
            os.path.abspath(path)
        ))


class Taggo:
    hashtag_re = re.compile(r'\B#([^ \.,]+)\b')

    # What should we name the file inside the folder belonging to a tag?
    # You should include enough data here so we wont get a name-conflict.
    # In case of conflicts, it will get overwritten, we do no check..
    tagged_file_name = "{rel_folders} - {basename}"

    def __init__(self, args):
        self.args = args
        logger.debug("Initializing using options: {}".format(args.__dict__))

    def run(self):
        logger.debug("run()")
        _verify_path_exist(self.args.src, 'src-path')
        if os.path.exists(self.args.dst):
            logger.debug("dst path exists")
            if not os.path.isdir(self.args.dst):
                raise ErrorInArgumentException('dst exists and is not a directory')
        else:
            logger.debug("dst folder not found, creating")
            os.makedirs(self.args.dst)

        _verify_path_exist(self.args.dst, 'dst-path')
        logger.debug("Using paths src({}), dst({})".format(
            self.args.src, self.args.dst
        ))

        # Information we can use with tagged_file_name to decide what to name
        # the file inside the tagged folder.
        tagged_file_meta = {
            'rel_folders': '',  # Folders where we found the file, / replaced with _
            'basename': '',  # Original filename
        }

        for dirpath, dirnames, filenames in os.walk(self.args.src):
            logger.debug("Checking directory: {}".format(dirpath))
            relative_path = dirpath.split(os.path.sep)
            if len(relative_path) == 1:
                tagged_file_meta['rel_folders'] = 'root'
            else:
                tagged_file_meta['rel_folders'] = '_'.join(relative_path)

            for filename in filenames:
                if "#" not in filename:
                    # quick way to skip
                    continue

                tagged_file_meta['basename'] = filename
                tags = set(self.hashtag_re.findall(filename))
                fullpath = os.path.join(dirpath, filename)
                logger.debug("  file({}), tags({})".format(
                    filename, tags
                ))

                for tag in tags:
                    tag = tag.replace("-", os.path.sep)
                    tag_folder = os.path.join(self.args.dst, tag)
                    tag_name = self.tagged_file_name.format(**tagged_file_meta)
                    logger.debug("    making tag {}".format(tag_name))

                    if not os.path.isdir(tag_folder):
                        logger.debug("    making directory: {}".format(tag_folder))
                        #os.makedirs(tag_folder)


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
    except TaggoException as e:
        logger.error(e)

if __name__ == "__main__":
    main()

