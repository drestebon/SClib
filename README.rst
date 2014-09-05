SClib
=====

A simple hack that allows easy and straightforward evaluation of C functions
within python code, boosting flexibility for better trade-off between
computation power and feature availability, such as visualization and existing
computation routines in SciPy.

At the core of SClib is ctypes [Hell]_, which actually does the whole work: it
maps Python data to C compatible data and provides a way to call functions in
DLLs or shared libraries.  SClib acts as glue: it puts things together for the
user, to provide him with an easy to use interface.

Installation
------------

Dependencies
............

SClib depends on the following packages:

    1. A compiler and a linker, e.g. gcc, ld
    2. Numpy_

.. _Numpy: http://numpy.scipy.org/

Install
.......

First, get the latest source code using:

.. code-block:: bash

    $ git clone https://github.com/drestebon/SClib.git

In your SClib folder, edit setup.py to reflect the configuration of your system, then do

.. code-block:: bash

    $ python setup.py build
    $ sudo python setup.py install


SClib is also available at PyPI_, you can install it with:

.. _PyPI: https://pypi.python.org/pypi/SClib/1.0.0

.. code-block:: bash

    $ pip install SClib

Usage
-----

Initialize a library in the python side with the path to the DLL (or shared
library) and a list with the names of the functions you want to call:

.. code-block:: python

   In [1]: import SClib as sc
   In [2]: lib = sc.Clib('test.so', ['fun'])

The functions are then available as a members of the library and can be called
with the appropriate number of arguments, which are one dimensional arrays of
numbers.  The function returns a list containing the output arrays of the
function:

.. code-block:: python

   In [3]: out, = lib.fun([0])

In the C counterpart, the function declaration must be accompanied with
specifications of the inputs and outputs lengths and types. This is
accomplished with the helper macros defined in SClib.h:

.. code-block:: c

   #include <SClib.h>
   SCL_OL(fun, 1,   1);    /* outputs lengths */
   SCL_OT(fun, 1, INT);    /* outputs types */
   SCL_IL(fun, 1,   1);    /* inputs lengths */
   SCL_IT(fun, 1, INT);    /* inputs types */
   void fun(int * out, int * in) {
       *out = 42;
   }

The first argument of all the macros is the functions name, the second is the
number of outputs or inputs accordingly. From then on, one argument for each
input/output defines its length and type:

.. code-block:: c

   #include <SClib.h>
   SCL_OL(<function name>, <number of outputs>, <length of output 0>, <length of output 1>, ... );
   SCL_OT(<function name>, <number of outputs>, <type of output 0>,   <type of output 1>,   ... );
   SCL_IL(<function name>, <number of inputs>, <length of input 0>, <length of input 1>, ... );
   SCL_IT(<function name>, <number of inputs>, <type of input 0>,   <type of input 1>,   ... );

type can be either INT, LINT, FLOAT, DOUBLE or LDOUBLE.

An arbitrary number of inputs or outputs can be specified, for example:

.. code-block:: c

   #include <math.h>
   #include <SClib.h>
   SCL_OL(fun, 2,   1,     2);   /* outputs lengths */
   SCL_OT(fun, 2, INT, FLOAT);   /* outputs types */
   SCL_IL(fun, 2,   1,     2);   /* inputs lengths */
   SCL_IT(fun, 2, INT, FLOAT);   /* inputs types */
   void fun(int * out0, float * out1,
            int * in0, float * in1) {
       *out0 = 42*in0[0];
       out1[0] = in1[0]*in1[1];
       out1[1] = powf(in1[0], in1[1]);
   }

In the function declaration, all the outputs must precede the inputs and must
be placed in the same order as in the PY macros.

These specifications are processed during compilation time, but only the number
of inputs and outputs is static, the lengths of each component can be
overridden at run time:

.. code-block:: python

   In [4]: lib.INPUT_LEN['fun'] = [10, 1]
   In [5]: lib.retype()

In these use cases the length of the arguments should be given to the function
through an extra integer argument.

In the function body, both inputs and outputs should be treated as one
dimensional arrays.

References
==========

.. [Hell]   Heller. *The ctypes module.*,
            https://docs.python.org/3.4/library/ctypes.html#module-ctypes
