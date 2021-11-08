#!/usr/bin/env python3

import argparse     # Parsing input arguments
import subprocess   # Runs VMD
import platform     # Linux vs Windows check

import os           # os.remove is used for .vmd file
import time         # sleeps before removing file

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import sys
sys.path.insert(1, './data_files')

import safari_input

def load(file_in):

    lines = []
    
    safio = safari_input.SafariInput(file_in)
    bounds = [[safio.XSTART, safio.XSTOP],[safio.YSTART, safio.YSTOP]]
    mask = [safio.x_points, safio.y_points]

    min_x = bounds[0][0]
    min_y = bounds[1][0]

    max_x = bounds[0][1]
    max_y = bounds[1][1]

    dx = max_x - min_x
    dy = max_y - min_y

    X = []
    Y = []
    Z = []
    S = []

    if file_in.endswith('.input'):
        file_in = file_in.replace('.input', '.crys')
    elif file_in.endswith('.dbug'):
        file_in = file_in.replace('.dbug', '.crys')

    file = open(file_in, 'r')
    for line in file:
        args = line.split()
        if len(args)==5:
            lines.append(args)

            x = float(args[0])
            y = float(args[1])
            z = float(args[2])

            if x < min_x - dx or x > max_x + dx:
                continue
            if y < min_y - dy or y > max_y + dy:
                continue

            X.append(x)
            Y.append(y)
            Z.append(z)
            S.append(args[3])

    file.close()
    X = np.array(X)
    Y = np.array(Y)
    Z = np.array(Z)
    return X, Y, Z, S, bounds, mask

def plot_crystal(x, y, z, S, ax, do_lims=True):
    ax.scatter3D(x, y, z,c='orange')

    if do_lims:
        min_x = np.min(x)
        min_y = np.min(y)
        min_z = np.min(z)

        max_x = np.max(x)
        max_y = np.max(y)
        max_z = np.max(z)

        dx = np.max(x) - np.min(x)
        dy = np.max(y) - np.min(y)
        dz = np.max(z) - np.min(z)

        dmax = max(dx, max(dy, dz))

        mean_x = (min_x + max_x) / 2
        mean_y = (min_y + max_y) / 2
        mean_z = (min_z + max_z) / 2
        min_y = mean_y - dmax/2
        max_y = mean_y + dmax/2
        min_x = mean_x - dmax/2
        max_x = mean_x + dmax/2
        min_z = mean_z - dmax/2
        max_z = mean_z + dmax/2

        ax.set_xlim(min_x, max_x)
        ax.set_ylim(min_y, max_y)
        ax.set_zlim(min_z, max_z)

def add_active_area(ax, bounds, mask):
    min_x = bounds[0][0]
    min_y = bounds[1][0]

    max_x = bounds[0][1]
    max_y = bounds[1][1]

    # Points for the loop around the active area
    X = [min_x, max_x, max_x, min_x]
    Y = [min_y, min_y, max_y, max_y]

    # Plot the loop
    for i in range(len(X)):
        x = [X[i-1], X[i]]
        y = [Y[i-1], Y[i]]
        z = [0, 0]
        ax.plot3D(x, y, z, c='green')

    # Mask is the actual active area if present
    X = mask[0]
    Y = mask[1]
    # Similar loop around the mask
    for i in range(len(X)):
        x = [X[i-1], X[i]]
        y = [Y[i-1], Y[i]]
        z = [0, 0]
        ax.plot3D(x, y, z, c='blue')

def plot(filename, ax, do_lims=True, do_bounds=True):
    X, Y, Z, S, bounds, mask = load(filename)
    plot_crystal(X, Y, Z, S, ax)
    if do_bounds:
        add_active_area(ax, bounds, mask)
    return

if __name__ == "__main__" :
    filename = './var/204.dbug'

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    
    plot(filename, ax)

    fig.show()
    input("Enter to exit.")