from tuneit.graph import visualize, Node
from tuneit.tunable import *
from tuneit.tunable import Tunable
from pytest import raises


class unpickable:
    def __getstate__(self):
        raise NotImplementedError


def test_object():
    zero = Object(0)
    assert zero.uid == None
    assert zero.key == Object(0).key
    assert zero == Object(zero)
    assert Object(0, uid=True).key != Object(0, uid=True).key

    assert compute(zero) == 0
    assert (
        Object(0, label="foo", uid="bar").key == Object(1, label="foo", uid="bar").key
    )

    a = Object(unpickable())
    assert a.key == a.key
    assert a.key != Object(unpickable()).key

    one = Object(1, deps=zero)
    assert zero.key in one.dependencies


def test_function():
    with raises(TypeError):
        function(1)

    zero = Object(0)
    assert compute(Function(str, args=(zero))) == "0"
    assert Function(int.__str__).__label__ == "str"
    assert Function(int.__mul__).__label__ == "*"
    assert Function(int.__setattr__).__label__ == "setattr"
    assert Function(int.__setattr__, args=(0, "foo")).__label__.startswith(".foo=")

    one = Object(1)
    fnc = Function(str, args=zero, kwargs={"one": one})
    assert zero.key in fnc.dependencies
    assert one.key in fnc.dependencies

    lst = Object([1, 2]).tunable()
    lst = lst.append(3)
    assert compute(lst) == [1, 2, 3]

    lst = [1, 2]
    lst = function(lst.append, 3)
    assert compute(lst) == [1, 2, 3]


def one():
    return tunable(tunable(1, uid=True))


def test_tunable():
    with raises(TypeError):
        Tunable(1)

    a = tunable(2)
    b = a * a * one()

    assert compute(b) == 4

    assert Node(b).copy() == b

    to_string = tunable(lambda *args: str(*args))
    c = to_string(b)
    assert compute(c) == "4"

    to_string.__name__ = "foo"
    assert compute(to_string).__name__ == "foo"

    to_string = Function(str)
    c = to_string(b)
    assert compute(c) == "4"

    assert repr(b).startswith("Tunable")
    assert visualize(b).source

    with raises(TypeError):
        bool(tunable(1))
