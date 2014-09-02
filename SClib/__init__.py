#!/usr/bin/python
import numpy as np
import ctypes as ctypes
import os
from subprocess import check_output

def error(message):
    import sys
    sys.stderr.write("error: %s\n" % message)
    sys.exit(1)

# Funcion en c
class Clib:
    """Loads the functions listed in fnames from the library in lib_path"""

    MF_TEXT = """
CC      = gcc
CCOPTS  = -Wall -O2 -ffast-math -fPIC -g
LIBS    = -lm
INCLUDE = -I/usr/include -I{}
LDFLAGS = -L/usr/lib
LIB_DIR = .

clean:
	rm -rf *.o $(LIB_DIR)/*.so

#####################################################################
# Workers
#####################################################################
$(LIB_DIR)/%.so: %.o
	$(CC) -shared -o $@ $<

%.o: %.c
	$(CC) $(INCLUDE) -c $(CCOPTS) $< $(LIBS)
""".format(os.path.dirname(__file__))

    def __init__(self, lib_path, fnames=[]):

        self.lib_path = lib_path

        self.make(loaded=False)

        self.lib = ctypes.CDLL(lib_path)

        self.TYPE = [ctypes.c_int,
                     ctypes.c_long,
                     ctypes.c_float,
                     ctypes.c_double,
                     ctypes.c_longdouble]

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

    def make(self, loaded=True):
        if not os.path.isfile("Makefile"):
            fd = open("Makefile", "w")
            fd.write(self.MF_TEXT)
            fd.close()

        if str(check_output(["make", self.lib_path])).find("is up to date")<0:
            if loaded:
                try:
                    self.reload()
                except:
                    print("SClib: tried to reload after $ make {}, but did not work".format(self.lib_path))

