
if __name__ == "__main__":
    from subprocess import check_output
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import SClib as sc
    import numpy as np

    # Compile and load
    libname = "./di_c.so"
    functions = ['ctrl', 'c_init', 'wrap']

    try:
        ex_lib = sc.Clib(libname, functions)
    except:
        pass

    # Library initialization
    tau0   = 5
    tau1   = 5
    u_hat  = 1
    x0_hat = 1
    h      = 1

    ex_lib.c_init([tau0, tau1, u_hat, x0_hat, h])

    # Evaluar 1 punto
    r = np.array([0.0, -.0])
    y = np.array([0.0, 2.2])
    x = np.array([0.0, 2.2])
    u = ex_lib.ctrl(r, y, x)[0]

    print("ctrl(r={}, y={}, x={}) = {}".format(r, y, x, u))

    # Wrap pa dominio cuadrado
    Nx = int(200+1);
    Ny = int(200+1);
    x = np.linspace(-1.5, 1.5, num=Nx)
    y = np.linspace(-1.5, 1.5, num=Ny)

    ex_lib.INPUT_LEN['wrap'][0:2] = [Nx, Ny]
    ex_lib.OUTPUT_LEN['wrap']     = [Nx*Ny]
    ex_lib.retype()

    RES = ex_lib.wrap(x, y, r, [Nx ,Ny])[0].reshape((Nx, Ny))

    #fig = plt.figure(1)
    fig = plt.figure(figsize=(3.5,2.1))
    Y, X = np.meshgrid(y, x)

    plt.clf()

    #ax = fig.add_subplot(1,1,1, projection='3d')
    #ax.plot_wireframe(X, Y, RES)
    plt.contourf(X, Y, RES, cmap=cm.gray)

    plt.xlabel('x_0')
    plt.ylabel('x_1')
    plt.title('u=\pi(x)')
    plt.colorbar()

    fig.tight_layout(pad=0.5)

    plt.draw()
    plt.show()

