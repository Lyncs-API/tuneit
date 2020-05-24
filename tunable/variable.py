"Tunable variables"

__all__ = [
    "variable",
    "Variable",
    "Permutation",
]

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from itertools import permutations
from math import factorial
from .tunable import Tunable, Object, varname, compute


def variable(var, value=None, label=None, uid=None, fixed=False):
    """
    A tunable variable.

    Parameters
    ----------
    var: Iterable
        An iterator over the possible values of the variable
    value: Any
        The default value for the variable. If None the first element is used.
    label: str
        A label used to identify the variable
    uuid: Any
        Unique identifier for the variable.
    """
    label = label or varname()
    return Tunable(Variable(var, value=value, label=label, uid=uid, fixed=fixed))


@dataclass
class Variable(Object):
    "The Variable dataclass"
    default: Any = None
    fixed: bool = False

    def __init__(self, var, value=None, fixed=False, **kwargs):
        if not isinstance(var, Iterable):
            raise TypeError("The first argument of Variable must be iterable")

        super().__init__(var, **kwargs)

        if value is None:
            self.default = next(iter(self))
        else:
            self.default = value
        if fixed:
            self.value = self.default
        elif len(self.var) < 2:
            self.value = self.default

    @Object.value.setter
    def value(self, value):
        if self.fixed:
            raise RuntimeError("Cannot change a value that has been fixed")
        self._value = value
        self.fixed = True

    @property
    def var(self):
        "Alias of obj"
        return self.obj

    def __len__(self):
        return len(self.var)

    def __iter__(self):
        return iter(self.var)

    @property
    def __graph__(self):
        return self.value

    def __compute__(self):
        if not self.fixed:
            self.value = self.default
        return compute(self.value)

    @property
    def __dot_attrs__(self):
        return dict(shape="diamond", color="green" if self.fixed else "red")

    def copy(self, **kwargs):
        "Returns a copy of self"
        kwargs.setdefault("value", self.value if self.fixed else self.default)
        kwargs.setdefault("fixed", self.fixed)
        return super().copy(**kwargs)

    def __repr__(self):
        return "%s(%s%s)" % (
            type(self).__name__,
            self.var,
            ", fixed=True" if self.fixed else "",
        )


class Permutation(Variable):
    "Permutations of the given list"

    def __len__(self):
        return factorial(len(self.var))

    def __iter__(self):
        return permutations(self.var)
