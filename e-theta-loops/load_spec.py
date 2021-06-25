import numpy as np
import matplotlib      # Main plotting
#Qt5Agg is the backend
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt 

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
        self.load(file)
        self.img = None

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

    def process_data(self, d_phi=1):
        l_E = len(self.detections) - 1
        l_T = len(self.detections[1])
        l_P = len(self.detections[1][0])

        data = np.zeros((l_E, l_T))


        for n_E in range(l_E):
            table = self.detections[n_E]
            for n_T in range(l_T):
                row = table[n_T]
                for n_P in range(l_P):
                    P = interp(n_P, l_P, self.p_range[0], self.p_range[1])
                    if P > self.phi - d_phi/2 and P < self.phi + d_phi/2:
                        data[n_E][n_T] = data[n_E][n_T] + row[n_P]
        print(l_T)
        print(l_E)
        self.img = data

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
                    table.append(data_row)
        del self.detections[0]

    def load(self, file):
        spec_file = open(file, 'r')
        entire_file = spec_file.read()
        components = entire_file.split('--------------------------------------------------------')
        header = components[1]
        data = components[2]
        self.parse_header(header)
        self.parse_data(data)


if __name__ == "__main__" :
    spec = Spec('./test.spec')
    spec.process_data()
    print(spec)

    fig, ax = plt.subplots()

    e_max = spec.e_range[1]
    e_min = spec.e_range[0]
    t_min = spec.t_range[0]
    t_max = spec.t_range[1]

    del_e = e_max-e_min
    del_t = t_max-t_min

    im = ax.imshow(spec.img, interpolation="bicubic", extent=(t_min, t_max, e_max, e_min))
    ax.invert_yaxis()
    ax.set_aspect(aspect=del_t/del_e)
    fig.colorbar(im, ax=ax)
    ax.set_title("Energy vs Theta")
    ax.set_xlabel('Outgoing angle (Degrees)')
    ax.set_ylabel('Outgoing Energy (eV)')
    fig.show()

    input("Enter to exit")