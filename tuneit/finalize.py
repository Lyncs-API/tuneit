"""
High Level vision of Tunable object
"""

__all__ = [
    "finalize",
]

from .graph import Node, Key
from .variable import Variable
from .tunable import Object, Function, compute


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
            str(dep) for dep in self.dependencies if isinstance(self[dep], Variable)
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

    def __getitem__(self, key):
        if isinstance(key, Object):
            key = key.key
        return self.graph[key].value

    def __setitem__(self, key, value):
        self.graph[key] = value

    def __copy__(self):
        return HighLevel(super().__copy__())

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

    def get_variable(self, variable):
        "Returns the varible corresponding to var"
        if isinstance(variable, Variable):
            variable = variable.key
        if isinstance(variable, Key):
            variable = Key(variable).key

        if not variable in self.variables:
            # Smart search
            matches = list(
                filter(lambda var: var.startswith(variable + "-"), self.variables)
            )
            if len(matches) > 1:
                raise KeyError(
                    "More than one variable matched to %s: %s" % (variable, matches)
                )
            if len(matches) == 0:
                raise KeyError("%s is not a variable of %s" % (variable, self))
            variable = matches[0]

        return self[variable]

    def fix(self, variable, value=None):
        "Fixes the value of the variable"
        self.get_variable(variable).fix(value)

    def compute(self, **kwargs):
        "Computes the result of the Node"
        kwargs.setdefault("graph", self.graph)
        return compute(self.value, **kwargs)
