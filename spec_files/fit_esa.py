#!/usr/bin/env python3

import argparse                     # Parsing command line arguments
import numpy as np                  # Array manipulation/maths
import matplotlib                   # Plotting
import os                           # Path related stuff
import scipy.signal as signal       # Peak finding

import matplotlib.pyplot as plt     # Plotting
import traceback                    # Error handling

from scipy.optimize import curve_fit# Fitting the gaussians
from scipy.stats import linregress  # for R-value on the plot

# Basic gaussian fitting function
def gaussian(x, a, sigma, mu):
    dx = x-mu
    dx2 = dx*dx
    s2 = sigma*sigma
    return a*np.exp(-dx2/(2*s2))

# This function is a linear + any number of gaussians
def multiples(x, *params):
    # y = x * params[0] + params[1]
    y = np.zeros(len(x))
    for i in range(0, len(params), 3):
        a = params[i]
        sigma = params[i+1]
        mu = params[i+2]
        y = y + gaussian(x, a, sigma, mu)
    return y

def make_axis(emin, emax, e_0, size):
    start = emin/e_0
    end = emax/e_0
    dE = (end - start) / size
    return np.array([start + dE * x for x in range(size)])

def peak_finder(values, axis, min_h = 10, min_w = 1, grad=True, integrate=None, winv=5):

    # In this case, we will use the second derivative for peak finding.
    if grad:
        derivative = np.gradient(values)
        derivative -= np.min(derivative)
        derivative /= np.max(derivative)

        # We want the - gradient here as we are looking for "peaks"
        grad2 = -np.gradient(derivative)
        grad2 = grad2.clip(0)
        grad2 /= (np.max(grad2) - np.min(grad2))

        # Apply the gaussian integration function to smooth out the 2nd derivative plot
        if integrate is not None:
            grad2, scale = integrate(len(grad2), winv, axis, grad2, axis)
        
        # We clipped earlier, and then smoothed out, so 0 should be fine for this.
        min_h = 0.0
        # This is width in grid points, 1 or 2 is probably fine, much larger will miss very narrow peaks as in 0K simulations
        min_w = 1

        matched, properties = signal.find_peaks(grad2, prominence=min_h, width=min_w)
    else:
        matched, properties = signal.find_peaks(values, prominence=min_h, width=min_w)

    if len(matched) == 0:
        if grad:
            return peak_finder(values, axis, min_h, min_w, False)
        return None

    width = properties['widths']
    height = properties['prominences']

    max_h = np.max(values) / np.max(height)

    params = []

    dx = axis[len(axis)-1] - axis[0]
    dy = values[len(axis)-1] - values[0]

    # Compile some initial guesses
    for i in range(len(matched)):
        index = matched[i]
        h = height[i]
        w = (axis[index]-axis[index-1])*width[i]
        # For non-deriviative fitting, this returns
        # the full-width of the entire peak, we want
        # at the mid point, so dividing by 2 gives
        # a better initial guess.
        if not grad:
            w /= 2
        h = height[i] * max_h
        h = (values[index] + h) / 2
        u = axis[index]
        params.append(h)
        params.append(w)
        params.append(u)
    return params

def fit_esa(values, axis, actualname=None, plot=True, min_h = 10, min_w = 1, manual_params=None, guess_func=peak_finder, fit_func=multiples, integrate=None, winv=5):

    if manual_params is None:
        params = peak_finder(values, axis, min_h, min_w, integrate=integrate, winv=winv)
        if params is None:
            return None, fit_func, 'no peaks'
    else:
        params = manual_params
    
    x_min = np.min(axis)
    x_max = np.max(axis)

    try:
        popt, pcov = curve_fit(fit_func, axis, values, p0=params)
    except:
        if plot:
            fig,ax = plt.subplots()

            x_0 = axis
            y_0 = fit_func(x_0, *params)

            ax.plot(axis, values, label='Data')
            ax.plot(x_0, y_0, label='Initial Guess')
            ax.set_xlabel('Energy (eV)')
            ax.set_ylabel('Intensity')
            ax.set_title(actualname)
            ax.legend()
            fig.show()

        return None, fit_func, 'Convergance Error'

    x_0 = axis

    y_0 = fit_func(x_0, *params)
    y_1 = fit_func(x_0, *popt)

    m,b,r,p,err = linregress(values, y_1)

    x_0 = np.array(make_axis(axis[0], axis[-1], 1, 512))

    fit_label = 'R={:.5f}\n'.format(r)

    for i in range(0, len(popt), 3):
        fit_label = fit_label + 'Peak: I={:.2f},E={:.2f}eV,sigma={:.2f}eV\n'.format(popt[i], popt[i+2], abs(popt[i+1]))


    if not actualname.endswith(' fit'):
        fit_file = open(actualname + ' fit', 'w')
        y_2 = y_1 / (np.max(y_1) - np.min(y_1))
        y_2 = y_2 - np.min(y_2)
        for i in range(len(x_0)):
            fit_file.write('{}\t{}\n'.format(x_0[i], y_2[i]))
        fit_file.close()

    if plot:
        fig,ax = plt.subplots()
        ax.plot(axis, values, label='Data')
        ax.plot(x_0, y_0, label='Initial Guess')
        ax.plot(x_0, y_1, label=fit_label)
        ax.set_xlabel('Energy (eV)')
        ax.set_ylabel('Intensity')
        ax.set_title(actualname)
        ax.legend()
        fig.show()

    return popt, fit_func, 'None'

def interp(y_b, y_a, x_b, x_a, x):
    if y_b == y_a:
        return y_b
    dy_dx = (y_a-y_b)/(x_a-x_b)
    dy = dy_dx * (x - x_b)
    return y_b + dy

def load_data(compare_file):
    spec_file = open(compare_file, 'r')
    sE = []
    sI = []
    sErr = []
    started = False
    for line in spec_file:
        if not started:
            #Skip header line
            started = True
            continue
        args = line.split()
        sE.append(float(args[0]))
        sI.append(float(args[1]))
        if len(args) > 2:
            sErr.append(float(args[2]))
    spec_file.close()
    sE = np.array(sE)
    sI = np.array(sI)
    if len(sErr) > 0:
        sErr = np.array(sErr)
    else:
        sErr = None
    return sE, sI, sErr

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", help="Directory to run from")
    args = parser.parse_args()
    directory = '.' 
    if args.directory:
        directory = args.directory

    filename = './2eV'

    sE, sI, err = load_data(filename)
    fit_esa(sI, sE, filename)

    input("Enter to exit")
    