"""
Function for checking the results
"""
# pylint: disable=C0303,C0330

import operator
from numpy import allclose
from .base import sample
from ..finalize import finalize

__all__ = [
    "crosscheck",
]


def crosscheck(
    tunable,
    *variables,
    comparison=allclose,
    samples=None,
    reference=None,
    label="xcheck",
    **kwargs
):
    """
    Crosscheck the result of tunable against the reference.
    
    Parameters
    ----------
    comparison: callable (default = numpy.allclose)
        The function to use for comparison. It is called as fnc(reference, value)
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
    if reference is None:
        reference = finalize(tunable).copy().compute(**kwargs)

    return sample(
        tunable,
        *variables,
        callback=lambda res: comparison(reference, res),
        samples=samples,
        label=label,
        **kwargs
    )
