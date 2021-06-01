Example: A small tuning example using sparse matrices
=====================================================

:code:`tuneit` is imported as shown below along with some other packages that are used in this example:

.. code-block:: python

   from tuneit import *
   import scipy.sparse as sp
   import scipy as s
   import numpy as np

Firstly, a simple graph is constructed, which computes the multiplication of a sparse matrix with a vector. 
The graph contains one variable to be tuned, which represents the different formats that can be used for the matrix.
The following function creates a matrix and by using :code:`alternatives` more options are added for the creation of a matrix and its format (available in the :code:`scipy.sparse` package).

.. code-block:: python

    @alternatives( 
        coo = lambda mat: sp.coo_matrix(mat),
        csc = lambda mat: sp.csc_matrix(mat),
        csr = lambda mat: sp.csr_matrix(mat),
        bsr = lambda mat: sp.bsr_matrix(mat)
    )
    def matrix(mat):
        return s.matrix(mat.todense())

In this way, we have created a function :code:`matrix` that expresses the given sparse matrix in an appropriate format and a variable 
to be tuned. The range of the variable :code:`which_matrix` contains all different options that can be used to express the matrix, which are included in the function above (:code:`matrix,coo,csc,csr,bsr`). 

The graph takes as input the matrix and the vector to be multiplied. One option is to create a matrix and a vector at random:

.. code-block:: python

   mat=scipy.sparse.random(100,100,0.1)
   vec=np.random.rand(100,1)

Or just create two generic data objects, which will take their actual value later on: (this is the option used in this example)

.. code-block:: python

   mat=data(info=["shape","dtype"])
   vec=data(info=["shape","dtype"])
  
:code:`data()` creates a generic data object as no specific value is passed in the function. Even though no value is passed, some information 
about the new data object can be given using :code:`info`. As shown above, some characteristics about the new objects are given by the 
attributes :code:`shape` and :code:`dtype`. 

In addition, the :code:`matrix` function constructed previously can now be used. The new :code:`mat` object created after 
:code:`matrix` is called on the object :code:`mat` (created above) is a tunable object.

.. code-block:: python

   mat=matrix(mat)

Furthermore, we define a random sparse matrix and a random vector that will be used later on when actual values are needed to be passed for the :code:`mat,vec` objects created above.

.. code-block:: python

    matrix_value = sp.random(100,100,0.1)
    vector_value = np.random.rand(100)

The final graph :code:`mul` that expresses the multiplication between the vector :code:`vec` and the sparse matrix :code:`mat` is created 
as shown below:

.. code-block:: python

   mul=mat*vec
   
Once the graph is completed we can finalize it with the function :code:`finalize`.

.. code-block:: python

   mul = finalize(mul)

This closes the graph and provides us a high-level interface for processing the graph (e.g. we can simply compute it by calling it).

.. code-block:: python

   out = mul(mat=matrix_value, vec=vector_value)


Visualize
---------

The graph can now be visualized using:

.. code-block:: python

   mul.visualize()

The result is shown below:

.. image:: images/visualised_graph1.png

The data objects are shown in rectangles, the functions to be computed are presented in oval shapes, while the variables that have not taken a fixed value yet are shown in red diamonds. 

Note: Each node in the graph is represented by its name (such as :code:`matrix`) concatenated with a random sequence of characters, which
is not shown in its visualisation (for instance :code:`matrix-2b53519cefa68a68788760b169fee0b4`). 
The small indices included in the nodes of the visualised graph allow the user to distinguish between multiple operations of the same kind 
(e.g. multiplications) and to find out the whole unique name of a node in case it is needed in an operation:

For instance the following code should return the whole name of the node that contains the index 2 in the visualization of the graph :code:`mul`: 

.. code-block:: python

   mul.graph[2]


Crosscheck 
----------

The function :code:`crosscheck` can be called on the finalised object :code:`mul` as shown below. 

.. code-block:: python

   mul.crosscheck(mat=matrix_value,vec=vector_value)

If it is called using real values (since the input :code:`mat,vec` of the graph was created using generic data objects) the sampler object
created will iterate through all the possible alternative options for the variable of the graph (:code:`which_matrix`) and return :code:`True` only for the ones 
that produce the correct result of the graph. The :code:`crosscheck` function is basically a way to check that all alternatives options return the correct result.

The result of the above operation is:

.. table::

    ==============  ========
    which_matrix    xcheck
    ==============  ========
    coo             True
    csc             True
    csr             True
    bsr             True
    matrix          True
    ==============  ========


Benchmark 
---------

The function :code:`benchmark` can be called on the finalised object :code:`mul` as shown below. 

.. code-block:: python

   mul.benchmark(mat=matrix_value,vec=vector_value)

