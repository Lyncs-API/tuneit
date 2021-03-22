"""
High Level vision of Tunable object
"""

__all__ = ["finalize"]

from .graph import Node, Key, Graph
from .variable import Variable
from .tunable import Object, Function, compute, Data, data

# from .subgraph import Subgraph


def finalize(tunable):
    "Returns a finalized tunable object that has several high-level functions"
    if not isinstance(tunable, Node):
        raise TypeError("Only tunable objects can be finalized")
    return HighLevel(tunable)


class HighLevel(Node):
    "HighLevel view of a Node"

    @property
    def datas(self):
        "List of dependencies that are a variable"
        return tuple(
            str(dep) for dep in self.dependencies if isinstance(self[dep], Data)
        )

    @property
    def variables(self):
        "List of dependencies that are a variable"
        return tuple(
            str(dep) for dep in self.dependencies if isinstance(self[dep], Variable)
        )

    @property
    def direct_variables(self):
        "List of first dependencies that are a variable"
        return tuple(
            str(dep)
            for dep in self.direct_dependencies
            if isinstance(self[dep], Variable)
        )

    @property
    def functions(self):
        "List of dependencies that are a functions"
        return tuple(
            dep for dep in self.dependencies if isinstance(self[dep], Function)
        )

    @property
    def tunable_variables(self):
        "List of variables that are tunable"
        return tuple(var for var in self.variables if not self[var].fixed)

    @property
    def fixed_variables(self):
        "List of variables that are fixed"
        return tuple(var for var in self.variables if self[var].fixed)

    def depends_on(self, value):
        "Returns true if the given value is in the graph"
        if isinstance(value, Key):
            return Key(value).key in self.dependencies
        if isinstance(value, Object):
            return self.depends_on(value.key)
        return False

    def get_node(self, key):
        "Returns a node of the graph as a finalized graph"
        key = self.get_key(key)
        return HighLevel(self.graph[key])

    def __getitem__(self, key):

        key = self.get_key(key)
        return self.graph[key].value

    def __setitem__(self, key, value):
        key = self.get_key(key)
        self.graph[key] = value

    def get_key(self, key, ntype=None):

        if isinstance(key, Object):
            key = key.key
        if isinstance(key, Key):
            key = Key(key).key
        if key in self.graph:
            return key
        if not isinstance(key, str):
            raise TypeError("key should be string")

        keys = self.dependencies
        if ntype:
            keys = (k for k in keys if isinstance(self[k], ntype))

        # Smart search
        matches = list(filter(lambda k: str(k).startswith(key + "-"), keys))
        if len(matches) > 1:
            raise KeyError("More than one key matched to %s: %s" % (key, matches))
        if len(matches) == 0:
            raise KeyError("%s is not a key of %s" % (key, self))

        return matches[0]

    def __copy__(self):
        return HighLevel(super().__copy__())

    def __call__(self, *args, compute_kwargs=None, **kwargs):
        "kwargs are data input of the graph"
        if args:
            raise ValueError("args not supported, please pass them as kwargs")

        tmp = self.copy()

        for key, val in kwargs.items():
            try:
                tmp.get_data(key).set(val)
                continue
            except KeyError:
                pass
            tmp.fix(key, val)

        compute_kwargs = compute_kwargs or {}
        return tmp.compute(**compute_kwargs)

    def copy(self, reset=False, reset_tunable=True):
        "Copy the content of the graph unrelating the tunable variables"
        res = self.__copy__()

        if reset:
            for var in res.variables:
                res[var] = res[var].copy(reset_value=True)
        elif reset_tunable:
            for var in res.tunable_variables:
                res[var] = res[var].copy(reset_value=True)

        return res

    def get_variable(self, key):
        "Returns the variable corresponding to var"
        key = self.get_key(key, ntype=Variable)
        return self[key]

    def get_data(self, key):
        "Returns the varible corresponding to var"
        key = self.get_key(key, ntype=Data)
        return self[key]

    def add_deps(
        self, start_node, end_node=None
    ):  # start_node, end_node must be a strings
        if not end_node:
            end_node = self
        else:
            end_node = self.get_node(end_node)

        start_node = self.get_variable(
            start_node
        )  # TO DO: should work for all types not variable only

        end_node.value.deps = end_node.value.deps + (Key(start_node.key),)

    def precompute(self, **kwargs):
        for key in self.dependencies:
            if self[key].precompute:
                self[key] = Data(
                    self.get_node(key).compute(**kwargs), label=self[key].label
                )

    def fix(self, variable, value=None):
        "Fixes the value of the variable"
        self.get_variable(variable).fix(value)

    def compute(self, **kwargs):
        "Computes the result of the Node"
        kwargs.setdefault("graph", self.graph)
        return compute(self.value, **kwargs)

    def remove(self, nodes):
        "Removes the list of nodes from the graph"
        for node in nodes:
            del self.graph[node]

    def merge(self, nodes=None):
        "Returns a new graph with the list of nodes merged into a single node"
        # if not nodes:
        # mergers = detect_mergers
        # for nodes in mergers... all the rest
        for node in nodes:
            if not isinstance(self[node], Function):
                raise ValueError("The node does not represent a function")
        last_node, merge = self.mergeable(nodes)
        if not merge:
            raise ValueError("Group of nodes not mergeable")
        deps = tuple(
            set(
                [
                    str(dep)
                    for node in nodes
                    for dep in self.get_node(node).first_dependencies
                    if dep not in nodes
                ]
            )
        )
        sub = {node: self[node] for node in nodes}
        sub.update(
            {dep: Data(None, label=f"dep{i}", info=dep) for (i, dep) in enumerate(deps)}
        )
        sub = finalize(Graph(sub)[last_node])
        new_node = Function(
            sub,
            label="merged",
            kwargs={f"dep{i}": Key(dep) for (i, dep) in enumerate(deps)},
        )
        new_graph = self.copy(reset=True)
        nodes.remove(last_node)
        new_graph.remove(nodes)
        new_graph[last_node] = new_node
        return new_graph

    def consecutive(self, nodes):
        "implements a DFS to check if the undirected graph is connected (if all nodes are consecutive)"
        stack = [nodes[0]]
        unvisited = nodes[1:]
        while stack:
            u = stack[-1]
            appended = False
            for w in [str(dep) for dep in self.get_node(u).first_dependencies]:
                if w in unvisited:
                    unvisited.remove(w)
                    stack.append(w)
                    appended = True
                    break
            if not appended:
                for w in [
                    str(node)
                    for node in nodes
                    if u in self.get_node(node).first_dependencies
                ]:
                    if w in unvisited:
                        unvisited.remove(w)
                        stack.append(w)
                        appended = True
                        break
            if not appended:
                stack.pop()
        if not unvisited:
            return True
        return False

    def one_output(self, nodes):
        "gets a list of nodes and checks that they only produce one output"
        common = []
        common_outside = []
        all_nodes = [
            str(n) for n in self.dependencies if isinstance(self[str(n)], Function)
        ]

        # If the whole graph is given or if the subgraph contains the last node of the whole graph:
        all_deps = [
            str(dep)
            for node in all_nodes
            for dep in self.get_node(str(node)).first_dependencies
        ]
        for node in all_nodes:
            if node not in all_deps and node in nodes:
                common_outside = common_outside + [node]
        if len(common_outside) == 1:
            return common_outside[0], True
        elif len(common_outside) > 1:
            return common_outside, False

        # If a subgraph is given:
        for node in all_nodes:
            deps = list(
                set(
                    [str(dep) for dep in self.get_node(str(node)).first_dependencies]
                ).intersection(nodes)
            )
            if node in nodes:
                common = common + deps
            else:
                common_outside = common_outside + deps
        if len(set(common_outside)) == 1 and set(common + common_outside) == set(nodes):
            return common_outside[0], True
        return common_outside, False

    def mergeable(self, nodes):
        last_node, res = self.one_output(nodes)
        if self.consecutive(nodes) and res:
            return last_node, True
        return last_node, False
