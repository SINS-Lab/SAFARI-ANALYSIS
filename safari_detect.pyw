#!/usr/bin/env python3

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

import data_files.detect_processor as dtect_proc
from data_files.detect_processor import SpotDetector
from data_files.detect_processor import Spectrum
import data_files.detect_processor as detect
import data_files.safari_input as safari_input
import data_files.esa_data as esa_data

import spec_files.load_spec as load_spec
import spec_files.fit_esa as esa
from spec_files.load_spec import Spec

import traj_files.plot_traj as plot_traj

import misc.crystalview as crystalview

import threading

global root_path

root_path = os.path.expanduser(".")

if platform.system() == 'Windows':
    font_12 = ('Times New Roman', 12)
    font_14 = ('Times New Roman', 14)
    font_16 = ('Times New Roman', 16)
    font_18 = ('Times New Roman', 18)
    font_20 = ('Times New Roman', 20)

    plt.rcParams.update({'font.family': 'Times New Roman'})
else:
    font_12 = ('DejaVu Sans', 12)
    font_14 = ('DejaVu Sans', 14)
    font_16 = ('DejaVu Sans', 16)
    font_18 = ('DejaVu Sans', 18)
    font_20 = ('DejaVu Sans', 20)

    plt.rcParams.update({'font.family': 'DejaVu Sans'})

plt.rcParams.update({'font.size': 18})

instances = []

# Constructs and starts an instance of the gui
def spawn_gui_proc():
    gui = DetectGui()
    root = None
    if len(instances) != 0:
        root = tk.Toplevel(instances[0].root)
    instances.append(gui)
    gui.start(root=root)

# Starts an instance of the gui as a new process
def spawn_gui():
    spawn_gui_proc()

