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
from tabulate import tabulate
from ..finalize import finalize


class Sampler:
    "Base class for sampling values of a tunable object"

    def __init__(
        self,
        tunable,
        variables=None,
        n_samples=None,
        callback=None,
        callback_calls=False,
        label=None,
        **kwargs,
    ):
        "Initializes the tunable object and the variables"

        self.tunable = finalize(tunable).copy()
        self.compute_kwargs = kwargs

        if callback:
            self.callback = callback
        self.callback_calls = callback_calls

        if label:
            self.label = label

        if variables:
            self.variables = tuple(
                str(tunable.get_variable(var).key) for var in variables
            )

            set_vars = set(self.variables)
            set_tunable = set(self.tunable.tunable_variables)
            if not set_vars <= set_tunable:
                raise ValueError(
                    f"Variable(s) {set_vars-set_tunable} have been fixed and cannot be tuned"
                )

            # Fixes the tunable variable not involved
            for var in set_tunable.difference(set_vars):
                self.tunable.fix(var)

        else:
            self.variables = self.tunable.tunable_variables

        if n_samples:
            self.n_samples = n_samples

    @property
    def max_samples(self):
        "Size of the parameter space (product of variables' size)"
        lens = tuple(self.tunable[var].size for var in self.variables)
        return reduce(operator.mul, lens)

    @property
    def n_samples(self):
        "Number of samples"
        return getattr(self, "_n_samples", self.max_samples)

    @n_samples.setter
    def n_samples(self, value):
        if not (isinstance(value, int) and value > 0):
            raise ValueError("n_samples must be a positive integer")
        self._n_samples = min(value, self.max_samples)

    def __len__(self):
        self.n_samples

    @property
    def samples(self):
        "Samples of the parameters space"

        iters = tuple(self.tunable[var].values for var in self.variables)
        values = product(*iters)

        if self.n_samples >= self.max_samples:
            return tuple(values)

        idxs = sorted(random.sample(range(self.max_samples), self.n_samples))

        return tuple(
            val for idx, val in filter(lambda _: _[0] in idxs, enumerate(values))
        )

    def sample_values(self):
        "Returns the sampled values"
        return list(self)

    @property
    def callback(self):
        return getattr(self, "_callback", lambda _: _)

    @callback.setter
    def callback(self, value):
        "Function to be called on the result"
        if not callable(value):
            raise TypeError("callback must be a callable")
        self._callback = value

    def __iter__(self):
        for params in self.samples:
            tmp = self.tunable.copy()
            for var, val in zip(self.variables, params):
                tmp.fix(var, val)
            try:
                if self.callback_calls:
                    result = self.callback(lambda: tmp.compute(**self.compute_kwargs))
                else:
                    result = self.callback(tmp.compute(**self.compute_kwargs))
            except Exception as err:
                result = err
            yield params, result

    @property
    def label(self):
        "Label used for the result"
        return getattr(self, "_label", self.tunable.label)

    @label.setter
    def label(self, value):
        self._label = str(value)

    @property
    def headers(self):
        "Headers for the values returned by the sampler"
        return tuple(self.tunable[var].label for var in self.variables) + (self.label,)

    def tabulate(self, **kwargs):
        "Returns a table of the values"
        kwargs.setdefault("headers", self.headers)
        return tabulate((params + (repr(result),) for params, result in self), **kwargs)

    def _repr_html_(self):
        return self.tabulate(tablefmt="html")


def sample(tunable, *variables, samples=100, **kwargs):
    """
    Samples the value of the tunable object
    
    Parameters
    ----------
    variables: list of str
        Set of variables to sample.
    samples: int
        The number of samples to run. If None, all the combinations are sampled.
    kwargs: dict
        Variables passed to the compute function. See help(tunable.compute)
    """
    return Sampler(tunable, variables=variables, n_samples=samples, **kwargs)
