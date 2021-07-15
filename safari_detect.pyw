import tkinter as tk
from tkinter import filedialog

import os
from pathlib import Path
import platform     # Linux vs Windows check

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import style
from matplotlib.figure import Figure
from data_files.detect_processor import SpotDetector
from data_files.detect_processor import Spectrum
import data_files.detect_processor as detect
import data_files.safari_input as safari_input
import spec_files.load_spec as load_spec
import spec_files.fit_esa as esa
from spec_files.load_spec import Spec
import threading

global root_path

root_path = os.path.expanduser(".")

font_12 = ('Times New Roman', 12)
font_14 = ('Times New Roman', 14)
font_16 = ('Times New Roman', 16)
font_18 = ('Times New Roman', 18)
font_20 = ('Times New Roman', 20)

plt.rcParams.update({'font.family': 'Times New Roman'})
plt.rcParams.update({'font.size': 18})

processes = []

# Constructs and starts an instance of the gui
def spawn_gui_proc():
    gui = DetectGui()
    gui.start()

# Starts an instance of the gui as a new process
def spawn_gui():
    p = threading.Thread(target=spawn_gui_proc)
    p.start()
    processes.append(p)

# Detector limits object
class Limits:
    def __init__(self):
        self._names_ = {
                        't_min':"Min Theta: ",
                        't_max':"Max Theta: ",
                        'p_min':'Min Phi: ',
                        'p_max':"Max Phi: ",
                        'e_min':"Min Energy: ",
                        'e_max':"Max Energy: "
                        }

        self.p_min = 0
        self.p_max = 0
        self.e_min = 0
        self.e_max = 0
        self.t_min = 0
        self.t_max = 90

        self.last_phi = 600
        self.last_e = -1

# Detector settings object
class Settings:
    def __init__(self):
        self._names_ = {'theta':'Theta: ',
                        'phi':"Phi: ",
                        'asize':"Angular Size: ",
                        'esize':"Energy Res: "
                        }

        self.theta = 45
        self.phi = 0
        self.asize = 1
        self.esize = 1