If it is called using real values (since the input :code:`mat,vec` of the graph was created using generic data objects) the sampler object
will iterate through all the possible alternative options for the variable of the graph (:code:`which_matrix`) and time the execution of graph using each
option. The :code:`benchmark` function is basically a way to compare the execution times of all alternatives options of the variable.

The result of the above operation is:

.. table::

    ==============  ============
    which_matrix    Time
    ==============  ============
    coo             475.300 usec
    csc             1.076 msec
    csr             1.478 msec
    bsr             845.800 usec
    matrix          803.200 usec
    ==============  ============

The :code:`bechmark` function has also an argument called :code:`record`, which if it set to :code:`True` allows the execution times of the graph
using alternative options for the variable to be stored in a :code:`panda` dataframe. In addition, now there is the option of also comparing
the execution times that result not only by the various alternatives for the variable, but also different inputs. For example, in the code below
different sizes of inputs are passed in each execution of the sampler object :code:`obj`. As a result, the returned dataframe :code:`trials` (can be accessed using the sampler object) will contain the execution
time of the graph for all combinations of alternative options of the variable and different sizes of inputs.

.. code-block:: python

   sampler = mul.benchmark(record=True) 
   for n in [2**exponent for exponent in range(15)]:
       sampler().run(mat=sp.random(n,n,0.1),vec=np.random.rand(n,1))
   
The dataframe can be accessed as shown below:

.. code-block:: python   

   sampler.trials
   
The produced dataframe looks like this:

.. table::

    ==========  ==============  ==============  ===========   ===========   ===========   =========
      trial_id  which_matrix    mat_shape       mat_dtype     vec_shape     vec_dtype          time
    ==========  ==============  ==============  ===========   ===========   ===========   =========
             0  coo             (1, 1)          float64       (1, 1)        float64       0.0020286
             1  csc             (1, 1)          float64       (1, 1)        float64       0.0042852
             2  csr             (1, 1)          float64       (1, 1)        float64       0.0021259
             3  bsr             (1, 1)          float64       (1, 1)        float64       0.0021831
             4  matrix          (1, 1)          float64       (1, 1)        float64       0.0005839
           ...  ...             ...             ...           ...           ...           ...
            70  coo             (16384, 16384)  float64       (16384, 1)    float64       0.333415
            71  csc             (16384, 16384)  float64       (16384, 1)    float64       6.21665
            72  csr             (16384, 16384)  float64       (16384, 1)    float64       6.42704
            73  bsr             (16384, 16384)  float64       (16384, 1)    float64       7.46502
            74  matrix          (16384, 16384)  float64       (16384, 1)    float64       6.29298
    ==========  ==============  ==============  ===========   ===========   ===========   =========

The dataframe can be then used to compare different sizes of inputs for the different alternatives for the variable. One way to do this visually
is producing a graph like it is shown below:

.. image:: images/plot.png


Optimize:
---------

For the purposes of this example, we would like to tune the variable :code:`which_matrix` based only on the computation time of the multiplication 
(i.e. excluding the time taken by the function :code:`matrix` to construct the matrix). In order to achieve this, a link has to be added 
between the multiplication and :code:`which_matrix`, as they are not currently directly connected (:code:`which_matrix` is added as a dependency to the last node 
of the graph):

.. code-block:: python

   mul.add_deps('which_matrix')

The new link can be observed by running the code:

.. code-block:: python

   mul.visualize()

.. image:: images/visualised_graph2.png

In addition, the :code:`matrix` node in the graph needs to be marked as one to be precomputed so that its computation time is not 
taken into account when the execution of the graph is timed during the tuning of the variable. 
Note: In the following operation we can use the name :code:`matrix` for the node only because it is unique in the graph. If there were 
multiple operations of the same kind (e.g. the function :code:`matrix` is used twice in the graph), then the full name of the node would 
have to be used.

.. code-block:: python

   mul['matrix'].precompute=True 

The only thing left to do is to actually tune the variable by calling the following functions:

.. code-block:: python

   mul.optimize(mat=matrix_value,vec=vector_value,sampler='optuna')()

A tuner object has been created by calling the :code:`optimize()` function on the graph to be tuned and passing it the sampler to be used.
The :code:`optuna` package is one of the options that are offered by :code:`tuneit` to be used as a sampler.

The tuner object is called, while also passing actual values for the sparse matrix and the vector. This is necessary, because 
during the tuning of the variable the computation of the graph will be carried out for the first time. Each time the tuner object is 
called, the tuner executes one more trial and it returns the value that was used for the variable in that trial and the resulting computation 
time along with the best trial executed so far. 
Note: A trial is a single execution of the objective function (which in this case is the timing of an execution) using a different combination
of values for the variables that are tuned. 

.. 
   do I need to include a picture of the result here? (what the tuner returns after it is called a few times)
