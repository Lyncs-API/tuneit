from tuneit.graph import visualize
from tuneit.tunable import *
from tuneit.variable import *
from tuneit.tunable import Tunable
from tuneit.finalize import finalize
from pytest import raises


def test_finalize():
    with raises(TypeError):
        finalize(1)

    a = variable(range(10), default=2)

    assert finalize(a)[finalize(a).value] == finalize(a).value

    c = variable(range(10))
    b = finalize(a * a + c)

    assert set(b.variables) == set([finalize(a).key, finalize(c).key])
    assert b.tunable_variables == b.variables
    assert b.compute() == 4
    assert b.fixed_variables == b.variables
    assert not b.tunable_variables

    assert len(b.functions) == 2
    assert not b.depends_on(1)
    assert b.depends_on(a)
    assert b.depends_on(finalize(a).value)

    b = b.copy(reset=True)
    assert b.tunable_variables == b.variables
    assert finalize(a).value.fixed

    d = b.copy()
    assert d.compute() == 4
    assert b.tunable_variables == b.variables
    assert d.fixed_variables == b.variables

    b.fix("a")
    b.fix(finalize(c).value, 1)
    assert b.compute() == 5
    assert b.fixed_variables == b.variables

    with raises(KeyError):
        b.fix("foo")

    a = variable(range(10), uid=True)
    with raises(KeyError):
        finalize(a * b).fix("a")
