import typing


def load_module(path: str) -> typing.Any:
    splited_path = path.split(".")
    mod = __import__(".".join(splited_path[:-1]))
    for component in splited_path[1:]:
        mod = getattr(mod, component)
    return mod
