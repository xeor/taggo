taggo
=====

.. image:: https://img.shields.io/pypi/v/taggo.svg
        :target: https://pypi.python.org/pypi/taggo

.. image:: https://img.shields.io/travis/xeor/taggo.svg
        :target: https://travis-ci.org/xeor/taggo

.. image:: https://img.shields.io/coveralls/xeor/taggo.svg
        :target: https://coveralls.io/github/xeor/taggo?branch=master

.. image:: https://readthedocs.org/projects/taggo/badge/?version=latest
        :target: https://taggo.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/xeor/taggo/shield.svg
     :target: https://pyup.io/repos/github/xeor/taggo/
     :alt: Updates

Tag organizer that uses names of files and folders to create symlinks.
Tags are defined by using #hashtags in the name. They can also be as many sub levels as you want, like #sub-hash-tag

**note**
This version should work now, but the "old" version is still tagged at https://github.com/xeor/taggo/tree/0.2.
The old version worked fine at python 2 (but not 3). It also had config-file instead of parameters. Check out the
repo if you want it..

* Free software: MIT license
* Documentation: https://taggo.readthedocs.io
* Source: https://github.com/xeor/taggo
* Issues: https://github.com/xeor/taggo/issues

Introduction
------------

This project is in beta stage, please report bugs :)

Any questions, thoughts, bugs are very welcome!


Requirements
------------

* Python 3.6 or newer for now.. Will possible work on earlier versions as well.


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

FAQ
---

* Why the name taggo?

  * It's a tagging tool. It does stuff with tags. What do you suggest? Tagging, taggs, tags, tag2fold... no.. Taggo!

* Why do you want to create tags with symlinks?

  * Because everyone have underestimated the power of tagging data.
  * Photo filenames are just wasted, what does DCIM1234.jpg tell you?
  * You know you miss one folder that contains all your dog pictures.
  * You sould not depend on a 3rd party program/database to manage
    your files/photos.
