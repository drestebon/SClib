#!/usr/bin/python
import numpy as np
import ctypes as ctypes
import sys
import os

def error(message):
    sys.stderr.write("error: %s\n" % message)
    sys.exit(1)

# Funcion en c
class Clib:
    def __init__(self, lib_path, fnames=[]):
        self.lib_path = lib_path

        self.lib = ctypes.CDLL(lib_path)

        self.TYPE = [ctypes.c_int, ctypes.c_long, ctypes.c_float, ctypes.c_double, ctypes.c_longdouble]
        self.N_INPUTS = {}
        self.INPUT_LEN = {}
        self.INPUT_TYPE = {}
        self.INPUT_DTYPE = {}
        self.N_OUTPUTS = {}
        self.OUTPUT_LEN = {}
        self.OUTPUT_TYPE = {}
        self.OUTPUT_DTYPE = {}

        self.fnames = []

        for x in fnames:
            if hasattr(self.lib, x):
                self.N_INPUTS[x] = ctypes.c_int.in_dll(self.lib,"_"+x+"_N_INPUTS_").value
                foo = (ctypes.c_int*self.N_INPUTS[x]).in_dll(self.lib,"_"+x+"_INPUT_LEN_")
                self.INPUT_LEN[x] = [foo[i] for i in range(self.N_INPUTS[x])]
                foo = (ctypes.c_int*self.N_INPUTS[x]).in_dll(self.lib,"_"+x+"_INPUT_TYPE_")
                self.INPUT_TYPE[x] = [(self.TYPE[foo[i]]*self.INPUT_LEN[x][i]) for i in range(self.N_INPUTS[x])]
                self.INPUT_DTYPE[x] = [self.TYPE[foo[i]] for i in range(self.N_INPUTS[x])]

                self.N_OUTPUTS[x] = ctypes.c_int.in_dll(self.lib,"_"+x+"_N_OUTPUTS_").value
                foo = (ctypes.c_int*self.N_OUTPUTS[x]).in_dll(self.lib,"_"+x+"_OUTPUT_LEN_")
                self.OUTPUT_LEN[x] = [foo[i] for i in range(self.N_OUTPUTS[x])]
                foo = (ctypes.c_int*self.N_OUTPUTS[x]).in_dll(self.lib,"_"+x+"_OUTPUT_TYPE_")
                self.OUTPUT_TYPE[x] = [(self.TYPE[foo[i]]*self.OUTPUT_LEN[x][i]) for i in range(self.N_OUTPUTS[x])]
                self.OUTPUT_DTYPE[x] = [self.TYPE[foo[i]] for i in range(self.N_OUTPUTS[x])]

                self.fnames.append(x)
                if not hasattr(self, x):
                    self.make_fun(x)
                else:
                    print(x+"() already exists in class for library "+lib_path)
            else:
                print("__init__(): "+x+"() discarded: no symbol found")

    def retype(self):
        for x in self.fnames:
            foo = (ctypes.c_int*self.N_INPUTS[x]).in_dll(self.lib,"_"+x+"_INPUT_TYPE_")
            self.INPUT_TYPE[x] = [(self.TYPE[foo[i]]*self.INPUT_LEN[x][i]) for i in range(self.N_INPUTS[x])]
            foo = (ctypes.c_int*self.N_OUTPUTS[x]).in_dll(self.lib,"_"+x+"_OUTPUT_TYPE_")
            self.OUTPUT_TYPE[x] = [(self.TYPE[foo[i]]*self.OUTPUT_LEN[x][i]) for i in range(self.N_OUTPUTS[x])]

    def reload(self):
        self.unload()
        self.__init__(self.lib_path,self.fnames)

    def unload(self):
        while self.isLoaded():
            try:
                handle = self.lib._handle
            except:
                error("unload(): no se pudo del self.lib")
            libdl = ctypes.CDLL("libdl.so")
            libdl.dlclose(handle)

    def isLoaded(self):
       libp = os.path.abspath(self.lib_path)
       ret = os.system("lsof -p %d | grep %s > /dev/null" % (os.getpid(), libp))
       return (ret == 0)

    def eval(self,fun,*args):
        if not hasattr(self.lib, fun) or fun not in self.fnames:
            error("eval(): "+fun+"() not available")

        if(len(args)!=self.N_INPUTS[fun]):
            error("feval("+fun+"): len(args) = {0} != N_INPUTS = {1}".format(len(args),self.N_INPUTS[fun]))

        if([len(args[i]) for i in range(len(args))] != self.INPUT_LEN[fun]):
            error("feval("+fun+"): false input dimessions, got: {}, expected: {}".format([len(args[i]) for i in range(len(args))], self.INPUT_LEN[fun]))

        py = [self.OUTPUT_TYPE[fun][i]() for i in range(self.N_OUTPUTS[fun])]
        px = [self.INPUT_TYPE[fun][i](*args[i]) for i in range(self.N_INPUTS[fun])]

        fargs = py+px

        getattr(self.lib, fun)(*fargs)
        return [np.frombuffer(py[i],dtype=self.OUTPUT_DTYPE[fun][i]) for i in range(self.N_OUTPUTS[fun])]

    def make_fun(self, fun):
        if self.N_INPUTS[fun] > 0:
            inputs = 'in0'+''.join([', in{}'.format(x) for x in range(1, self.N_INPUTS[fun])])
        else:
            inputs = ''
        code = "def {0}(self, {1}): return self.eval('{0}', {1})".format(fun, inputs)
        d = {}
        exec(code, d)
        setattr(self.__class__, fun, d[fun])


if __name__ == "__main__":
    from subprocess import check_output
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    # Compile and load
    libname = "di_c.so"
    libpath = os.getcwd()+"/lib/"+libname
    functions = ['ctrl', 'init', 'wrap']

    try:
        ex_lib = Clib(libpath, functions)
    except:
        pass

    os.chdir('src')
    if str(check_output(["make", '../lib/'+libname])).find("is up to date")<0:
        try:
            ex_lib.reload()
        except:
            ex_lib = Clib(libpath, functions)
    os.chdir('..')

    # Library initialization
    tau0   = 5
    tau1   = 5
    u_hat  = 1
    x0_hat = 1
    h      = 1

    ex_lib.init([tau0, tau1, u_hat, x0_hat, h])

    # Evaluar 1 punto
    r = np.array([0.0, -.0])
    y = np.array([0.0, 2.2])
    x = np.array([0.0, 2.2])
    u = ex_lib.ctrl(r, y, x)[0]

    print("ctrl(r={}, y={}, x={}) = {}".format(r, y, x, u))

    # Wrap pa dominio cuadrado
    Nx = int(100+1);
    Ny = int(100+1);
    x = np.linspace(-3, 3, num=Nx)
    y = np.linspace(-3, 3, num=Ny)

    ex_lib.INPUT_LEN['wrap'][0:2] = [Nx, Ny]
    ex_lib.OUTPUT_LEN['wrap']     = [Nx*Ny]
    ex_lib.retype()

    RES = ex_lib.wrap(x, y, r, [Nx ,Ny])[0].reshape((Nx, Ny))

    fig = plt.figure(1)
    Y, X = np.meshgrid(y, x)

    plt.clf()

    #ax = fig.add_subplot(1,1,1, projection='3d')
    #ax.plot_wireframe(X, Y, RES)
    plt.contourf(X, Y, RES, cmap=cm.gray)

    plt.xlabel('x0')
    plt.ylabel('x1')
    plt.title('u=pi(x)')

    plt.draw()
    plt.show()

