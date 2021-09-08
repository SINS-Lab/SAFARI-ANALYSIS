import numpy as np                  # Array manipulation/maths
import matplotlib                   # Plotting
import os                           # Path related stuff
import scipy.signal as signal       # Peak finding
import matplotlib.pyplot as plt     # Plotting

def load_esa(filename, scale_by_E=True, normalise=True):
    file = open(filename, 'r')
    E = []
    I = []
    for line in file:
        if line.startswith('#') or line.strip() == '':
            continue
        args = line.split()
        if len(args) < 2:
            continue
        E.append(float(args[0]))
        I.append(float(args[1]))
    file.close()
    E = np.array(E)
    I = np.array(I)
    if scale_by_E:
        I = I / E
    if normalise:
        I = I / np.max(I)
    return E, I

# This is an ESA Spectrum
class Spec:
    def load(self, filename):
        self.Energies = []
        self.Counts = []
        self.times = []
        self.intensity = []
        spec_file = open(filename, 'r')
        started = False
        self.hasCounts = False
        for line in spec_file:
            if not started:
                started = line.startswith('! Energy(eV)')
                continue
            args = line.split()
            if len(args) > 2:
                #These are read as floats for normalizing later
                self.Energies.append(float(args[0]))
                self.Counts.append(float(args[1]))
                self.times.append(float(args[2]))
                self.hasCounts = True
            else:# Simlulated ones don't output this info
                i = float(args[1])
                if(i>1e-5):
                    self.Energies.append(float(args[0])*254.6)
                    self.times.append(0)
                    self.intensity.append(i)
                    self.Counts.append(i)
                    self.hasCounts = False
            if len(args) > 3:
                self.intensity.append(float(args[3]))
        spec_file.close()
        self.Energies = np.array(self.Energies)
        self.Counts = np.array(self.Counts)
        self.hasCounts = np.sum(self.Counts) > 0.5
        self.times = np.array(self.times)
        if len(self.intensity) > 0:
            self.intensity = np.array(self.intensity)

        new_file = filename + '.esa'
        spec_file = open(new_file, 'w')
        spec_file.write('# Generated ESA Data file\n')
        spec_file.write('# Columns as follows:\n')
        spec_file.write('# Energy (eV)\tIntensity (Arb)\tTime (s)\n')
        for i in range(len(self.Energies)):
            E = self.Energies[i]
            I = self.Counts[i]
            t = self.times[i]
            spec_file.write('{}\t{}\t{}\n'.format(E, I, t))
        spec_file.close()

if __name__ == "__main__" :
    filename = './var/SPEC00'

    spec = Spec()
    spec.load(filename)
    
    E, I = load_esa(filename+'.esa')