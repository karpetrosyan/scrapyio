import random
import typing
from pathlib import Path

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


def random_filename(numbers_range: int = 10, random_suffix_length: int = 4) -> str:
    numers: str = "".join(str(i) for i in range(numbers_range))
    random_number: typing.List[str]
    filename: str
    while True:
        random_number = [random.choice(numers) for _ in range(random_suffix_length)]
        filename = "dump_" + "".join(random_number)
        path = Path(filename)
        if not path.exists():
            return filename
