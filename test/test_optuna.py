from tuneit import *
import numpy
from tuneit.tools.time import Time, default_timer
from tuneit.tools.optuna import OptunaSampler
import pytest
import optuna
from optuna.trial import Trial
from optuna.trial import create_trial
from optuna.distributions import CategoricalDistribution
from optuna.trial import TrialState
from tuneit.finalize import HighLevel
from optuna.study import Study
from hashlib import md5
from dill import dumps


def test_optuna_sampler():
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
    result = searching(
        preprocessing(numpy.random.randint(1000, size=(10000))), element
    )  # input size: 10 000, type: integers
    fz = finalize(result)

    callback_function = lambda fnc: Time(default_timer(fnc))
    obj_A = OptunaSampler(
        fz, callback=callback_function, storage="sqlite:///example.db"
    )
    assert isinstance(obj_A, OptunaSampler)
    assert isinstance(obj_A.tunable, HighLevel)
    assert not bool(
        obj_A.compute_kwargs
    )  # at the moment no kwargs are used for the compute function, so compute_kwargs must be empty
    assert callable(obj_A.callback)
    assert obj_A.n_trials > 0

    # test get_study function
    study = obj_A.get_study()
    assert isinstance(study, Study)
    name=obj_A.tunable.get_info()
    name["callback"] = obj_A.callback
    assert study.study_name == md5(dumps(name)).hexdigest()
    assert [*study.user_attrs.keys()] == ["callback"]
    obj_B = OptunaSampler(
        fz, callback=callback_function, storage="sqlite:///example.db", n_trials=10
    )
    assert obj_A.compute() == finalize(result).compute()  # test compute function
    assert obj_B.compute() == finalize(result).compute()
    name_A = obj_A.get_study().study_name
    name_B = obj_B.get_study().study_name
    assert name_A == name_B
    assert len(study.trials) >= 11

    # test _call_wrapper function
    assert obj_A._call_wrapper(obj_A.tunable) == finalize(result).compute()

    # test objective function
    tid = study._storage.create_new_trial(study._study_id)
    trial = Trial(study, trial_id=tid)
    assert isinstance(obj_A.objective(trial), Time)

    # test get_next_trial
    temp = obj_A.get_next_trial(trial)
    assert len(temp.fixed_variables) == 2
    var_A = temp.get_variable("which_preprocessing")
    var_B = temp.get_variable("which_searching")
    assert var_A.fixed and var_B.fixed

    # test get_suggetions
    selected_options = obj_A.get_suggestions(trial)
    assert len(selected_options) == len(fz.variables)
    assert [*selected_options.values()][0] in preprocessing.keys()
    assert [*selected_options.values()][1] in searching.keys()

    # test get_var_args function
    assert OptunaSampler.get_var_args("categorical", ["a", "b", "c"]) == (
        tuple(["a", "b", "c"]),
    )
    args = OptunaSampler.get_var_args("discrete_uniform", range(100))
    assert len(args) == 3
    assert args[0] == min(range(100))
    assert args[1] == max(range(100))
    assert args[2] == 1

    # test deduce_type function
    assert OptunaSampler.deduce_type(range(100)) == "discrete_uniform"
    assert OptunaSampler.deduce_type([1, 2, 17, 25]) == "categorical"
    assert OptunaSampler.deduce_type(preprocessing.values()) == "categorical"

    # test best_params
    best = obj_A.best_params()
    assert len(best.keys()) == len(fz.variables)
    assert [*best.values()][0] in preprocessing.keys()
    assert [*best.values()][1] in searching.keys()

    optuna.delete_study(name_A, storage="sqlite:///example.db")


# If I want to delete the study and start a new one the next time I run the tests
# optuna.delete_study(name_B, storage="sqlite:///example.db")
