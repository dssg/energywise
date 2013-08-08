import sys
from collections import Counter
import random
from utils import *
import numpy as np
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from plotter_new import extract_legend
import matplotlib.cm as cm

#def make_scatter_mat_fig(fig, mat, names = None, colors = None, color_map = None, target = None):
def make_scatter_mat_fig(fig, mat, names = None, classes = None, color_map = None, target = None, class_names = None, zoom = 100, tight = True):
    #Note: Target is a report
    label_fontsize = 36
    nrows, ncols = mat.shape
    if classes is not None:
        classes = np.array(classes)
        class_set = set(classes)
        if color_map is not None:
            colors = [color_map[c] for c in classes] #the colors of each point
        
    for frow in range(ncols):
        for fcol in range(ncols):
            col1 = mat[:, frow]
            col2 = mat[:, fcol]
            ax = fig.add_subplot(ncols, ncols, frow * ncols + fcol + 1)
            
            if frow == fcol:
                #We're looking at a diagonal plot and we're going to make a histogram.
                hist_alpha = 1.0
                if tight:
                    ax.set_yticks([])
                #if classes are provided, make stacked histogram
                if color_map is not None:
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
                    
                    print color_map
                    n, bins, patchs = ax2.hist(sub_hists, histtype = 'bar',
                                               color = [color_map[c] for c in class_set], lw = 0)
                    hist_alpha = 0.5 #Make aggregate histogram semi-transparent.
                    
                #Make a histogram of total (aggregate values)
                ax.hist(col1, color = "grey", alpha = hist_alpha)
                #ax.set_ylabel("Total")

                if target is not None:
                    target_x = target[names[frow]]
                    ax.axvline(target_x, 0, 1, ls = "dashed", c = "red", label = "Target")
            else:
                ax.grid(True)
                low  = (100 - zoom) / 2
                high = 100 - low

                ##mins = min(np.percentile(col1, low),  np.percentile(col2, low))
                ##maxs = max(np.percentile(col1, high), np.percentile(col2, high))
                mins = min(np.min(col1), np.min(col2))
                maxs = max(np.max(col1), np.max(col2))
                
                ax.plot([mins,maxs], [mins,maxs], ls = "dashed", color = "black", label = r"$x = y$") 
                if target is not None:
                    target_x = target[names[fcol]]
                    target_y = target[names[frow]]
                    ax.axvline(target_x, 0, 1, ls = "dashed", c = "red", label = "Target")
                    ax.axhline(target_y, 0, 1, ls = "dashed", c = "red", label = "Target")

                if frow > fcol:
                    #We're below the diagonal and we're going to make a scatter plot.
                    if classes is not None:
                        for c in set(classes):
                            if class_names is not None and c in class_names:
                                label = class_names[c]
                            else:
                                label = str(c)

                            ax.scatter(col2[classes == c], col1[classes == c], c = [color_map[x] for x in classes[classes == c]], label = label, alpha = .4, lw = 0, s = 3)
                    else:
                        ax.scatter(col2, col1, alpha = .4, c = "purple", lw = 0)

                    #ax.set_xlim(np.min(col2), np.max(col2))
                    #ax.set_ylim(np.min(col1), np.max(col1))
                    ax.set_xlim(np.percentile(col2, low), np.percentile(col2, high))
                    ax.set_ylim(np.percentile(col1, low), np.percentile(col1, high))
                    
                else:
                    #We're above the diagonal and we're going to make a 2dhist.
                    ax.hist2d(col2, col1, bins = 50, norm = LogNorm())
                    ax.set_xlim(np.percentile(col2, low), np.percentile(col2, high))
                    ax.set_ylim(np.percentile(col1, low), np.percentile(col1, high))

                    #ax.set_xlim(np.min(col2), np.max(col2))
                    #ax.set_ylim(np.min(col1), np.max(col1))

            if fcol == ncols -1: #We're at the right most column
                ax.yaxis.set_ticks_position("right")
            elif fcol != 0 and fcol != frow: #We're not on the left or a diagonal 
                #ax.set_yticks([])
                ax.set_yticklabels([])
            if frow == 0: #We're at the top
                ax.xaxis.set_ticks_position("top")
            elif frow != ncols - 1 and fcol != frow: #We're not at the bottom or a diagonal
                #ax.set_xticks([])
                ax.set_xticklabels([])
            if frow == 0 and names is not None: #We're at the top, and we have names of columns to place
                ax.set_xlabel(names[fcol], rotation = 45, fontsize = label_fontsize, va = "bottom")
                ax.xaxis.set_label_coords(0.5, 3.4)
                ax.xaxis.set_label_position("top")

            if fcol == 0 and names is not None: #We're on the left, and we have names of rows to place
                ax.set_ylabel(names[frow], rotation = 30, ha = "right", fontsize = label_fontsize)
            ax.legend()
            labels = ax.get_xticklabels() 
            for label in labels: 
                label.set_rotation(45) 
    if tight:
        fig.subplots_adjust(hspace = 0.001, wspace = 0.001)

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
        toDel = ["naics", "avg_weekday_min", "var", "spectral_power", "num_missing", "total"]
        for d in toDel:
            if d in agg:
                print "removing", d
                del agg[d]
            else:
                print d, "not found"

        dat, names = from_agg_report_to_mat(agg)
        
        qdump(((dat, names), "A tuple (dat, names) from the agg report"), "agg_mat.pkl")
        exit()

    big = True# False
    add_str = ""
    add_str = "_small"
    if big:
        target = None
        t, desc = qload("agg_mat" + add_str + ".pkl")
        dat, names = t
        classes, desc = qload("naics_codes" + add_str + ".pkl")
        counts = Counter(classes)
        print "\n"
        print classes
        classes = np.array([c if counts[c] >= 0 else '9999' for c in classes])
        print classes
        color_map = {}
        #dat = dat[np.logical_and(classes != 9999, classes != 0)]
        dat = dat[classes != "Unknown"]
        classes = np.array(classes)
        #classes= classes[np.logical_and(classes != 9999, classes != 0)]
        classes = classes[classes != "Unknown"]
        print classes, "---"
        unique_classes = set(list(classes))
        color_map = {}
        i = 0
        mycolors = "bgrcmyk"
        print unique_classes
        for c in unique_classes:
            thecolor = mycolors[i % 7]
            color_map[c] = thecolor
            i += 1
            
        figsize = (40, 40)
        class_names = None
    else:
        dat, names, classes, color_map, class_names = get_dummy_data()
        target = dict(Glory = 1.4, Teamwork = 2.3, Confidence = 4.2, Procastination = 2.0)
        figsize = (10, 10)

    fig = plt.figure(figsize = figsize)
    zoom = 100
    tight = False# True
    print dat
    make_scatter_mat_fig(fig, dat, classes = classes, names = names, color_map = color_map, target = target, class_names = class_names, zoom = zoom, tight = tight)
    print target
    print color_map
    sys.stdout.flush()
    if big:
        plt.savefig(fig_loc + "agg_no9999_zoom" + str(zoom) + ("tight" if tight else "") + add_str + ".png", bbox_inches='tight', dpi = 200)
        #plt.savefig("agg.pdf", bbox_inches='tight')

        #plt.show()
    else:
        plt.show()
        

