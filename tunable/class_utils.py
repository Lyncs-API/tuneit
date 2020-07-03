"""
Utils for creating tunable classes
"""
# pylint: disable=C0103

__all__ = [
    "TunableClass",
    "tunable_property",
    "derived_property",
    "derived_method",
    "alternatives",
]

from functools import partial, wraps
from .graph import Graph, Node, visualize
from .tunable import Tunable, tunable, Function, function
from .variable import Variable, variable
from .finalize import finalize


class TunableClass:
    "Base class for tunable classes"

    def __init__(self, value=None):
        self.value = value

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
            else:
                var = Variable(super().__get__(obj, owner), label=self.name)
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
        if obj is None:
            return self.fget
        deps = (dep.__get__(obj, owner) for dep in self.deps)
        deps = tuple(dep.value for dep in deps)
        if any((isinstance(dep, Tunable) for dep in deps)):
            return Function(
                self.fget, deps=deps, args=(obj,), label=self.name
            ).tunable()
        return super().__get__(obj, owner)


class alternatives(dict):
    """
    Class for defining alternative implementations of a function

    Usage
    -----
    @alternatives(fnc1, label = fnc2, other_label = fnc3)
    def fnc(*args, **kwargs):
        ...
    """

    @classmethod
    def args_to_kwargs(cls, *args):
        "Turns args into kwargs using as a key the arg name"

        kwargs = {}
        for arg in args:
            if isinstance(arg, dict):
                kwargs.update(arg)
            elif hasattr(arg, "__name__"):
                kwargs[arg.__name__] = arg
            else:
                raise ValueError(f"{arg} has no __name__")

        return kwargs

    def __init__(self, *args, **kwargs):
        super().__init__(**self.args_to_kwargs(*args), **kwargs)
        self.default = next(iter(self))

    @wraps(dict.update)
    def update(self, *args, **kwargs):
        super().update(**self.args_to_kwargs(*args), **kwargs)

    @property
    def default(self):
        "The default value"
        return self._default

    @default.setter
    def default(self, key):
        if key not in self:
            raise KeyError(f"{key} unknown alternative")
        self._default = key
        wraps(self[key])(self)
        self.__name__ = key

    def add(self, fnc):
        "Adds a value to the alternatives"
        kwargs = self.args_to_kwargs(fnc)
        self.update(kwargs)
        return next(iter(kwargs))

    def __call__(self, *args, _key=None, **kwargs):
        if len(args) == 1 and callable(args[0]):
            self.default = self.add(args[0])
            return self

        if _key:
            return self[_key](*args, **kwargs)

        return function(
            self,
            *args,
            _key=variable(self.keys(), default=self.default, label=self.__name__),
            **kwargs,
        )
