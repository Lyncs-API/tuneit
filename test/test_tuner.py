from tuneit import *
import numpy
from tuneit.tools.tuner import Tuner
from tuneit.tools.time import Time,default_timer
from tuneit.tools.optuna import OptunaSampler
from tuneit.tools.base import Sampler
import pytest

def test_tuner():
    # simple example to use in tests 
    # building a graph with variables for sorting (preprocessing) and searching to be tuned:

    @alternatives(
        mergesort = lambda a: numpy.sort(a, kind='mergesort'),
        heapsort = lambda a: numpy.sort(a, kind='heapsort'),
        timsort=lambda a: numpy.array(sorted(a)),
    )
    def preprocessing(array):
        res = numpy.sort(array) 
        return res

    @alternatives(
        indices = lambda a, b: [i for i, x in enumerate(a.tolist()) if x == b][0], 
        array_search = lambda a, b: numpy.where(a == b)[0][0],       
        binary_search = lambda a, b: numpy.searchsorted(a, b), 
    )
    def searching(array, element):
        l = array.tolist()
        index = l.index(element)
        return index

    element = 65
    result = searching(preprocessing(numpy.random.randint(1000,size=(10000))),element) #input size: 10 000, type: integers



    # test optimise function
    obj_A = optimise(result, sampler = "optuna")
    assert isinstance(obj_A,Tuner)

    # test tune function
    obj_B = tune(result,callback=lambda fnc: Time(default_timer(fnc)))
    assert isinstance(obj_B,Tuner)
    
    # test Tuner class
    obj_C = Tuner(result,sampler = "optuna",callback=lambda fnc: Time(default_timer(fnc)))
    assert isinstance(obj_C, Tuner)
    assert bool(obj_C.tuner_kwargs)
    assert callable(obj_B.tuner_kwargs.get("callback", None))
    # test compute function in Tuner
    assert obj_C.compute()==finalize(result).compute()
    # test get_best_trial function in Tuner
    res = obj_C.get_best_trial()
    assert isinstance(res,dict)
    assert 'preprocessing' in {k.split('-')[0]:v for k,v in res.items()}
    assert next(v for k,v in res.items() if k.startswith('preprocessing')) in preprocessing.keys()
    assert 'searching' in {k.split('-')[0]:v for k,v in res.items()}
    assert next(v for k,v in res.items() if k.startswith('searching')) in searching.keys()
    # test get_sampler function in Tuner
    assert obj_C.get_sampler() == OptunaSampler
    assert Tuner(result,sampler = None,callback=lambda fnc: Time(default_timer(fnc))).get_sampler() == Sampler
    with pytest.raises(ValueError):
        Tuner(result,sampler = "hello",callback=lambda fnc: Time(default_timer(fnc))).get_sampler()
    #test get_sampler_kwargs function in Tuner
    kwargs = obj_C.get_sampler_kwargs()
    assert kwargs["storage"]=="sqlite:///example.db"
    assert kwargs["callback"]==obj_C.tuner_kwargs.get("callback", None)
    kwargs = Tuner(result,sampler = None,callback=lambda fnc: Time(default_timer(fnc))).get_sampler_kwargs()
    assert not bool(kwargs)



