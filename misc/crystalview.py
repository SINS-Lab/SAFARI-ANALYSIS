#!/usr/bin/env python3

import argparse     # Parsing input arguments
import subprocess   # Runs VMD
import platform     # Linux vs Windows check

import os           # os.remove is used for .vmd file
import time         # sleeps before removing file

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

# A bunch of functions for fortran IO
def parseVar(input):
    string = str(input)
    if string.endswith('d0') or string.endswith('D0'):
        var = string.replace('D0','').replace('d0','')
        return float(var)
    if string == 't' or string == 'T':
        return True
    if string == 'f' or string == 'F':
        return False
    if isInt(string):
        return int(string)
    if isFloat(string):
        return float(string)
    return string

def parseLine(input):
    vars = input.split()
    ret = []
    for var in vars:
        ret.append(parseVar(var))
    return ret

def toStr(input):
    if isinstance(input, bool):
        return 't' if input else 'f'
    return str(input)

def serializeArr(input):
    output = ''
    n = 0
    for var in input:
        if n == 0:
            output = toStr(var)
        else:
            output = output + ' ' + toStr(var)
        n = n + 1
    return output

def serialize(*input):
    return serializeArr(input)

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def isFloat(s):
    try: 
        float(s)
        return True
    except ValueError:
        return False

