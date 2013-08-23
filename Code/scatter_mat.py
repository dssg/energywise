import sys
from   collections import Counter
import random
from   utils import *
import numpy as np
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
from   matplotlib.colors import LogNorm
from   utils import extract_legend
import matplotlib.cm as cm

def make_scatter_mat_fig(fig, mat,
                         names = None, classes = None, color_map = None,
                         target = None, class_names = None, zoom = 100, tight = True,
                         label_fontsize = 14, target_name = "Target", show_diag = True,
                         show_grid = True):
    """Given a figure, this function populates it with a scatter matrix.
    Subfigures along the diagonal show histograms over individual features (separated by class, when appropriate).
    Subfigures below the diagonal show scatter plots (where colors correspond to classes, when appropriate).
    Subfigures above the diagonal show 2d histograms of the bivariate distributions. 

    Parameters:
    fig -- the matplotlib.pyplot.figure object to be filled.
    mat -- An n by d numpy.ndarray where each row is a data point, and each column is a feature. 
    names [None] -- A list d of column names.
    classes [None] -- A list of n classes (one per data point).
    color_map [None] -- A dictionary mapping a class to a color. The colors are used in the histograms and scatter plots.
    target [None] -- A single point to be highlighted.
                     In every 2d subfigure, crosshairs are placed showing the target.
                     It may be an integer, a dictionary, or an ndarray.
                     If target is an integer i, then the i-th data point in mat is highlighted.
                     If target is a dictionary, it maps names to values (e.g., {"height": 4.2, "weight": 1.2}).
                     If target is an ndarray, then it is treated as a data point as if it was in mat.
    class_names [None] -- A dictionary mapping a class to its name (used in legend).
    zoom [100] -- The percentage of the span to show on each axis of each subplot.
                  For example, if zoom = 95, each subplot has its x and y limits reduced to the 2.5 and 97.5 percentiles of the points shown in that subplot.
    tight [True] -- If True, tick and ticklabels on the diagonal subplots (histograms) are hidden, and inter-subplot space is greatly reduced.
    label_fontsize [14] -- The fontsize of the feature labels.
    target_name ["Target"] -- The name of the target, used in figure legend.
    show_diag [True] -- If True, a dashed line correpsonding to x = y is shown in each off-diagonal subplot.
    show_grid [True] -- If True, grid lines are shown on all off-diagonal subplots.
    """

    nrows, ncols = mat.shape
    if isinstance(target, dict):
        assert names is not None, "Feature names must be specified if target is a dict"
        nt = []
        for c in range(ncols):
            nt.append(target[names[c]])
        target = np.array(nt)
        print target, "<<<"
    elif isinstance(target, int):
        target = mat[target, :]
    else:
        assert isinstance(target, np.ndarray) or isinstance(target, list), "Argument 'target' is of unsupported type"

    if classes is not None:
        classes = np.array(classes)
        class_set = set(classes)

        if color_map is None:
            unique_classes = set(list(classes))
            color_map = {}
            i = 0
            mycolors = ["Blue",
                        "BlueViolet",
                        "Brown",
                        "BurlyWood",
                        "CadetBlue",
                        "Chartreuse",
                        "Chocolate",
                        "Crimson",
                        "Cyan",
                        "DarkBlue"
                        "DarkGreen",
                        "DarkMagenta",
                        "DarkOliveGreen"]
            for c in unique_classes:
                thecolor = mycolors[i % len(mycolors)]
                color_map[c] = thecolor
                i += 1

    bmax = ncols * ncols
    p = 0
    for frow in range(ncols):
        for fcol in range(ncols):
            p += 1
            progress_bar(p, bmax)
            col1 = mat[:, frow]
            col2 = mat[:, fcol]
            ax = fig.add_subplot(ncols, ncols, frow * ncols + fcol + 1)
            
            if frow == fcol:
                #We're looking at a diagonal plot and we're going to make a histogram.
                hist_alpha = 1.0
                if tight:
                    ax.set_yticks([])
                #if classes are provided, make stacked histogram
                if classes is not None:
                    ax2 = ax.twinx()
                    #ax2.set_ylabel("Individuals")
                    if tight:
                        ax2.set_yticks([])

                    sub_hists = []
                    for c in class_set:
                        to_append = col1[classes == c]
                        if type(to_append) == np.float64:
                            sub_hists.append([to_append])
                        else:
                            sub_hists.append(col1[classes == c])
                    
                    n, bins, patchs = ax2.hist(sub_hists, histtype = 'bar',
                                               color = [color_map[c] for c in class_set], lw = 0)
                    hist_alpha = 0.5 #Make aggregate histogram semi-transparent.
                    
                #Make a histogram of total (aggregate values)
                ax.hist(col1, color = "grey", alpha = hist_alpha)

                if target is not None:
                    target_x = target[frow]
                    ax.axvline(target_x, 0, 1, ls = "dashed", c = "red", label = target_name)
            else:
                if show_grid:
                    ax.grid(True)
                low  = (100 - zoom) / 2
                high = 100 - low

                mins = min(np.min(col1), np.min(col2))
                maxs = max(np.max(col1), np.max(col2))
                
                if show_diag: 
                    ax.plot([mins,maxs], [mins,maxs], ls = "dashed", color = "black", label = r"$x = y$") 
                if target is not None:
                    target_x = target[fcol]
                    target_y = target[frow]
                    
                    ax.axvline(target_x, 0, 1, ls = "dashed", c = "red", label = target_name)
                    ax.axhline(target_y, 0, 1, ls = "dashed", c = "red", label = target_name)

                if frow > fcol:
                    #We're below the diagonal and we're going to make a scatter plot.
                    if classes is not None:
                        for c in set(classes):
                            if class_names is not None and c in class_names:
                                label = class_names[c]
                            else:
                                label = str(c)

                            ax.scatter(col2[classes == c], col1[classes == c], c = color_map[c], label = label, alpha = .4, lw = 0, s = 10)
                    else:
                        ax.scatter(col2, col1, alpha = .4, c = "purple", lw = 0)

                    ax.set_xlim(np.percentile(col2, low), np.percentile(col2, high))
                    ax.set_ylim(np.percentile(col1, low), np.percentile(col1, high))
                    
                else:
                    #We're above the diagonal and we're going to make a 2dhist.
                    ax.hist2d(col2, col1, bins = 50, norm = LogNorm())
                    ax.set_xlim(np.percentile(col2, low), np.percentile(col2, high))
                    ax.set_ylim(np.percentile(col1, low), np.percentile(col1, high))

            if fcol == ncols -1 and fcol != frow: #We're at the right most column
                ax.yaxis.set_ticks_position("right")
            elif fcol != 0 and fcol != frow: #We're not on the left or a diagonal 
                ax.set_yticklabels([])
            if frow == 0: #We're at the top
                ax.xaxis.set_ticks_position("top")
            elif frow != ncols - 1 and fcol != frow: #We're not at the bottom or a diagonal
                ax.set_xticklabels([])
            if frow == ncols - 1 and names is not None: #We're at the bottom, and we have names of columns to place
                ax.set_xlabel(names[fcol], rotation = 45, fontsize = label_fontsize, va = "top")

            if fcol == 0 and names is not None: #We're on the left, and we have names of rows to place
                ax.set_ylabel(names[frow], rotation = 30, ha = "right", fontsize = label_fontsize)
            ax.legend()
            labels = ax.get_xticklabels() 
            for label in labels: 
                label.set_rotation(45) 
    if tight:
        fig.subplots_adjust(hspace = 0.001, wspace = 0.001)

    extract_legend(fig, loc = 'lower left')

