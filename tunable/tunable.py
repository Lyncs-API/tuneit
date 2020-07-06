"The Tunable class and derived instances"
# pylint: disable=C0303,C0330

__all__ = [
    "compute",
    "Tunable",
    "tunable",
    "Object",
    "function",
    "Function",
]

import operator
import warnings
from inspect import ismethod
from collections import deque
from collections.abc import Iterable
from hashlib import md5
from dill import dumps
from uuid import uuid4
from dataclasses import dataclass
from typing import Any
from varname import varname as _varname

from .graph import Graph, Node, Key


def varname(caller=1, default=None):
    "Wrapper of varname.varname that silences the warning and returns a default value if given."
    warnings.filterwarnings("error" if default is not None else "ignore")
    try:
        return _varname(caller + 1)
    except Warning:
        return default
    finally:
        warnings.filterwarnings("default")


def compute(obj, **kwargs):
    "Compute the value of a tunable object"
    kwargs.setdefault("maxiter", 3)
    if kwargs["maxiter"] <= 0:
        return obj
    if isinstance(obj, Node):
        kwargs.setdefault("graph", Node(obj).graph)
    if isinstance(obj, Key) and not isinstance(obj, Node):
        obj = kwargs["graph"][obj].value
    try:
        obj = obj.__compute__(**kwargs)
        kwargs["maxiter"] -= 1
        obj = compute(obj, **kwargs)
    except AttributeError:
        pass
    return obj


def tunable(obj, deps=None, label=None, uid=None):
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
    return Object(obj, deps=deps, label=label, uid=uid).tunable()


@dataclass
class Object:
    "A generic object dataclass"
    obj: Any
    deps: Any = None
    label: str = None
    uid: Any = None

    @classmethod
    def extract_deps(cls, deps):
        "Converts a list of deps into Nodes"
        if deps is None:
            return ()
        if not isinstance(deps, Iterable) or isinstance(deps, (Object, Node)):
            deps = (deps,)
        keys = None
        if isinstance(deps, dict):
            keys = deps.keys()
            deps = deps.values()
        deps = tuple(
            dep.tunable()
            if isinstance(dep, Object)
            else Node(dep)
            if isinstance(dep, Node)
            else dep
            for dep in deps
        )
        if keys:
            return tuple(zip(keys, deps))
        return deps

    def __post_init__(self):
        if isinstance(self.obj, Object):
            if self.uid is None:
                self.uid = self.obj.uid
            if self.label is None:
                self.label = self.obj.label
            self.obj = self.obj.obj

        self.deps = Object.extract_deps(self.deps)

        if self.uid is True:
            self.uid = str(uuid4())

        if self.label is None:
            if isinstance(self.obj, Node):
                self.label = Node(self.obj).label
            else:
                try:
                    self.label = self.obj.__name__
                except AttributeError:
                    self.label = repr(self.obj)

    def tunable(self):
        "Returns a tunable object"
        return Tunable(self)

    @property
    def dependencies(self):
        "Returns the list of dependencies for the Object"
        return Node(self.tunable()).dependencies

    def copy(self, **kwargs):
        "Returns a copy of self"
        kwargs.setdefault("deps", self.deps)
        kwargs.setdefault("label", self.label)
        kwargs.setdefault("uid", self.uid)
        return type(self)(self.obj, **kwargs)

    @property
    def key(self):
        "Get the key used by Tunable"
        key = self.label + "-"

        if self.uid:
            key = key + md5(dumps(self.uid)).hexdigest()
        else:
            try:
                parts = tuple(
                    Key(part) if isinstance(part, Key) else part for part in self
                )
                key = key + md5(dumps(parts)).hexdigest()
            except Exception as _:
                print(_)
                self.uid = str(uuid4())
                return self.key

        return Key(key)

    def __iter__(self):
        yield self.obj
        yield from self.deps

    def __compute__(self, **kwargs):
        # pylint: disable=W0108
        cmpt = lambda obj: compute(obj, **kwargs)
        deque(map(cmpt, self.deps))
        return self.obj

    @property
    def __label__(self):
        return self.label

    @property
    def __dot_attrs__(self):
        return dict(shape="rect")


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
    return Function(fnc, args=args, kwargs=kwargs).tunable()


