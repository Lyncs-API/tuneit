from tunable.graph import visualize
from tunable.tunable import *
from tunable.variable import *
from tunable.tunable import Tunable
from tunable.finalize import finalize
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
    assert d == Variable(range(10))
    assert d != Variable(range(11))
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
