"""
Base methods for the tunable tools
"""
# pylint: disable=C0303,C0330

__all__ = [
    "sample",
]

import operator
import random
from functools import reduce
from itertools import product
from ..finalize import finalize


def init(tunable, variables):
    "Initializes the tunable object and the variables"

    tunable = finalize(tunable).copy()
    variables = variables if variables is not None else tunable.tunable_variables
    variables = tuple(tunable.get_variable(var).key for var in variables)

    set_vars = set(variables)
    set_tunable = set(tunable.tunable_variables)
    if not set_vars <= set_tunable:
        raise ValueError(
            "Variable(s) %s have been fixed and cannot be tuned"
            % set_vars.difference(set_tunable)
        )

    # Fixes the tunable variable not involved
    for var in set_tunable.difference(set_vars):
        tunable.fix(var)

    return tunable, variables


def sample(tunable, variables=None, samples=100, **kwargs):
    """
    Samples the value of the tunable object
    
    Parameters
    ----------
    variables: list of str
        Set of variables to sample during the comparison
    samples: int
        The number of samples to use in the crosscheck. If None, all the combinations are sampled.
    kwargs: dict
        Variables passed to the compute function. See help(tunable.compute)
    """
    tunable, variables = init(tunable, variables)

    lens = tuple(tunable[var].size for var in variables)
    iters = tuple(tunable[var].values for var in variables)
    tot = reduce(operator.mul, lens)
    values = product(*iters)

    if tot > samples:
        idxs = set(random.sample(range(tot), samples))
        values = map(lambda t: t[1], filter(lambda t: t[0] in idxs, enumerate(values)))

    yield (variables, tunable)
    for value in values:
        tmp = tunable.copy()
        for var, val in zip(variables, value):
            tmp.fix(var, val)
        try:
            result = tmp.compute(**kwargs)
        except Exception as err:
            result = err
        yield (value, result)
