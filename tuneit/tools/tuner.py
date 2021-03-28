__all__ = [
    "tune",
]

from .base import Sampler
from ..finalize import HighLevel

try:
    from .optuna import OptunaSampler
except ImportError:
    OptunaSampler = None


class Tuner(HighLevel, attrs=["tuner_kwargs"]):
    def __init__(self, tunable, **kwargs):
        "Initializes the tunable object and the variables"
        super().__init__(tunable)
        self.tuner_kwargs = kwargs

    def copy(self, **kwargs):
        tmp = super().copy(**kwargs)
        return Tuner(tmp, **self.tuner_kwargs)

    def compute(self, **kwargs):
        "Calls a sampler to tune the whole graph"
        # graph_manager = self.divide_graph()
        # for subgraph in graph_manager:
        #     value = self.get_sampler()(subgraph,**self.get_sampler_kwargs()).compute(**kwargs)
        #     graph_manager.store(subgraph, value)
        value = self.get_sampler()(self, **self.get_sampler_kwargs()).compute(**kwargs)
        return value

    def get_best_trial(self):
        "Returns the best options for the variables of the graph after it has been tuned"
        return self.get_sampler()(self, **self.get_sampler_kwargs()).best_params()

    def get_sampler(self):
        "Returns the name of the appropriate sampler class to be called based on the sampler argument in kwargs"
        sampler = self.tuner_kwargs.get("sampler", None)
        if not sampler:
            return Sampler
        if sampler in [
            "Optuna",
            "optuna",
        ]:
            if OptunaSampler is None:
                raise ImportError("Optuna not installed")
            return OptunaSampler
        raise ValueError(f"Unknown sampler {sampler}")

    def get_sampler_kwargs(self):
        "Returns the appropriate arguments for the selected sampler"
        sampler_kwargs = {}
        if self.get_sampler() is OptunaSampler:
            sampler_kwargs = {
                "callback": self.tuner_kwargs.get("callback", None),
                "storage": "sqlite:///example.db",
            }
        return sampler_kwargs


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
