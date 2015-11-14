taggo
=====

Tag organizer that uses names of files and folders to create symlinks.
Tags are defined by using #hashtags in the name. They can also be as many sub levels as you want, like #sub-hash-tag

:Status:
    Beta stage.. Report bugs :)
:Documentation:
    This page
:Author:
    Lars Solberg
:Blog post:
    http://blog.boa.nu/2012/11/tagging-files-and-folders-using-hashtags-and-symlinks.html

Introduction
------------

This project is in beta stage, please report bugs :)

Resources
---------

* `Dockerized version <https://github.com/xeor/dockerfiles/tree/master/taggo>`_
* Project hosting `GitHub <https://github.com/xeor/taggo>`_.
* Bug reports are handled on the `issue tracker
  <https://github.com/xeor/taggo/issues>`_.

Any questions, thoughts, bugs are very welcome!


Requirements
------------

* Python 2.6 or newer (not 3.x)

Installation
------------

The only file you will need is the one called taggo. It creates a file
called taggo.cfg if it doesnt exists in the same directory.

What it does
------------

Taggo creates symlinks based on hashtags it finds in the file or foldername.

Here are some examples

.. list-table:: Filename examples
   :widths: 10 40
   :header-rows: 1

   * - Fil/folder names
     - Creates
   * - A random name.jpg
     - 
   * - dcim1234 #People-Lars #food.jpg
     - 1 link in a folder People/Lars/... and one in food/
   * - 2012-09-25 Oslo tour #Earth-Europe-Norway-Oslo/dcim123...
     - Link to the folder under Earth/Europe/Norway/Oslo/2012-09-25....
   * - dcim123,#tag1.jpg
     - Link to the file under tag1/
   * - dcim321#tag2.jpg
     - Nothing, a tag needs a space, . or , in front and back of the tag.

usage
-----

.. list-table:: Commandline options
   :widths: 10 40
   :header-rows: 1

   * - Command
     - Description
   * - ./taggo help
     - Display help
   * - ./taggo run_once
     - Delete dead symlinks in the tag folder, then goes trough and the ones we are missing.
   * - ./taggo cleanup
     - Deletes dead symlinks in the tag folder.
   * - ./taggo make_tags
     - Creates new tags
   * - ./taggo rename FROM TO
     - Renames tags in the filenames themself. Useful if you have files with tag typos or if you want to do a cleanup. Support both folders and files. Note that this does not change the symlinks, only sourcefiles. You should run run_once after renaming.

taggo.cfg
---------

.. list-table:: Configuration options
   :widths: 10 40
   :header-rows: 1

   * - Option
     - Description
   * - [general] debug
     - Turn on (1) or off (1) extra debug when taggo is running
   * - [general] tag_indicator
     - Which tag should a tag begin with (default #)
   * - [general] subtag_separator
     - Character that separates subtags (default -)
   * - [general] use_relative_links
     - Turn on (1) or off (0) to create symlinks that uses relative paths or not. Default to using full path
   * - [general] rel_folders_replacer
     - What to replace the / with when using the path in the name as %(rel_folders)s
   * - [general] tag_filenames
     - Filename to give tags (symlinks). %(rel_folders)s is replaced with related folders upto this folder. %(basename)s is replaced with the filename itself.
   * - [general] strip_dot_files
     - Take away folders/files if they starts with a . (default true)
   * - [paths] content_folder
     - Folder to look for files we can symlink to. Set it to example "./pictures" if there is a folder called pictures relative to taggo. Or use full path.
   * - [paths] tag_folder
     - Same as content_folder, except this is the folder where we are going to place the symlinks.

FAQ
---

* Why the name taggo?

  * I just wanted a name for this for now.. Got any better names,
    please share

* Why do you want to create tags with symlinks?

  * Because everyone have underestimated the power of tagging data.
  * Photo filenames are just wasted, what does DCIM1234.jpg tell you?
  * You know you miss one folder that contains all your dog pictures.
  * You sould not depend on a 3rd party program/database to manage
    your files/photos.
