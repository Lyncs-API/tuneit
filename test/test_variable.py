from tuneit.graph import visualize
from tuneit.tunable import *
from tuneit.variable import *
from tuneit.tunable import Tunable
from tuneit.finalize import finalize
from pytest import raises


def test_variable():
    A = Variable(range(10), default=2)
    a = A.tunable()
    C = Variable(range(10))
    c = C.tunable()
    b = a * a + c * tunable(1)

    assert not A.fixed
    assert not C.fixed
    assert compute(b) == 4
    assert A.fixed
    assert C.fixed
    assert A.value == 2
    assert C.value == 0

    assert visualize(b).source

    with raises(TypeError):
        variable(1)

    with raises(ValueError):
        variable(range(10), default=11)

    d = Variable(range(10))
    assert d == Variable(range(10), uid=d.uid)
    assert d != Variable(range(10))
    assert d.size == 10
    with raises(ValueError):
        d.value = 11

    d.value = 2
    assert d == 2
    assert "2" in repr(d)
    with raises(RuntimeError):
        d.value = 3

    d = Variable(range(10))
    d.value = Variable(range(10))

    d = Permutation((1, 2, 3))
    d.value = (3, 2, 1)
    assert d.size == 6

    d = Variable([0])
    assert d.fixed
    assert d.value == 0

    with raises(ValueError):
        d = Variable([])

    d = Variable((i for i in [1, 2, 3]))
    assert d.values == (1, 2, 3)