def from_agg_report_to_mat(agg):
    names = agg.keys()
    ncols = len(names)
    nrows = len(agg[names[0]])
    toR = np.zeros(shape = (nrows, ncols), dtype = float)

    for i, name in enumerate(names):
        toR[:, i] = np.array(agg[name])
    return toR, names


def get_dummy_data():
    npoints = 200
    dat = np.random.normal(0.0, 1.0, size = (npoints, 4))
    classes = np.array([random.sample(["red", "green", "blue", "black"], 1)[0] for x in range(npoints)])
    dat[classes == "black", 2] += 10
    dat[:, 0] *= 4
    dat[classes == "red", 2] += 2* dat[classes == "red", 0] + 2
    dat[classes == "green", 1] += 3* dat[classes == "green", 3]
    names = ["Glory", "Teamwork", "Confidence", "Procastination"]
    color_map = dict(zip(classes, classes))
    class_names =dict(red = "Team A", green = "Opfor", blue = "The Jelly Bullies", black = "Hawx of Nature") 
    return dat, names, classes, color_map, class_names

if __name__ == "__main__":
    if False:#True:
        agg, desc = qload("agg_reps.pkl")
        #toDel = ["naics", "avg_weekday_min", "var", "spectral_power", "num_missing", "total"]
        toDel = []
        for d in toDel:
            if d in agg:
                print "removing", d
                del agg[d]
            else:
                print d, "not found"

        dat, names = from_agg_report_to_mat(agg)
        
        qdump(((dat, names), "A tuple (dat, names) from the agg report"), "agg_mat.pkl")
        # exit()

    big = False
    add_str = ""
    add_str = "_btype"
    if big:
        target = None
        t, desc = qload("agg_mat" + add_str + ".pkl")
        dat, names = t
        classes, desc = qload("naics_codes" + add_str + ".pkl")
        counts = Counter(classes)

        #classes = np.array([c if counts[c] >= 0 else 9999 for c in classes])
        classes = np.array([c if counts[c] >= 0 else 'Other' for c in classes])
        color_map = None
        dat = dat[np.logical_and(classes != "Other", classes != "Unknown")]

        
        classes = np.array(classes)
        classes = classes[np.logical_and(classes != "Other", classes != "Unknown")]

        unique_classes = set(list(classes))
        color_map = {}
        i = 0            
        figsize = (40, 40)
        class_names = None
    else:
        dat, names, classes, color_map, class_names = get_dummy_data()
        #target = dict(Glory = 1.4, Teamwork = 2.3, Confidence = 4.2, Procastination = 2.0)
        #target = dat[0, :]
        target = 4
        figsize = (14, 14)

    fig = plt.figure(figsize = figsize)
    zoom = 100
    tight = True
    label_fontsize = 14
    args = dict(classes = classes,
                names = names,
                #color_map = color_map,
                target = target,
                class_names = class_names,
                zoom = zoom,
                tight = tight,
                label_fontsize = label_fontsize,
                target_name = "Henry the Badger",
                show_diag = True,
                show_grid = False)
    
    make_scatter_mat_fig(fig, dat, **args)
    if big:
        plt.savefig(fig_loc + "agg_no9999_zoom" + str(zoom) + ("tight" if tight else "") + add_str + ".png", bbox_inches='tight', dpi = 200)
        #plt.savefig("agg.pdf", bbox_inches='tight')

        #plt.show()
    else:
        #plt.tight_layout()
        #plt.savefig(fig_loc + "scatter_mat_demo.png", dpi = 200)
        
        plt.show()
        

