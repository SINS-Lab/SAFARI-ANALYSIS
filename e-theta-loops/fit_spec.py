import numpy as np
import argparse        # Parsing command line arguments
import matplotlib      # Main plotting
#Qt5Agg is the backend
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt 
import load_spec
from load_spec import Spec
import fit_esa as esa


if __name__ == "__main__" :

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input file")
    parser.add_argument("-d", "--data", help="data comparison file")
    args = parser.parse_args()

    spec = Spec(args.input)
    spec.process_data(d_phi=0.5)
    print(spec)

    fig, ax = plt.subplots()

    e_max = spec.e_range[1]
    e_min = spec.e_range[0]
    t_min = spec.t_range[0]
    t_max = spec.t_range[1]

    del_e = e_max-e_min
    del_t = t_max-t_min

    img = spec.img

    im = ax.imshow(img, interpolation="bicubic", extent=(t_min, t_max, e_max, e_min))
    ax.invert_yaxis()
    ax.set_aspect(aspect=del_t/del_e)
    fig.colorbar(im, ax=ax)
    ax.set_title("Energy vs Theta")
    ax.set_xlabel('Outgoing angle (Degrees)')
    ax.set_ylabel('Outgoing Energy (eV)')
    
    axis = esa.make_axis(e_min, e_max, spec.energy, img.shape[0]) * spec.energy
    X = []
    Y = []
    S = []
    for i in range(img.shape[1]):
        slyce = img[:,i]
        params = esa.fit_esa(slyce, axis,actualname=" fit", plot=False,min_h = max(np.max(slyce)/10,10))
        T = load_spec.interp(i, img.shape[1], t_min, t_max)
        if params is not None and len(params > 2):
            for j in range(2, len(params), 3):
                E = params[j+2]
                if E > spec.energy or E < 0:
                    continue
                X.append(T)
                Y.append(E)
                S.append(abs(params[j+1]))
        else:
            print("No fits at angle {}".format(T))

    if len(X) > 0:
        ax.scatter(X,Y,c='y',s=4,label="Simulation")
        ax.errorbar(X,Y,yerr=S, c='y',fmt='none',capsize=2)

    if args.data is not None:
        theta, energy, err = esa.load_data(args.data)
        ax.scatter(theta,energy,c='r',s=4,label="Data")
        if err is not None:
            ax.errorbar(theta,energy,yerr=err, c='r',fmt='none',capsize=2)
    ax.legend()
    fig.show()
    
    input("Enter to exit")