from tuneit.graph import visualize
from tuneit.tunable import *
from tuneit.variable import *
from tuneit.class_utils import *
from tuneit.tunable import Tunable
from tuneit.finalize import finalize
from pytest import raises
from tuneit.variable import Variable
from tuneit.finalize import HighLevel
import testfixtures
import pickle
import scipy.sparse as sp
import scipy as s


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

    x = variable([1, 2, 3, 4])
    y = variable([15, 16, 17, 18])
    z = variable([10, 20, 30, 40])
    w = variable([0, 50, 100])
    a = x + y + z + w - z
    a_final = finalize(a)

    b = w ** x - y
    d = a + b
    d_final = finalize(d)
    nodes_a = list(
        str(node)
        for node in a_final.dependencies
        if not isinstance(a_final[node], Variable)
    )
    nodes_d = list(
        str(node)
        for node in d_final.dependencies
        if not isinstance(d_final[node], Variable)
    )

    # one_output
    assert a_final.one_output(nodes_a)[1] == True
    assert d_final.one_output(nodes_d[1:])[1] == False

    # consecutive
    assert a_final.consecutive(nodes_a) == True
    assert d_final.consecutive(nodes_d) == True
    assert d_final.consecutive(nodes_d[1:]) == False

    # mergeable
    assert a_final.mergeable(nodes_a)[1] == True
    assert d_final.mergeable(nodes_d[1:])[1] == False

    # merge
    last_node = d_final.one_output(nodes_d[1:4])[0]
    with raises(ValueError):
        d_final.merge(list(str(dep) for dep in d_final.dependencies))
    with raises(ValueError):
        d_final.merge(nodes_d[1:])
    merged_graph = d_final.merge(nodes_d[1:4])
    assert isinstance(merged_graph, HighLevel)
    assert len(nodes_d) - 2 == len(
        list(
            str(node)
            for node in merged_graph.dependencies
            if not isinstance(merged_graph[node], Variable)
        )
    )  # tests remove
    nodes = list(
        d_final.get_node(node)
        for node in d_final.dependencies
        if not isinstance(d_final[node], Variable)
    )[1:4]
    assert set(
        [dep for node in nodes for dep in node.first_dependencies if dep not in nodes]
    ) == set(list(merged_graph.get_node(last_node).first_dependencies))


def test_pickle():
    # HighLevel
    x = data()
    y = data()
    z = x * y
    z = finalize(z)
    a = pickle.dumps(z)
    b = pickle.loads(a)
    assert testfixtures.compare(z, b, strict=True) is None

    # HighLevel object with alternatives: alternatives is not pickle-able

    # @alternatives(
    # coo = sp.coo_matrix,
    # csc = sp.csc_matrix,
    # csr = sp.csr_matrix,
    # bsr = sp.bsr_matrix
    # )
    # def matrix(mat):
    #    return s.matrix(mat.todense())

    # mat=data(info=["shape","dtype"])
    # vec=data(info=["shape","dtype"])
    # mat=matrix(mat)
    # mul=mat*vec
    # mul = finalize(mul)

    # a = pickle.dumps(mul)
    # b = pickle.loads(a)
    # assert testfixtures.compare(mul,b, strict=True) is None
