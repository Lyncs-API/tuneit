import optuna
from optuna.trial import Trial
from optuna import exceptions
from hashlib import md5
from dill import dumps
from tuneit.finalize import HighLevel


class OptunaSampler:
    "Creates a sampler using the optuna package"

    optuna_types = {
        "discrete_uniform": Trial.suggest_discrete_uniform,
        "float": Trial.suggest_float,
        "int": Trial.suggest_int,
        "loguniform": Trial.suggest_loguniform,
        "uniform": Trial.suggest_uniform,
        "categorical": Trial.suggest_categorical,
    }

    def __init__(self, tunable, callback=None, storage=None, n_trials=None, **kwargs):
        """
        Initialises the parameters of the class:

        Parameters
        ----------
        tunable: HighLevel object
            A finalised tunable object whose parameters will be tuned.
        kwargs: Any
            Variables that will be used for the computation of the graph.
        n_trials: int
            The number of trials optuna will execute for the tunable object.
        storage: sqlite file name
            Local file where the trials in this study will be saved.
            Example: "sqlite:///example.db"
        callback: callable
            The objective function to be used for the tuning of parameters.
        """

        self.tunable = HighLevel(tunable).copy()
        self.compute_kwargs = kwargs

        self.callback = callback

        self.n_trials = n_trials or 1

        self.storage = storage

    def get_study(self):
        "Creates a new study or loads a pre-existing one if the name already exists"
        attrs = self.tunable.get_info()
        attrs["callback"] = self.callback
        name = md5(dumps(attrs)).hexdigest()
        try:
            study = optuna.create_study(study_name=name, storage=self.storage)
            for key, val in attrs.items():
                study.set_user_attr(
                    key, repr(val)
                )  # because the value should be JSON serializable
        except exceptions.DuplicatedStudyError:
            study = optuna.load_study(study_name=name, storage=self.storage)
        return study

    @property
    def catches(self):
        return (Exception,)

    def compute(self, **kwargs):
        "Returns the value of the graph after completing the set number of trials for the tuning of the parameters"
        self.get_study().optimize(
            lambda trial: self.objective(trial, **kwargs),
            self.n_trials,
            catch=self.catches,
        )
        value = self._value
        del self._value
        return value

    def _call_wrapper(self, graph, **kwargs):
        "Computes and returns the value of the graph"
        self._value = graph.compute(**kwargs)
        return self._value

    def objective(self, trial, **kwargs):
        "Computes and returns the objective function (callback) value for the next trial"
        tmp = self.get_next_trial(trial)
        tmp.precompute(**kwargs)
        return self.callback(lambda: self._call_wrapper(tmp, **kwargs))

    def get_next_trial(self, trial):
        "Returns the next trial: a tunable object whose variables have been fixed with a combination of options"
        tmp = self.tunable.copy(reset=True)
        vars = self.tunable.variables
        values = self.get_suggestions(trial)
        for v in vars:
            tmp.fix(v, values[v])
        return tmp

    def get_suggestions(self, trial):
        "Returns a suggested option for each variable that will be tuned"
        vars = self.tunable.variables
        values = {}
        for v in vars:
            var = self.tunable.get_variable(v)
            var_values = var.values
            var_type = self.deduce_type(var_values)
            var_args = self.get_var_args(var_type, var_values)
            values[v] = OptunaSampler.optuna_types[var_type](trial, v, *var_args)
        return values

    @staticmethod
    def get_var_args(var_type, var_values):
        "Returns the arguments needed for each optuna type of variable"
        if var_type == "categorical":
            return (tuple(var_values),)
        elif var_type == "discrete_uniform":
            step = 1  # default
            return min(var_values), max(var_values), step

    @staticmethod
    def deduce_type(variable):
        "Returns a type compatible with optuna: discrete_uniform, float, int, loguniform, uniform, categorical"
        # only categorical and discrete uniform are supported for the time being
        if isinstance(variable, range):
            return "discrete_uniform"
        return "categorical"

    def best_params(self, **kwargs):
        "Returns the best options for the variables of this graph"
        study = self.get_study()
        study.optimize(
            lambda trial: self.objective(trial, **kwargs),
            self.n_trials,
            catch=self.catches,
        )
        return study.best_params
