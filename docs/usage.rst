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

cli options (run)
^^^^^^^^^^^^^^^^^

--metadata
""""""""""

Add extra-data to use in filters or symlink-name. Use metadata-addon multiple times to add multiple.

Currently you can define:

* stat
* filetype
* exif
* md5


--auto-cleanup
""""""""""""""

Run cleanup (see own command) after we are done


--filter
""""""""

Taggo uses `jmespath`, for filtering. This is a very powerfull json query-language (http://jmespath.org/).

Examples
* --filter='tag.original == `test`'
* --filter='contains(paths.*, `archive`) && "file-ext" == `jpg`'


--nametemplate, --nametemplate-file, --nametemplate-folder
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Let say we have

* src folder: tests/test_files/
* a tagged file: tests/test_files/tagged/folders/i-3 #Hollydays-Christmas.jpg
* dst folder: temp

Then the template tags will become

* tag[original]: 'Hollydays-Christmas'
* tag[as-folders]: 'Hollydays/Christmas'

* tag-param[original]: If your tag was in the format #tag(param here), this would be "param here"

* rel_folders: tagged_folders
** Which is a `_` separated list of folders from the file, all the way up to the dst folder
** It will be set to "root" if there are no list of relative paths
** We will not include the tagged folder itself if we this is a tagged folder.

* basename: i-3 #Hollydays-Christmas.jpg
** Name of the file

* paths[0]: folders
* paths[1]: tagged
* paths[2]:

You can add additional template-values you can use by using `metadata`, see below for info.

You can also use `dot notation`, like `{tag.original}`.

A good way to test what you have to play with is using taggo like this:
`taggo --debug run --metadata md5 --metadata exif --metadata stat --metadata filetype --dry "folder/#tag1.txt .`

Example templates:

* --nametemplate, like `--nametemplate "{tag[as-folders]}/{basename}"`
* --nametemplate-file "{md5}" --nametemplate-folder "{tag[as-folders]}/{basename}" --metadata-addon md5

Note that if you want to use `--nametemplate-file` or `--nametemplate-folder`, both needs to be defined. Else `--nametemplate` is used.

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

