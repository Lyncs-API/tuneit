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
            return getattr(type(self), key).__get__(self).value

        return fget

    @classmethod
    def setter(cls, key):
        "Returns the setter function"

        def fset(self, value):
            getattr(type(self), key).__get__(self).value = value

        return fset


class CastableType(type):
    """
    A metaclass for castable classes.

    >>> from tunable.meta import CastableType
    
    >>> class Foo(metaclass=CastableType, slots=["foo"]):
    ...     pass
    
    >>> class Bar(Foo, slots=["bar"], bind=False):
    ...     pass
    
    >>> Bar.__slots__
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
    def __prepare__(cls, name, bases, **kwargs):
        "Collects the slots from bases"

        slots = set()
        attrs = dict()
        for base in bases:
            if isinstance(base, CastableType):
                slots.update(base.__slots__)

        for slot in kwargs.get("slots", []):
            key = "%s_%s" % (name, slot)
            attrs[slot] = property(Slot.getter(key), Slot.setter(key))
            slots.add(key)

        attrs["__slots__"] = list(slots)
        print(attrs)
        return attrs

    def __new__(cls, name, bases, attrs, **kwargs):
        "Checks that all slots of bases are subset of __slots__"

        slots = set(attrs["__slots__"])
        bases = list(bases)
        bind = kwargs.get("bind", True)
        for base in list(bases):
            if isinstance(base, CastableType):
                assert slots.issuperset(
                    base.__slots__
                ), """
                Given slots do not match with base class
                """
                if not bind:
                    bases.remove(base)

        return super().__new__(cls, name, tuple(bases), attrs)

    def __call__(cls, *args, **kwargs):
        "Either calls the class initialization or simply casts"

        args = tuple(args)

        # pylint: disable=E1120
        obj = cls.__new__(cls)
        # pylint: enable=E1120

        if len(args) == 1 and (
            isinstance(args[0], cls) or issubclass(cls, type(args[0]))
        ):
            for slot in obj.__slots__:
                try:
                    value = getattr(type(args[0]), slot).__get__(args[0])
                    getattr(cls, slot).__set__(obj, value)
                except AttributeError:
                    getattr(cls, slot).__set__(obj, Slot())
        else:
            for slot in obj.__slots__:
                getattr(cls, slot).__set__(obj, Slot())
            try:
                obj.__init__(*args, **kwargs)
            except AttributeError:
                pass

        return obj

    def __subclasscheck__(cls, child):
        "Checks if child is subclass of class"
        return isinstance(child, CastableType) and set(child.__slots__).issuperset(
            cls.__slots__
        )

    def __instancecheck__(cls, instance):
        "Checks if instance is instance of cls"
        return issubclass(type(instance), cls)
