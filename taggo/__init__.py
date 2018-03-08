from __future__ import print_function

import re
import os
import sys
import json
import logging
import datetime
import textwrap
import argparse

from collections import defaultdict

try:
    import jmespath
except ImportError:
    pass

from . import (exceptions, utils)

__author__ = """Lars Solberg"""
__email__ = 'lars.solberg@gmail.com'
__version__ = '0.13.9'

# hashtag_re = re.compile(r'\B#([^ \.,]+)\b')

# Hashtag with optional param matcher
#  hashtag_re.findall('#test not#me #abc(test=123,la=la) #aaa(111) #aaa(222) lala')
#    > [('test', ''), ('abc', 'test=123,la=la'), ('aaa', '111'), ('aaa', '222')]
hashtag_re = re.compile(r"""
        \B                   # Else we might match on eg no#tag
        \#                   # Tag-character.. The hashtag
        (                    # Main tag-name group
            [^ \.,\(\)]+     # Tag themself can contain anything except space, "." and "," (end of sentences problem)
                             # and ()-brackets (they are used in params)
        )
        (?:                  # Parameter-group, non-capturing wrapping
            \(               # Parameter-start
                (.+?)        # Whatever is inside, as little as possible before the \) below. Make a capture-group
            \)               # Parameter-end
        )?                   # This whole parameter-group is optional
        """, re.X)


def hashtags_in(string):
    return [i[0] for i in hashtag_re.findall(string)]


# Logging that sends info and debug to stdout, and warning or greater to stderr
# https://stackoverflow.com/a/16066513/452081
class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


class SkipFile(Exception):
    pass


logger = logging.getLogger("taggo")

h1 = logging.StreamHandler(sys.stdout)
h1.setLevel(logging.DEBUG)
h1.addFilter(InfoFilter())
logger.addHandler(h1)

h2 = logging.StreamHandler()
h2.setLevel(logging.WARNING)
logger.addHandler(h2)


