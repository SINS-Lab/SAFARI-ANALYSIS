import argparse                    # Parsing input arguments
import numpy as np                 # Array processing
import math                        # sqrt, etc
import matplotlib                  # Plotting
#Qt5Agg is the backend
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt    # Plotting
import scipy.constants as consts   # Converting safari-time to seconds

class Traj:

    def time_unit(self):
        amu = consts.physical_constants["atomic mass unit-kilogram relationship"][0]
        eV = consts.physical_constants["atomic unit of charge"][0]
        A = consts.angstrom
        return A*math.sqrt(amu/eV)

    def load(self, filename):

        #Coordinates
        self.x = []
        self.y = []
        self.z = []

        #Momenta
        self.px = []
        self.py = []
        self.pz = []

        #Times
        self.t = []  #Total Time
        self.dt = [] #Current Time step

        #Energies
        self.T = []  #Kinetic
        self.V = []  #Potential
        self.E = []  #Total
        self.dV = [] #Potential Change

        #Counters
        self.n = []  #Time step
        self.near=[] #Number nearby

        traj_file = open(filename, 'r')
        num = 0
        for line in traj_file:
            if num == 0:
                num = num + 1
                continue
            num = num + 1
            args = line.split()
            self.x.append(float(args[0]))
            self.y.append(float(args[1]))
            self.z.append(float(args[2]))

            self.px.append(float(args[3]))
            self.py.append(float(args[4]))
            self.pz.append(float(args[5]))

            self.t.append(float(args[6]))
            self.n.append(int(args[7]))

            self.T.append(float(args[8]))
            self.V.append(float(args[9]))
            self.E.append(float(args[10]))

            self.near.append(int(args[11]))
            self.dt.append(float(args[12]))
            #self.dr_max.append(float(args[13])) We dont use this
            #self.dV.append(float(args[14]))
        self.x = np.array(self.x)
        self.y = np.array(self.y)
        self.z = np.array(self.z)

        self.px = np.array(self.px)
        self.py = np.array(self.py)
        self.pz = np.array(self.pz)

        self.t = np.array(self.t)
        #Convert to femtoseconds
        self.t = self.t * self.time_unit() * 1e15

        self.T = np.array(self.T)
        self.V = np.array(self.V)
        self.E = np.array(self.E)

    def plot_energies(self, ax):
        ax.plot(self.t, self.V, label="Interaction Potential")
        ax.plot(self.t, self.T, label="Kinetic Energy")
        ax.plot(self.t, self.E, label="Total Energy")

        ax.set_xlabel('Time (fs)')
        ax.set_ylabel('Energy (eV)')
        ax.legend()

    def plot_traj_1d(self, ax, axis='z'):
        ax.plot(self.t, self.z)

        ax.set_xlabel('Time (fs)')
        ax.set_ylabel('Z Position (Å)')

    def plot_traj_3d(self, ax):
        ax.scatter3D(self.x,self.y,self.z)
        ax.scatter3D([self.x[0]],[self.y[0]],[self.z[0]],'red')

if __name__ == "__main__" :
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input file")
    parser.add_argument("-s", "--save", help="Whether to save the graphs", action='store_true')
    args = parser.parse_args()

    traj = Traj()
    traj.load(args.input)

    fig, ax = plt.subplots()
    traj.plot_energies(ax)
    fig.show()

    fig2, ax2 = plt.subplots()
    traj.plot_traj_1d(ax2)
    fig2.show()

    fig3 = plt.figure()
    ax3 = plt.axes(projection='3d')
    traj.plot_traj_3d(ax3)
    fig3.show()

    if args.save:
        fig.savefig(args.input.replace('.traj', '_energy.png'))
        fig2.savefig(args.input.replace('.traj', '_z_t.png'))

    input("Enter to exit.")
