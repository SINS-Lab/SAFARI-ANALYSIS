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


class Limits:
    def __init__(self):
        # Names of the values, for showing in the options box
        self._names_ = {
            't_min':"Min Theta: ",
            't_max':"Max Theta: ",
            'p_min':"Min Phi: ",
            'p_max':"Max Phi: ",
            'e_min':"Min Energy: ",
            'e_max':"Max Energy: "
        }
        # Units to go with the value, use `` if no units
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

        # A help string to show in the help menu
        self.help_text = '   General settings for detector limits:\n\n'+\
                         '   Min Theta: Minimum outgoing theta-angle for particles (Degrees)\n'+\
                         '   Max Theta: Maximum outgoing theta-angle for particles (Degrees)\n'+\
                         '   Min Phi: Minimum outgoing phi-angle for particles (Degrees)\n'+\
                         '   Max Phi: Maximum outgoing phi-angle for particles (Degrees)\n'+\
                         '   Min Energy: Minimum outgoing energy for particles (eV)\n'+\
                         '   Max Energy: Maximum outgoing energy for particles (eV)\n\n'+\
                         '   Clicking Update will apply the changes and attempt to re-plot if applicable\n'+\
                         '   Clicking Cancel will close the window without applying changes'

        # This is the label to click to ge the above help text,
        # this is also used for the label in the settings dropdown
        self._label = 'Detector Limits'

        # If this is set to a function, it will be called whenever
        # the settings have been changed via a gui interaction
        self._callback = None

class Settings:
    def __init__(self):
        # Names of the values, for showing in the options box
        self._names_ = {
            'theta':'Theta: ',
            'phi':"Phi: ",
            'asize':"Angular Size: ",
            'esize':"Energy Res: "
        }
        # Units to go with the value, use `` if no units
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

        # A help string to show in the help menu
        self.help_text = '   General settings for detector position and resolution:\n\n'+\
                         '   Theta: elevation angle for the detector, measured from normal (Degrees)\n'+\
                         '   Phi: azimuthal angle for detector (Degrees)\n'+\
                         '   Angular Size: spatial size of detector (Degrees)\n'+\
                         '   Energy Res: gaussian bin width for detector (eV)\n\n'+\
                         '   Clicking Update will apply the changes and attempt to re-plot if applicable\n'+\
                         '   Clicking Cancel will close the window without applying changes'

        # This is the label to click to ge the above help text,
        # this is also used for the label in the settings dropdown
        self._label = 'Detector Settings'

        # If this is set to a function, it will be called whenever
        # the settings have been changed via a gui interaction
        self._callback = None

class CompSettings:
    def __init__(self):
        # Names of the values, for showing in the options box
        self._names_ = {
            'scale_by_E':'Apply E Scaling: ',
            'normalise':"Normalise Data: "
        }
        # Units to go with the value, use `` if no units
        self._units_ = {
            'scale_by_E':'',
            'normalise':''
        }
        self.scale_by_E = True
        self.normalise = True

        # A help string to show in the help menu
        self.help_text = '   Data Settings:\n\n'+\
                         '   Apply E Scaling: If checked, intensity is scaled inversely with energy\n'+\
                         '   Normalise Data: If checked, the data is normalised'

        # This is the label to click to ge the above help text,
        # this is also used for the label in the settings dropdown
        self._label = 'Data Settings'

        # If this is set to a function, it will be called whenever
        # the settings have been changed via a gui interaction
        self._callback = None

class TrajSettings:
    def __init__(self):
        # Names of the values, for showing in the options box
        self._names_ = {
            'show_lattice':'Show Lattice: ',
        }
        # Units to go with the value, use `` if no units
        self._units_ = {
            'show_lattice':''
        }
        self.show_lattice = False

        # A help string to show in the help menu
        self.help_text = '   Traj Settings:\n\n'+\
                         '   Show Lattice: If checked, the lattice will be shown as well'

        # This is the label to click to ge the above help text,
        # this is also used for the label in the settings dropdown
        self._label = 'Traj Settings'

        # If this is set to a function, it will be called whenever
        # the settings have been changed via a gui interaction
        self._callback = None

