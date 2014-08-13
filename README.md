SClib
=====

SClib is a simple hack that allows easy and straightforward evaluation of C
functions within python code, boosting flexibility for better trade-off between
computation power and feature availability, such as visualization and existing
computation routines in SciPy.

In the included use example we use SClib to evaluate the control and system
derivatives in a feedback control loop for electrical motors.  With this and the
integration routines available in SciPy, we can run simulations of the control
loop a la Simulink. The use of C code not only boosts the speed of the
simulations, but also enables to test the exact same code that we use in the
test rig to get experimental results. Integration with (I)Python gives us the
flexibility to analyze and visualize the data.

