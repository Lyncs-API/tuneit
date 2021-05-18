.. Tunable documentation master file.

Tuneit: 
=======

Welcome to Tuneit's documentation!
===================================

..
   title needs to change

Basic Concepts
--------------
The Tuneit package works with computational graphs, which have two main phases:

- A construction phase, where the graph is being built. Every operation that needs to be performed will be added to the graph as node along with all the variables and data input and output. Each type of node is visualised differently in the graph as it is shown below:
  
  * Variables: they are represented using diamonds. The outline is red in case the variable does not have a value yet and green in case the                 variable has been assigned a fixed value.
  * Operations: they are represented using oval shapes.
  * Data: All data objects are represented with rectangles. Most of them represent data inputs, except for the last node in the graph, which
          is represents the data output.
          
  .. 
     add image images/ 

- A finalization phase. After the graph is finalized, a number of operations (described in the next section) can be performed on it.


Key Features and Functions
--------------------------
Once a computational graph has been built and finalized, it can be used in a number of operations.

- **Visualize:** Using the :code:`visualize()` function the graph can be visualized as it is shown above.
- **Compute:** By simply calling the finalized object of the graph, the value final of the graph is computed and returned. 
- **Crosshcheck:** The :code:`crosscheck()` function will iterate through all the different options for a variable and return :code:`True` 
  only for the ones that return the correct result of the graph. 
- **Benchmark:** By using the :code:`benchmark()` function, the computation times of all the different combinations of options for the 
  variables can be compared. In addition, by using the attribute :code:`record` of the function, all those times can be recorded in a  
  dataframe. Furthermore, the :code:`record` option allows for comparisons between not only the execution times that result by the various 
  alternatives for the variables, but also different inputs.
- **Optimize:** By using the :code:`optimize()` function, the variables of the graph can be tuned. Each time it is called, it returns the 
  values that were used for the variables in that trial and the resulting computation time along with the best trial executed so far. 
  A trial consists of the timing of an execution of the graph using a different combination of values for the variables that are tuned. 


.. toctree::
   :maxdepth: 2
   :caption: Contents:
    
   installation
   example


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