class SafariInput:

    def __init__(self, fileIn):
        self.fileIn = fileIn

        self.file_type = ".input"
        if fileIn.endswith(".dbug"):
            self.file_type = ".dbug"

        self.filename = self.fileIn.replace(self.file_type, '')
        
        # Inialize All variables
        self.E0 = 1625.0
        self.THETA0 = 55.0
        self.PHI0 = 45.0
        self.MASS = 22.989
        self.SYMION = 'Na'

        self.EMIN = 0.5
        self.EMAX = 1625.0
        self.ESIZE = 16.0
        self.ASIZE = 5.0

        self.NDTECT = 1
        self.save_errored = False
        self.DTECTPAR = [45.0, 1.0, 1.0]

        self.x_points = []
        self.y_points = []
        
        self.DELLOW = 1e-8
        self.DELT0 = 10.0
        self.DEMAX = 0.3
        self.DEMIN = 0.0
        self.ABSERR = 5e-6
        self.NPART = 45
        self.RECOIL = True
        self.Z1 = 5.0
        self.MAX_STEPS = 30000
        self.RRMIN = 0.0
        self.RRSTEP = 2.5e-3
        self.ZMIN = 0.0
        self.ZSTEP = 3e-4
        self.MAXDIV = 10
        self.MINDIV = 2

        self.NWRITX = 666 # SCAT_FLAG
        self.NWRITY = 666 # SCAT_MODE

        self.RAX = 4
        self.RAY = 4

        self.NPAR = 4
        self.IPOT = 1
        self.POTPAR = [9125.84, 4.44, 66703.59, 11.24]
        self.NIMPAR = 2
        self.IIMPOT = 1
        self.PIMPAR = [1.26, 2.0]
        self.TEMP = 0.0
        self.SEED = 0.9436337324
        self.Ion_Index = 1
        self.IMAGE = True
        self.SENRGY = -1.5
        self.BDIST = 8.18

        self.AX = 4.09
        self.AY = 4.09
        self.AZ = 4.09

        self.NBASIS = 1
        self.BASIS = [[0.0, 0.0, 0.0, 1]]
        self.NTYPES = 1

        self.ATOMS = [[107.87, 47, 'Ag']]
        self.SPRINGS = [[5.0, 5.0, 5.0]]
        self.CORR = True
        self.ATOMK = 0
        self.RNEIGH = 8.36405
        
        #No idea on good defaults for these
        self.NUMCHA = 10000
        self.XSTART = 0
        self.XSTEP = 0.1
        self.XSTOP = 10
        self.YSTART = 0
        self.YSTEP = 0.1
        self.YSTOP = 10

        self.NBZ = 1
        self.TOL = 0
        self.NBG = 1
        self.GTOL = 0
        self.GMAX = [0]
        self.NG = [0]
        self.NZ = [0]
        self.ZMAX = [0]

        self.face = [0,0,1]
        self.load_crystal = False
        self.loaded_face = [0,0,1]

        self.F_a = 0
        self.F_b = 0

        self.load()
        return
        
    def load(self):
        if not os.path.exists(self.fileIn):
            return

        file = open(self.fileIn, 'r')
        # This starts at 1, so it matches the file lines.
        n = 1
        # This is used for offsetting the lines depending
        # on whether anything depends on entries before.
        o = 0

        for line in file:
            # The variable names here are identical to 
            # the ones used in the fortran source.

            # This is a comment in the file
            if line.startswith("#"):
                continue

            # This file is a .dbug, and so started with this
            if line.startswith("Loading Info From:"):
                continue

            # This file is a .dbug, anything after this is not input file anymore
            if line.startswith("Loaded SAFIO"):
                break
            
            args = parseLine(line)
            # Number of arguments, used for padding arrays with 0
            num = len(args)
            # Ignore blank lines.
            if num == 0:
                continue

            # E0 THETA0 PHI0 MASS SYMION
            if n == 1:
                self.E0 = args[0]
                self.THETA0 = args[1]
                self.PHI0 = args[2]
                self.MASS = args[3]
                self.SYMION = args[4]
                # Ensure phi is in correct range
                while self.PHI0 > 180:
                    self.PHI0 -= 360
                while self.PHI0 < -180:
                    self.PHI0 += 360
                
            #EMIN,EMAX,ESIZE,ASIZE
            if n == 2:
                self.EMIN = args[0]
                self.EMAX = args[1]
                self.ESIZE = args[2]
                self.ASIZE = args[3]
            # Detector type
            if n == 3:
                self.NDTECT = args[0]
                if len(args) > 1:
                    self.save_errored = args[1]
            # Detector Params, 4 of them
            if n == 4:
                self.DTECTPAR = args
            # min and max time steps
            if n == 5:
                self.DELLOW = args[0]
                self.DELT0 = args[1]
            # DEMAX,DEMIN,ABSERR
            if n == 6:
                self.DEMAX = args[0]
                self.DEMIN = args[1]
                self.ABSERR = args[2]
            # NPART - ATOMS ON SURFACE
            if n == 7:
                self.NPART = args[0]
            # Recoil
            if n == 8:
                self.RECOIL = args[0]
            # Interaction Height
            if n == 9:
                self.Z1 = args[0]
            # Table Entries
            if n == 10:
                self.MAX_STEPS = args[0]
            # R min and R step
            if n == 11:
                self.RRMIN = args[0]
                self.RRSTEP = args[1]
            # Z min and Z step
            if n == 12:
                self.ZMIN = args[0]
                self.ZSTEP = args[1]
            # Min and Max div, Here we check if o needs incrementing.
            if n == 13:
                if o <= 0:
                    self.MAXDIV = args[0]
                    self.MINDIV = args[1]
                    # This will be decremented after leaving this if
                    o = 4
                else:
                    if o == 3:
                        self.NUMCHA = args[0]
                    if o == 2:
                        self.XSTART = args[0]
                        self.XSTEP = args[1]
                        self.XSTOP = args[2]
                        for i in range(3, len(args)):
                            self.x_points.append(args[i])

                    if o == 1:
                        self.YSTART = args[0]
                        self.YSTEP = args[1]
                        self.YSTOP = args[2]
                        for i in range(3, len(args)):
                            self.y_points.append(args[i])
            # NWRITX, NWRITY
            if n == 14:
                self.NWRITX = args[0]
                self.NWRITY = args[1]
            # RAX and RAY
            if n == 15:
                self.RAX = args[0]
                self.RAY = args[1]
            # NPAR and IPOT
            if n == 16:
                self.NPAR = args[0]
                self.IPOT = args[1]
            # Parameters for IPOT
            if n == 17:
                self.POTPAR = []
                for i in range(self.NPAR):
                    if i<num:
                        self.POTPAR.append(args[i])
                    else:
                        self.POTPAR.append(0)
            # NIMPAR and IIMPOT
            if n == 18:
                self.NIMPAR = args[0]
                self.IIMPOT = args[1]
            # Parameters for IIMPOT, as well as other stuff?
            if n == 19:
                if o <= 0:
                    self.PIMPAR = []
                    for i in range(self.NIMPAR):
                        if i<num:
                            self.PIMPAR.append(args[i])
                        else:
                            self.PIMPAR.append(0)
                    if self.IIMPOT == 2:
                        # This will be decremented after leaving this if
                        o = 7
                elif o == 6:
                    self.NBZ = args[0]
                    self.TOL = args[1]
                elif o == 5:
                    self.ZMAX = []
                    for i in range(self.NBZ):
                        if i<num:
                            self.ZMAX.append(args[i])
                        else:
                            self.ZMAX.append(0)
                elif o == 4:
                    self.NZ = []
                    for i in range(self.NBZ):
                        if i<num:
                            self.NZ.append(args[i])
                        else:
                            self.NZ.append(0)
                elif o == 3:
                    self.NBG = args[0]
                    self.GTOL = args[1]
                elif o == 2:
                    self.GMAX = []
                    for i in range(self.NBG):
                        if i<num:
                            self.GMAX.append(args[i])
                        else:
                            self.GMAX.append(0)
                elif o == 1:
                    self.NG = []
                    for i in range(self.NBG):
                        if i<num:
                            self.NG.append(args[i])
                        else:
                            self.NG.append(0)
            # Temp, Seed, Ion_Index
            if n == 20:
                self.TEMP = args[0]
                self.SEED = args[1]
                self.Ion_Index = args[2]
            # Use Image Charge
            if n == 21:
                self.IMAGE = args[0]
            # SENRGY and BDIST
            if n == 22:
                self.SENRGY = args[0]
                self.BDIST = args[1]
            # AX and AY
            if n == 23:
                self.AX = args[0]
                self.AY = args[1]
                self.AZ = args[2]
            # Load the basis cell
            if n == 24:
                # How many atoms in the basis
                if o <= 0:
                    self.NBASIS = args[0]
                    o = self.NBASIS + 1
                    self.BASIS = []
                # Load each atom
                else:
                    # X, Y, Z, Atom Type
                    site = [args[0], args[1], args[2], args[3]]
                    self.BASIS.append(site)
            # Number of atom types
            if n == 25:
                # Load number of atoms
                if o <= 0:
                    self.NTYPES = args[0]
                    self.ATOMS = []
                    self.SPRINGS = []
                    # 2 lines per atom.
                    o = self.NTYPES * 2 + 1
                # Load atom parameters
                else:
                    # Even entries are the atom
                    if o % 2 == 0:
                        # Mass, Charge, and Symbol
                        atom = [args[0], args[1], args[2]]
                        self.ATOMS.append(atom)
                    #Odd entries are the spring
                    else:
                        # Spring parameters, X, Y and Z
                        spring = [args[0], args[1], args[2]]
                        self.SPRINGS.append(spring)
            # CORR,ATOMK,RNEIGH
            if n == 26:
                self.CORR = args[0]
                self.ATOMK = args[1]
                self.RNEIGH = args[2]
            # load in the face
            if n == 27:
                self.face = [args[0], args[1], args[2]]
                if len(args) > 3:
                    self.load_crystal = args[3]
                if self.load_crystal:
                    self.loaded_face = [args[4], args[5], args[6]]
            if n==28:
                self.F_a = args[0]
                self.F_b = args[1]
                
            # Decrement our sub-line first.
            o = o - 1
            # Only increment this if not in a sub-line section.
            if o <= 0:
                n = n+1
        file.close()
        return

def load(file_in):

    lines = []
    
    safio = SafariInput(file_in)
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

def plot_crystal(x, y, z, S, ax):
    ax.scatter3D(x, y, z,c='orange')

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

def plot(filename, ax):
    X, Y, Z, S, bounds, mask = load(filename)
    plot_crystal(X, Y, Z, S, ax)
    add_active_area(ax, bounds, mask)
    return

if __name__ == "__main__" :
    filename = './var/204.dbug'

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    
    plot(filename, ax)

    fig.show()
    input("Enter to exit.")