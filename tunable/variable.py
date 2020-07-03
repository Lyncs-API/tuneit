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
from .tunable import Tunable, Object, varname


def variable(var, default=None, label=None, uid=None):
    """
    A tunable variable.

    Parameters
    ----------
    var: Iterable
        An iterator over the possible values of the variable
    default: Any
        The default value for the variable. If None the first element is used.
    label: str
        A label used to identify the variable
    uuid: Any
        Unique identifier for the variable.
    """
    label = label or varname()
    return Variable(var, default=default, label=label, uid=uid).tunable()


class Value:
    "Simple class to hold the value of the variable"
    __slots__ = ["value"]

    @property
    def fixed(self):
        "Returns if the value has been fixed"
        return hasattr(self, "value")


@dataclass
class Variable(Object):
    "The Variable dataclass"
    default: Any = None
    _value: Value = None

    def __post_init__(self):
        if not isinstance(self.var, Iterable):
            raise TypeError("The first argument of Variable must be iterable")

        if not hasattr(self.var, "__len__"):
            self.obj = tuple(self.obj)

        if self.default is None:
            try:
                self.default = next(iter(self.values))
            except StopIteration:
                raise ValueError("Given an empty range for the variable")

        if self.default not in self.values:
            raise ValueError("Default value not in variable's value")

        if self._value is None:
            self._value = Value()

        if self.size < 2 and not self.fixed:
            self.value = self.default

        assert isinstance(self._value, Value), "Value must be of Value type"

        if self.uid is None:
            self.uid = True

        super().__post_init__()

    @property
    def fixed(self):
        "Returns if the value has been fixed"
        return self._value.fixed

    def fix(self, value=None):
        "Fixes the value of the variable"
        if self.fixed and value != self.value:
            raise RuntimeError("Cannot change a value that has been fixed")
        if value is None:
            value = self.default
        if isinstance(value, Variable):
            value = value.tunable()
        if isinstance(value, Iterable) and not isinstance(value, str):
            value = tuple(value)
        if not isinstance(value, Tunable) and value not in self.values:
            raise ValueError("Value %s not compatible with variable" % (value,))
        self._value.value = value

    @property
    def value(self):
        "Returns the value of the variable. If it is not fixed, the default value is returned."
        if self.fixed:
            return self._value.value
        return self.tunable()

    @value.setter
    def value(self, value):
        self.fix(value)

    @property
    def var(self):
        "Alias of obj"
        return self.obj

    def __iter__(self):
        yield self.var
        if self.fixed:
            yield self.value

    def __eq__(self, other):
        if self.fixed:
            if isinstance(other, Variable):
                if not other.fixed:
                    return False
                other = other.value
            return self.value == other
        if isinstance(other, Variable):
            return super().__eq__(other)
        return False

    @property
    def size(self):
        "Returns the size of the variable range"
        return len(self.var)

    @property
    def values(self):
        "Returns the value in the variable range"
        return self.var

    def __compute__(self, **kwargs):
        if not self.fixed:
            self.value = self.default
        return self.value

    @property
    def __dot_attrs__(self):
        return dict(shape="diamond", color="green" if self.fixed else "red")

    def copy(self, reset=False, reset_value=False, **kwargs):
        "Returns a copy of self"
        kwargs.setdefault("default", self.default)
        if reset or reset_value:
            kwargs.setdefault("_value", None)
        else:
            kwargs.setdefault("_value", self._value)
        if reset:
            kwargs.setdefault("uid", True)
        else:
            kwargs.setdefault("uid", self.uid)
        return super().copy(**kwargs)

    def __repr__(self):
        return "%s(%s%s)" % (
            type(self).__name__,
            self.var,
            (", value=%s" % str(self.value)) if self.fixed else "",
        )


class Permutation(Variable):
    "Permutations of the given list"

    @property
    def size(self):
        return factorial(len(self.var))

    @property
    def values(self):
        return permutations(self.var)
