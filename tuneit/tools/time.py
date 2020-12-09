"Tools for measuring and optimize the execution time"
# pylint: disable=C0303,C0330

__all__ = [
    "benchmark",
    "optimize",
    "optimise",
]

from timeit import timeit
from .base import sample
from .tuner import tune


class Time(float):
    "Time formatter"
    units = {"nsec": 1e-9, "usec": 1e-6, "msec": 1e-3, "sec": 1.0}

    def __str__(self):
        scales = [(scale, unit) for unit, scale in Time.units.items()]
        scales.sort(reverse=True)
        for scale, unit in scales:
            if self >= scale:
                break

        return f"{self / scale:.3f} {unit}"

    __repr__ = __str__


def default_timer(fnc, number=1):
    return timeit(fnc, number=number) / number


def benchmark(
    tunable,
    *variables,
    timer=default_timer,
    timer_kwargs=None,
    samples=None,
    label="Time",
    **kwargs,
):
    """
    Samples the execution time.

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
    timer_kwargs: dict
        Arguments passed to the timer. For default timer:
        - number: (int) number of iterations
    kwargs: dict
        Variables passed to the compute function. See help(tunable.compute)
    """

    return sample(
        tunable,
        *variables,
        callback=lambda fnc: Time(timer(fnc, **(timer_kwargs or {}))),
        callback_calls=True,
        samples=samples,
        label=label,
        **kwargs,
    )


def optimise(tunable, timer=default_timer, timer_kwargs=None, **kwargs):
    """
    Optimizes the execution time changing the tunable parameters.

    Parameters
    ----------
    comparison: callable (default = numpy.allclose)
        The function to use for comparison. It is called as fnc(reference, value)
        and should return a value from 0 (False) to 1 (True).
    reference: Any
        The reference value. If None, than the default values are used to produce the result.
    variables: list of str
        Set of variables to sample.
    n_trials: int
        The number of trials per call.
    timer_kwargs: dict
        Arguments passed to the timer. For default timer:
        - number: (int) number of iterations
    kwargs: dict
        Variables passed to the compute function. See help(tunable.compute)
    """

    return tune(
        tunable,
        callback=lambda fnc: Time(timer(fnc, **(timer_kwargs or {}))),
        callback_calls=True,
        **kwargs,
    )


optimize = optimise
