import os
import re
import logging

from collections import defaultdict

from . import filters

logger = logging.getLogger("taggo")


# Original from https://gist.github.com/jacobtomlinson/9031697
def remove_empty_folders(path, remove_root=True):
    if not os.path.isdir(path):
        return

    # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                remove_empty_folders(fullpath)

    # if folder empty, delete it, but not if it's an symlink (happens if it's a link to a folder that is empty..
    # Don't delete those)
    files = os.listdir(path)
    if len(files) == 0 and remove_root and not os.path.islink(path):
        logger.info("Removing empty folder: {}".format(path))
        os.rmdir(path)


# Original from
# https://stackoverflow.com/questions/30212413/backport-python-3-4s-regular-expression-fullmatch-to-python-2
def fullmatch(regex, string):
    if hasattr(re, 'fullmatch'):
        return regex.fullmatch(string)

    m = re.match(regex, string)
    if m and m.span()[1] == len(string):
        return m


def get_exif_data(filepath):
    import piexif

    try:
        exifdata = piexif.load(filepath)
    except piexif.InvalidImageDataError:
        return {}

    # How to present?
    # exifdata['GPS'][piexif.GPSIFD.GPSLatitudeRef],  # N
    # exifdata['GPS'][piexif.GPSIFD.GPSLatitude],     # ((59, 1), (50, 1), (1111, 100))
    # exifdata['GPS'][piexif.GPSIFD.GPSLongitudeRef], # E
    # exifdata['GPS'][piexif.GPSIFD.GPSLongitude],    # (10, 1), (50, 1), (3000, 100))
    gpslatlon = None

    return {
        'exif_ImageLength': exifdata['0th'][piexif.ImageIFD.ImageLength],
        'exif_ImageWidth': exifdata['0th'][piexif.ImageIFD.ImageWidth],
        'exif_Make': exifdata['0th'][piexif.ImageIFD.Make].decode('utf-8'),
        'exif_Model': exifdata['0th'][piexif.ImageIFD.Model].decode('utf-8'),
        'exif_Orientation': exifdata['0th'][piexif.ImageIFD.Orientation],

        'exif_Flash': exifdata['Exif'][piexif.ExifIFD.Flash],

        'exif_GPSAltitudeRef': exifdata['GPS'][piexif.GPSIFD.GPSAltitudeRef],
        'exif_GPSLatLon': gpslatlon,
    }


def get_rel_folders_string(relative_path, is_file):
    if (not relative_path) or (len(relative_path) == 1 and not is_file):
        return 'root'

    if is_file:
        return '_'.join(relative_path)
    else:
        return '_'.join(relative_path[:-1])


try:
    import filetype
    filetype_matchers = [i for i in dir(filetype) if i.endswith('_matchers')]
except ImportError:
    pass


def get_filetype_data_group(filetype_obj):
    for fm in filetype_matchers:
        if filetype_obj in getattr(filetype, fm):
            return fm.split('_')[0]
    return ''


def get_filetype_data(filepath):
    filetype_obj = filetype.guess(filepath)
    if not filetype_obj:
        return {}

    return {
        'filetype_extension': filetype_obj.extension,
        'filetype_mime': filetype_obj.mime,
        'filetype_group': get_filetype_data_group(filetype_obj),
        'filetype_mime_0': filetype_obj.mime.split('/')[0],
        'filetype_mime_1': filetype_obj.mime.split('/')[1]
    }


def from_string_to_py(value, filtername):
    # All we got in filters are strings... We need to convert them to make them easier to handle
    if value == 'None':
        return None

    if filtername in ['contains', 'icontains']:
        return value.split(',')

    if filtername in ['gt', 'gte', 'lt', 'lte']:
        return int(value)

    # Nothing special to do..
    return value


def make_filters(filter_list):
    # param: test, value: [a,b,c], filter: contains
    # param: test2, value: something, filter: exact
    # param: filetype_group, value: image, filter: exact

    ready_filters = defaultdict(list)

    for f in filter_list:
        # 'filetype_group=image'
        # 'filetype_group__in=image,video'
        parts = f.rsplit('__', 1)
        if len(parts) == 1:
            search_param, search_value = parts[0].rsplit('=', 1)
            search_filtername = 'exact'
        else:
            search_param, search_info = parts
            search_filtername, search_value = search_info.rsplit('=', 1)

        search_value = from_string_to_py(search_value, search_filtername)

        func = getattr(filters, search_filtername)

        # We run filters by group, trying to run them in the correct order.
        # Those filter that doesnt belong to a group should be quick to execute. We put them first.
        group = search_param.split('_')[0]
        if group not in ['filetype']:
            group = 'pre'

        ready_filters[group].append({
            'key': search_param,
            'value': search_value,
            'func': func,
        })

    return ready_filters
