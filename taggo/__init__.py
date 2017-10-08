import os
import logging
import argparse

__author__ = """Lars Solberg"""
__email__ = 'lars.solberg@gmail.com'
__version__ = '0.4.3'

logger = logging.getLogger("taggo")


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
    def __init__(self, args):
        logger.debug(f"Initializing using options: {args.__dict__}")

    def run(self):
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
    getattr(t, args.cmd)


if __name__ == "__main__":
    main()
