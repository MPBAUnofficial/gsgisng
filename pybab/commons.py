def dict_join(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result
