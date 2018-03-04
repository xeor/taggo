=======
History
=======

0.13.0 (2018-03-04)
-------------------

* Dropping python 2.x support... Some things might end up being problematic to support. Like symlinks for directories in windows.
  So instead of making a bunch of hacks around functionality. It is now dropped.

0.12.0 (2018-03-03)
-------------------

* Making symlink name template configurable
* Symlink collision handling
* Logs to stdout/stderr depending on message severety
* Option to output log as json
* Option to prompt/wait after each symlink. Usefull for debugging
* Lots of things around symlink-name-templates, it's now completly configurable.
* Possible to have extrainfo (used in symlink-name) from a tag parameter. Like #tag(info)
* Using powerful filters to not symlink certain files, or only symlink some files.
* Metadata-addons to use special file-info as in the symlink-name, like md5, stat, exif-data, ...
* Output data as json, if you want a logparser to use it. Single-lines..
* Configurable collision handling. If symlink already exist and points to a different file.
* Making `pip install taggo[all]` to get all metadata-addon required libs
* --auto-cleanup option in `run`
* Log different messages to stdout or stderr


0.11.0 (2018-02-20)
-------------------

* Fixing up docker image


0.10.0 (2017-11-04)
-------------------

* Basic docker image

0.9.0 (2017-10-21)
------------------

* Python 2.7 support

0.8.0 (2017-10-21)
------------------

* Good test coverage
* Things are mostly working
* Rename functionality
* List/info
* Much more

0.4.0 (2017-10-08)
------------------

* Started a complete rewrite, mainly focusing on using python 3.6
* Test on PyPI.. Non working version.

0.2 (2017-10-07)
------------------

* Checkpoint of the old version working only with 2.x. This checkpoint contains code from many years ago.
