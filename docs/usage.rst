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

--metadata-addon, --metadata-default
""""""""""""""""""""""""""""""""""""

Add extra-data to use in filters or symlink-name. Use metadata-addon multiple times to add multiple.

Currently you can define:

* stat
* filetype
* exif
* md5

Use `--metadata-default` to define defaults if some of the addons is not producing data on everything.
Example `--metadata-default key_should_exist=value`

--auto-cleanup
""""""""""""""

Run cleanup (see own command) after we are done


--filter, --filter-mode
"""""""""""""""""""""""

Filters are checked in the order of how expensive the metadata is to calculate.. If a filter have a match, and there are no more filter to check.
We will include or skip the file acordonly..

We do some string to object convertion, so if you define surtain strings, they behave specially. Example:

* --filter 'value=None': Matches if value is not defined.

Filters are split up with the `key`, an `operator`, then a `value`.
A filter can example be `file-ext=jpeg`, `file-ext__contains=jpeg,png,gif`.
We add `exact` as a operator if it is not specified. You specify an operator like above where `contains` is the operator.

Valid operators are:

* `exact`: The default (==)
* `neq`: Not equal (!=)
* `contains`: Value must be a comma-separated list of items to match against.
* `icontains`: Same as contains, but doesnt care about case
* `startswith`, `istartswith`, `endswith`, `iendswith`: Selfexplain
* `gt`, `gte`, `lt`, `lte`: GreaterThan, GreaterThanEqueal, LessThan, LessThanEqual. Values must be numbers!
* `regex`: Checks using python re.match()

Include (--filter-mode=include) are using logical AND. In other words, every --filter you define must match in order for it to be included.
Exclude used logical OR. So, if any of the exclude filter matches. It will be excluded.

If you are using a filter that we don't have data on, example `--filter non_existing=abc`, we will ignore it.

--filter-query
""""""""""""""

If you install `jmespath`, you can use `--filter-query`. This is a very powerfull json query-language (http://jmespath.org/).
See what the pros and cons are on the comparison of --filter-query and --filter below.

Examples
* --filter-query='tag.original == `test`'
* --filter-query='contains(paths.*, `archive`) && "file-ext" == `jpg`'


--symlink-name, --symlink-name-file, --symlink-name-folder
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

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

* file-ext (only on --symlink-name-file): .jpg

* md5 (only on --symlink-name-file, need --metadata-addon md5): d41d8cd98f00b204e9800998ecf8427e

* stat (need --metadata-addon stat)
** This makes a bunch of file/folder stats available (using the python os.stat) function. Use --debug to see what you have.
** We will also make a _iso version of atime, ctime and mtime with iso8601 of the value
** As well as _year, _month and _day

* exif (only on --symlink-name-file, need --metadata-addon exif, and python package `piexif` installed)
** You should set the template-keys you depends on with default-values using --metadata-default, or you might easiely get errors
** These will be available (flat)
*** exif_...

Example

* --symlink-name, like `--symlink-name "{tag[as-folders]}/{basename}"`
* --symlink-name-file "{md5}" --symlink-name-folder "{tag[as-folders]}/{basename}" --metadata-addon md5

Note that if you want to use `--symlink-name-file` or `--symlink-name-folder`, both needs to be defined. Else `--symlink-name` is used.

Difference between `--filter` and `--filter-query`
--------------------------------------------------

TLDR: If possible, use `--filter` for speed :)

The longer story, is that --filter knows what you are filtering on, before it completes all the metadata-addon calculations.
This is because the correct filter gets checked after each metadata calculation. Example, when the `stat` addon is done, the `stat` filters are checked.
If the filter dictates that it should skip the file, no more metadata calculation is done for that file.
This is usefull and can save you some time. However, there are some big cons using the --filter:

* You wont be able to filter on data that is not flat. Example, there are no way to filter on `paths[]...`
* It is not that powerfull, and doing logical AND, OR, NOT and such are a pain.

The `--filter-query` is using jmespath, and it have a very powerfull querylanguage. It can handle more logic, and is much more powerfull than `--filter`.
However.. There are some cons:

* It depends on a 3rd party lib (`pip install jmespath`)
* The filter are checked once per file, after all metadata addons are calculated.

Both filter-types can however be combined.. So you can do a quick check using --filter, then a more advanced check later using --filter-query

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

