import optuna
from optuna.trial import Trial
from optuna import exceptions
from hashlib import md5
from dill import dumps


class OptunaSampler:

    optuna_types = {
        "discrete_uniform": Trial.suggest_discrete_uniform,
        "float": Trial.suggest_float,
        "int": Trial.suggest_int,
        "loguniform": Trial.suggest_loguniform,
        "uniform": Trial.suggest_uniform,
        "categorical": Trial.suggest_categorical,
    }

    def __init__(self, tunable, callback=None, storage=None, n_trials=None, **kwargs):

        self.tunable = tunable.copy()
        self.compute_kwargs = kwargs

        self.callback = callback

        if n_trials:
            self.n_trials = n_trials
        else:
            self.n_trials = 1  # default

        self.storage = storage

    def get_attributes(self):
        return {"callback": self.callback}

    def get_study(self):
        attrs = self.get_attributes()
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
        "returns the value of the graph"
        self.get_study().optimize(
            lambda trial: self.objective(trial, **kwargs),
            self.n_trials,
            catch=self.catches,
        )
        value = self._value
        del self._value
        return value

    def _call_wrapper(self, graph, **kwargs):
        self._value = graph.compute(**kwargs)
        return self._value

    def objective(self, trial, **kwargs):
        tmp = self.get_next_trial(trial)
        return self.callback(lambda: self._call_wrapper(tmp, **kwargs))

    def get_next_trial(self, trial):
        tmp = self.tunable.copy(reset=True)
        vars = self.tunable.variables
        values = self.get_suggestions(trial)
        for v in vars:
            tmp.fix(v, values[v])
        return tmp

    def get_suggestions(self, trial):
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
        if var_type == "categorical":
            return (tuple(var_values),)
        elif var_type == "discrete_uniform":
            step = 1  # default
            return min(var_values), max(var_values), step

    @staticmethod
    def deduce_type(variable):
        "returns a type compatible with optuna: discrete_uniform, float, int, loguniform, uniform, categorical"
        # only categorical and discrete uniform are supported for the time being
        if isinstance(variable, range):
            return "discrete_uniform"
        return "categorical"

    def best_params(self, **kwargs):
        study = self.get_study()
        study.optimize(
            lambda trial: self.objective(trial, **kwargs),
            self.n_trials,
            catch=self.catches,
        )
        return study.best_params
