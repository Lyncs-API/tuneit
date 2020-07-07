"Defines the CastableType metaclass used by the module"
# pylint: disable=C0303,C0330

__all__ = [
    "CastableType",
]


class Slot:
    """
    An holder of the slot value. 
    Needed for passing by reference the slots between views of the class.
    """

    __slots__ = ["value"]

    @classmethod
    def getter(cls, key):
        "Returns the getter function"

        def fget(self):
            return getattr(type(self), "__values__").__get__(self)[key].value

        return fget

    @classmethod
    def setter(cls, key):
        "Returns the setter function"

        def fset(self, value):
            getattr(type(self), "__values__").__get__(self)[key].value = value

        return fset


class CastableType(type):
    """
    A metaclass for castable classes.

    >>> from tunable.meta import CastableType
    
    >>> class Foo(metaclass=CastableType, attrs=["foo"]):
    ...     pass
    
    >>> class Bar(Foo, attrs=["bar"], bind=False):
    ...     pass
    
    >>> Bar.__attrs__
        ["Foo_foo", "Bar_bar"]
    >>> issubclass(Bar, Foo)
        True
    >>> bar = Bar()
    >>> hasattr(bar, "foo")
        False

    **Note**: since we initialized Bar with bind=False
    it has not inherit the methods from the parent class.
    
    To access the methods of the parent class one
    needs to cast the instance to the parent class.
    
    >>> foo = Foo(bar)
    >>> hasattr(foo, "foo")
        True    
    """

    @classmethod
    def caster(cls, scls):
        "Returns the cast function for the given subclass (scls)"

        def __cast__(self):
            if not isinstance(self, scls):
                raise TypeError("Cannot cast %s" % repr(self))
            for key in tuple(getattr(type(self), "__values__").__get__(self).keys()):
                if key not in scls.__attrs__:
                    del getattr(type(self), "__values__").__get__(self)[key]
            object.__setattr__(self, "__class__", scls)

        return __cast__

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        "Collects the attrs from bases"

        attrs = set()
        class_attrs = {}
        for base in bases:
            if isinstance(base, CastableType):
                attrs.update(base.__attrs__)

        for attr in kwargs.get("attrs", ()):
            key = "%s_%s" % (name, attr)
            class_attrs[attr] = property(Slot.getter(key), Slot.setter(key))
            attrs.add(key)

        class_attrs["__attrs__"] = tuple(attrs)
        class_attrs["__slots__"] = ("__values__",)
        return class_attrs

    def __new__(cls, name, bases, class_attrs, **kwargs):
        "Checks that all attrs of bases are subset of __attrs__"

        attrs = set(class_attrs["__attrs__"])
        bases = list(bases)
        bind = kwargs.get("bind", True)
        for base in list(bases):
            if isinstance(base, CastableType):
                assert attrs.issuperset(
                    base.__attrs__
                ), """
                Given attrs do not match with base class
                """
                if not bind:
                    bases.remove(base)

        self = super().__new__(cls, name, tuple(bases), class_attrs)
        self.__cast__ = cls.caster(self)
        return self

    def __call__(cls, *args, **kwargs):
        "Either calls the class initialization or simply casts"

        args = tuple(args)

        # pylint: disable=E1120
        obj = cls.__new__(cls)
        # pylint: enable=E1120
        values = dict()
        getattr(cls, "__values__").__set__(obj, values)

        if len(args) == 1 and (
            isinstance(args[0], cls) or issubclass(cls, type(args[0]))
        ):
            for attr in obj.__attrs__:
                values[attr] = (
                    getattr(type(args[0]), "__values__")
                    .__get__(args[0])
                    .get(attr, Slot())
                )
        else:
            for attr in obj.__attrs__:
                values[attr] = Slot()
            try:
                obj.__init__(*args, **kwargs)
            except AttributeError:
                pass

        return obj

    def __subclasscheck__(cls, child):
        "Checks if child is subclass of class"
        return isinstance(child, CastableType) and set(child.__attrs__).issuperset(
            cls.__attrs__
        )

    def __instancecheck__(cls, instance):
        "Checks if instance is instance of cls"
        return issubclass(type(instance), cls)
