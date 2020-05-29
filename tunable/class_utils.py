"""
Utils for creating tunable classes
"""
# pylint: disable=C0103

__all__ = [
    "TunableClass",
    "tunable_property",
    "derived_property",
    "derived_method",
]

from functools import partial, wraps
from uuid import uuid4
from .graph import Graph, Node, visualize
from .tunable import Tunable, tunable, Function
from .variable import Variable
from .finalize import finalize


class TunableClass:
    "Base class for tunable classes"

    def __init__(self, value=None):
        self.value = value
        self.uid = value

    @property
    def value(self):
        "Returns the underlying tunable value of the class"
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value, Node):
            self._value = Tunable(value)
        elif isinstance(value, TunableClass):
            self._value = value.value
        else:
            self._value = tunable(value, label="value")

    @property
    def node(self):
        "Returns the node of the tunable value"
        return finalize(self.value)

    @property
    def graph(self):
        "Returns the underlying graph"
        return Graph(self.value)

    @property
    def __graph__(self):
        return self.value

    @property
    def uid(self):
        "Unique id of the field"
        return self._uid

    @uid.setter
    def uid(self, value):
        if value is None:
            self._uid = str(uuid4())
        elif isinstance(value, TunableClass):
            self._uid = value.uid
        else:
            self._uid = value

    def visualize(self, **kwargs):
        "Visualizes the class graph"
        return visualize(self.value, **kwargs)

    def compute(self, **kwargs):
        "Computes the class graph"
        self.value = tunable(self.node.compute(**kwargs), label="value")

    @property
    def result(self):
        "Returns the value of the class after computing"
        self.compute()
        return self.node.value.obj

    @property
    def variables(self):
        "List of variables in the class graph"
        return self.node.variables

    @property
    def tunable_variables(self):
        "List of tunable variables in the class graph"
        return self.node.tunable_variables

    @property
    def fixed_variables(self):
        "List of fixed variables in the class graph"
        return self.node.fixed_variables


class tunable_property(property):
    """
    Returns a tunable property of the class.
    The output of a tunable property is threated as a Variable
    """

    @property
    def name(self):
        "Name of the property"
        return self.fget.__name__

    @property
    def key(self):
        "Key where to store the property value"
        return getattr(self, "_key", "_" + self.name)

    @key.setter
    def key(self, value):
        self._key = value

    def __get__(self, obj, owner):
        try:
            return getattr(obj, self.key)
        except AttributeError:
            var = super().__get__(obj, owner)
            if isinstance(var, Variable):
                var.label = self.name
                var.uid = var.uid or obj.uid
            else:
                var = Variable(
                    super().__get__(obj, owner), label=self.name, uid=obj.uid
                )
            setattr(obj, self.key, var)
            return self.__get__(obj, owner)

    def __set__(self, obj, value):

        var = self.__get__(obj, type(obj))

        if isinstance(value, Variable):
            setattr(obj, self.key, value)
        else:
            var.value = value


def skip_n_args(fnc, num):
    "Decorator that calls a function skipping the first n arguments"

    @wraps(fnc)
    def wrapped(*args, **kwargs):
        return fnc(*args[num:], **kwargs)

    return wrapped


def derived_method(*deps):
    """
    Returns a method that depends on a tunable property.
    """

    assert all(
        (isinstance(dep, tunable_property) for dep in deps)
    ), "TODO: improve check"

    def decorator(fnc):
        @wraps(fnc)
        def derived(self, *args, **kwargs):
            _deps = (dep.__get__(self, type(self)) for dep in deps)
            _deps = tuple(dep.value for dep in _deps)
            if any((isinstance(dep, Tunable) for dep in _deps)):
                return Function(
                    fnc, deps=_deps, args=(self,) + args, kwargs=kwargs
                ).tunable()
            return fnc(self, *args, **kwargs)

        return derived

    return decorator


class derived_property(property):
    """
    Returns a property that depends on a tunable property.
    """

    @property
    def name(self):
        "Name of the property"
        return self.fget.__name__

    def __new__(cls, *deps, **kwargs):
        if "deps" not in kwargs:
            return partial(derived_property, deps=deps)
        return super().__new__(cls, *deps, **kwargs)

    def __init__(self, *args, deps=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.deps = deps or ()
        self.__name__ = self.name

        assert all(
            (isinstance(dep, tunable_property) for dep in self.deps)
        ), "TODO: improve check"

    def __get__(self, obj, owner):
        deps = (dep.__get__(obj, owner) for dep in self.deps)
        deps = tuple(dep.value for dep in deps)
        if any((isinstance(dep, Tunable) for dep in deps)):
            return Function(self, deps=deps, args=(obj,)).tunable()
        return super().__get__(obj, owner)

    def __call__(self, obj):
        return self.__get__(obj, type(obj))
