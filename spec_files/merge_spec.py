import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import load_spec
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

    input("Enter to exit")