import filetype

filetype_matchers = [i for i in dir(filetype) if i.endswith('_matchers')]


def get_filetype_data_group(filetype_obj):
    for fm in filetype_matchers:
        if filetype_obj in getattr(filetype, fm):
            return fm.split('_')[0]
    return ''


def run(filepath):
    filetype_obj = filetype.guess(filepath)
    if not filetype_obj:
        return {}

    return {
        'extension': filetype_obj.extension,
        'mime': filetype_obj.mime,
        'group': get_filetype_data_group(filetype_obj),
        'mime_0': filetype_obj.mime.split('/')[0],
        'mime_1': filetype_obj.mime.split('/')[1]
    }
