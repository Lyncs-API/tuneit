"The Tunable class and derived instances"
# pylint: disable=C0303,C0330

__all__ = [
    "compute",
    "function",
    "Function",
    "tunable",
    "variable",
]

import operator
import warnings
from hashlib import md5
from pickle import dumps
from uuid import uuid4
from dataclasses import dataclass
from collections.abc import Iterable
from copy import copy
from typing import Any
from varname import varname as _varname

from .graph import Graph, Node


def varname(caller=1, default=None):
    "Wrapper of varname.varname that silences the warning and returns a default value if given."
    warnings.filterwarnings("error" if default is not None else "ignore")
    try:
        return _varname(caller + 1)
    except Warning:
        return default
    finally:
        warnings.filterwarnings("default")


def compute(obj):
    "Compute the value of a tunable object"
    try:
        return obj.__compute__()
    except AttributeError:
        return obj


def tunable(obj, label=None, uid=None):
    """
    A tunable object.
    
    Parameters
    ----------
    obj: Any
        The object hold as tunable
    label: str
        A label for the object
    uid: Any
        Unique identifier for the object.
    """
    label = label or varname(default="")
    return Tunable(Object(obj, label=label, uid=uid))


@dataclass
class Object:
    "A generic object dataclass"
    obj: Any
    label: str = None
    uid: Any = None

    def __post_init__(self):
        if isinstance(self.obj, Object):
            self.uid = self.obj.uid
            self.label = self.obj.label
            self.obj = self.obj.obj

        if self.uid is True:
            self.uid = str(uuid4())

        if self.label:
            self.__name__ = self.label
        elif isinstance(self.obj, Node):
            self.__name__ = Node(self.obj).label
        else:
            try:
                self.__name__ = self.obj.__name__
            except AttributeError:
                self.__name__ = repr(self.obj)

    def __compute__(self):
        return compute(self.obj)

    @property
    def __label__(self):
        return self.label or self.__name__

    @property
    def __dot_attrs__(self):
        return dict(shape="rect")

    def __iter__(self):
        yield self.obj


def function(fnc, *args, **kwargs):
    """
    A tunable function call.
    
    Parameters
    ----------
    fnc: callable
        The function to call
    args: tuple
        List of args for the function
    kwargs: dict
        List of named args for the function
    """
    return Tunable(Function(fnc, args=args, kwargs=kwargs))


@dataclass
class Function(Object):
    "The Function dataclass"

    args: list = None
    kwargs: dict = None

    labels = {
        "add": "+",
        "sub": "-",
        "mul": "*",
        "div": "/",
        "truediv": "//",
        "eq": "==",
        "ne": "!=",
        "ge": ">=",
        "gt": ">",
        "le": "<=",
        "lt": "<",
    }

    def __post_init__(self):
        if not callable(self.fnc):
            raise TypeError("The first argument of Function must be callable")

        if self.args is None:
            self.args = []
        else:
            self.args = list(self.args)

        if self.kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = dict(self.kwargs)

        super().__post_init__()

    @property
    def fnc(self):
        "Alias of obj"
        return self.obj

    def __iter__(self):
        yield self.fnc
        yield from self.args
        yield from self.kwargs.items()

    def __call__(self, *args, **kwargs):
        return function(self, *self.args, *args, **self.kwargs, **kwargs)

    def __compute__(self):
        fnc = compute(self.fnc)
        args = list(map(compute, self.args))
        kwargs = dict(zip(self.kwargs.keys(), map(compute, self.kwargs.items())))
        return fnc(*args, **kwargs)

    @property
    def __label__(self):
        if self.__name__ in Function.labels:
            return Function.labels[self.__name__]

        if self.fnc in (getattr, setattr):
            return "." + self.args[1] + "=" if self.fnc is setattr else ""

        return super().__label__

    @property
    def __dot_attrs__(self):
        return dict(shape="oval")


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
    value: Any = None
    fixed: bool = False

    def __post_init__(self):
        if not isinstance(self.var, Iterable):
            raise TypeError("The first argument of Variable must be iterable")

        if self.value is None:
            self.value = next(iter(self.var))

        super().__post_init__()

    @property
    def var(self):
        "Alias of obj"
        return self.obj

    def __compute__(self):
        return compute(self.value)

    @property
    def __dot_attrs__(self):
        return dict(shape="diamond", color="red" if self.fixed else "green")


def get_key(obj):
    "Get the key used by Tunable"
    try:
        key = obj.__name__
    except AttributeError:
        key = "???"
    try:
        key += "-" + md5(dumps(obj)).hexdigest()
    except TypeError:
        key += "-" + md5(bytes(str(uuid4()), "utf-8")).hexdigest()
    return key


class Tunable(Node, bind=False):
    "A class that turns any operation on instances into a graph node"

    def __init__(self, obj):
        Node.__init__(Node(self), get_key(obj), obj)

    def __setattr__(self, key, value):
        tmp = function(setattr, copy(self), key, value)
        Node(self).key = Node(tmp).key
        Graph(self).backend = Graph(tmp).backend

    def __call__(self, *args, **kwargs):
        return function(self, *args, **kwargs)

    def __repr__(self):
        return "Tunable(%s)" % Node(self).key

    def __bool__(self):
        raise TypeError

    __nonzero__ = __bool__

    def __getstate__(self):
        return Node(self).key

    def __copy__(self):
        return Tunable(Node(Node(self).key, Node(self).value))

    def __compute__(self):
        return compute(Node(self).value)


def default_operator(fnc):
    "Default operator wrapper"
    return lambda *args, **kwargs: function(fnc, *args, **kwargs)


def add_operators(cls, wrapper):
    "Wraps all the operators with wrapper and adds them to the class"
    setattr(cls, "__getattr__", wrapper(getattr))

    for fnc in dir(operator):
        if fnc.startswith("__"):
            try:
                fnc2 = getattr(operator, fnc[2:-2])
            except AttributeError:
                try:
                    fnc2 = getattr(operator, fnc[2:-1])
                except AttributeError:
                    continue

            assert fnc2 is getattr(operator, fnc)
            setattr(cls, fnc, wrapper(fnc2))


add_operators(Tunable, default_operator)
