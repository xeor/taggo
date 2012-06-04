taggo
=====

Tag organizer that uses filenames and symlinks to create tags.


:Status:
    Alpha stage.. Dont use :)
:Documentation:
    http://taggo.readthedocs.org/en/latest/
:Author:
    Lars Solberg

Introduction
------------

This project is in beta stage, please report bugs :)

Resources
---------

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

Taggo creates symlinks based on several criterias. Here is a list of
rules it uses to deside if it creates a symlink in the tag folder or
not.


.. list-table:: Tag naming rules
   :widths: 10 40
   :header-rows: 1

   * - Rule
     - Description
   * - Ignored folders
     - If we are in one ignored folder (currently just .AppleDouble and "iPod Photo Cache", we are ignoring every files in it. Note; we will still go into subfolders...
   * - No file id-name
     - The first word (split by space), is taken away in the filename.
   * - No fileext
     - Everything after the last . and the . itself is taken away.
   * - No numbers and space only tags
     - If the only thing the tag contains is numbers and spaces, it is ignored.
   * - Starts with numbers
     - Tags that starts with numbers are also ignored.

Filename to tagname examples
----------------------------

Here is a list of examples on how this works with the default configuration.
The example is with a picture gallery, and taggo is configured to use
/pictures as main path for where it finds the files it will tag, and
/tags for where to store the symlinks.

.. list-table:: Naming examples
   :widths: 35 40
   :header-rows: 1

   * - Filepath
     - Symlink
   * - /pictures/2011-07-27 14.40.38 Animals-Lions.jpg
     - /tags/Animals/Lions/root - 2011-07-27 14.40.38 Animals-Lions.jpg
   * - /pictures/2011 trip/dcim1234 Animals-Lions.jpg
     - /tags/Animals/Lions/2011 trip - dcim1234 Animals-Lions.jpg
   * - /pictures/2012 Paris tour/DCIM1237 Food, People-John, People-Paul.jpg
     - /tags/Food/2012 Paris tour - DCIM1237 Food, People-John, People-Paul.jpg

       /tags/People/John/2012 Paris tour - DCIM1237 Food, People-John, People-Paul.jpg

       /tags/People/Paul/2012 Paris tour - DCIM1237 Food, People-John, People-Paul.jpg

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
