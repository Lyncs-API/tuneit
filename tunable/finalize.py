"""
High Level vision of Tunable object
"""

from .graph import Node
from .tunable import Variable, Function


def finalize(tunable):
    "Returns a finalized tunable object that has several high-level functions"
    if not isinstance(tunable, Node):
        raise TypeError("Only tunable objects can be finalized")
    return HighLevel(tunable)


class HighLevel(Node):
    "HighLevel view of a Node"

    @property
    def variables(self):
        "List of dependencies that are a variable"
        return tuple(
            dep
            for dep in self.dependencies
            if isinstance(self.graph[dep].value, Variable)
        )

    @property
    def functions(self):
        "List of dependencies that are a functions"
        return tuple(
            dep
            for dep in self.dependencies
            if isinstance(self.graph[dep].value, Function)
        )

    @property
    def tunable_variables(self):
        "List of variables that are tunable"
        return tuple(var for var in self.variables if self.graph[var].value.tunable)

    @property
    def fixed_variables(self):
        "List of variables that are fixed"
        return tuple(var for var in self.variables if not self.graph[var].value.tunable)
