import os
import datetime


def run(filepath):
    stat_datastore = {}
    stat = os.stat(filepath)
    for keyname in dir(stat):
        if not keyname.startswith('st_'):
            continue
        value = getattr(stat, keyname)
        keyname = keyname.replace('st_', '', 1)
        if keyname in ['atime', 'ctime', 'mtime']:
            timestamp = datetime.datetime.fromtimestamp(value)
            value = {
                'iso': timestamp.isoformat(),
                'year': timestamp.year,
                'month': timestamp.month,
                'day': timestamp.day
            }

        stat_datastore[keyname] = value

    return stat_datastore
