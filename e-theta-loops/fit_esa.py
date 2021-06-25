#!/usr/bin/env python3

import argparse                     # Parsing command line arguments
import numpy as np                  # Array manipulation/maths
import matplotlib                   # Plotting
import os                           # Path related stuff
import scipy.signal as signal       # Peak finding

#Qt5Agg is the backend
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt     # Plotting

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
    y = x * params[0] + params[1]
    for i in range(2, len(params), 3):
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

def fit_esa(values, axis, actualname=None, plot=True, min_h = 10, min_w = 1):
    matched, properties = signal.find_peaks(values, prominence=min_h, width=min_w)

    if len(matched) == 0:
        print("No peaks found?")
        return None

    width = properties['widths']
    height = properties['prominences']

    max_h = np.max(height)
    peaks = []
    widths = []
    heights = []

    params = []

    dx = axis[len(axis)-1] - axis[0]
    dy = values[len(axis)-1] - values[0]

    m = dy/dx
    b = values[0] - m * axis[0]

    params.append(m)
    params.append(b)

    
    for i in range(len(matched)):
        index = matched[i]
        h = height[i]
        if(h > max_h/10):
            peaks.append(axis[index])
            widths.append((axis[index]-axis[index-1])*width[i])
            heights.append(height[i])
            n = len(heights) - 1
            h = values[index]
            # We want half-width for guess at sigma
            w = widths[n] / 2
            u = axis[index]
            params.append(h)
            params.append(w)
            params.append(u)

    x_min = np.min(axis)
    x_max = np.max(axis)

    try:
        popt, pcov = curve_fit(multiples, axis, values, p0=params)
    except:
        return None

    x_0 = axis

    y_0 = multiples(x_0, *params)
    y_1 = multiples(x_0, *popt)

    m,b,r,p,err = linregress(values, y_1)

    x_0 = np.array(make_axis(axis[0], axis[-1], 1, 512))
    y_0 = multiples(x_0, *params)
    y_1 = multiples(x_0, *popt)

    fit_label = 'R={:.5f}\nLinear: {:.2e}x+{:.2f}\n'.format(r, popt[0], popt[1])

    for i in range(2, len(popt), 3):
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

    return popt

def interp(y_b, y_a, x_b, x_a, x):
    if y_b == y_a:
        return y_b
    dy_dx = (y_a-y_b)/(x_a-x_b)
    dy = dy_dx * (x - x_b)
    return y_b + dy

def toRange(min_e, max_e, size, vals, val_min_e, val_max_e):
    out = np.zeros(size)
    dout = (max_e - min_e) / size


    val_num = len(vals)
    dval = (val_max_e-val_min_e) / val_num

    val_index = 0
    val_index_max = val_num - 1

    for i in range(val_num):
        e_here = val_min_e + i * dval
        e_next = val_min_e + (i+1) * dval
        if e_next > min_e and val_index == 0:
            val_index = i
            if val_index > 0:
                val_index = val_index - 1
        if e_next > max_e:
            val_index_max = i
            break


    val = vals[val_index]


    prev_val = vals[val_index]
    prev_val_index = val_index

    j = 0

    for i in range(size):
        e_here = min_e + i*dout

        val_prev_e = val_min_e + prev_val_index * dval
        while val_prev_e > e_here:
            prev_val_index  = prev_val_index - 1
            val_prev_e = val_min_e + prev_val_index * dval


        val_next_e = val_min_e + val_index * dval
        while val_next_e < e_here:
            val_index  = val_index + 1
            val_next_e = val_min_e + val_index * dval

        val_index = min(val_index, val_num - 1)
        prev_val_index = min(prev_val_index, val_num - 1)
        val_index = max(val_index, 0)
        prev_val_index = max(prev_val_index, 0)

        val = vals[val_index]
        prev_val = vals[prev_val_index]

        out[i] = interp(prev_val, val, val_prev_e,\
                                       val_next_e,\
                                       e_here)
    return out

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
    