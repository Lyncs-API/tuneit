from tuneit import *
import numpy
from tuneit.tools.time import Time, default_timer
from tuneit.tools.base import Sampler
from tuneit.finalize import HighLevel
import itertools


def test_sampler():
    # simple example to use in tests
    # building a graph with variables for sorting (preprocessing) and searching to be tuned:

    @alternatives(
        mergesort=lambda a: numpy.sort(a, kind="mergesort"),
        heapsort=lambda a: numpy.sort(a, kind="heapsort"),
        timsort=lambda a: numpy.array(sorted(a)),
    )
    def preprocessing(array):
        res = numpy.sort(array)
        return res

    @alternatives(
        indices=lambda a, b: [i for i, x in enumerate(a.tolist()) if x == b][0],
        array_search=lambda a, b: numpy.where(a == b)[0][0],
        binary_search=lambda a, b: numpy.searchsorted(a, b),
    )
    def searching(array, element):
        l = array.tolist()
        index = l.index(element)
        return index

    element = 65
    result = searching(preprocessing(numpy.random.randint(1000, size=(10000))), element)
    fz = finalize(result)

    callback_function = lambda fnc: Time(default_timer(fnc))

    obj = sample(
        result,
        ["which_preprocessing", "which_searching"],
        callback=callback_function,
        callback_calls=True,
    )
    assert isinstance(obj, Sampler)
    assert callable(obj.callback)
    assert obj.callback == callback_function
    assert len(obj.variables) == 2
    assert obj.variables[0] in fz.variables
    assert obj.variables[1] in fz.variables
    assert not obj.compute_kwargs
    assert isinstance(obj.tunable, HighLevel)

    assert obj.max_samples == 16
    assert obj.n_samples == 16
    assert obj.samples == tuple(
        itertools.product([*preprocessing.keys()], [*searching.keys()]),
    )
    values = obj.sample_values()
    for a in [x[1] for x in values]:
        assert isinstance(a, Time)
    assert [x[0] for x in values] == list(obj.samples)
    assert obj.value == fz.compute()

    obj_B = benchmark(fz.copy(reset=True))
    assert isinstance(obj_B, Sampler)
    assert obj_B.samples == obj.samples
    assert obj_B.value == obj.value

    obj_C = crosscheck(fz.copy(reset=True))
    assert isinstance(obj_C, Sampler)
    values2 = obj_C.sample_values()
    for a in [x[1] for x in values2]:
        assert isinstance(a, bool)
    assert obj_C.samples == obj.samples
