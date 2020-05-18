"""
Graph and node structures.
"""

__all__ = [
    "visualize",
]

from collections import OrderedDict, deque
from collections.abc import Iterable
from .meta import CastableType


class Graph(metaclass=CastableType, slots=["backend"]):
    """
    A Graph class.
    """

    def __init__(self, graph=None):
        if isinstance(graph, Graph):
            graph = graph.backend
        self.backend = graph or OrderedDict()

    def __getitem__(self, key):
        if isinstance(key, Node):
            key = Node(key).key
        node = Node(self)
        node.key = key
        return node

    def __setitem__(self, key, value):
        self.backend[key] = value

    def __getattr__(self, key):
        return getattr(self.backend, key)

    def __contains__(self, key):
        if isinstance(key, Node):
            key = Node(key).key
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
            return self.backend.update(Graph(value).backend)
        return self.backend.update(value)


class Node(Graph, bind=False, slots=["key"]):
    """
    A node of the graph
    """

    def __init__(self, key, value=None):
        Graph.__init__(self.graph, join_graphs(value))
        self.graph[key] = value
        self.key = key

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
        return self.graph.backend[self.key]

    @value.setter
    def value(self, value):
        "Sets the value of the node"
        self.__init__(self.key, value)

    @property
    def graph(self):
        "Returns the graph that the node is part of"
        return Graph(self)

    def __eq__(self, value):
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

    @property
    def dependencies(self):
        "Iterates over the dependencies"
        deps = [self.key]
        yield deps[0]
        for val in self:
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
        return Graph(graphs)

    if isinstance(graphs, dict):
        return join_graphs(graphs.values())

    if isinstance(graphs, str):
        return Graph()

    if hasattr(graphs, "__graph__"):
        return join_graphs(graphs.__graph__)

    if isinstance(graphs, Iterable):
        graph = Graph()
        graphs = map(join_graphs, graphs)
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
        assert end in graph, "end not in graph"
        end = graph[end]
        keys = list(end.dependencies)
    else:
        keys = list(graph.keys())

    if isinstance(start, Node):
        start = Node(start).key

    if start:
        assert start in keys, "start not in graph"

    dot = default_graph(**kwargs)

    for key in keys:
        node = graph[key]

        if start and start not in node.dependencies:
            continue

        dot.node(node.key, node.label, **node.dot_attrs)

        for left in node:
            if not isinstance(left, Node):
                continue
            left = Node(left).key
            if start and start not in graph[left].dependencies:
                continue
            dot.edge(left, node.key)

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

    return Digraph(**kwargs)
