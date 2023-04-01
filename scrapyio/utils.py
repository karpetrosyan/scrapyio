import typing

T = typing.TypeVar("T")
Y = typing.TypeVar("Y")


def load_module(path: str) -> typing.Any:
    splited_path = path.split(".")
    mod = __import__(".".join(splited_path[:-1]))
    for component in splited_path[1:]:
        mod = getattr(mod, component)
    return mod


def first_not_none(o1: T, o2: Y) -> Y:
    if o1 is not None:
        return typing.cast(Y, o1)
    return o2