class DetectGui:

    def __init__(self):

        self.last_run = None
        self.canvas = None
        self.toolbar = None

        self.dataset = None
        self.detector = SpotDetector(45,0,1)

        self.limits = Limits()
        self.dsettings = Settings()

        self.helpMessage ='Analysis code for SAFARI data files\nimport a data file using the File menu.'
        self.copyrightMessage ='Copyright © 2021 Patrick Johnson All Rights Reserved.'
        return

    # Starts the tk application, adds the file menus, etc
    def start(self):
        self.root = tk.Tk()
        
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        self.root.title("SAFARI Detect")
        self.root.geometry("1280x768")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_detect)
        if platform.system() == 'Windows':
            self.root.iconbitmap("sins-lab.ico")

        #Creates File menu
        filemenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New Instance", command=lambda: spawn_gui())
        filemenu.add_separator()
        filemenu.add_command(label="Select File", command=lambda: self.select_file())
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=lambda: self.exit_detect())

        #Creates Settings menu
        settingsmenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Settings', menu=settingsmenu)
        settingsmenu.add_command(label='Detector Settings', command=lambda: self.edit_options(self.dsettings, "Detector Settings", self.options_callback))
        settingsmenu.add_command(label='Detector Limits', command=lambda: self.edit_options(self.limits,"Detector Limits", self.options_callback))

        #Creates Plot menu
        filemenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Plot", menu=filemenu)
        filemenu.add_command(label="Intensity vs Energy", command=lambda: self.i_vs_e_plot())
        filemenu.add_command(label='Impact Plot', command=lambda: self.impact_plot())
        filemenu.add_separator()
        filemenu.add_command(label='Energy vs Theta Plot', command=lambda: self.e_vs_t_plot(fit=False))
        filemenu.add_command(label='Energy vs Theta Plot - Fit', command=lambda: self.e_vs_t_plot(fit=True))

        #Creates Help menu
        helpmenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Help', menu=helpmenu)
        helpmenu.add_command(label='About', command= lambda: self.about())

        self.root.mainloop()

    #Opens About Window with description of software
    def about(self):
        t = tk.Toplevel(self.root)
        t.wm_title("About")
        t.configure(background='white')
        l = tk.Label(t, text = self.helpMessage, bg='white', font = font_14)
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)
        messageVar = tk.Message(t, text = self.copyrightMessage, bg='white', fg='black', font = font_14, width = 600)
        messageVar.place(relx = 0.5, rely = 1, anchor = tk.S)

    # Exits the application
    def exit_detect(self):
        self.root.quit()
        self.root.destroy()

    # Callback for updating the detector/dataset based on changes to dsettings and limits
    def options_callback(self, window):
        self.detector = SpotDetector(self.dsettings.theta,self.dsettings.phi,self.dsettings.asize)
        self.detector.ss_cmd = "python3 data_files/detect_impact.py"
        self.detector.safio = self.dataset.safio
        self.detector.safio.ESIZE = self.dsettings.esize
        self.detector.plots = False
        self.detector.pics = True
        self.dataset.clear()
        self.dataset.safio = self.detector.safio
        self.dataset.crystal = detect.loadCrystal(self.filename)
        self.dataset.detector = self.detector
        if window is not None:
            window.destroy()
        if self.last_run is not None:
            self.last_run()
            self.last_run = None

    # Generates a window with options for editing floating point fields for thing
    # thing must have a _names_ attribute which is a map of <attr> to <name>, where
    # <name> is what the box will be labelled. These values should all be floats!
    def edit_options(self, thing, name, callback):
        if self.dataset is None:
            ret = self.select_file()
            if ret is None:
                return
            else:
                self.dataset = ret

        window = tk.Toplevel(self.root)
        window.wm_title(name)
        h = int(len(thing._names_)*20 + 150)
        window.geometry('400x{}'.format(h))

        fields = {}
        i = 0
        for key,value in thing._names_.items():
            label = tk.Label(window, text = value, font = font_14)
            label.place(relx=0.4, y=50 + i * 20, anchor = tk.E)
            entry = tk.Entry(window, font = font_14, width = 10)
            entry.insert(0, getattr(thing,key))
            entry.place(relx=0.4, y=50  + i * 20, anchor = tk.W)
            i = i + 1
            fields[key] = entry

        def update():
            for key,value in fields.items():
                setattr(thing, key, float(value.get()))
            callback(window)
        
        do_update = update
        def return_pressed(*args):
            do_update()
        window.bind('<Return>', return_pressed)
        
        update_button = tk.Button(window, text = 'Update', relief = 'raised', activebackground='green', font = font_16, width = 15, height = 1,\
                    command = update)
        update_button.place(relx=0.5, y=h-60, anchor = tk.CENTER)
        cancel_button = tk.Button(window, text = 'Cancel', relief = 'raised', activebackground='red', font = font_16, width = 15, height = 1,\
                    command = lambda: [window.destroy()])
        cancel_button.place(relx=0.5, y=h-20, anchor = tk.CENTER)

    # Sets title to showing current input file
    def title_selected(self):
        self.root.title("SAFARI Detect: {}".format(self.filename))

    # Sets title to saying loading, please wait
    def title_loading(self):
        self.root.title("SAFARI Detect: {}; Loading, Please Wait".format(self.filename))

    # Selects the file to load from, will only show .input and .dbug files
    def select_file(self):
        global root_path
        newfile = filedialog.askopenfilename(initialdir = root_path, title = "Select file",filetypes = (("SAFARI input spec",".input"),("SAFARI input spec",".dbug")))
        if newfile == '':
            return None
        self.filename = newfile
        root_path = os.path.dirname(newfile)
        self.root.title("SAFARI Detect {}".format(self.filename))
        safio = safari_input.SafariInput(self.filename)

        detectorParams = safio.DTECTPAR
        self.detector = SpotDetector(45,safio.PHI0,1)
        self.detector.ss_cmd = "python3 data_files/detect_impact.py"

        if self.limits.last_phi != safio.PHI0:
            self.limits.last_phi = safio.PHI0
            self.limits.p_max = safio.PHI0 + .5
            self.limits.p_min = safio.PHI0 - .5
        
        if self.limits.last_e != safio.E0:
            self.limits.last_e = safio.E0
            self.limits.e_min = safio.EMIN
            self.limits.e_max = safio.EMAX

        self.dsettings.theta = self.detector.theta
        self.dsettings.phi = self.detector.phi
        self.dsettings.asize = 1
        self.dsettings.esize = safio.ESIZE

        self.dataset = Spectrum()
        self.dataset.crystal = detect.loadCrystal(self.filename)
        self.dataset.name = self.filename.replace('.input', '').replace('dbug', '')
        self.dataset.safio = safio
        self.detector.safio = self.dataset.safio
        self.dataset.detector = self.detector

        self.dataset.plots = False
        self.dataset.pics = False

        if self.last_run is not None:
            self.last_run()

        return self.dataset

    # Initializes the dataset based on limits defined by limits
    def init_data(self):
        _emin = self.limits.e_min
        _emax = self.limits.e_max
        _phimin = self.limits.p_min
        _phimax = self.limits.p_max
        _thmin = self.limits.t_min
        _thmax = self.limits.t_max

        self.title_loading()

        self.dataset.clean(emin=_emin,emax=_emax,\
                    phimin=_phimin,phimax=_phimax,\
                    thmin=_thmin,thmax=_thmax)

        self.title_selected()
        
        self.dataset.plots = False
        self.dataset.pics = True
        self.detector.plots = False
        self.detector.pics = True

    # Displays the matplotlib figure fig in the main window
    def show_fig(self, fig):

        if self.canvas is not None:
            # If we already have a canvas and toolbar, remove them

            # message is not even set on some Linux systems, causing
            # errors when trying to call destroy() below
            self.canvas.get_tk_widget().message = None
            self.toolbar.message = None

            self.canvas.get_tk_widget().destroy()
            self.toolbar.destroy()

        # create the Tkinter canvas containing the Matplotlib figure
        self.canvas = FigureCanvasTkAgg(fig, master = self.root)
        self.canvas.draw()

        # create the toolbar and place it
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # place the canvas on the Tkinter window
        self.canvas.get_tk_widget().pack(side="top",fill='both',expand=True)

    # Produces an energy vs theta plot, this requires the .spec file to exist.
    def e_vs_t_plot(self, fit=False):
        
        # Select a file if we don't have one already.
        if self.dataset is None:
            ret = self.select_file()
            if ret is None:
                # If no file to select, just return early
                return
            else:
                self.dataset = ret

        self.last_run = self.e_vs_t_plot
        
        self.title_loading()

        spec_file = self.filename.replace('.input','').replace('.dbug','')+'.spec'
        spec = Spec(spec_file)
        spec.big_font = False
        spec.process_data(d_phi=self.limits.p_max-self.limits.p_min)
        spec.make_e_t_plot(do_plot=False)

        fig, ax = spec.fig, spec.ax

        if fit:
            e_max = spec.e_range[1]
            e_min = spec.e_range[0]
            t_min = spec.t_range[0]
            t_max = spec.t_range[1]
            axis = esa.make_axis(e_min, e_max, spec.energy, spec.img.shape[0]) * spec.energy
            X = []
            Y = []
            S = []
            for i in range(spec.img.shape[1]):
                slyce = spec.img[:,i]
                params = esa.fit_esa(slyce, axis,actualname=" fit", plot=False,min_h = max(np.max(slyce)/10,100),min_w=1)
                # +0.5 to shift the point to the middle of the bin
                T = load_spec.interp(i+0.5, spec.img.shape[1], t_min, t_max)
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

            # if data is not None:
            #     theta, energy, err = esa.load_data(data)
            #     ax.scatter(theta,energy,c='r',s=4,label="Data")
            #     if err is not None:
            #         ax.errorbar(theta,energy,yerr=err, c='r',fmt='none',capsize=2)
            ax.legend()


        self.show_fig(fig)
        self.title_selected()

        fig_name = spec_file.replace('.spec', '__fit_spec.png') if fit else spec_file.replace('.spec', '_spec.png')
        fig.savefig(fig_name)

    # Produces an intensity vs energy plot
    def i_vs_e_plot(self):
        
        # Select a file if we don't have one already.
        if self.dataset is None:
            ret = self.select_file()
            if ret is None:
                # If no file to select, just return early
                return
            else:
                self.dataset = ret

        self.last_run = self.i_vs_e_plot
        self.init_data()

        self.title_loading()
        energy, intensity, scale = self.detector.spectrumE(res=self.detector.safio.ESIZE)
        fig, ax = self.detector.fig, self.detector.ax
        self.show_fig(fig)
        self.title_selected()

    # Produces an impact plot
    def impact_plot(self):

        # Select a file if we don't have one already.
        if self.dataset is None:
            ret = self.select_file()
            if ret is None:
                # If no file to select, just return early
                return
            else:
                self.dataset = ret
            
        self.last_run = self.impact_plot
        self.init_data()

        self.title_loading()
        self.detector.impactParam(basis=self.dataset.crystal)
        fig, ax = self.detector.fig, self.detector.ax
        self.show_fig(fig)
        self.title_selected()

def start():
    if len(processes) == 0:
        spawn_gui()

if __name__ == '__main__':
    start()