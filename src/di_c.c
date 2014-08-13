#include <math.h>
#include "SClib.h"

#define EPS 0.0
#define fsgn(x) ((EPS < x) - (x < -EPS))

static float tau0, tau1;
static float u_hat, x0_hat, h;
static float tau;
static float m, _K, __K;

      PYO(c_init,0);
PYO_TYPES(c_init,0)
      PYI(c_init,1, 5);
PYI_TYPES(c_init,1, FLOAT)
void c_init(float * params)
{
    tau0 = params[0];
    tau1 = params[1];

    u_hat  = params[2];
    x0_hat = params[3];
    h      = params[4];

    tau = tau0/(2*tau1*u_hat);
    m = h/(2*tau1);
    _K = h*u_hat/(2*tau0);
    __K = 8*tau0*tau1/(h*h*u_hat);
}

void di_dtm(float * xp, float * x, float * u, float * d)
{
    static float dx[2];
    static float dx1;

    dx[0] = u[0]/tau0;
    dx[1] = (x[0]-d[0])/tau1;

    dx1 = dx[0]/tau1;

    xp[0] = x[0] + h*dx[0];
    xp[1] = x[1] + h*(dx[1]+0.5*h*dx1);
}

float pwm1(float *x, int ioa)
{
    float u_idx[3] = {0.0, u_hat, -u_hat};
    float d;
    int c;

    if(x[1]*x[0] <= 0)
        c = 1;
    else if(x[2]*x[0] <= 0)
        c = 2;
    else
        return u_idx[ioa];

    d = x[c]-x[0];
    if(d != 0.0)
        d = -x[0]/d;
    else
        return u_idx[ioa];

    return d*(u_idx[c]-u_idx[0])+u_idx[0];
}

#define SIMOUT_LEN 20
      PYO(ctrl,2, 1,    SIMOUT_LEN);
PYO_TYPES(ctrl,2, FLOAT,FLOAT);
      PYI(ctrl,3,     2,    2,    2);
PYI_TYPES(ctrl,3, FLOAT,FLOAT,FLOAT);
void ctrl(float * u,  /* outputs */
           float * f,
           float * r,  /* inputs  */
           float * y,
           float * x
           )
{
    static float d;
    static float xp[2], xpp[3];
    float u_s[3] = {0.0, u_hat, -u_hat};

    static float x0T, b;

    static float x0ss, x1sup, x1inf;
    static float x0, x1;

    static float Fc, Fco;

    static int i, io;

    for(i=0;i<SIMOUT_LEN;i++) f[i] = NAN;

    d = r[1];

    x0ss  = d;
    x1sup = -x0_hat-x0ss;
    x1inf =  x0_hat-x0ss;
    x1sup =  x1sup*x1sup*tau;
    x1inf = -x1inf*x1inf*tau;

    for(i=0;i<3;i++)
    {
        /* ####### Prediccion ######### */
        u[0] = u_hat*u_s[i];

        di_dtm(xp, x, u, &d);

        x0 = xp[0]-d;
        x1 = xp[1]-r[0];

        if(x1 >= x1sup)
            x1 = x1sup;
        else if(x1 <= x1inf)
            x1 = x1inf;
        Fc = fabsf(fsgn(x0)*x0*x0*tau+x1);

        if(!i)         { Fco = Fc; io = 0; }
        else if(Fc<Fco){ Fco = Fc; io = i; }

        x0 = xp[0]-d;
        x1 = xp[1]-r[0];

        if(i==0)
        {
            b = x1-x0*m;
            if (b<0) x0T = (-1+sqrtf(1-__K*b))*_K;
            else     x0T = ( 1-sqrtf(1+__K*b))*_K;

            if      (x0T+d < -x0_hat) x0T = -x0_hat-d;
            else if (x0T+d >  x0_hat) x0T =  x0_hat-d;
        }

        xpp[i] = x0-x0T;
    }

    u[0] = pwm1(xpp, io);
    /*u[0] = u_s[io];*/
}

      PYO(wrap,1, 0);
PYO_TYPES(wrap,1, FLOAT);
      PYI(wrap,4, 0,         0,     2,   2);
PYI_TYPES(wrap,4, FLOAT, FLOAT, FLOAT, INT);
void wrap(float * u,    /* outputs */
          float * x0,    /* inputs */
          float * x1,
          float * r,
          int * shape
          )
{
    int i, j;
    static float f[SIMOUT_LEN];
    static float x[2];
    static float *xp;

    for (i = 0; i < shape[0]; i++, x0++)
    {
        x[0] = *x0;
        for (j = 0, xp=x1; j < shape[1]; j++)
        {
            x[1] = *xp++;
            ctrl(u++, f, r, f, x);
        }
    }
}


