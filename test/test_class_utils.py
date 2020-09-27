from pytest import raises
from tuneit import TunableClass


def test_init():
    a = TunableClass(10)
    assert a.node.value == 10
