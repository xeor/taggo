import re


def exact(data, value):
    return data == value


def neq(data, value):
    return data != value


def contains(data, value):
    return data in value


def icontains(data, value):
    if data is None:
        return False

    value = [i.lower() for i in value]
    return data.lower() in value


def startswith(data, value):
    return data.startswith(value)


def istartswith(data, value):
    return data.lower().startswith(value.lower())


def endswith(data, value):
    return data.endswith(value)


def iendswith(data, value):
    return data.lower().endswith(value.lower())


def gt(data, value):
    return value > int(data)


def gte(data, value):
    return value >= int(data)


def lt(data, value):
    return value < int(data)


def lte(data, value):
    return value <= int(data)


def regex(data, value):
    return re.match(value, data) is not None
