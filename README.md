# tuneit: tune, benchmark and crosscheck

[![python](https://img.shields.io/pypi/pyversions/tuneit.svg?logo=python&logoColor=white)](https://pypi.org/project/tuneit/)
[![pypi](https://img.shields.io/pypi/v/tuneit.svg?logo=python&logoColor=white)](https://pypi.org/project/tuneit/)
[![license](https://img.shields.io/github/license/Lyncs-API/tuneit?logo=github&logoColor=white)](https://github.com/Lyncs-API/tuneit/blob/master/LICENSE)
[![build & test](https://img.shields.io/github/workflow/status/Lyncs-API/tuneit/build%20&%20test?logo=github&logoColor=white)](https://github.com/Lyncs-API/tuneit/actions)
[![codecov](https://img.shields.io/codecov/c/github/Lyncs-API/tuneit?logo=codecov&logoColor=white)](https://codecov.io/gh/Lyncs-API/tuneit)
[![pylint](https://img.shields.io/badge/pylint%20score-8.8%2F10-yellowgreen?logo=python&logoColor=white)](http://pylint.pycqa.org/)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg?logo=codefactor&logoColor=white)](https://github.com/ambv/black)

Tuneit is a generic purpose tool for optimizing and crosschecking calculations.
Its usage is simple and with few changes one can turn few lines of Python code
into a tunable and dynamical calculation.

## Installation

The package can be installed via `pip`:

```
pip install [--user] tuneit
```

## A simple tuning example using sparse matrices

We can import tuneit as shown below along with some other packages that are used in this example:

```
from tuneit import *
import scipy.sparse as sp
import numpy as np
```

Firstly, we construct a simple graph that containes one variable to be tuned and computes the multiplication of a sparse matrix with a vector:

We write a function that creates the sparse matrix and using *alteratives* we can add more options for the format that will be used to express the matrix (available in the scipy.sparse package).

```
@alternatives(
    coo = lambda matrix: sp.coo_matrix(matrix),
    csc = lambda matrix: sp.csc_matrix(matrix),
    csr = lambda matrix: sp.csr_matrix(matrix)
)
def create_matrix(matrix): 
    res = sp.bsr_matrix(matrix)
    return res
```

In this way, we have created a function `create_matrix` that expresses the given sparse matrix in an appropriate format and a variable to be tuned (whose range contains all the different options of formats presented in the function for the creation of the matrix). The default name of the variable is `which_create_matrix` after the name of the function that creates it, but it can be easily changed as shown below:

```
create_matrix.var_name="foo"
```

Our graph takes as input the matrix and the vector to be multiplied. For the purpose of this example, instead of creating a matrix and vector at random we can create two generic data objects that can take their actual value later on.

Instead of:
```
mat=scipy.sparse.random(100,100,0.1)
vec=np.random.rand(100)
```
we can just use:
```
mat=data(info=["shape","dtype"])
vec=data(info=["shape","dtype"])
mat=create_matrix(mat)
```

`data()` creates a generic data object as no specific value is passed in the function. Even though no value is passed, some information about the new data object can be given using `info`. As shown above, some characteristics about the new objects are given by the attributes `shape` and `dtype`.
In addition, the `create_matrix` function constructed previously can now be used. The new `mat` object created after `create_matrix` is called on the data object `mat` is a tunable object.

We can create the final graph `mul` that expresses the multiplication of the vector `vec` and sparse matrix `mat` as shown below:

```
mul=finalize(mat*vec)
```

We can now visualize the graph using:

```
visualize(mul)
```
The data objects are shown in rectangles, the functions to be computed are presented in oval shapes, while the variables that have not taken a fixed value yet are shown in red diamonds.

For the purposes of this example, we would like to tune the variable `foo` based only on the computation time of the multiplication (i.e. excluding the time taken by the function `create_matrix` to contruct the matrix). In order to achieve this, we have to add a link between the multiplication and `foo` as they are not currently connected (we add `foo` as a dependency to the last node of the graph):

```
mul.add_deps('foo')
```

In addition, we mark the `create_matrix` node in the graph as one to be precomputed so that its computation time is not included in the overall time that will be used to tune the variable.

```
mul['create_matrix'].precompute=True 
```

The only thing left to do is to actually tune the variable by calling the following functions:

```
obj = optimise(mul,sampler='optuna')
```
A tuner object has been created by passing the graph to be tuned along with the sampler to be used to the `optimise()` function. The optuna package is utilised by tuneit as one of the options to be used.

Now, we can simply call the tuner object while also passing actual values for the sparse matrix and the vector, because now will be the first time that those are necessary when the computations of the graph will be carried out. Each time the object is called the tuner executes one more trial that uses a different option for the variable and it returns the resulting computation time along with the best trial executed so far. 

For example:
```
obj(mat=sp.random(100,100,0.1),vec=np.random.rand(100))
```


