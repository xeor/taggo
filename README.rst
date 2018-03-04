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
This version is a completey different version than the old (https://github.com/xeor/taggo/tree/0.2).
The old version works for python 2 (but not 3). It also had config-file instead of parameters. Check out the
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

* 3.6+


Docker
------

Start the container with environment variables like `CRON_TAGGO_0` with the format `* * * * *|run ....`

* CRON_TAGGO_n where n is a number, start at 0, have as many as you want.
* We take care automaticly that only 1 of each number is running at a time. Example, if one of your job is running every minute and it takes more than a minute to finish. It wont start the 2nd time.
* The environment variable is split in 2 by a `|`. The first param is a cron, the 2nd is the parameters sent to the `taggo` command.

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
