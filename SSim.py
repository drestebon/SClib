#!/usr/bin/python2.7

import numpy as np
import SClib as sc

from scipy.integrate import ode
from scipy.integrate import odeint

#import pbserver

from subprocess import check_output
from subprocess import call
import os
import sys


def error(message):
    sys.stderr.write("error: %s\n" % message)
    sys.exit(1)

class SSim:
    def __init__(self,G,C,Tsim,Ts,h,atol=1e-2,rtol=1e-2,integrator='dopri5', x_postp=None):
        self.rtol = rtol
        self.atol = atol

        self.path = os.getcwd()

        self.Glib  = G[0]
        self.Gfun = G[1::]+[x_postp] if x_postp else G[1::]

        self.x_postp = x_postp

        self.Clib  = C[0]
        self.Cfun = C[1::]

        for x in [self.Glib,self.Clib]:
            if self.compile(x):
                print("init(): "+x+" to be reloaded")
                self.unload_lib(x)

        self.G = sc.Clib(self.path+"/lib/"+self.Glib,self.Gfun)
        self.C = sc.Clib(self.path+"/lib/"+self.Clib,self.Cfun)

        self.XDIM = self.G.OUTPUT_LEN[self.Gfun[0]][0]
        self.YDIM = self.G.OUTPUT_LEN[self.Gfun[1]][0]

        self.CYDIM = self.C.INPUT_LEN[self.Cfun[0]][1]
        self.CXDIM = self.C.INPUT_LEN[self.Cfun[0]][2]

        self.UDIM, self.CODIM = self.C.OUTPUT_LEN[self.Cfun[0]][0:2]

        CItypes = self.C.INPUT_DTYPE[self.Cfun[0]]
        GItypes = self.G.INPUT_DTYPE[self.Gfun[0]]
        COtypes = self.C.OUTPUT_DTYPE[self.Cfun[0]]
        GOtypes = self.G.OUTPUT_DTYPE[self.Gfun[0]]

        self.h_Ts   = int(np.rint(h/Ts))
        self.Tsim_h = int(np.rint(Tsim/h))

        if Tsim<h:
            error("sim.__init__(): shit makes no sense Tsim < h? ({} < {})".format(Tsim, h))


        # Allocation
        self.t  = np.linspace(0,Tsim,num=self.h_Ts*self.Tsim_h+1)
        self.tf = np.append(self.t,np.zeros((self.h_Ts,)))
        self.tk = np.linspace(0,Tsim,num=self.Tsim_h+1)

        self.x  = np.zeros((self.Tsim_h*self.h_Ts+1,self.XDIM),order='C',dtype=GItypes[0])

        self.y  = np.zeros((self.Tsim_h+1,self.YDIM),order='C',dtype=CItypes[1])
        self.u  = np.zeros((self.Tsim_h+1,self.UDIM),order='C',dtype=COtypes[0])
        self.Co = np.zeros((self.Tsim_h+1,self.CODIM),order='C',dtype=COtypes[1])

        if integrator == 'dopri5':
            self.csim = ode(self.dxdt_dopri5)
            self.csim.set_integrator('dopri5',rtol=self.rtol,atol=self.atol)
            self.integrate = self.dopri5
        else:
            self.integrate = self.lsoda

    def compile(self,x):
        return str(check_output(["make", '../lib/'+x],cwd="./src")).find("is up to date")<0

    def unload_lib(self,lib):
        libpath = self.path+"/lib/"+lib
        sc.Clib(libpath).unload()

    def reload(self):
        if self.compile(self.Glib):
            print("reload(): "+self.Glib+" to be reloaded")
            try:
                self.G.reload()
            except:
                print("reload(): no se pudo descargar "+self.Glib)
        else:
            print("reload(): "+self.Glib+" is up to date")

        if self.compile(self.Clib):
            print("reload(): "+self.Clib+" to be reloaded")
            try:
                self.C.reload()
            except:
                print("reload(): no se pudo descargar "+self.Clib)
        else:
            print("reload(): "+self.Clib+" is up to date")


    def set_r(self,r):
        try:
            if len(r) == 1:
                self.r = r*np.ones(len(self.tk))
            if len(r) == len(self.tk):
                self.r = r
            else:
                self.r = np.array(len(self.tk)*[r,])
        except:
            self.r = r*np.ones(len(self.tk))


    def set_d(self,d):
        try:
            if len(d) == 1:
                self.d = d*np.ones(len(self.tk))
            if len(d) == len(self.tk):
                self.d = d
            else:
                self.d = np.array(len(self.tk)*[d,])
        except:
            self.d = d*np.ones(len(self.tk))

    def state_post_processing(self, x, t, u):
        return self.G.eval(self.x_postp, x, [t], u)[0]

    def dxdt_dopri5(self,t,x,args):
        return self.G.eval(self.Gfun[0],x,[t],*args)[0]

    def dopri5(self,xk,X,U,D,tck):
        self.csim.set_initial_value(X, tck[0])
        self.csim.set_f_params((U,D,))
        for t, i in zip(tck[1::], range(self.h_Ts)):
            self.csim.integrate(t)
            if self.x_postp:
                xk[i][...]  = self.state_post_processing(np.atleast_1d(self.csim.y),t,U)
            else:
                xk[i][...]  = np.atleast_1d(self.csim.y)

    def dxdt_lsoda(self,x,t,*args):
        return self.G.eval(self.Gfun[0],x,[t],*args)[0]

    def lsoda(self,xk,X,U,D,tck):
        if self.x_postp:
            foo = odeint(self.dxdt_lsoda,X,tck,(U,D,),rtol=self.rtol,atol=self.atol)[1::]
            for t, i in zip(tck[1::], range(self.h_Ts)):
                xk[i][...]  = self.state_post_processing(np.atleast_1d(foo[i]),t,U)
        else:
            xk[...] = odeint(self.dxdt_lsoda,X,tck,(U,D,),rtol=self.rtol,atol=self.atol)[1::]

    def output(self,x,u):
        return self.G.eval(self.Gfun[1],x,u)

    def run_sim(self,xi):
        # Condiciones iniciales
        self.x[0][...] = np.atleast_1d(xi)
        self.x[-1][...] = self.x[0]

        X = np.atleast_1d(self.x[0])

        U0 = np.atleast_1d(self.u[0])

        self.y[0][...] = np.atleast_1d(self.output(X,U0)[0])

        Y = np.atleast_1d(self.y[0])
        R = np.atleast_1d(self.r[0])
        D = np.atleast_1d(self.d[0])

        self.u[0][...], self.Co[0][...] = self.C.eval(self.Cfun[0],R,Y[0:self.CYDIM],X[0:self.CXDIM])[0:2]

        U = np.atleast_1d(self.u[0])

        # Datos por calcular
        ts  = self.tf[1::].reshape((self.Tsim_h+1,self.h_Ts))
        foo = np.roll(ts[:,-1],1)
        foo[0] = 0
        ts  = np.hstack((foo.reshape((-1,1)),ts))
        xs  = self.x[1::].reshape((self.Tsim_h,self.h_Ts,self.XDIM))
        ys  = self.y[0:-1].reshape((self.Tsim_h,self.YDIM))
        us  = self.u[0:-1].reshape((self.Tsim_h,self.UDIM))
        Cos = self.Co[0:-1].reshape((self.Tsim_h,self.CODIM))
        rs  = self.r[0:-1]
        ds  = self.d[0:-1]

        #pbar = pbserver.Sbar()

        for tck, tk, xk, yk, uk, Cok, rk, dk, k in \
           zip(ts, self.tk, xs, ys, us, Cos, rs, ds, range(self.Tsim_h)):

            X = np.atleast_1d(xs[k-1][-1])
            Y = self.output(X,U0)[0] 
            R = np.atleast_1d(rk)
            D = np.atleast_1d(dk)

            uk[...], Cok[...] = self.C.eval(self.Cfun[0],R,Y[0:self.CYDIM],X[0:self.CXDIM])[0:2]

            Y = self.output(X,uk)[0] 
            yk[...] = np.atleast_1d(Y)

            U = uk

            self.integrate(xk,X,U,D,tck)

            #if not k%(self.Tsim_h//20+1):
                #pbar.update(self.Tsim_h, k+1, self.Glib+" "+self.Clib)

        self.y[-1][...] = np.atleast_1d(self.output(np.atleast_1d(self.x[-1]),np.atleast_1d(self.u[-2]))[0])
        self.u[-1][...] = self.u[-2]
        self.Co[-1][...] = self.Co[-2]

        #pbar.update(1, 1, self.Glib+" "+self.Clib)

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    h    = 1
    Tsim = 50
    Ts   = h/100

    sim = SSim(["di.so",'dxdt','c','f_init'],
               ["di_c.so",'ctrl','c_init'],
               Tsim, Ts, h,
               rtol=1e-13,
               atol=1e-13,
               integrator='lsoda')
               #integrator='dopri5')

    sim.reload()

    tau0   = 5.0
    tau1   = 5.0
    u_hat  = 1.0
    x0_hat = 1.0

    sim.G.eval('f_init',[tau0, tau1])
    sim.C.eval('c_init',[tau0, tau1, u_hat, x0_hat, h])

    r = 0 #np.array([2 if x >= 1.0 else 0 for x in sim.tk])
    d = 0 #np.array([0.5 if x >= 20.0 else 0 for x in sim.tk])

    sim.set_r(r)
    sim.set_d(d)
    sim.set_r(np.vstack((sim.r,np.array([sim.d]))).transpose())

    import numpy.random as rnd


    fig = plt.figure(figsize=(3.5,2.1))

    for i in range(80):
        x0 = np.array([2, 3])*rnd.random((1,2))[0]-np.array([1, 1.5])
        sim.run_sim(x0)
        plt.plot(sim.x[:,0], sim.x[:,1], 'k')

    plt.xlabel('x_0')
    plt.ylabel('x_1')
    fig.tight_layout(pad=0.5)
    plt.draw()
    plt.show()

