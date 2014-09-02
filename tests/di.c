#include <math.h>
#include "SClib.h"

/* Parametros */
static double tau0, tau1;

      PYO(f_init,0);
PYO_TYPES(f_init,0);
      PYI(f_init,1, 2);
PYI_TYPES(f_init,1, DOUBLE);
void f_init(double * params)
{
    tau0 = params[0];
    tau1 = params[1];
}

      PYO(dxdt,1,      2);
PYO_TYPES(dxdt,1, DOUBLE);
      PYI(dxdt,4,      2,      1,      1,      1);
PYI_TYPES(dxdt,4, DOUBLE, DOUBLE, DOUBLE, DOUBLE);
void dxdt(double * dx,   /* outputs */
          double * x,    /* inputs  */
          double * t,
          double * u,
          double * d
          )
{
    dx[0] = u[0]/tau0;
    dx[1] = (x[0]-d[0])/tau1;
}

      PYO(c,1, 2);
PYO_TYPES(c,1, DOUBLE);
      PYI(c,2, 2,      1);
PYI_TYPES(c,2, DOUBLE, DOUBLE);
void c(double * y,   /* outputs */
       double * x,    /* inputs  */
       double * u
       )
{
    static int i;
    for (i = 0; i < 2; i++)
        y[i] = x[i];
}

