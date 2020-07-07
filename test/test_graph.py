import pytest
from tuneit.graph import Graph, Node, Key


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

    with pytest.raises(KeyError):
        Node("foo", (a["foo"], "bar"))

    assert isinstance(a["foo"], Node)
    assert "foo" in a
    assert "foo" in list(a)
    assert isinstance(a["foo"].value, str) and a["foo"].key == "foo"
    assert isinstance(a["foo"].value, str) and a["foo"].value == "bar"

    assert a["foo"] == Node("foo", a)
    assert a["foo"] == "bar"
    assert a["foo"] == Key(a["foo"])
    assert str(a["foo"]) == "bar"
    assert a["foo"] != a
    assert a[a["foo"]] == a["foo"]
    assert a["foo"] in a

    assert repr(a).startswith("Graph")
    assert repr(a["foo"]).startswith("Node")
    assert repr(Key(a["foo"])).startswith("Key")

    assert a == a.backend

    assert a.visualize()
    with pytest.raises(KeyError):
        a.visualize(end="bar")
    with pytest.raises(KeyError):
        a.visualize(start="bar")

    assert b.graph.visualize(end=b).source == b.visualize().source
    assert b.visualize().source == b.visualize(start="foo").source
    assert b.visualize().source != b.visualize(start=a["foo2"]).source


def test_dict_methods():
    a = Graph(dict(one=1, two=2, three=3))
    assert a.get("one", None) == 1
    assert a.get("four", None) == None

    b = a.copy()
    assert a == b
    assert b.pop("one") == 1
    assert "one" not in b
    assert "one" in a

    b.update(a)
    assert a == b
