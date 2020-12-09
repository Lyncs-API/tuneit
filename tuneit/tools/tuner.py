__all__ = [
    "tune",
]

# import optuna
# from optuna.trial import Trial
from .base import Sampler
from ..finalize import HighLevel


class Tuner(HighLevel, attrs=["tuner_kwargs"]):
    def __init__(self, tunable, **kwargs):
        "Initializes the tunable object and the variables"
        super().__init__(tunable)
        self.tuner_kwargs = kwargs

    def _compute(self, graph):
        # fix parameters getting suggestions from sampler
        # compute within callback
        # give parameters and call back values to a fnc
        return value

    def compute(self, **kwargs):
        graph_manager = self.divide_graph()
        for subgraph in graph_manager:
            value = self._compute(subgraph)
            graph_manager.store(subgraph, value)

        return value

    def get_sampler(self):
        sampler = self.tuner_kwargs.get("sampler", None)
        if not sampler:
            return Sampler
        if sampler in [
            "Optuna",
            "optuna",
        ]:
            return OptunaSampler
        raise ValueError(f"Unknown tuner {tuner}")


def tune(tunable, **kwargs):
    """
    Tunes the value of the tunable object

    Parameters
    ----------
    variables: list of str
        Set of variables to sample.
    tuner: str or class
        The tune to use. Options = None, Optuna, ...
    kwargs: dict
        Variables passed to the tuner function
    """
    return Tuner(tunable, **kwargs)