class Menu:
    def __init__(self):
        self._opts_order = []
        self._help_order = self._opts_order
        self._options = {}
        self._labels = {}
        self._helps = {}
        self._label = ''

class Module:

    def __init__(self, root):

        # This is the gui instance that owns this module.
        self.root = root
        self.base_name = "SAFARI Detect"
        
        self.last_run = None
        self.canvas = None
        self.toolbar = None

        self.dataset = None
        self.detector = SpotDetector(45,0,1)

        self.dsettings = Settings()
        self.limits = Limits()
        self.comp_setitngs = CompSettings()
        self.traj_settings = TrajSettings()

        self.dsettings._callback = self.options_callback
        self.limits._callback = self.options_callback

        self.safio_file = None
        self.traj_file = None

        self.compare_esa_file = None

        self.comparison_file = None

        self.fig, self.prep_fig = None, None
        self.waiting = False

        self.single_shots = {}

    def get_tk(self):
        return self.root.root

    def on_start(self):
        # This is called when the module is first added, after making the settings,
        # menus, etc.
        self.get_tk().after(500, self.check_figs)
        self.get_tk().after(500, self.check_single_shot)

    def on_stop(self):
        # This is called when the program is exited
        print("Closing")

    def get_settings(self):
        # Return an array or collection of settings here
        # Module can have more than 1 set of settings.
        return [self.dsettings, self.limits, self.comp_setitngs, self.traj_settings]

    def get_menus(self):

        # This returns what menus (except for settings) should be made for this module


        # "File" menu
        _file_menu = Menu()

        _file_menu._options["select_dbug_input"] = lambda: self.select_file()
        _file_menu._options["select_comp_data"] = lambda: self.select_data()
        _file_menu._options["select_traj_file"] = lambda: self.select_traj_file()

        _file_menu._opts_order.append("select_dbug_input")
        _file_menu._opts_order.append("select_comp_data")
        _file_menu._opts_order.append("select_traj_file")

        _file_menu._labels["select_dbug_input"] = "Select File"
        _file_menu._labels["select_comp_data"] = "Select Comparison Data"
        _file_menu._labels["select_traj_file"] = "Select Traj"

        dbug_input_info = '   Select a .input or .dbug file for the run.\n\n'+\
                          '   This is used for Intensity vs. Energy plots,\n'+\
                          '   Impact Plots, and Energy vs. Theta plots\n\n'

        comp_data_info = '   Select a .dat or .txt file containing a spectrum.\n\n'+\
                         '   This is used for Intensity vs. Energy plots,\n'+\
                         '   Impact Plots, and Energy vs. Theta plots\n\n'

        traj_file_info = '   Select a .traj file for inspecting single shot runs.'

        _file_menu._helps["select_dbug_input"] = dbug_input_info
        _file_menu._helps["select_comp_data"] = comp_data_info
        _file_menu._helps["select_traj_file"] = traj_file_info

        _file_menu._label = "File"


        # "Plot" menu
        _plot_menu = Menu()

        # Add some options, the value is the function to run on click
        _plot_menu._options["i_vs_e_plot"] = lambda: self.i_vs_e_plot()
        _plot_menu._options["impact_plot"] = lambda: self.impact_plot()
        _plot_menu._options["e_vs_t_plot"] = lambda: self.e_vs_t_plot(fit=False)
        _plot_menu._options["e_vs_t_plot_fit"] = lambda: self.e_vs_t_plot(fit=True)
        _plot_menu._options["traj_energy_plot"] = lambda: self.traj_energy_plot()
        _plot_menu._options["traj_plot"] = lambda: self.traj_plot()
        _plot_menu._options["crystal_plot"] = lambda: self.crystal_plot()

        _plot_menu._opts_order.append("i_vs_e_plot")
        _plot_menu._opts_order.append("impact_plot")
        _plot_menu._opts_order.append("sep") # "sep" is reserved to place a separator in the dropdown
        _plot_menu._opts_order.append("e_vs_t_plot")
        _plot_menu._opts_order.append("e_vs_t_plot_fit")
        _plot_menu._opts_order.append("sep")
        _plot_menu._opts_order.append("traj_energy_plot")
        _plot_menu._opts_order.append("traj_plot")
        _plot_menu._opts_order.append("sep")
        _plot_menu._opts_order.append("crystal_plot")

        # Adds some help menu text for these as well

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

        _plot_menu._helps["i_vs_e_plot"] = i_vs_e_info
        _plot_menu._helps["impact_plot"] = impact_info
        _plot_menu._helps["e_vs_t_plot"] = e_vs_t_info
        _plot_menu._helps["traj_energy_plot"] = traj_energy_info
        _plot_menu._helps["traj_plot"] = traj_info
        _plot_menu._helps["crystal_plot"] = crys_info

        # Adds labels for the non-separator values
        _plot_menu._labels["i_vs_e_plot"] = "Intensity vs. Energy Plot"
        _plot_menu._labels["impact_plot"] = "Impact Plot"
        _plot_menu._labels["e_vs_t_plot"] = "Energy vs. Theta Plot"
        _plot_menu._labels["e_vs_t_plot_fit"] = "Energy vs. Theta Plot (Fit)"
        _plot_menu._labels["traj_energy_plot"] = "Trajectory Energy Plot"
        _plot_menu._labels["traj_plot"] = "Trajectory Plot"
        _plot_menu._labels["crystal_plot"] = "Crystal Plot"

        # Specify a label for the menu
        _plot_menu._label = "Plot"

        # Returns an array of menus (only 1 in this case)
        return [_file_menu, _plot_menu]

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

    # Selects a file for comparison to the plots.
    # the .dat and .txt files are to contain an e-theta loop from data to compare to spec files
    # the .esa files are for comparing to energy vs intensity logs.
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
        self.get_tk().title("SAFARI Detect {}".format(self.safio_file))
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
        self.canvas = FigureCanvasTkAgg(fig, master = self.get_tk())
        self.canvas.draw()

        # create the toolbar and place it
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.get_tk(), pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # place the canvas on the Tkinter window
        self.canvas.get_tk_widget().pack(side="top",fill='both',expand=True)

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
            
        self.get_tk().after(100, self.check_figs)

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
        self.get_tk().after(500, self.check_single_shot)

    # This records that the run has started, so it can be watched for updating application title
    def register_single_shot(self, vmd_file):
        self.single_shots[vmd_file] = 0

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

    # Produces a plot of energy as a function of time for the projectile during a single shot run
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

    # Produces a 3d trajectory plot for the particle
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

    # Produces a 3d plot of the crystal used for scattering, also includes indications of the overlay of the 
    # active area of the surface, as well as the possible surface mask
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

    # Adds the loaded .esa file to the given plots, used for comparing Intensity vs. Energy plots
    def add_esa_spec(self, plots):
        fig, ax = plots
        E, I = esa_data.load_esa(self.compare_esa_file, scale_by_E=self.comp_setitngs.scale_by_E, normalise=self.comp_setitngs.normalise)
        E = E / self.detector.safio.E0
        ax.plot(E, I, label="Data")

    # Sets title to showing current input file
    def title_selected(self):
        self.title_text('')

    # Sets title to saying loading, please wait
    def title_loading(self):
        self.title_text('Loading, Please Wait')

    # Updates the title of the window to include the given text
    def title_text(self, text):
        if text.strip() != '':
            self.get_tk().title("{} {}; {}".format(self.base_name, self.safio_file, text))
        else:
            self.get_tk().title("{} {}".format(self.base_name, self.safio_file))