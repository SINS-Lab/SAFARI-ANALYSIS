import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import load_spec
import fit_esa as esa
import os

def merge(spec, scale, spec_in):
    if spec_in is None:
        for i in range(len(spec.detections)-1):
            for j in range(len(spec.detections[1])):
                row_a = spec.detections[i][j]
                spec.detections[i][j] = row_a * scale
        return spec
    # We should check here that phi and theta and e ranges are the same.
    # But That can be done later, so if relevant issues occur, this is where to fix it!
    for i in range(len(spec.detections)-1):
        for j in range(len(spec.detections[0])):
            row_a = spec.detections[i][j]
            row_b = spec_in.detections[i][j]
            spec_in.detections[i][j] = row_b + scale * row_a
    return spec_in

def load_scales(filename):
    file = open(filename,'r')
    scales = {}
    for line in file:
        if line.startswith('#'):
            continue
        vars = line.split('\t')
        name = vars[0]
        scale = float(vars[1])
        scales[name] = scale
    file.close()
    return scales

def load_and_merge(directory):
    scales = load_scales(os.path.join(directory, 'scales.tab'))
    spec = None
    for filename, scale in scales.items():
        new_spec = load_spec.Spec(os.path.join(directory, filename))
        spec = merge(new_spec, scale, spec)
    return spec

if __name__ == "__main__" :
    spec = load_and_merge('./var/to_merge')
    spec.process_data()
    spec.make_e_t_plot()

    fig, ax = spec.fig, spec.ax

    e_max = spec.e_range[1]
    e_min = spec.e_range[0]
    t_min = spec.t_range[0]
    t_max = spec.t_range[1]
    axis = esa.make_axis(e_min, e_max, spec.energy, spec.img.shape[0]) * spec.energy
    
    def min_w(slyce):
        return 2

    guess_params = []
    for i in range(spec.img.shape[1]):
        if i>78:
            guess_params.append([100,1,12])
        else:
            guess_params.append(None)

    spec.try_fit(esa.fit_esa, axis, ax, min_w=min_w,guess_params=guess_params)

    input("Enter to exit")