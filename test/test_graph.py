from tunable.graph import Graph, Node


class String(str):
    def __init__(self, val):
        self.__name__ = val
        self.__label__ = val
        self.__dot_attrs__ = {}

    def __iter__(self):
        raise TypeError


def test_graph():
    a = Graph()
    a["foo"] = String("bar")
    b = Node("foo2")
    b.value = (a["foo"], "bar", {"one": 1})

    assert isinstance(a["foo"], Node)
    assert "foo" in a
    assert "foo" in list(a)
    assert isinstance(a["foo"].value, str) and a["foo"].key == "foo"
    assert isinstance(a["foo"].value, str) and a["foo"].value == "bar"
    assert a["foo"] == "bar"
    assert str(a["foo"]) == "bar"
    assert a[a["foo"]] == a["foo"]
    assert a["foo"] in a
    assert repr(a).startswith("Graph")
    assert repr(a["foo"]).startswith("Node")

    assert b.graph == a
    assert a == a.backend

    assert a.visualize().source == b.visualize().source
    assert a.visualize().source == b.visualize(start="foo").source
    assert b.visualize().source != b.visualize(start=a["foo2"]).source
