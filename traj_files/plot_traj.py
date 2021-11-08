import argparse                    # Parsing input arguments
import numpy as np                 # Array processing
import math                        # sqrt, etc
import matplotlib                  # Plotting
import matplotlib.pyplot as plt    # Plotting
import scipy.constants as consts   # Converting safari-time to seconds

class Traj:

    # Returns the SAFARI time unit in seconds
    def time_unit(self):
        amu = consts.physical_constants["atomic mass unit-kilogram relationship"][0]
        eV = consts.physical_constants["atomic unit of charge"][0]
        A = consts.angstrom
        return A*math.sqrt(amu/eV)

    # Loads from the given .traj file
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

    # Plots the various energies vs time
    def plot_energies(self, ax):
        ax.plot(self.t, self.V, label="Interaction Potential")
        ax.plot(self.t, self.T, label="Kinetic Energy")
        ax.plot(self.t, self.E, label="Total Energy")

        ax.set_xlabel('Time (fs)')
        ax.set_ylabel('Energy (eV)')
        ax.legend()

    # Plots the various derivatives of energies vs time
    def plot_power(self, ax):
        # V = np.gradient(self.V, self.t)
        # T = np.gradient(self.T, self.t)
        E = -np.gradient(self.E, self.t)
        ax.plot(self.t, E, label="Projectile Power Transfer")

        ax.set_xlabel('Time (fs)')
        ax.set_ylabel('Power (eV/fs)')
        ax.legend()

    # Adds just a plot of Z position vs time
    def plot_traj_1d(self, ax, axis='z'):
        ax.plot(self.t, self.z)

        ax.set_xlabel('Time (fs)')
        ax.set_ylabel('Z Position (Å)')

    # Adds to the given axis, via scatter3D plot
    def plot_traj_3d(self, fig, ax):
        x,y,z = self.x, self.y, self.z

        dir_x = [x[-1]-x[-2]]
        dir_y = [y[-1]-y[-2]]
        dir_z = [z[-1]-z[-2]]

        ax.quiver([x[-1]], [y[-1]], [z[-1]], dir_x, dir_y, dir_z, length=1.0, normalize=True)
        ax.scatter3D(x, y, z, c='red')
        self.zoomed=True

        min_z = np.min(z)
        max_z = np.max(z)
        ax.set_zlim(min_z, max_z)
        
        # This will rescale the plot when double clicked
        def onclick(event):
            if event.dblclick:
                min_x = np.min(x)
                min_y = np.min(y)

                max_x = np.max(x)
                max_y = np.max(y)

                dx = np.max(x) - np.min(x)
                dy = np.max(y) - np.min(y)

                # If we are zoomed, instead rescale based on largest
                if self.zoomed:
                    if(dy < dx):
                        mean_y = (min_y + max_y) / 2
                        min_y = mean_y - dx/2
                        max_y = mean_y + dx/2
                    elif(dy > dx):
                        mean_x = (min_x + max_x) / 2
                        min_x = mean_x - dy/2
                        max_x = mean_x + dy/2
                    self.zoomed = False
                # Otherwise do nothing, as we are already scaled correctly
                else:
                    self.zoomed = True
                ax.set_xlim(min_x, max_x)
                ax.set_ylim(min_y, max_y)

            fig.canvas.draw()

        # Apply the event to the canvas
        fig.canvas.mpl_connect('button_press_event', onclick)

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
    traj.plot_traj_3d(fig3, ax3)
    fig3.show()

    if args.save:
        fig.savefig(args.input.replace('.traj', '_energy.png'))
        fig2.savefig(args.input.replace('.traj', '_z_t.png'))

    input("Enter to exit.")
