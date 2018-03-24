import re
import os
import sys
import json
import logging
import textwrap
import argparse
import importlib

from collections import defaultdict

import jmespath
from box import Box

from . import (exceptions, utils)

__author__ = """Lars Solberg"""
__email__ = 'lars.solberg@gmail.com'
__version__ = '0.14.3'

if sys.version_info[0:2] < (3, 6):
    raise Exception('You need at least python 3.6')

DEFAULT_NAMETEMPLATE = "{tag[as-folders]}/{path[hierarcy_str]} - {path[basename]}"
TAG_CHARACTER = "#"
TAG_PATH_SEPARATOR = "-"

# If we are at the top directory, what should the name be?
TAG_PATH_HIERARCY_TOP_NAME = "root"

# What character should we replace folder separator with to get path[hierarcy_str]
TAG_PATH_HIERARCY_SEPARATOR = "_"

# Hashtag with optional param matcher
#  hashtag_re.findall('#test not#me #abc(test=123,la=la) #aaa(111) #aaa(222) lala')
#    > [('test', ''), ('abc', 'test=123,la=la'), ('aaa', '111'), ('aaa', '222')]
hashtag_re = re.compile(r"""
        \B                   # Else we might match on eg no#tag
        \#                   # Tag-character.. The hashtag
        (                    # Main tag-name group
            [^\.,\(\)\s]+    # Tags can contain anything except whitespaces, "." and "," (end of sentences problem)
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


# Make a list of (num, name) of available metadata plugins.
# We shoulnt load/import them just yet..
dir_path = os.path.dirname(os.path.realpath(__file__))
metadata_files_re = re.compile(r'^([0-9]{2})_([0-9a-zA-Z_]+)\.py$')
available_metadata_addons = []
for i in os.listdir(os.path.join(dir_path, 'metadata')):
    if metadata_files_re.match(i):
        available_metadata_addons.append(
            metadata_files_re.findall(i)[0]
        )
available_metadata_addons = sorted(available_metadata_addons, key=lambda x: int(x[0]))

setattr(logging, 'VERBOSE', 15)


# Logging that sends info, verbose and debug to stdout, and warning or greater to stderr
# https://stackoverflow.com/a/16066513/452081
class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.VERBOSE, logging.INFO)


class SkipFile(Exception):
    pass


class Logger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

        logging.addLevelName(logging.VERBOSE, "VERBOSE")

    def verbose(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.VERBOSE):
            self._log(logging.VERBOSE, msg, args, **kwargs)

logger = Logger("taggo")

h1 = logging.StreamHandler(sys.stdout)
h1.setLevel(logging.DEBUG)
h1.addFilter(InfoFilter())
logger.addHandler(h1)

h2 = logging.StreamHandler()
h2.setLevel(logging.WARNING)
logger.addHandler(h2)

# Default
logger.setLevel(logging.INFO)

_json_output = False
_dry = False
_metadata = None
_filters = None


def configure(*, output=None, dry=None, metadata=None, filters=None):
    if output is not None:
        global _json_output
        _json_output = False
        logger.disabled = False

        if output == "DEBUG" or os.environ.get("DEBUG"):
            logger.setLevel(logging.DEBUG)
        elif output == "VERBOSE" or os.environ.get("VERBOSE"):
            logger.setLevel(logging.VERBOSE)
        elif output == "INFO":
            logger.setLevel(logging.INFO)
        elif output == "JSON":
            _json_output = True
        elif output == "QUIET":
            logger.disabled = True
        else:
            raise Exception('Invalid output option')

    if dry is not None:
        global _dry
        _dry = dry

    if metadata:
        global _metadata
        _metadata = metadata

    if filters:
        global _filters
        _filters = filters


def log(text, loglevel='info', category='general', data=None):
    if _json_output:
        data = data or {}

        # Be smart about if we run from terminal or not..
        # Maybe this can be streamed to the runner somehow if run from a script
        data['_category'] = category
        data['_loglevel'] = loglevel
        data['_text'] = text
        getattr(logger, loglevel)(json.dumps(data))
    else:
        getattr(logger, loglevel)(text)


def _handle_paths(symlink_basepath, sourcepath):
    symlink_basepath = os.path.abspath(symlink_basepath)
    sourcepath = os.path.abspath(sourcepath)
    log(f"Using symlink_basepath: {symlink_basepath}", loglevel='verbose')
    log(f"Using sourcepath: {sourcepath}", loglevel='verbose')

    if not os.path.exists(sourcepath):
        raise exceptions.NotFoundException(f"Unable to find sourcepath: {sourcepath}")

    return symlink_basepath, sourcepath


def _check_filter(group, metadata_store):
    if not _filters:
        return None

    for f in _filters.get(group, []):
        if not jmespath.search(f, metadata_store.data):
            raise SkipFile


def _path_variants(dirpath):
    hierarcy = dirpath.split(os.path.sep)
    hierarcy.remove('')  # Remove the "." entry

    current_folder = hierarcy[-1]

    return {
        'current_folder': current_folder,
        'hierarcy': hierarcy,
        'hierarcy_rev': hierarcy[::-1]
    }


def _path_hierarcy_string(path_hierarcy, is_file, separator=TAG_PATH_HIERARCY_SEPARATOR):
    # Convert a path hierarcy (list of paths) to a string that can be used in templates.
    # We can't do this before we know if it's a file or not..

    if (not path_hierarcy) or (len(path_hierarcy) == 1 and not is_file):
        return TAG_PATH_HIERARCY_TOP_NAME

    if is_file:
        return separator.join(path_hierarcy)
    else:
        return separator.join(path_hierarcy[:-1])


def find_tags(name):
    tagdata = {}
    for tag in set(hashtag_re.findall(name)):
        tagname, tagparams = tag
        tagdata[tagname] = tagparams.split(',')
    return tagdata


def _tag_variants(tagset):
    tag, param = tagset

    return {
        'name': tag,
        'param': param,

        # We replaces - with folder-separator so we can
        # use eg #tag-tag2 as a way of making tags in tags..
        # Inside nested folders..
        'as-folders': tag.replace(TAG_PATH_SEPARATOR, os.path.sep)
    }


class Metadata:
    scopes = ['global', 'path', 'tag']

    def __init__(self):
        self.data = {k: {} for k in self.scopes}

    def __repr__(self):
        from pprint import pformat
        return pformat(self.data, indent=2)

    def __getitem__(self, key):
        return self.data[key]

    def find(self, key):
        for scope in self.scopes:
            try:
                return self.data[scope][key]
            except KeyError:
                pass
        return None

    def add(self, scope, name, value):
        self.data[scope][name] = value

    def add_multiple(self, scope, data):
        if not data:
            return None

        for name, value in data.items():
            self.add(scope, name, value)

    def clear(self, scope):
        self.data[scope] = {}


def run(sourcepath, symlink_basepath, metadata=None, filters=None, nametemplate=None, auto_cleanup=False, dry=False):
    # Will make metadata and filters available in global scope
    configure(metadata=metadata or {}, filters=filters or {}, dry=dry)

    symlink_basepath, sourcepath = _handle_paths(symlink_basepath, sourcepath)
    metadata_store = Metadata()

    if os.path.isdir(sourcepath):
        # Start on top, and look recursive for everything below the start-directory
        for dirpath, _, filenames in os.walk(sourcepath):
            metadata_store.clear('path')

            # FIXME, check if we can get this another way. It is populated inside make_symlink
            if TAG_CHARACTER in os.path.dirname(dirpath):
                make_symlink(symlink_basepath, dirpath, metadata_store=metadata_store)

            for filename in filenames:
                if TAG_CHARACTER in filename:
                    make_symlink(
                        symlink_basepath,
                        os.path.join(dirpath, filename),
                        metadata_store=metadata_store,
                        nametemplate=nametemplate
                    )
    else:
        # A parent folder can contain a TAG_CHARACTER, but we should ignore it,
        # since it is not "us" (current file).
        if TAG_CHARACTER in os.path.basename(sourcepath):
            make_symlink(
                symlink_basepath,
                sourcepath,
                metadata_store=metadata_store,
                nametemplate=nametemplate
            )

    if auto_cleanup:
        cleanup(sourcepath)


def _nametemplate(nametemplate, is_file):
    if isinstance(nametemplate, dict):
        return nametemplate.get('file' if is_file else 'folder')

    if not nametemplate:
        return DEFAULT_NAMETEMPLATE

    return nametemplate


def _symlink_paths(nametemplate, metadata, symlink_basepath):
    try:
        relative_path = nametemplate.format_map(Box(metadata.data, default_box=True)).replace('{}', '').lstrip('/')
    except KeyError as error:
        log(
            f'Invalid key in name-template ({nametemplate}) {error} while trying to make symlink.'
            'Valid keys are, enable --verbose or --debug to see what keys you can use.',
            loglevel='error', category='error-in-nametemplate',
            data={
                'nametemplate': nametemplate,
                'metadata': metadata.data,
                'error': error
            }
        )
        sys.exit(3)

    full_path = os.path.join(symlink_basepath, relative_path)
    full_path = os.path.join(symlink_basepath, relative_path)
    symlink_folder = os.path.dirname(full_path)

    if not _dry:
        try:
            os.makedirs(symlink_folder, exist_ok=True)
        except NotADirectoryError:
            log(
                f'dst exist but is not a folder. Cant continue',
                loglevel='error', category='dst-folder-is-file',
                data={
                    'symlink_folder': symlink_folder
                }
            )
            sys.exit(5)

    return full_path, symlink_folder


def _collision_handler(rule, symlink_full_path, symlink_basepath, symlink_destination):
    should_overwrite = True
    symlinkpath_exists = False

    if os.path.isfile(symlink_full_path):
        symlinkpath_exists = True

    if rule in ["smart", "overwrite-if-symlink"]:
        if symlinkpath_exists:
            if not os.path.islink(symlink_full_path):
                should_overwrite = False

    if rule in ["smart", "overwrite-if-dst-same"]:
        if not symlink_full_path.startswith(symlink_basepath):
            should_overwrite = False

    if rule == "no-overwrite":
        should_overwrite = False

    if symlinkpath_exists:
        existing_symlink_destination = os.readlink(symlink_full_path)
        if symlink_destination == existing_symlink_destination:
            # Don't bother
            raise SkipFile('A symlink like this exists')

        log(
            f'Link ({symlink_full_path}) points to ({existing_symlink_destination}), we want ({symlink_destination})',
            loglevel='error', category='collision',
            data={
                'symlink_full_path': symlink_full_path,
                'existing_symlink_destination': existing_symlink_destination,
                'symlink_destination': symlink_destination
            }
        )

        if rule == "bail-if-different":
            sys.exit(20)

    if symlinkpath_exists and should_overwrite:
        if not _dry:
            os.remove(symlink_full_path)

    return True


def _handle_file_metadata(sourcepath, metadata_store):
    metadata_store.add('path', 'sourcepath', sourcepath)
    metadata_store.add('path', 'file-ext', sourcepath.split('.')[-1])

    if not _metadata:
        log(f'  * metadata unset', loglevel='debug')
        return

    log(f'  * _metadata is {_metadata}', loglevel='debug')

    for num, metaname in available_metadata_addons:
        if metaname not in _metadata:
            continue

        log(f'  * metadata-check: {metaname}', loglevel='debug')
        module = f'{num}_{metaname}'
        mod = importlib.import_module(f'.metadata.{module}', package='taggo')
        metadata_store.add('path', metaname, mod.run(sourcepath))
        _check_filter(f'after-{metaname}', metadata_store)


def make_symlink(symlink_basepath, sourcepath, *, nametemplate=None, metadata_store=None, collision_rule=None):
    metadata_store = metadata_store or Metadata()

    is_file = os.path.isfile(sourcepath)

    metadata_store.add_multiple('path', _path_variants(os.path.dirname(sourcepath)))
    metadata_store.add('path', 'hierarcy_str', _path_hierarcy_string(metadata_store['path'].get('hierarcy'), is_file))
    metadata_store.add('path', 'basename', os.path.basename(sourcepath))

    if is_file:
        try:
            log(f'  * is_file', loglevel='debug')
            log(f'  * checking metadata now', loglevel='debug')
            _check_filter('early', metadata_store)
            _handle_file_metadata(sourcepath, metadata_store)
        except SkipFile:
            log(f'  * skipping, filter didnt match', loglevel='verbose')
            log(metadata_store.data, loglevel='debug')
            return

    tags = find_tags(metadata_store['path']['basename'])
    metadata_store.add('path', 'tags', tags)
    log(f'  * found tags: {tags}', loglevel='debug')

    for tagset in tags.items():
        log(f'doing {tagset}', loglevel='debug')
        metadata_store.clear('tag')
        metadata_store.add_multiple('tag', _tag_variants(tagset))
        nametemplate = _nametemplate(nametemplate, is_file)
        symlink_full_path, symlink_folder = _symlink_paths(nametemplate, metadata_store, symlink_basepath)
        symlink_destination = os.path.relpath(sourcepath, symlink_folder)

        log(f'  * metadata_store: {metadata_store.data}', loglevel='debug')
        log(f'  * should create:', loglevel='debug')
        log(f'    * symlink: {symlink_full_path}', loglevel='debug')
        log(f'    * destination: {symlink_destination}', loglevel='debug')

        try:
            _check_filter('late', metadata_store)
            _collision_handler(collision_rule, symlink_full_path, symlink_basepath, symlink_destination)
        except SkipFile as reason:
            log(f'  * skipping: {reason}', loglevel='debug')
            continue

        try:
            if not _dry:
                os.symlink(
                    symlink_destination,
                    symlink_full_path,
                    target_is_directory=not is_file
                )

            log(
                f'Made {symlink_full_path} -> {symlink_destination}',
                loglevel='info', category='made-symlink',
                data={
                    'symlink_full_path': symlink_full_path,
                    'symlink_destination': symlink_destination
                }
            )
        except OSError as e:
            pass


def cleanup(dst, dry=False):
    configure(dry=dry)

    dst_path = os.path.abspath(dst)
    if not os.path.isdir(dst_path):
        raise exceptions.FolderException(f"Didnt find directory: {dst_path}")

    for root, _, files in os.walk(dst_path):
        for f in files:
            full_path = os.path.join(root, f)
            if not os.path.islink(full_path):
                continue

            symlink_destination = os.path.normpath(os.path.join(root, os.readlink(full_path)))
            exists = os.path.exists(symlink_destination)
            log(f"Symlink: {full_path}", loglevel='debug')
            log(f"  points to: {symlink_destination}", loglevel='debug')
            log(f"  destination exists: {exists}", loglevel='debug')

            if not exists:
                log(
                    f'Deleting dead symlink ({full_path}) pointed to {symlink_destination}',
                    loglevel='info', category='deleted-symlink',
                    data={
                        'symlink_path': full_path,
                        'symlink_destination': symlink_destination
                    }
                )

                if not _dry:
                    os.unlink(full_path)

    # This will eventually trigger another os.walk on what we just looped over.
    # But we might have just cleaned out a lot of old files, making folders empty after
    # our part1 cleanup. Doing it again is quick, and much less error prune than baking
    # in the logic in the loop above.
    utils.remove_empty_folders(dst_path, remove_root=False)


def rename(src, original, new, dry=False):
    configure(dry=dry)
    src_path = os.path.abspath(src)
    if not os.path.isdir(src_path):
        raise exceptions.FolderException(f"Didnt find src directory: {src_path}")
    log(f"Will look in folder '{src_path}' for tags to rename from '{original}' to '{new}'", loglevel="verbose")

    original_tag = f"#{original}"
    if not utils.fullmatch(hashtag_re, original_tag):
        raise exceptions.Error(f"Invalid hashtag: '{original_tag}'")

    new_tag = f"#{new}"
    if not utils.fullmatch(hashtag_re, new_tag):
        raise exceptions.Error(f"Invalid hashtag: '{new_tag}'")

    if original_tag == new_tag:
        raise exceptions.Error("There is no need to rename tag to the same...?")

    queue = []
    log("Starting collecting list of files/folders to rename:", loglevel="verbose")
    for root, dirs, files in os.walk(src_path):
        if dirs:
            for d in dirs:
                if original in hashtags_in(d):
                    full_path = os.path.join(root, d)
                    log(f"  Found directory: {full_path}", loglevel="verbose")
                    queue.append(full_path)

        if files:
            for f in files:
                if original in hashtags_in(f):
                    full_path = os.path.join(root, f)
                    log(f"  Found file: {full_path}", loglevel="verbose")
                    queue.append(full_path)

    # Start with the longest path, so we can be sure that we are not renaming a
    # folder that contains another file or folder we also should rename.
    # We must sort, or be dirty in the os.walk loop. This is much cleaner.
    for e in sorted(queue, key=len, reverse=True):
        dirname = os.path.dirname(e)
        old_basename = os.path.basename(e)
        new_basename = old_basename.replace(original_tag, new_tag)
        log(f"Renaming: {dirname}{os.path.sep}{{{old_basename} -> {new_basename}}}")
        if not _dry:
            os.rename(e, os.path.join(dirname, new_basename))


def info(src):
    src_path = os.path.abspath(src)
    log(f"Using src-path: {src_path}", loglevel="verbose")

    if not os.path.isdir(src_path):
        raise exceptions.FolderException(f"Didnt find src-path: {src_path}")

    folder_tags = []
    file_tags = []
    for root, dirs, files in os.walk(src_path):
        for d in dirs:
            folder_tags += hashtags_in(d)
        for f in files:
            file_tags += hashtags_in(f)

    folder_tags = sorted(set(folder_tags))
    file_tags = sorted(set(file_tags))

    log("Folder tags:")
    for folder_tag in folder_tags:
        log(f"  {folder_tag}")

    log("")
    log("File tags:")
    for file_tag in file_tags:
        log(f"  {file_tag}")


def _parse_cli_nametemplate(nametemplate, file=None, folder=None):
    if file and folder:
        return {'file': file, 'folder': folder}
    else:
        return nametemplate


def _parse_cli_filter(filter_data):
    # Example
    #  in: [['a'], ['a', 'mid'], ['b', 'pre', 'post', 'mid'], ['this is a filter']]
    #  out: {'late': {'this is a filter', 'a', 'b'}, 'mid': {'a', 'b'}, 'pre': {'b'}, 'post': {'b'}}

    filters = defaultdict(set)
    for entry in filter_data:
        query = entry.pop(0)
        if entry:
            for when in entry:
                filters[when].add(query)
        else:
            filters['late'].add(query)
    return dict(filters)


def _parse_cli_metadata(metadata_data):
    # Example
    #  in: [['a', 'opt1=1', 'opt2=2'], ['b']]
    #  out: {'a': {'opt1': '1', 'opt2': '2'}, 'b': {}}

    metadata = {}
    for entry in metadata_data:
        pluginname = entry.pop(0)
        metadata[pluginname] = {}
        for option in entry:
            try:
                option_name, option_value = option.split('=', 1)
            except ValueError:
                log(
                    f'Invalid option ({option}). Need an = sign',
                    loglevel='critical',
                    category='invalid-option-metadata',
                    data={'option': option}
                )
                sys.exit(1)
            metadata[pluginname][option_name] = option_value

    return metadata


def main(known_args=None, reraise=False):
    # We can set known_args to test the cli, or if you
    # got a special need where you want to run taggo that way.

    parser = argparse.ArgumentParser(
        description="Create symlinks to files/folders based on their names"
    )

    logoptions = parser.add_mutually_exclusive_group()
    logoptions.add_argument(
        "--debug",
        action="store_true",
        help="Print debug-info about what we are doing",
    )
    logoptions.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra info about what we are doing",
    )
    logoptions.add_argument(
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

    # What should we name the symlink?
    # You should include enough data here so we wont get a name-conflict.
    # In case of conflicts, the collision-handler below will decide what to do.
    parser_run.add_argument(
        "--nametemplate",
        help="A template-based name of what you want to call the symlinks themself."
             "See docs for more info. (default: %(default)s)",
        default=DEFAULT_NAMETEMPLATE,
        metavar='TEMPLATE'
    )

    parser_run.add_argument(
        "--nametemplate-file",
        help="Template if we link to a file",
        default=None,
        metavar='TEMPLATE'
    )

    parser_run.add_argument(
        "--nametemplate-folder",
        help="Template if we link to a folder",
        default=None,
        metavar='TEMPLATE'
    )

    parser_run.add_argument(
        "--filter",
        help=textwrap.dedent("""\
        Filtering using jmespath. Make sure it matches (returns true) for the files you want to include.
        You can specify multiple filters.

        If you want to specify WHEN you want to check against this filter, use one or more of the
        additional options below. This can be useful if you just want to check eg. the file-ext,
        which is available early.. You don't need to wait for all the metadata extensions to run.

          * early: As early as possible.
          * after-{metadata}: eg "after-exif", see below for which order they are run.
          * late: Just when we are about to create the links.. (this is the default if you dont specify WHEN)
          """),
        action="append",
        nargs='+',
        default=[],
        metavar=('FILTER', 'WHEN')
    )

    parser_run.add_argument(
        "--metadata",
        help=textwrap.dedent("""\
        Add extra metadata that will be available in filters and the name-templates.
        They are not enabled by default because some of them depends on 3rd party, or
        the might take additional time when we scan.
        You can also add options, using eg"--metadata pluginname option=value option2=value2",
        if the plugin supports that.

        Plugins, in order they run..

          * stat: File stat, like accesstime, size and so on..
          * filetype: Checks the first bytes of a file to figure out what it is
          * exif: Get some additional image-data available.
          * md5: Calculate the md5 checksum of a file.
          """),
        action="append",
        nargs='+',
        default=[],
        metavar=('PLUGIN', 'OPTIONS')
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
        help="Source folder/file"
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

    if args.verbose or os.environ.get("VERBOSE"):
        configure(output='VERBOSE')

    if args.debug or os.environ.get("DEBUG"):
        configure(output='DEBUG')

    if args.quiet or os.environ.get("QUIET"):
        configure(output='QUIET')

    try:
        if args.cmd == 'run':
            run(
                args.src, args.dst,
                filters=_parse_cli_filter(args.filter),
                metadata=_parse_cli_metadata(args.metadata),
                auto_cleanup=args.auto_cleanup,
                dry=args.dry,
                nametemplate=_parse_cli_nametemplate(
                    args.nametemplate,
                    file=args.nametemplate_file,
                    folder=args.nametemplate_folder
                )
            )
        elif args.cmd == 'cleanup':
            cleanup(args.dst, dry=args.dry)
        elif args.cmd == 'rename':
            rename(args.src, args.original, args.new, dry=args.dry)
        elif args.cmd == 'info':
            info(args.src)
    except exceptions.Error as e:
        log(e, loglevel='error', category='exception')
        if reraise:
            raise
        sys.exit(2)


if __name__ == "__main__":  # pragma: no cover
    main()  # pragma: no cover
