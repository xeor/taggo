import hashlib


def run(filepath):
    return hashlib.md5(open(filepath, 'rb').read()).hexdigest()
