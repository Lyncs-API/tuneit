__all__ = [
    "SlotsBased",
]


class SlotsBased(type):
    """
    A metaclass for slots-based classes.

    >>> from tunable.meta import SlotsBased
    
    >>> class Foo(metaclass=SlotsBased):
    ...     __slots__ = ["_foo"]
    ...     def foo(self):
    ...         pass
    
    >>> class Bar(Foo, bind=False):
    ...     __slots__ += ["_bar"]
    ...     def bar(self):
    ...         pass
    
    >>> Bar.__slots__
        ["_foo", "_bar"]
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
        for base in bases:
            if isinstance(base, SlotsBased):
                slots.update(base.__slots__)

        return {"__slots__": list(slots)}

    def __new__(cls, name, bases, attrs, **kwargs):
        "Checks that all slots of bases are subset of __slots__"

        slots = set(attrs["__slots__"])
        bases = list(bases)
        bind = kwargs.get("bind", True)
        for base in list(bases):
            if isinstance(base, SlotsBased):
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
        obj = cls.__new__(cls)

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
        return isinstance(child, SlotsBased) and set(child.__slots__).issuperset(
            cls.__slots__
        )

    def __instancecheck__(cls, instance):
        "Checks if instance is instance of cls"
        return issubclass(type(instance), cls)


class Slot:
    __slots__ = ["_value"]

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
