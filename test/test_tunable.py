from tunable.graph import visualize
from tunable.tunable import *
from tunable.tunable import Tunable
from tunable.finalize import finalize
from pytest import raises

def one():
    return tunable(tunable(1, uid=True))

def test_tunable():
    a = variable(range(10), value=2)
    c = variable(range(10))
    b = a*a*one()+c*Tunable(1)
    
    assert compute(b) == 4
    assert repr(b).startswith("Tunable")
    assert visualize(b).source
    assert set(finalize(b).variables) == set([finalize(a).key, finalize(c).key])
    assert set(finalize(b).tunable_variables) == set([finalize(a).key, finalize(c).key])
    assert finalize(b).fixed_variables == ()
    
    to_string = tunable(str)
    c = to_string(b)
    assert compute(c) == "4"

    to_string = Function(str)
    c = to_string(b)
    assert compute(c) == "4"

    b.__name__ = to_string(a)
    assert visualize(b).source

    with raises(TypeError):
        function(1)

    with raises(TypeError):
        variable(1)

    with raises(TypeError):
        bool(tunable(1))