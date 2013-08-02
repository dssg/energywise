import sys
from collections import Counter
import random
from utils import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from plotter_new import extract_legend
import matplotlib.cm as cm

def make_scatter_mat_fig(fig, mat, names = None, colors = None, color_map = None):
    nrows, ncols = mat.shape
   
    for frow in range(ncols):
        for fcol in range(ncols):
            col1 = mat[:, frow]
            col2 = mat[:, fcol]
            ax = fig.add_subplot(ncols, ncols, frow * ncols + fcol + 1)


            if frow == fcol:
                ax.hist(col1)
            else:
                mins = min(np.min(col1), np.min(col2))
                maxs = max(np.max(col1), np.max(col2))
                
                ax.plot([mins,maxs], [mins,maxs], ls = "dashed", color = "black", label = r"$x = y$") 

                if frow > fcol:
                    if colors is not None:
                        for c in set(colors):
                            if color_map is not None and c in color_map:
                                label = color_map[c]
                            else:
                                label = str(c)

                            ax.scatter(col2[colors == c], col1[colors == c], c = colors[colors == c], label = label, alpha = .4)
                    else:
                        ax.scatter(col2, col1, alpha = .4, c = "purple", lw = 0)
                    ax.set_xlim(np.min(col2), np.max(col2))
                    ax.set_ylim(np.min(col1), np.max(col1))
                    
                else:
                    ax.hist2d(col2, col1, bins = 50, norm = LogNorm())
                    ax.set_xlim(np.min(col2), np.max(col2))
                    ax.set_ylim(np.min(col1), np.max(col1))

            if fcol == ncols -1:
                ax.yaxis.set_ticks_position("right")
            elif fcol != 0 and fcol != frow:
                ax.set_yticks([])
            if frow == 0:
                ax.xaxis.set_ticks_position("top")
            elif frow != ncols - 1 and fcol != frow:
                ax.set_xticks([])
                
            if frow == 0  and names is not None:
                ax.set_xlabel(names[fcol], rotation = 15)
                ax.xaxis.set_label_coords(0.5, 1.4)
                ax.xaxis.set_label_position("top")
            if fcol == 0 and names is not None:
                ax.set_ylabel(names[frow], rotation = 30, ha = "right")
            ax.legend()
            labels = ax.get_xticklabels() 
            for label in labels: 
                label.set_rotation(45) 
    extract_legend(fig)

def from_agg_report_to_mat(agg):
    names = agg.keys()
    ncols = len(names)
    nrows = len(agg[names[0]])
    toR = np.zeros(shape = (nrows, ncols), dtype = float)

    for i, name in enumerate(names):
        toR[:, i] = np.array(agg[name])
    return toR, names


def get_dummy_data():
    npoints = 400
    dat = np.random.normal(0.0, 1.0, size = (npoints, 4))
    colors = np.array([random.sample(["red", "green", "blue", "black"], 1)[0] for x in range(npoints)])
    dat[colors == "black", 2] += 10
    dat[:, 0] *= 4
    dat[colors == "red", 2] += 2* dat[colors == "red", 0] + 2
    dat[colors == "green", 1] += 3* dat[colors == "green", 3]
    names = ["Glory", "Teamwork", "Confidence", "Procastination"]
    color_map = dict(red = "Team A", green = "Opfor", blue = "The Jelly Bullies", black = "Hawx of Nature")
    return dat, names, colors, color_map

if __name__ == "__main__":
    """
    agg, desc = qload("agg_reps_small.pkl")
    dat, names = from_agg_report_to_mat(agg)
    qdump(((dat, names), "A tuple (dat, names) from the agg report"), "agg_mat_small.pkl")
    """
    big = True
    add_str = ""
    #add_str = "_small"
    if big:
        t, desc = qload("agg_mat" + add_str + ".pkl")
        dat, names = t
        colors, desc = qload("naics_codes" + add_str + ".pkl")
        counts = Counter(colors)
        colors = np.array([c if counts[c] >= 200 else 9999 for c in colors])
        color_map = {}
        #dat = dat[colors != 9999]
        #colors = colors[colors != 9999]
        unique_colors = set(colors)
        cmap = {}
        i = 0
        mycolors = "bgrcmykw"
        
        for c in unique_colors:
            thecolor = mycolors[i % len(mycolors)]
            cmap[c] = thecolor
            i += 1
            color_map[thecolor] = c
        colors = np.array([cmap[c] for c in colors])
        figsize = (100, 100)

    else:
        dat, names, colors, color_map = get_dummy_data()
        figsize = (10, 10)

        
    fig = plt.figure(figsize = figsize)


    make_scatter_mat_fig(fig, dat, colors = colors, names = names, color_map = color_map)
    if big:
        plt.savefig(fig_loc + "agg_big_no9999" + add_str + ".png", bbox_inches='tight')
        #plt.savefig("agg.pdf", bbox_inches='tight')

        plt.show()
    else:
        plt.show()