class Taggo:
    def __init__(self, args):
        self.args = args
        logger.debug("Using taggo version: {}".format(__version__))
        logger.debug("Our working directory is: {}".format(os.getcwd()))
        logger.debug("Initializing using options: {}".format(args.__dict__))

    def _output(self, loglevel, text, _type, **kwargs):
        if self.args.json_output:
            kwargs['_type'] = _type
            getattr(logger, loglevel)(json.dumps(kwargs))
        else:
            if text:
                getattr(logger, loglevel)(text)

    def _handle_file_metadata(self, full_path):
        data = {}
        data['file-ext'] = '{}'.format(full_path.split('.')[-1])

        if 'stat' in self.args.metadata_addon:
            stat = os.stat(full_path)
            for k in dir(stat):
                if not k.startswith('st_'):
                    continue
                value = getattr(stat, k)
                data[k] = value
                if k in ['st_atime', 'st_ctime', 'st_mtime']:
                    timestamp = datetime.datetime.fromtimestamp(value)
                    data['{}_iso'.format(k)] = timestamp.isoformat()
                    data['{}_year'.format(k)] = timestamp.year
                    data['{}_month'.format(k)] = timestamp.month
                    data['{}_day'.format(k)] = timestamp.day
            self._check_filter('stat', data)

        if 'filetype' in self.args.metadata_addon:
            data.update(utils.get_filetype_data(full_path))
            self._check_filter('filetype', data)

        if 'exif' in self.args.metadata_addon:
            data.update(utils.get_exif_data(full_path))
            self._check_filter('exif', data)

        if 'md5' in self.args.metadata_addon:
            import hashlib
            data['md5'] = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
            self._check_filter('md5', data)

        return data

    def _check_filter(self, group, data):
        for f in self.filters[group]:
            symlink_data = data.get(f['key'])

            if not symlink_data:
                # No way for us to guess, data is missing.. Ie. "--filter non_existing=abc"
                continue

            filter_result = f['func'](
                symlink_data, f['value']
            )

            if self.args.filter_mode == 'include' and filter_result is False:
                raise SkipFile

            if self.args.filter_mode == 'exclude' and filter_result is True:
                raise SkipFile

    def _make_symlinks(self, basename, symlink_name_data, dirpath, dst_path, is_file=True):
        tags = set(hashtag_re.findall(basename))
        logger.debug("  {}({}) have tags({})".format(
            'file' if is_file else 'folder',
            basename,
            tags
        ))

        symlink_name_data = symlink_name_data.copy()
        symlink_name_data['basename'] = basename

        self._check_filter('pre', symlink_name_data)

        # Filename is only set if we are making a symlink from a file
        if is_file:
            full_path = os.path.join(dirpath, basename)
            symlink_name_data.update(self._handle_file_metadata(full_path))
        else:
            full_path = dirpath

        for tag in tags:
            if self.args.prompt_each:
                try:
                    input()
                except KeyboardInterrupt:
                    sys.exit(0)

            tag, param = tag

            symlink_name_data['tag'] = {'original': tag}
            symlink_name_data['tag-param'] = {'original': param}

            # We replaces - with folder-separator so we can
            # use eg #tag-tag2 as a way of making tags in tags..
            # Inside nested folders..
            tag = tag.replace('-', os.path.sep)
            symlink_name_data['tag']['as-folders'] = tag

            # Make name from our template, also removing any / in the beginning, since
            # it will make os.path.join confused.
            if self.args.symlink_name_file and self.args.symlink_name_folder:
                if is_file:
                    symlink_name_template = self.args.symlink_name_file
                else:
                    symlink_name_template = self.args.symlink_name_folder
            else:
                symlink_name_template = self.args.symlink_name

            for entry in self.args.metadata_default:
                entry_split = entry.split('=')
                if not len(entry_split) >= 2:
                    self._output(
                        'error', 'Invalid symlink-name-default {}. Ignoring..'.format(entry),
                        'invalid-symlink-name-default',
                        entry=entry
                    )
                    continue
                key = entry_split[0]
                val = '='.join(entry_split[1:])
                if key not in symlink_name_data:
                    symlink_name_data[key] = val

            if self.args.filter_query:
                if not jmespath.search(self.args.filter_query, symlink_name_data):
                    raise SkipFile

            try:
                symlink_name = symlink_name_template.format(**symlink_name_data).lstrip('/')
            except KeyError as e:
                self._output(
                    'error',
                    'Invalid key in name-template ({}) {} while trying to make symlink for {}.'
                    'Correct it, or use --symlink-name-default. Valid keys are: {}'.format(
                        symlink_name_template, e, full_path, ', '.join(symlink_name_data.keys())
                    ),
                    'error-in-template',
                    invalid_key=e.args[0], template=symlink_name_template, data=symlink_name_data, full_path=full_path
                )
                continue

            logger.debug("Making symlink-name ({}) from symlink-name-data: {}".format(
                symlink_name, symlink_name_data
            ))

            full_symlink_path = os.path.join(dst_path, symlink_name)
            tag_folder = os.path.dirname(full_symlink_path)

            # Find the related path to the file, from our symlink.
            # It is better to have a symlink pointing to our destination
            # via a relative path, than an absolute path.
            symlink_destination = os.path.relpath(full_path, tag_folder)

            if not os.path.isdir(tag_folder):
                logger.debug("    making tag-directory: {}".format(tag_folder))
                if not self.args.dry:
                    os.makedirs(tag_folder)

            logger.debug("    making symlink:")
            logger.debug("      in: {}".format(full_symlink_path))
            logger.debug("      to: {}".format(symlink_destination))

            should_overwrite = True
            symlinkpath_exists = False

            if os.path.exists(full_symlink_path):
                symlinkpath_exists = True

            if self.args.collision_handler in ["smart", "overwrite-if-symlink"]:
                if symlinkpath_exists:
                    if not os.path.islink(full_symlink_path):
                        should_overwrite = False

            if self.args.collision_handler in ["smart", "overwrite-if-dst-same"]:
                if not full_symlink_path.startswith(self.args.dst):
                    should_overwrite = False

            if self.args.collision_handler == "no-overwrite":
                should_overwrite = False

            if symlinkpath_exists:
                existing_symlink_destination = os.readlink(full_symlink_path)
                if symlink_destination == existing_symlink_destination:
                    # Don't bother
                    logger.debug("    Already exists... Skipping")
                    continue

                self._output(
                    'error',
                    'Link ({}) points to ({}), now we want ({})'.format(
                        full_symlink_path, existing_symlink_destination, symlink_destination
                    ),
                    'collision',
                    symlink_path=full_symlink_path,
                    existing_symlink_destination=existing_symlink_destination,
                    symlink_destination=symlink_destination
                )

                if self.args.collision_handler == "bail-if-different":
                    sys.exit(20)

                logger.debug("    Symlink already existing but with another destination.")
                logger.debug("      old: {}".format(existing_symlink_destination))
                logger.debug("      new: {}".format(symlink_destination))
                logger.debug("      will we overwrite: {}".format(should_overwrite))

            if symlinkpath_exists and should_overwrite:
                if not self.args.dry:
                    os.remove(full_symlink_path)
            try:
                if not self.args.dry:
                    os.symlink(symlink_destination, full_symlink_path, target_is_directory=not is_file)

                self._output(
                    'info',
                    'Made {} -> {}'.format(full_symlink_path, symlink_destination),
                    'made-symlink',
                    symlink_path=full_symlink_path,
                    symlink_destination=symlink_destination
                )
            except OSError as e:
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

        self.filters = utils.make_filters(self.args.filter)
        symlink_name_data = {}

        for dirpath, dirnames, filenames in os.walk(src_path):
            logger.debug("Checking directory: {}".format(dirpath))

            relative_path = dirpath.split(os.path.sep)
            current_folder = relative_path[-1]
            relative_path.pop(0)  # Remove the "." entry

            # Make and expose a reversed list of folders where 0 is the item nearest
            # the end of the path. We use a defaultdict in case there are nothing there,
            # we don't want taggo to crash.
            path_hierarcy = defaultdict(lambda: '')
            path_hierarcy.update({k: v for k, v in enumerate(reversed(relative_path))})
            symlink_name_data['paths'] = path_hierarcy

            if "#" in current_folder:
                symlink_name_data['rel_folders'] = utils.get_rel_folders_string(relative_path, False)

                try:
                    self._make_symlinks(
                        basename=os.path.basename(dirpath),
                        symlink_name_data=symlink_name_data,
                        dirpath=dirpath,
                        dst_path=dst_path,
                        is_file=False
                    )
                except SkipFile:
                    continue

            for filename in filenames:
                if "#" not in filename:
                    continue

                symlink_name_data['rel_folders'] = utils.get_rel_folders_string(relative_path, True)

                try:
                    self._make_symlinks(
                        basename=filename,
                        symlink_name_data=symlink_name_data,
                        dirpath=dirpath,
                        dst_path=dst_path,
                        is_file=True
                    )
                except SkipFile:
                    continue

        if self.args.auto_cleanup:
            self.cleanup()

    def cleanup(self):
        dst_path = os.path.abspath(self.args.dst)
        if not os.path.isdir(dst_path):
            raise exceptions.FolderException("Didnt find directory: {}".format(dst_path))

        for root, dirs, files in os.walk(dst_path):
            for f in files:
                full_path = os.path.join(root, f)
                if not os.path.islink(full_path):
                    continue

                symlink_destination = os.path.normpath(os.path.join(root, os.readlink(full_path)))
                exists = os.path.exists(symlink_destination)
                logger.debug("Symlink: {}".format(full_path))
                logger.debug("  points to: {}".format(symlink_destination))
                logger.debug("  destination exist: {}".format(exists))
                if not exists:
                    self._output(
                        'info',
                        'Deleting dead symlink ({}) pointed to {}'.format(full_path, symlink_destination),
                        'deleted-symlink',
                        symlink_path=full_path,
                        symlink_destination=symlink_destination
                    )

                    if not self.args.dry:
                        os.unlink(full_path)

        # This will eventually trigger another os.walk on what we just looped over.
        # But we might have just cleaned out a lot of old files, making folders empty after
        # our part1 cleanup. Doing it again is quick, and much less error prune than baking
        # in the logic in the loop above.
        utils.remove_empty_folders(dst_path, remove_root=False)

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
                    if self.args.original in hashtags_in(d):
                        full_path = os.path.join(root, d)
                        logger.debug("  Found directory: {}".format(full_path))
                        queue.append(full_path)

            if files:
                for f in files:
                    if self.args.original in hashtags_in(f):
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
                folder_tags += hashtags_in(d)
            for f in files:
                file_tags += hashtags_in(f)

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
        help="Print no outputs",
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output in json-format (1 entry per line). This will not work when debug is enabled."
             "Json-output will also contain some additional info",
    )

    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    # run
    parser_run = subparsers.add_parser("run", help="", formatter_class=argparse.RawTextHelpFormatter)
    parser_run.add_argument(
        "--dry",
        help="Dont actually do anything",
        action="store_true"
    )

    # What should we name the file inside the folder belonging to a tag?
    # You should include enough data here so we wont get a name-conflict.
    # In case of conflicts, it will get overwritten, we do no check..
    parser_run.add_argument(
        "--symlink-name",
        help="A template-based name of what you want to call the symlinks themself."
             "See docs for more info. (default: %(default)s)",
        default="{tag[as-folders]}/{rel_folders} - {basename}"
    )

    parser_run.add_argument(
        "--symlink-name-file",
        help="Template if we link to a file",
        default=None
    )

    parser_run.add_argument(
        "--symlink-name-folder",
        help="Template if we link to a folder",
        default=None
    )

    parser_run.add_argument(
        "--filter",
        help="Only handle files matching a filter. Can be specified more than once.",
        action="append",
        default=[]
    )

    parser_run.add_argument(
        "--filter-mode",
        help="Should we include or exclude files matching the filter."
             "Include uses locical AND, and exclude uses logical OR. (default: %(default)s)",
        choices=["include", "exclude"],
        default="include"
    )

    parser_run.add_argument(
        "--filter-query",
        help="Filtering using jmespath. Make sure it matches (returns true) for the files you want to include.",
        default=None
    )

    parser_run.add_argument(
        "--metadata-addon",
        help="Enable additional keys for the symlink-name template and filtering."
             "Use multiple times to enable several.",
        action="append",
        default=[]
    )

    parser_run.add_argument(
        "--metadata-default",
        help="Create default for keys that are not populated.."
             "Example if we don't have exif data on an image,"
             "you might want to set the key you depend on to something default."
             "Use multiple times to define several defaults. Use = to separate."
             "Example '--metadata-default keyname=value",
        action="append",
        default=[]
    )

    parser_run.add_argument(
        "--prompt-each",
        help="Wait for keypress between each symlink.. Usefull for testing",
        action="store_true"
    )

    parser_run.add_argument(
        "--auto-cleanup",
        help="Run the cleanup command after we are done.",
        action="store_true"
    )

    parser_run.add_argument(
        "--collision-handler",
        help=textwrap.dedent("""\
        There are a couple of different modes you can set for handling symlink-name collisions.
        Tweeking these can be usefull to detect too loose --symlink-template..
        We will also log to stderr if this happens.

          * smart (default): Only overwrite if it is a symlink, and it's destination-path is within our dst-path.
          * no-overwrite: Don't overwrite if anything exists at that path. Aka, "append only"
          * overwrite-if-symlink: Only overwrite if it's a symlink.
          * overwrite-if-dst-same: Overwrite if destination-path of existing symlink is within our dst-path.
          * bail-if-different: Exit with exit-code 20 if destination path is different.
          """),
        choices=["smart", "no-overwrite", "overwrite-if-symlink", "overwrite-if-dst-same", "bail-if-different"],
        default="smart"
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
    parser_cleanup = subparsers.add_parser("cleanup", help="Remove dead symlinks from symlink folder")
    parser_cleanup.add_argument(
        "--dry",
        help="Dont actually do anything",
        action="store_true"
    )
    parser_cleanup.add_argument(
        "dst",
        help="Folder that contains your symlinks"
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
        logger.setLevel(logging.DEBUG)
    else:
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
