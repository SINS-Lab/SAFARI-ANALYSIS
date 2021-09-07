import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import scipy.signal as signal       # Peak finding

def interp(n, l, start, end):
    return start + n * (end - start) / l

class Spec:

    def __init__(self, file):
        self.detections = []
        self.energy = 0
        self.theta = 0
        self.phi = 0
        self.counts = 0
        self.e_range = [0,0]
        self.t_range = [0,0]
        self.p_range = [0,0]
        self.file = file

        self.min_e = 0

        self.fig, ax = None, None
        self.prep_fig = None

        self.fits = {}

        self.load(file)

        self.e_res = self.energy/100

        self.integrate = None

        self.img = None
        self.theta_phi = None
        self.big_font = True
        self.figsize = (12.0, 9.0)

    def parse_header(self, header):
        rows = header.split('\n')
        for line in rows:
            vars = line.split(' ')
            if line.startswith('Energy range:'):
                self.e_range[0] = float(vars[2])
                self.e_range[1] = float(vars[4])
            elif line.startswith('Theta range:'):
                self.t_range[0] = float(vars[2])
                self.t_range[1] = float(vars[4])
            elif line.startswith('Phi range:'):
                self.p_range[0] = float(vars[2])
                self.p_range[1] = float(vars[4])
            elif line.startswith('Energy:'):
                self.energy = float(vars[1])
            elif line.startswith('Theta:'):
                self.theta = float(vars[1])
            elif line.startswith('Phi:'):
                self.phi = float(vars[1])
            elif line.startswith('Total Counts:'):
                self.counts = float(vars[2])

    def process_data(self, d_phi=1, do_phi=True):
        l_E = len(self.detections) - 1
        l_T = len(self.detections[1])
        l_P = len(self.detections[1][0])

        self.img = np.zeros((l_E, l_T))
        if do_phi:
            self.theta_phi = np.zeros((l_T, l_P))

        for n_E in range(l_E):
            table = self.detections[n_E]
            for n_T in range(l_T):
                row = table[n_T]
                for n_P in range(l_P):
                    P = interp(n_P, l_P, self.p_range[0], self.p_range[1])
                    if do_phi:
                        self.theta_phi[n_T][n_P] = self.theta_phi[n_T][n_P] + row[n_P]
                    if P > self.phi - d_phi/2 and P < self.phi + d_phi/2:
                        self.img[n_E][n_T] = self.img[n_E][n_T] + row[n_P]

    def make_e_t_plot(self, data=None, do_plot=True, do_norm = True,do_log = True, do_fits=False):
        e_max = self.e_range[1]
        e_min = self.e_range[0]
        t_min = self.t_range[0]
        t_max = self.t_range[1]
        p_min = self.p_range[0]
        p_max = self.p_range[1]

        del_e = e_max-e_min
        del_t = t_max-t_min
        del_p = p_max-p_min

        img = self.img

        in_plot = np.sum(img)

        if do_plot:
            file_name = self.file.replace('.spec', '_raw_img.png')
            matplotlib.image.imsave(file_name, img)

        self.log_img = np.log(img + 1)
        if do_log:
            img = self.log_img
        
        self.norm_img = img/np.max(img)

        if do_norm:
            img = self.norm_img
        
        if self.fig == None:
            fig, ax = plt.subplots(figsize=self.figsize)
            self.fig, self.ax = fig, ax
        else:
            fig, ax = self.fig, self.ax

        def prep_fig():
            if self.big_font:
                plt.rcParams.update({'font.size': 20})
            im = ax.imshow(img, interpolation="bicubic", extent=(t_min, t_max, e_max, e_min), cmap=plt.get_cmap('cividis'))
            ax.invert_yaxis()
            ax.set_aspect(aspect=del_t/del_e)
            cb = fig.colorbar(im, ax=ax)
            if do_log:
                cb.set_label("Relative Log Intensity")
            else:
                cb.set_label("Counts")
            ax.set_title("Energy vs Theta {}".format(int(in_plot)))
            ax.set_xlabel('Outgoing angle (Degrees)')
            ax.set_ylabel('Outgoing Energy (eV)')


            if do_fits:
                # This will result in displaying the plot for the particular column of the image when the column is double clicked.
                def onclick(event):
                    if event.dblclick and event.button == 1:
                        fig2, (ax2,ax3) = plt.subplots(2)
                        T = round(event.xdata - 0.5, 0)+0.5 
                        if T in self.fits:
                            slyce, (params, xaxis, fit_type) = self.fits[T]
                            ax2.plot(xaxis, slyce,label="Raw")

                            grad = np.gradient(slyce)
                            grad -= np.min(grad)
                            grad /= np.max(grad)

                            grad2 = -np.gradient(grad)
                            grad2 = grad2.clip(0)
                            grad2 /= (np.max(grad2) - np.min(grad2))

                            winv = self.winv
                            # Smooth out the second derivative plot
                            grad2, scale = self.integrate(len(grad2), winv, xaxis, grad2, xaxis)

                            min_h = 0.01
                            min_w = 1
                            
                            ax3.plot(xaxis, grad2, label='2nd Derivative')

                            min_h = (np.max(grad)-np.min(grad))/100

                            peak_params = self.peak_finder(slyce, xaxis, min_h, min_w, integrate=self.integrate,min_x=self.min_e)

                            # Plot the guess
                            if peak_params is not None:
                                fit_label = 'Guess\n'
                                for i in range(0, len(peak_params), 3):
                                    fit_label = fit_label + 'Peak: I={:.1f},E={:.1f}eV,sigma={:.1f}eV\n'.format(abs(peak_params[i]), peak_params[i+2], abs(peak_params[i+1]))
                                ax2.plot(xaxis, fit_type(xaxis, *peak_params),label=fit_label)

                            # Plot the fit
                            if params is not None:
                                fit_label = 'Fit\n'
                                for i in range(0, len(params), 3):
                                    fit_label = fit_label + 'Peak: I={:.1f},E={:.1f}eV,sigma={:.1f}eV\n'.format(abs(params[i]), params[i+2], abs(params[i+1]))
                                ax2.plot(xaxis, fit_type(xaxis, *params),label=fit_label)
                            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                            ax3.legend()
                        fig2.show()

                fig.canvas.mpl_connect('button_press_event', onclick)
        
        self.prep_fig = prep_fig

        if do_plot:
            prep_fig()
            fig.show()
            file_name = self.file.replace('.spec', '_displayed_img.png')
            matplotlib.image.imsave(file_name, img)

    def parse_data(self, data):
        rows = data.split('\n')
        table = []
        for row in rows:
            # This represents the row containing the energy value
            if not row.startswith('\t'):
                table = []
                self.detections.append(table)
            # Otherwise we are looking at a row of the table
            else:
                # This is the header row
                if row.startswith('\t\t'):
                    pass
                # This is a row of data
                else:
                    # trim to remove leading tab, then split
                    vars = row.strip().split()
                    # remove column label, which is first entry
                    del vars[0]
                    # convert to numbers and stick in the array
                    data_row = [int(i) for i in vars]
                    table.append(np.array(data_row))
        del self.detections[0]

    def load(self, file):
        spec_file = open(file, 'r')
        entire_file = spec_file.read()
        spec_file.close()
        components = entire_file.split('--------------------------------------------------------')
        header = components[1]
        data = components[2]
        self.parse_header(header)
        self.parse_data(data)

    def h_func(slyce):
        return max(np.max(slyce)/100, 1)

    def w_func(slyce):
        return 5

    def try_fit(self, fit_func, xaxis, ax, guess_params=None, min_h=h_func,min_w=w_func):
        t_min = self.t_range[0]
        t_max = self.t_range[1]
        X = []
        Y = []
        S = []
        H = []
        self.fits = {}
        for i in range(self.img.shape[1]):
            slyce = self.img[:,i]

            if self.integrate is not None:
                # In this case, when we integrate we use same winv calulation as in the intensity vs energy plots.
                # We do not use self.winv here, that is used for the fitting routine itself.
                winv = 1/self.e_res
                max_h = np.max(slyce)
                slyce, scale = self.integrate(self.img.shape[0], winv, xaxis, slyce, xaxis)
                slyce *= max_h
                
            # Here we decide on if we want to use an initial guess set, or make our own guesses.
            if guess_params is None:
                # If no guess is given, we also want to provide the integration function, as well as the width criteria for this fitting
                params, fit_type, err = fit_func(slyce, xaxis, actualname=" fit", plot=False,min_h=min_h(slyce),min_w=min_w(slyce),integrate=self.integrate,winv=self.winv,min_x=self.min_e) 
            else:
                # Otherwise we just use the manual guesses.
                params, fit_type, err = fit_func(slyce, xaxis, actualname=" fit", plot=False,min_h=min_h(slyce),min_w=min_w(slyce), manual_params=guess_params[i])


            # +0.5 to shift the point to the middle of the bin
            T = interp(i+0.5, self.img.shape[1], t_min, t_max)
            # Saves these for plotting later if needed via double clicking on main plot
            self.fits[T] = (slyce, (params, xaxis, fit_type))
            if params is not None and len(params) > 2:
                for j in range(0, len(params), 3):
                    E = params[j+2]
                    if E > self.energy or E < 0:
                        continue
                    X.append(T)
                    Y.append(E)
                    S.append(abs(params[j+1]))
                    H.append(abs(params[j]))
            else:
                print("No fits at angle {}, {}".format(T, err))
        # Plots the error bars and points, Also produces a file containing them
        if len(X) > 0:
            ax.scatter(X,Y,c='y',s=4,label="Simulation")
            ax.errorbar(X,Y,yerr=S, c='y',fmt='none',capsize=2)
            fit_file = open(self.file.replace('.spec', '_fits.dat'), 'w')
            fit_file.write('Angle(Degrees)\tEnergy(eV)\tWidth(eV)\tScale\n')
            for i in range(len(X)):
                fit_file.write('{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\n'.format(X[i]-0.5,Y[i],S[i],H[i]))
            fit_file.close()

