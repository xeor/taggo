=====
Usage
=====

Taggo is most usefull if you use it on the commandline

Files and folders example layout::

    root@4c95ee980234:/# find /data/
    /data/
    /data/2016
    /data/2016/best taco #recipes-dinner.txt
    /data/2016/python snippets #projects-programming-python.txt
    /data/2017
    /data/2017/#traveling-london
    /data/2017/#traveling-london/places to visit.txt
    /data/2017/#traveling-london/airplane tickets.pdf
    /data/2015
    /data/2015/chocolate cake #recipes-cake.txt
    /data/2015/truffle chicken #recipes-dinner.txt
    /data/2015/#important note.txt


Making symlinks
---------------

You can now run taggo to create symlinks to the tagged files::

    root@4c95ee980234:/# pip install taggo
    root@4c95ee980234:/# taggo run data tags
    root@4c95ee980234:/# find tags/
    tags/
    tags/traveling
    tags/traveling/london
    tags/traveling/london/2017_#traveling-london - #traveling-london
    tags/recipes
    tags/recipes/cake
    tags/recipes/cake/2015 - chocolate cake #recipes-cake.txt
    tags/recipes/dinner
    tags/recipes/dinner/2016 - best taco #recipes-dinner.txt
    tags/recipes/dinner/2015 - truffle chicken #recipes-dinner.txt
    tags/important
    tags/important/2015 - #important note.txt
    tags/projects
    tags/projects/programming
    tags/projects/programming/python
    tags/projects/programming/python/2016 - python snippets #projects-programming-python.txt

notice that we have created a folder hieracy based on your tags with symlinks pointing to the correct files.

Cleanup
-------

Symlinks that are dead can be cleaned up easiely::

    root@4c95ee980234:/# rm "/data/2016/best taco #recipes-dinner.txt"

    root@4c95ee980234:/# taggo cleanup tags/
    Deleting symlink /tags/recipes/dinner/2016 - best taco #recipes-dinner.txt

List tags
---------

To list tags available in a source directory::

    root@4c95ee980234:/# taggo info data/
    Folder tags:
      traveling-london

    File tags:
      important
      projects-programming-python
      recipes-cake
      recipes-dinner

Rename tags
-----------

You can also rename tags if you want them nested another way, or just got a typo::

    root@4c95ee980234:/# taggo rename data/ traveling-london traveling-uk-london
    Renaming: /data/2017/{#traveling-london -> #traveling-uk-london}

    root@4c95ee980234:/# taggo cleanup tags/
    Deleting symlink /tags/traveling/london/2017_#traveling-london - #traveling-london
    Removing empty folder: /tags/traveling/london
    Removing empty folder: /tags/traveling

    root@4c95ee980234:/# taggo run data tags

