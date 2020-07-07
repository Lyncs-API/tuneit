"""
Graph and node structures.
"""

__all__ = [
    "visualize",
]

from collections import deque
from collections.abc import Iterable
from .meta import CastableType


class Graph(metaclass=CastableType, attrs=["backend"]):
    """
    A Graph class.
    """

    def __init__(self, graph=None):
        if isinstance(graph, Graph):
            graph = graph.backend
        self.backend = {} if graph is None else dict(graph)

    def __getitem__(self, key):
        if isinstance(key, Key):
            key = Key(key).key
        node = Node(self)
        Key(node).key = key
        return node

    def __setitem__(self, key, value):
        if isinstance(key, Key):
            key = Key(key).key
        self.backend[key] = value

    def __delitem__(self, key):
        if isinstance(key, Key):
            key = Key(key).key
        del self.backend[key]

    def __getattr__(self, key):
        return getattr(self.backend, key)

    def __contains__(self, key):
        if isinstance(key, Key):
            key = Key(key).key
        return key in self.backend

    def __eq__(self, value):
        if isinstance(value, Graph):
            return self.backend == Graph(value).backend
        return self.backend == value

    def __repr__(self):
        return "Graph(%s)" % self

    def __str__(self):
        return str(self.backend)

    def __iter__(self):
        return iter(self.backend)

    def visualize(self, **kwargs):
        """
        Visualizes the complete graph.
        For more details see help(visualize).
        """
        return visualize(self, **kwargs)

    def update(self, value):
        "Updates the content of the dictionary"
        if isinstance(value, Graph):
            value = Graph(value).backend
        return self.backend.update(value)

    def copy(self):
        "Shallow copy of a Graph"
        return Graph(self.backend.copy())


class Key(metaclass=CastableType, attrs=["key"]):
    "Namespace for the keys of tunable objects"

    def __init__(self, key):
        if isinstance(key, Key):
            key = Key(key).key
        self.key = key

    def __repr__(self):
        return "Key(%s)" % repr(self.key)

    def __str__(self):
        return str(self.key)

    def __eq__(self, value):
        if isinstance(value, Key):
            return self.key == Key(value).key
        return self.key == value

    def __getattr__(self, key):
        return getattr(self.key, key)

    def __hash__(self):
        return hash(self.key)


class Node(Graph, Key, bind=False):
    """
    A node of the graph
    """

    def __init__(self, key, value=None):
        Graph.__init__(self.graph, join_graphs(value))
        Key.__init__(self.key, key)

        if key not in self.graph:
            self.graph[key] = value
        elif not isinstance(value, Graph) or self == value:
            raise KeyError("%s already in graph and the value will not be changed")

        for part in self:
            try:
                Key.__cast__(part)
            except TypeError:
                pass

    @property
    def key(self):
        "Returns the key of the node"
        return Key(self)

    @property
    def label(self):
        "Return the label used in the dot graph"
        try:
            label = self.value.__label__
            assert isinstance(label, str)
            return label
        except (AttributeError, AssertionError):
            return self.key.split("-")[0]

    @property
    def dot_attrs(self):
        "Return the node attributes used in the dot graph"
        try:
            attrs = self.value.__dot_attrs__
            assert isinstance(attrs, dict)
            return attrs
        except (AttributeError, AssertionError):
            return {}

    @property
    def value(self):
        "Value of the node"
        return self.graph.backend[Key(self).key]

    @value.setter
    def value(self, value):
        "Sets the value of the node"
        self.__init__(self.key, value)

    @property
    def graph(self):
        "Returns the graph that the node is part of"
        return Graph(self)

    def __eq__(self, value):
        if isinstance(value, Node):
            return self.key == value and self.value == Node(value).value
        if isinstance(value, Key):
            return self.key == value
        return self.value == value

    def __iter__(self):
        try:
            yield from self.value
        except TypeError:
            yield self.value

    def __repr__(self):
        return "Node(%s)" % (self.key)

    def __str__(self):
        return str(self.value)

    def __copy__(self):
        return Node(Key(self), Graph(self))

    def copy(self):
        return self.__copy__()

    @property
    def first_dependencies(self):
        "Iterates over the dependencies"
        for val in self:
            if isinstance(val, Key):
                yield Key(val)

    @property
    def dependencies(self):
        "Iterates over the dependencies"
        deps = [self.key]
        yield deps[0]
        for val in self:
            if isinstance(val, Key):
                val = self.graph[val]
            if isinstance(val, Node):
                for dep in Node(val).dependencies:
                    if dep not in deps:
                        deps.append(dep)
                        yield dep

    def visualize(self, **kwargs):
        """
        Visualizes the graph up to this node.
        For more details see help(visualize).
        """
        return visualize(self, **kwargs)


def join_graphs(graphs):
    "Joins all the graphs in graphs into a unique instance"

    if isinstance(graphs, Graph):
        return Graph(graphs).copy()

    if isinstance(graphs, dict):
        return join_graphs(graphs.values())

    if isinstance(graphs, str):
        return Graph()

    if isinstance(graphs, Iterable):
        graph = Graph()
        graphs = filter(lambda obj: isinstance(obj, Graph), graphs)
        deque(map(graph.update, graphs))
        return graph

    return Graph()


def visualize(graph, start=None, end=None, **kwargs):
    "Visualizes the graph returning a dot graph"
    assert isinstance(graph, Graph), "graph must be of type Graph"

    if isinstance(graph, Node):
        end = end or Node(graph).key

    graph = Graph(graph)

    if end is not None:
        if end not in graph:
            raise KeyError("Given end %s not in graph" % end)
        end = graph[end]
        keys = tuple(end.dependencies)
    else:
        keys = tuple(graph.keys())

    if isinstance(start, Node):
        start = Node(start).key

    if start and start not in keys:
        raise KeyError("Given start %s not in graph" % end)

    dot = default_graph(**kwargs)

    for key in keys:
        node = graph[key]

        if start and start not in node.dependencies:
            continue

        dot.node(str(key), node.label, **node.dot_attrs)

        for dep in node.first_dependencies:
            if start and start not in graph[dep].dependencies:
                continue
            dot.edge(str(dep), str(key))

    return dot


def default_graph(**kwargs):
    "Defines the default options for kwargs"
    try:
        # pylint: disable=import-outside-toplevel
        from graphviz import Digraph
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            """
            Visualize needs graphviz to be installed.
            Please run `pip install --user graphviz`.
            """
        )

    kwargs.setdefault("graph_attr", {})
    kwargs["graph_attr"].setdefault("rankdir", "LR")
    return Digraph(**kwargs)