@dataclass
class Function(Object):
    "The Function dataclass"

    args: tuple = None
    kwargs: dict = None

    labels = {
        "call": "(...)",
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

        self.args = Object.extract_deps(self.args)
        self.kwargs = dict(Object.extract_deps(self.kwargs))

        super().__post_init__()

    @property
    def fnc(self):
        "Alias of obj"
        return self.obj

    def copy(self, **kwargs):
        "Returns a copy of self"
        kwargs.setdefault("args", self.args)
        kwargs.setdefault("kwargs", self.kwargs)
        return super().copy(**kwargs)

    def __iter__(self):
        yield from super().__iter__()
        yield from self.args
        yield from self.kwargs.values()

    def __call__(self, *args, **kwargs):
        tmp = self.kwargs.copy()
        tmp.update(kwargs)
        return self.copy(args=(self.args + args), kwargs=tmp).tunable()

    def __compute__(self, **kwargs):
        # pylint: disable=W0108
        cmpt = lambda obj: compute(obj, **kwargs)
        fnc = cmpt(super().__compute__(**kwargs))
        args = tuple(map(cmpt, self.args))
        kwargs = dict(zip(self.kwargs.keys(), map(cmpt, self.kwargs.values())))
        res = fnc(*args, **kwargs)
        if res is None:
            if ismethod(fnc) or fnc is setattr:
                return args[0]
            if hasattr(fnc, "__self__"):
                return fnc.__self__
            if args:
                return args[0]
        return res

    @property
    def __label__(self):
        label = self.label
        if label.startswith("__"):
            label = label[2:]
        if label.endswith("__"):
            label = label[:-2]
        if label in Function.labels:
            return Function.labels[label]

        if (
            label in ("getattr", "setattr", "callattr")
            and self.args
            and len(self.args) >= 2
        ):
            return (
                "."
                + self.args[1]
                + (
                    "=..."
                    if label == "setattr"
                    else "(...)"
                    if label == "callattr" and (len(self.args) > 2 or self.kwargs)
                    else "()"
                    if label == "callattr"
                    else ""
                )
            )

        return label

    @property
    def __dot_attrs__(self):
        return dict(shape="oval")


def callattr(self, key, *args, **kwargs):
    "Get attribute from self and then calls it with args, kwargs"
    return getattr(self, key)(*args, **kwargs)


class Tunable(Node, bind=False):
    "A class that turns any operation into a graph node"

    def __init__(self, obj):
        if not isinstance(obj, Object):
            raise TypeError("Expected an Object")

        Node.__init__(Node(self), obj.key, obj.copy())

    def __setattr__(self, key, value):
        tmp = Node(function(setattr, Node(self).copy(), key, value))
        Key(self).key = tmp.key
        Graph(self).backend = tmp.graph.backend

    def __call__(self, *args, **kwargs):
        tmp = Node(self).value
        if (
            isinstance(tmp, Function)
            and tmp.fnc is getattr
            and len(tmp.args) == 2
            and not tmp.kwargs
        ):
            value = Function(callattr, args=tmp.args + args, kwargs=kwargs)
            graph = Graph(self).copy()
            del graph[Key(self)]
            graph[value.key] = value
            return Tunable(graph[value.key])
        return function(Tunable(Node(self).copy()), *args, **kwargs)

    def __repr__(self):
        return "Tunable(%s)" % Node(self).key

    def __bool__(self):
        raise TypeError

    __nonzero__ = __bool__

    def __getstate__(self):
        return Node(self).key

    def __compute__(self, **kwargs):
        # pylint: disable=W0613
        return Node(self).value


def default_operator(fnc):
    "Default operator wrapper"
    return lambda self, *args, **kwargs: function(
        fnc, Node(self).copy(), *args, **kwargs
    )


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

    def roperator(fnc):
        "Default operator wrapper"
        return lambda arg1, arg2: function(fnc, arg2, arg1)

    rops = (
        "__radd__",
        "__rmod__",
        "__rmul__",
        "__rpow__",
        "__rsub__",
        "__rtruediv__",
        "__rfloordiv__",
    )
    for fnc in rops:
        setattr(cls, fnc, roperator(getattr(operator, fnc[3:-2])))


add_operators(Tunable, default_operator)