# Detector limits object
class Limits:
    def __init__(self):
        self._names_ = {
            't_min':"Min Theta: ",
            't_max':"Max Theta: ",
            'p_min':"Min Phi: ",
            'p_max':"Max Phi: ",
            'e_min':"Min Energy: ",
            'e_max':"Max Energy: "
        }

        self._units_ = {
            't_min':"Degrees",
            't_max':"Degrees",
            'p_min':"Degrees",
            'p_max':"Degrees",
            'e_min':"eV",
            'e_max':"eV"
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
        self._names_ = {
            'theta':'Theta: ',
            'phi':"Phi: ",
            'asize':"Angular Size: ",
            'esize':"Energy Res: "
        }
        self._units_ = {
            'theta':'Degrees',
            'phi':"Degrees",
            'asize':"Degrees",
            'esize':"eV"
        }
        self.theta = 45
        self.phi = 0
        self.asize = 1
        self.esize = 1

class CompSettings:
    def __init__(self):
        self._names_ = {
            'scale_by_E':'Apply E Scaling: ',
            'normalise':"Normalise Data: "
        }
        self._units_ = {
            'scale_by_E':'',
            'normalise':''
        }
        self.scale_by_E = True
        self.normalise = True

class TrajSettings:
    def __init__(self):
        self._names_ = {
            'show_lattice':'Show Lattice: ',
        }
        self._units_ = {
            'show_lattice':''
        }
        self.show_lattice = False

class DetectGui:

    def __init__(self):

        self.last_run = None
        self.canvas = None
        self.toolbar = None

        self.dataset = None
        self.detector = SpotDetector(45,0,1)

        self.dsettings = Settings()
        self.limits = Limits()
        self.comp_setitngs = CompSettings()
        self.traj_settings = TrajSettings()

        self.settings = {
            "dsettings": self.dsettings,
            "dlimits": self.limits,
            "traj_settings": self.traj_settings,
            "comp_settings": self.comp_setitngs,
        }
        self.settings_cb = {
            "dsettings": self.options_callback,
            "dlimits": self.options_callback,
            "traj_settings": None,
            "comp_settings": None,
        }

        self.safio_file = None
        self.traj_file = None

        self.compare_esa_file = None

        self.comparison_file = None

        self.fig, self.prep_fig = None, None
        self.waiting = False

        self.base_name = "SAFARI Detect"

        self.single_shots = {}

        self.aboutMessage = 'Analysis code for SAFARI data files\nimport a data file using the File menu.'
        self.copyrightMessage = 'Copyright © 2021 Patrick Johnson All Rights Reserved.'

        file_type_info = '   File Menu Options:\n\n'+\
                              '   Select File: Select a .input or .dbug file for the run,\n'+\
                              '                 this is used for Intensity vs. Energy plots,\n'+\
                              '                 Impact Plots, and Energy vs. Theta plots\n\n'+\
                              '   Select Comparison Data: Select a .dat or .txt file containing a spectrum\n'+\
                              '                           to compare to the Energy vs. Theta plot.\n'+\
                              '                           Or a .esa file for comparing to Intensity vs. Energy Plots.\n\n'+\
                              '   Select Traj: Select a .traj file for inspecting single shot runs.'

        new_instance_info = '   This spawns a new window to allow analysing another dataset.\n\n'+\
                            '   This can assist with comparing multiple datasets or parameter sets.\n\n'+\
                            '   Note that closing the original window will close all windows!\n'+\
                            '   New windows have a number appended after "SAFARI Detect"'

        dsettings_help = '   General settings for detector position and resolution:\n\n'+\
                              '   Theta: elevation angle for the detector, measured from normal (Degrees)\n'+\
                              '   Phi: azimuthal angle for detector (Degrees)\n'+\
                              '   Angular Size: spatial size of detector (Degrees)\n'+\
                              '   Energy Res: gaussian bin width for detector (eV)\n\n'+\
                              '   Clicking Update will apply the changes and attempt to re-plot if applicable\n'+\
                              '   Clicking Cancel will close the window without applying changes'

        dlimits_help =   '   General settings for detector limits:\n\n'+\
                              '   Min Theta: Minimum outgoing theta-angle for particles (Degrees)\n'+\
                              '   Max Theta: Maximum outgoing theta-angle for particles (Degrees)\n'+\
                              '   Min Phi: Minimum outgoing phi-angle for particles (Degrees)\n'+\
                              '   Max Phi: Maximum outgoing phi-angle for particles (Degrees)\n'+\
                              '   Min Energy: Minimum outgoing energy for particles (eV)\n'+\
                              '   Max Energy: Maximum outgoing energy for particles (eV)\n\n'+\
                              '   Clicking Update will apply the changes and attempt to re-plot if applicable\n'+\
                              '   Clicking Cancel will close the window without applying changes'

        comp_settings_help = '   Data Settings:\n\n'+\
                             '   Apply E Scaling: If checked, intensity is scaled inversely with energy\n'+\
                             '   Normalise Data: If checked, the data is normalised'

        traj_settings_help = '   Traj Settings:\n\n'+\
                             '   Show Lattice: If checked, the lattice will be shown as well'

        i_vs_e_info = '   Intensity vs. Energy Plots:\n\n'+\
                      '   Use the .data file, loads from Select File option'

        impact_info = '   Impact Plots:\n\n'+\
                      '   Use the .data file, loads from Select File option\n\n'+\
                      '   This plot can be used to generate single shot runs.\n'+\
                      '   Single shot runs require the Sea-Safari and XYZ executables\n'+\
                      '   to be placed in the run directory for safari_detect, and\n'+\
                      '   if VMD is also installed, then it will open VMD showing the\n'+\
                      '   trajectory when the run completes'

        e_vs_t_info = '   Energy vs. Theta Plots:\n\n'+\
                      '   Use the .spec file, loads from Select File option\n\n'+\
                      '   The "Fit" version also attempts to fit peaks and error\n'+\
                      '   bars to the spectra represented by each column of the plot\n\n'+\
                      '   Comparison Data files can be plotted over the fit version of this plot'

        traj_energy_info = '   Trajectory Energy Plots:\n\n'+\
                           '   Use the .traj file generated by a single shot run, loads from Select Traj option\n\n'+\
                           '   These show energy as a function of time for the projectile in the single shot run\n\n'+\
                           '   Single Shot runs can be generated via the Impact Plots'

        traj_info = '   Trajectory Plots:\n\n'+\
                    '   Use the .traj file generated by a single shot run, loads from Select Traj option\n\n'+\
                    '   These show the physical trajectory for the projectile in the single shot run\n\n'+\
                    '   Single Shot runs can be generated via the Impact Plots'

        crys_info = '   Crystal Plots:\n\n'+\
                    '   These show the locations of the lattice sites, as well as the active area\n'+\
                    '   The green outlined box is the area of interest defined in the input files,\n'+\
                    '   and if there is a custom surface mask, it is outlined in blue.'

        self.help_text = {
            "new_instance": new_instance_info,
            "file_types": file_type_info,

            "i_vs_e_plot": i_vs_e_info,
            "impact_plot": impact_info,
            "e_vs_t_plot": e_vs_t_info,
            "traj_energy_plot": traj_energy_info,
            "traj_plot": traj_info,
            "crystal_plot": crys_info,

            "dsettings": dsettings_help,
            "dlimits": dlimits_help,
            "traj_settings": traj_settings_help,
            "comp_settings": comp_settings_help,
        }
        self.help_labels = {
            "new_instance": "New Instance",
            "file_types": "Select *",

            "i_vs_e_plot": "Intensity vs. Energy Plot",
            "impact_plot": "Impact Plot",
            "e_vs_t_plot": "Energy vs. Theta Plot",
            "traj_energy_plot": "Trajectory Energy Plot",
            "traj_plot": "Trajectory Plot",
            "crystal_plot": "Crystal Plot",

            "dsettings": "Detector Settings",
            "traj_settings": "Traj Settings",
            "dlimits": "Detector Limits",
            "comp_settings": "Data Settings",
        }

        self.files_keys = ["new_instance", "file_types"]
        self.plots_keys = ["i_vs_e_plot", "impact_plot", 'sp', "e_vs_t_plot", 'sp', "traj_energy_plot", "traj_plot", 'sp', 'crystal_plot']
        self.settings_keys = ["dsettings", "dlimits", 'traj_settings', 'sp', "comp_settings"]

        self.menus = {'File':self.files_keys, 'Settings':self.settings_keys, 'Plot':self.plots_keys}

    # Starts the tk application, adds the file menus, etc
    def start(self, root=None):
        if root == None:
            self.root = tk.Tk()
            self.first = True
        else:
            self.root = root
            self.base_name = "SAFARI Detect {}".format(len(instances))
            self.first = False

        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        self.root.title(self.base_name)
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
        filemenu.add_command(label='Select Comparison Data', command=lambda: self.select_data())
        filemenu.add_command(label="Select Traj", command=lambda: self.select_traj_file())
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=lambda: self.exit_detect())

        #Creates Settings menu
        settingsmenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Settings', menu=settingsmenu)
        for key in self.settings_keys:
            self.make_setting(key, settingsmenu)

        #Creates Plot menu
        filemenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Plot", menu=filemenu)
        filemenu.add_command(label="Intensity vs. Energy", command=lambda: self.i_vs_e_plot())
        filemenu.add_command(label='Impact Plot', command=lambda: self.impact_plot())
        filemenu.add_separator()
        filemenu.add_command(label='Energy vs. Theta Plot', command=lambda: self.e_vs_t_plot(fit=False))
        filemenu.add_command(label='Energy vs. Theta Plot - Fit', command=lambda: self.e_vs_t_plot(fit=True))
        filemenu.add_separator()
        filemenu.add_command(label='Trajectory Energy Plot', command=lambda: self.traj_energy_plot())
        filemenu.add_command(label='Trajectory Plot', command=lambda: self.traj_plot())
        filemenu.add_separator()
        filemenu.add_command(label='Crystal Plot', command=lambda: self.crystal_plot())

        #Creates Help menu
        helpmenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Help', menu=helpmenu)

        for name, keys in self.menus.items():
            helpmenu.add_cascade(label=name, menu=self.make_help_submenu(keys, helpmenu))

        helpmenu.add_command(label='About', command= lambda: self.about())

        # Queue up some tasks for general operation monitoring
        self.root.after(500, self.check_figs)
        self.root.after(500, self.check_single_shot)

        if root == None:
            self.root.mainloop()

    #Opens About Window with description of software
    def about(self):
        t = tk.Toplevel(self.root)
        t.wm_title("About")
        l = tk.Label(t, text = self.aboutMessage, font = font_14)
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)
        messageVar = tk.Message(t, text = self.copyrightMessage, fg='black', font = font_14, width = 600)
        messageVar.place(relx = 0.5, rely = 1, anchor = tk.S)

    # Wrapper for making a submenu, so that the keys and the submenu are in new scope.
    def make_help_submenu(self, keys, helpmenu):
        submenu = tk.Menu(helpmenu, tearoff=0)
        for key in keys:
            if key == 'sp':
                submenu.add_separator()
                continue
            label = self.help_labels[key]
            msg = self.help_text[key]
            submenu.add_command(label=label, command=self.make_help_settings(label, msg))
        return submenu

    # Wrapper for the help_settings so that label and msg are in new scope.
    def make_help_settings(self, label, msg):
        return lambda: self.help_settings(label, msg)

    def make_setting(self, key, menu):
        if key == 'sp':
            menu.add_separator()
            return
        name = self.help_labels[key]
        setting = self.settings[key]
        callback = self.settings_cb[key]
        menu.add_command(label=name, command=lambda: self.edit_options(setting, name, callback))

    def help_settings(self, title, msg):
        t = tk.Toplevel(self.root)
        t.wm_title(title)
        l = tk.Text(t, font = font_14)
        l.insert('end',msg)
        l.config(state='disabled')
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)

    # Exits the application
    def exit_detect(self):
        if(self.first):
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
        self.dataset.crystal = detect.loadCrystal(self.safio_file)
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
        if self.dataset is None and callback is not None:
            ret = self.select_file()
            if ret is None:
                return
            else:
                self.dataset = ret

        window = tk.Toplevel(self.root)
        window.wm_title(name)
        dh = 22
        h = int(len(thing._names_)*dh + 150)
        window.geometry('400x{}'.format(h))

        x_orig = 160

        fields = {}
        bools = {}
        i = 0
        for key,value in thing._names_.items():
            label = tk.Label(window, text = value, font = font_12)
            label.place(x=x_orig, y=50 + i * dh, anchor = tk.E)

            attr = getattr(thing,key)
            if isinstance(attr, bool):
                # Make an IntVar to store button check state
                var = tk.IntVar()
                var.set(1 if attr else 0)
                entry = tk.Checkbutton(window, variable=var)
                entry.place(x=x_orig, y=50 + i * dh, anchor = tk.W)
                fields[key] = entry
                bools[key] = var
            else:
                entry = tk.Entry(window, font = font_12, width = 10)
                entry.insert(0, attr)
                entry.place(x=x_orig, y=50 + i * dh, anchor = tk.W)

                fields[key] = entry

            label = tk.Label(window, text = thing._units_[key], font = font_12)
            label.place(x=x_orig + 100, y=50 + i * dh, anchor = tk.W)

            i = i + 1

        def update():
            for key,value in fields.items():
                if key in bools:
                    var = bools[key]
                    setattr(thing, key, True if var.get() else False)
                else:
                    setattr(thing, key, safari_input.parseVar(value.get()))
            if callback is not None:
                callback(window)
            elif window is not None:
                window.destroy()
        
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
        self.title_text('')

    # Sets title to saying loading, please wait
    def title_loading(self):
        self.title_text('Loading, Please Wait')

    def title_text(self, text):
        if text.strip() != '':
            self.root.title("{} {}; {}".format(self.base_name, self.safio_file, text))
        else:
            self.root.title("{} {}".format(self.base_name, self.safio_file))

    def select_data(self):
        global root_path
        self.comparison_file = filedialog.askopenfilename(initialdir = root_path, title = "Select file",filetypes = (("Comparison Data Fits",".dat"),("Comparison Data Fits",".txt"),("Comparison ESA Data",".esa")))
        test = str(self.comparison_file)
        if test == '' or test == '()':
            return None
        if test == '':
            self.comparison_file = None
        if self.comparison_file.endswith('esa'):
            self.compare_esa_file = self.comparison_file
            self.comparison_file = None
        if self.last_run is not None:
            self.last_run()

    # Selects the file to load from, will only show .input and .dbug files
    def select_file(self):
        global root_path
        newfile = filedialog.askopenfilename(initialdir = root_path, title = "Select file",filetypes = (("SAFARI input spec",".input"),("SAFARI input spec",".dbug")))
        test = str(newfile)
        if test == '' or test == '()':
            return None
        self.safio_file = newfile
        root_path = os.path.dirname(newfile)
        self.root.title("SAFARI Detect {}".format(self.safio_file))
        safio = safari_input.SafariInput(self.safio_file)

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
        self.dataset.crystal = detect.loadCrystal(self.safio_file)
        self.dataset.name = self.safio_file.replace('.input', '').replace('dbug', '')
        self.dataset.safio = safio
        self.detector.safio = self.dataset.safio
        self.dataset.detector = self.detector

        self.dataset.plots = False
        self.dataset.pics = False

        if self.last_run is not None:
            self.last_run()

        return self.dataset

    # Selects the file to load from, will only show .input and .dbug files
    def select_traj_file(self, open_traj=True):
        global root_path
        newfile = filedialog.askopenfilename(initialdir = root_path, title = "Select file",filetypes = (("SAFARI traj files",".traj"),("SAFARI traj files",".traj")))
        test = str(newfile)
        if test == '' or test == '()':
            return None
        self.traj_file = newfile
        root_path = os.path.dirname(newfile)
        if open_traj:
            if self.last_run == self.traj_plot:
                self.traj_plot()
            else:
                self.traj_energy_plot()
        return self.traj_file

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
        self.dataset.pics = False
        self.detector.plots = False
        self.detector.pics = False

    # This monitors for new figures to plot, so all plotting, etc happens on main thread
    def check_figs(self):
        if self.fig is not None:
            if self.prep_fig is not None:
                self.prep_fig()
            self.show_fig(self.fig)
            if self.fig_name is not None:
                self.fig.savefig(self.fig_name)
                self.fig_name = None
            self.fig = None
            self.prep_fig = None
            self.waiting = False
        if self.waiting:
            if self.canvas is not None:
                # We need to cleanup the canvas and toolbar
                self.canvas.get_tk_widget().message = None
                self.toolbar.message = None

                self.canvas.get_tk_widget().destroy()
                self.toolbar.destroy()
            # Next we should probably make some thing that lets us know that it is waiting?
            
        self.root.after(100, self.check_figs)

    # This monitors for if a single shot run is in progress, and if so, it will give an indication that it is still running
    def check_single_shot(self):

        if len(self.single_shots) > 0:
            to_clean = []
            for vmd_file, state in self.single_shots.items():
                # State 0: waiting for things to run
                if state == 0:
                    self.title_text("Running Single Shot!")
                    if os.path.isfile(vmd_file):
                        self.single_shots[vmd_file] = 1
                # State 1: vmd opened
                elif state == 1:
                    self.title_text("Finished Single Shot!")
                    if not os.path.isfile(vmd_file):
                        self.single_shots[vmd_file] = 2
                # State 2: completely finished
                else:
                    self.title_selected()
                    to_clean.append(vmd_file)
            for key in to_clean:
                self.single_shots.pop(key)
        self.root.after(500, self.check_single_shot)

    def register_single_shot(self, vmd_file):
        self.single_shots[vmd_file] = 0

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

        if not fit:
            self.last_run = self.e_vs_t_plot
        else:
            def replot():
                self.e_vs_t_plot(fit=True)
            self.last_run = replot

        self.fig = None
        self.waiting = True
        fig, ax = plt.subplots(figsize=(12.0, 9.0))
        
        # Wraps this for a separate thread, allowing off-thread processing, but still running all of the matplotlib stuff on the main thread
        def do_work():
            self.title_loading()
            spec_file = self.safio_file.replace('.input','').replace('.dbug','')+'.spec'
            spec = Spec(spec_file)

            spec.peak_finder = esa.peak_finder
            spec.min_e = self.limits.e_min

            spec.fig, spec.ax = fig, ax
            spec.big_font = False
            spec.process_data(d_phi=self.limits.p_max-self.limits.p_min)
            spec.make_e_t_plot(do_plot=False, do_fits=fit)

            if fit:
                self.title_text('Fitting, Please Wait')
                e_max = spec.e_range[1]
                e_min = spec.e_range[0]
                t_min = spec.t_range[0]
                t_max = spec.t_range[1]
                axis = esa.make_axis(e_min, e_max, spec.energy, spec.img.shape[0]) * spec.energy

                # Set the width for integration function
                spec.e_res = self.dsettings.esize
                # Sets width for integrating internally during fitting
                spec.winv = 5
                # Sets the gaussian integration function
                spec.integrate = dtect_proc.integrate

                # Attempt to fit the columns of the image
                spec.try_fit(esa.fit_esa, axis, ax)

                if self.comparison_file is not None:
                    theta, energy, err = esa.load_data(self.comparison_file)
                    ax.scatter(theta,energy,c='r',s=4,label="Data")
                    if err is not None:
                        ax.errorbar(theta,energy,yerr=err, c='r',fmt='none',capsize=2)
                    ax.legend()

            # Here we update these to indicate that we have finished processing
            self.prep_fig = spec.prep_fig
            self.fig_name = spec_file.replace('.spec', '_fit_spec.png')
            self.fig = fig
            # Reset title to selected now that we are done
            self.title_selected()
        # Schedule this on a worker thread
        thread = threading.Thread(target=do_work)
        thread.start()

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

        self.fig = None
        self.waiting = True
        plots = plt.subplots(figsize=(8.0, 6.0))

        # Wraps this for a separate thread, allowing off-thread processing, but still running all of the matplotlib stuff on the main thread
        def do_work():
            self.title_loading()
            self.init_data()
            self.title_text('Processing, Please Wait')
            energy, intensity, scale = self.detector.spectrumE(res=self.detector.safio.ESIZE, override_fig=plots)
            # Here we update these to indicate that we have finished processing
            self.prep_fig = self.detector.prep_fig

            if self.compare_esa_file is not None:
                def new_prep():
                    self.detector.prep_fig()
                    self.add_esa_spec(plots)
                self.prep_fig = new_prep

            self.fig_name = self.detector.fig_name
            self.fig = self.detector.fig
            self.title_selected()
        # Schedule this on a worker thread
        thread = threading.Thread(target=do_work)
        thread.start()

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

        self.fig = None
        self.waiting = True
        self.detector.ss_callback = self.register_single_shot
        plots = plt.subplots(figsize=(12.0, 9.0))

        # Wraps this for a separate thread, allowing off-thread processing, but still running all of the matplotlib stuff on the main thread
        def do_work():
            self.title_loading()
            self.init_data()
            self.title_text('Processing, Please Wait')
            self.detector.impactParam(basis=self.dataset.crystal, override_fig=plots)
            fig, ax = self.detector.fig, self.detector.ax
            # Here we update these to indicate that we have finished processing
            self.prep_fig = self.detector.prep_fig
            self.fig_name = self.detector.fig_name
            self.fig = self.detector.fig
            # Switch to finished title
            self.title_selected()
        # Schedule this on a worker thread
        thread = threading.Thread(target=do_work)
        thread.start()

    def traj_energy_plot(self):
        if self.traj_file is None:
            opened = self.select_traj_file()
            return

        self.last_run = self.traj_energy_plot

        self.fig = None
        self.waiting = True
        fig, ax = plt.subplots(figsize=(12.0, 9.0))

        def do_work():
            self.title_text('Loading Traj')
            traj = plot_traj.Traj()
            traj.load(self.traj_file)
            traj.plot_energies(ax)
            self.fig = fig
            self.fig_name = self.traj_file.replace('.traj', '_traj_energy.png')
            self.title_text('Trajectory Energies')
        # Schedule this on a worker thread
        thread = threading.Thread(target=do_work)
        thread.start()

    def traj_plot(self):
        if self.traj_file is None:
            opened = self.select_traj_file(open_traj=False)
            if opened is None:
                return

        self.last_run = self.traj_plot

        self.fig = None
        self.waiting = True
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        ax.set_xlabel('X (Å)')
        ax.set_ylabel('Y (Å)')
        ax.set_zlabel('Z (Å)')

        def do_work():
            self.title_text('Loading Traj')
            traj = plot_traj.Traj()
            traj.load(self.traj_file)

            if self.traj_settings.show_lattice and self.safio_file is not None:
                crystalview.plot(self.safio_file, ax, do_lims=False, do_bounds=False)

            traj.plot_traj_3d(fig, ax)
            self.fig = fig
            self.fig_name = self.traj_file.replace('.traj', '_traj.png')
            self.title_text('Trajectory Plot')

        # Schedule this on a worker thread
        thread = threading.Thread(target=do_work)
        thread.start()

    def crystal_plot(self):
        # Select a file if we don't have one already.
        if self.dataset is None:
            ret = self.select_file()
            if ret is None:
                # If no file to select, just return early
                return
            else:
                self.dataset = ret

        self.last_run = self.crystal_plot

        self.fig = None
        self.waiting = True

        fig = plt.figure()
        ax = plt.axes(projection='3d')
        ax.set_xlabel('X (Å)')
        ax.set_ylabel('Y (Å)')
        ax.set_zlabel('Z (Å)')

        # Wraps this for a separate thread, allowing off-thread processing, but still running all of the matplotlib stuff on the main thread
        def do_work():
            self.title_loading()
            self.title_text('Processing, Please Wait')
            crystalview.plot(self.safio_file, ax)
            # Here we update these to indicate that we have finished processing
            self.prep_fig = None
            self.fig_name = None
            self.fig = fig
            self.title_selected()
        # Schedule this on a worker thread
        thread = threading.Thread(target=do_work)
        thread.start()

    def add_esa_spec(self, plots):
        fig, ax = plots
        E, I = esa_data.load_esa(self.compare_esa_file, scale_by_E=self.comp_setitngs.scale_by_E, normalise=self.comp_setitngs.normalise)
        E = E / self.detector.safio.E0
        ax.plot(E, I, label="Data")

def start():
    if len(instances) == 0:
        spawn_gui_proc()

if __name__ == '__main__':
    start()