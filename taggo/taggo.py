import sys
import re

import os
import logging
import argparse


def setup_log(debug=False):
    if debug or os.environ.get("DEBUG"):
        loglevel = "DEBUG"
    else:
        loglevel = "INFO"

    logging.basicConfig(
        level=getattr(logging, loglevel),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


class Taggo:
    def __init__(self, args):
        logging.debug(f"Initializing using options: {args.__dict__}")

    def run(self):
        pass

    def cleanup(self):
        pass


if __name__ == "__main__":
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

    args = parser.parse_args()

    setup_log(args.debug)

    t = Taggo(args)
    getattr(t, args.cmd)


class TaggoOld:
    debug = False
    config = None
    content_folder = ''
    tags_folder = ''

    def __init__(self):
        self.mydir = os.path.dirname(os.path.abspath(__file__))

        # Look for config file in the taggo directory. If it's not
        # found, then we'll assume we want to use $HOME/.taggo.cfg
        self.config_file = None
        if os.path.isfile('%s/taggo.cfg' % self.mydir):
            self.config_file = '%s/taggo.cfg' % self.mydir
        else:
            home_path = os.environ.get('HOME', None)
            home_cfg = '%s/.taggo.cfg' % home_path
            self.config_file = home_cfg

        if not self.config_file:
            #print 'Writing default config to %s\n' % self.config_file
            self.write_config()

        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_file)
        self.debug = self.get_config('general', 'debug', 'bool')

        self.use_relative_links = self.get_config('general', 'use_relative_links', 'bool')
        self.content_folder = self._get_fullpath('content_folder')
        self.tags_folder = self._get_fullpath('tag_folder')
        self.strip_dot_files = self.get_config('general',
                                               'strip_dot_files', 'bool')

        self.tag_indicator = self.get_config('general', 'tag_indicator')

        self.hashtag_extracter = re.compile(r'\B%s([^ \.,]+)\b' % self.tag_indicator)

    def _get_fullpath(self, config_name):
        raw_folder = self.get_config('paths', config_name)
        if raw_folder[0] == '.':
            # Assume relativ path to the script home, as in the docs
            return os.path.abspath('%s/%s' % (self.mydir, raw_folder))
        else:
            return os.path.abspath(raw_folder)

    def _del_empty_dirs(self, s_dir):
        # Original @ https://gist.github.com/1569173

        b_empty = True

        for s_target in os.listdir(s_dir):
            s_path = os.path.join(s_dir, s_target)

            if os.path.isdir(s_path):
                if not self._del_empty_dirs(s_path):
                    b_empty = False
            else:
                b_empty = False

        if b_empty:
            # if self.debug:
            #     print 'deleting empty dir %s' % (s_dir,)

            os.rmdir(s_dir)  # os.rmdir can only allowed to delete empty directories

        return b_empty

    def _make_symlink(self, full_path):
        rel_folders_replacer = self.get_config('general',
                                               'rel_folders_replacer')
        subtag_separator = self.get_config('general', 'subtag_separator')
        tag_filenames = self.get_config('general', 'tag_filenames')

        # Populated with info we can use in the configuration when deciding on the naming
        replace_info = {}

        relative_path = full_path.replace(self.content_folder + os.path.sep, '', 1).split(os.path.sep)
        if len(relative_path) <= 1:
            replace_info['rel_folders'] = 'root'
        else:
            replace_info['rel_folders'] = rel_folders_replacer.join(relative_path[:-1])

        basename = relative_path[-1]
        replace_info['basename'] = basename

        tags = set(self.hashtag_extracter.findall(basename))

        for tag in tags:
            tag = tag.replace(subtag_separator, os.path.sep)
            tag_folder = os.path.join(self.tags_folder, tag)
            tag_name = tag_filenames % replace_info

            if not os.path.isdir(tag_folder):
                # if self.debug:
                #     print '* Creating folder(s) %s' % tag_folder
                os.makedirs(tag_folder)

            full_symlink_path = os.path.join(tag_folder, tag_name)
            if not os.path.islink(full_symlink_path):
                # if self.debug:
                #     print 'Source file: %s' % full_path
                #     print 'Symlink', full_symlink_path
                #     print
                os.symlink(full_path, full_symlink_path)

    def help(self):
        pass
        # print 'Usage: taggo option\n'
        # print "A default configuration file will be written if it doesn't exist.\n"
        # print 'Options:'
        # print '  help                 This text.'
        # print '  run_once             Cleanup first, and then create new tags. Once'
        # print '  cleanup              Look for and delete dead symlinks'
        # print '  make_tags            Create missing symlink tags'
        # print '  rename <from> <to>   Example "taggo rename People-Paul People-Family-Paul", or "taggo rename Pau Paul.'
        # print "                       This will only rename files, not tags, so you should run `run_once' after this."

    def write_config(self):
        config = ConfigParser.RawConfigParser()
        config.add_section('general')
        config.set('general', 'debug', '0 ; 1 is true, 0 is false')
        config.set('general', 'tag_indicator', '#')
        config.set('general', 'use_relative_links', '1 ; 1 is true, 0 is false')
        config.set('general', 'subtag_separator',
                   '- ; Character to split the tag into sub-tags on.')
        config.set('general', 'rel_folders_replacer', '_')
        config.set('general', 'tag_filenames',
                   '%(rel_folders)s - %(basename)s')
        config.set('general', 'strip_dot_files', '1')

        config.add_section('paths')
        config.set('paths', 'content_folder',
                   './pictures ; Full path or relative to main_folder if it starts with ./')
        config.set('paths', 'tag_folder', './tags ; Full path or relative to main_folder if it starts with ./')

        config_fp = open(self.config_file, 'wb')
        config.write(config_fp)
        config_fp.close()

    def get_config(self, section, item, type='normal'):
        try:
            if type == 'normal':
                return self.config.get(section, item)
            if type == 'bool':
                return self.config.getboolean(section, item)

        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as e:
            # print 'Configuration error: %s' % e
            sys.exit(2)

    def rename(self, original, to):
        # if self.debug:
        #     print 'Will rename every tags %s to %s' % (original, to)

        re_tag = re.compile(r'\B%s%s\b' % (self.tag_indicator, original))

        for root, dirs, files in os.walk(self.content_folder):
            if re_tag.search(root):
                new_folderpath = re_tag.sub('%s%s' % (self.tag_indicator, to), root)

                # if self.debug:
                #     print 'Going to rename folder', root
                #     print '  >', new_folderpath
                #     print

                os.rename(root, new_folderpath)
                root = new_folderpath

            for file in files:
                if re_tag.search(file):
                    new_filename = re_tag.sub('%s%s' % (self.tag_indicator, to), file)

                    new_path = os.path.join(root, new_filename)
                    old_path = os.path.join(root, file)

                    # if self.debug:
                    #     print 'Going to rename', old_path
                    #     print '  >', new_path
                    #     print

                    os.rename(old_path, new_path)

    def make_tags(self):
        """
        Function that goes through and creates missing tag folders and
        missing symlinks
        """

        # if self.debug:
        #     print 'Running make_tags()'

        for root, dirs, files in os.walk(self.content_folder):
            basefolder = os.path.basename(root)

            # If the option self.strip_dot_files is defined,
            # the dotfiles/dotfolders will be excluded.
            if self.strip_dot_files:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                files[:] = [f for f in files if not f.startswith('.')]

            if self.tag_indicator in basefolder:
                self._make_symlink(root)

            for file in files:
                # This line checks for the tag indicator and that the file
                # is not being included from the folder that contains the
                # symlinks that will be created with this loop.
                if self.tag_indicator in file and not root.startswith(
                        self.tags_folder):

                    # if self.debug:
                    #     print 'tag: %s (from %s)' % (file, root)
                    full_path = '%s/%s' % (root, file)
                    self._make_symlink(full_path)

    def cleanup(self):
        """
        Goes trough every symlink and checks if they are still valid.
        If they are not, it deletes them. There is no good way to
        detect where they belongs now, and make_tags will recreate
        them with the right path

        This is made so it's only possible to delete symlinks and empty
        folders, in other words, it should be very safe to use :)
        """

        # if self.debug:
        #     print 'Running cleanup()'
        #     print 'Starting removing dead links'

        for root, dirs, files in os.walk(self.tags_folder):
            if files:
                for f in files:
                    try:
                        full_path = os.path.join(root, f)
                        if not os.path.exists(os.readlink(full_path)):
                            os.unlink(full_path)
                            #if self.debug:
                            #    print 'Removing dead link %s' % full_path
                    except OSError:
                        pass

        # if self.debug:
        #     print 'Starting removing empty directories'
        self._del_empty_dirs(self.tags_folder)


# if __name__ == '__main__':
#     taggo = Taggo()
#
#     try:
#         arg = sys.argv[1]
#     except IndexError:
#         arg = None
#
#     if arg == 'make_tags':
#         taggo.make_tags()
#         sys.exit(0)
#
#     if arg == 'cleanup':
#         taggo.cleanup()
#         sys.exit(0)
#
#     if arg == 'run_once':
#         taggo.cleanup()
#         taggo.make_tags()
#         sys.exit(0)
#
#     if len(sys.argv) == 4:
#         if arg == 'rename':
#             taggo.rename(original=sys.argv[2], to=sys.argv[3])
#         sys.exit(0)
#
#     taggo.help()
