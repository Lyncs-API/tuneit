"""
Function for checking the results
"""
# pylint: disable=C0303,C0330

import operator
from .base import sample

__all__ = [
    "test",
    "crosscheck",
]


def test(tunable, fnc, **kwargs):
    """
    Tests the results of the tunable object
    
    Parameters
    ----------
    fnc: callable
        The function to use for testing the results. It is called as test(params, value)
        and should return a value from 0 (False) to 1 (True).
    variables: list of str
        Set of variables to sample.
    samples: int
        The number of samples to run. If None, all the combinations are sampled.
    kwargs: dict
        Variables passed to the compute function. See help(tunable.compute)
    """
    sampler = sample(tunable, **kwargs)

    yield next(sampler, None)

    for params, value in sampler:
        if not isinstance(value, Exception):
            value = fnc(params, value)
        yield params, value


def crosscheck(tunable, fnc=operator.eq, reference=None, **kwargs):
    """
    Crosscheck the result of tunable against the reference.
    
    Parameters
    ----------
    fnc: callable (default = eq)
        The function to use for comparison. It is called as test(reference, value)
        and should return a value from 0 (False) to 1 (True).
    reference: Any
        The reference value. If None, than the default values are used to produce the result.
    variables: list of str
        Set of variables to sample.
    samples: int
        The number of samples to run. If None, all the combinations are sampled.
    kwargs: dict
        Variables passed to the compute function. See help(tunable.compute)
    """
    sampler = sample(tunable, **kwargs)

    variables, tunable = next(sampler, None)

    if reference is None:
        reference = tunable.copy().compute(**kwargs)

    yield variables, tunable

    for params, value in sampler:
        if not isinstance(value, Exception):
            value = fnc(reference, value)
        yield params, value
