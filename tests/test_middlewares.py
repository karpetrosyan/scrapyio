from scrapyio.middlewares import TestMiddleWare
from scrapyio.middlewares import build_middlewares_chain


def test_building_middleware_chain():
    middlewares = build_middlewares_chain()
    assert len(middlewares) == 1
    assert isinstance(middlewares[0], TestMiddleWare)
