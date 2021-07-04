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

    e_max = spec.e_range[1]
    e_min = spec.e_range[0]
    t_min = spec.t_range[0]
    t_max = spec.t_range[1]
    p_min = spec.p_range[0]
    p_max = spec.p_range[1]

    del_e = e_max-e_min
    del_t = t_max-t_min
    del_p = p_max-p_min

    img = spec.img

    plt.rcParams.update({'font.size': 22})
    fig, ax = plt.subplots(figsize=(12.0, 9.0))
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
        params = esa.fit_esa(slyce, axis,actualname=" fit", plot=False,min_h = max(np.max(slyce)/10,10),min_w=1)
        # +0.5 to shift the point to the middle of the bin
        T = load_spec.interp(i+0.5, img.shape[1], t_min, t_max)
        if params is not None and len(params) > 2:
            for j in range(2, len(params), 3):
                E = params[j+2]
                if E > spec.energy or E < 0:
                    continue
                X.append(T)
                Y.append(E)
                S.append(abs(params[j+1]))
        else:
            print("No fits at angle {}, {}".format(T, params))

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

    fig2, ax2 = plt.subplots()
    im2 = ax2.imshow(spec.theta_phi, interpolation="bicubic", extent=(p_min, p_max, t_max, t_min))
    ax2.invert_yaxis()
    ax2.set_aspect(aspect=del_p/del_t)
    fig2.colorbar(im2, ax=ax2)
    ax2.set_title("Theta vs Phi")
    ax2.set_xlabel('Outgoing Phi (Degrees)')
    ax2.set_ylabel('Outgoing Theta (Degrees)')
    # fig2.show()

    fig.savefig(args.input.replace('.spec', '_fits.png'))
    
    input("Enter to exit")