if __name__ == "__main__" :
    spec = Spec('./test.spec')
    spec.process_data()
    print(spec)

    e_max = spec.e_range[1]
    e_min = spec.e_range[0]
    t_min = spec.t_range[0]
    t_max = spec.t_range[1]
    p_min = spec.p_range[0]
    p_max = spec.p_range[1]

    del_e = e_max-e_min
    del_t = t_max-t_min
    del_p = p_max-p_min

    fig, ax = plt.subplots()
    im = ax.imshow(spec.img, interpolation="bicubic", extent=(t_min, t_max, e_max, e_min))
    ax.invert_yaxis()
    ax.set_aspect(aspect=del_t/del_e)
    fig.colorbar(im, ax=ax)
    ax.set_title("Energy vs Theta")
    ax.set_xlabel('Outgoing angle (Degrees)')
    ax.set_ylabel('Outgoing Energy (eV)')
    fig.show()

    fig2, ax2 = plt.subplots()
    im2 = ax2.imshow(spec.theta_phi, interpolation="bicubic", extent=(p_min, p_max, t_max, t_min))
    ax2.invert_yaxis()
    ax2.set_aspect(aspect=del_p/del_t)
    fig2.colorbar(im2, ax=ax2)
    ax2.set_title("Theta vs Phi")
    ax2.set_xlabel('Outgoing Phi (Degrees)')
    ax2.set_ylabel('Outgoing Theta (Degrees)')
    fig2.show()

    input("Enter to exit")