# -*- coding: utf-8 -*-
"""
PyCorrFit

Module plotting
Everything about plotting with matplotlib is located here.
Be sure to install texlive-science and texlive-math-extra
"""


import codecs
import numpy as np
import matplotlib
# We do catch warnings about performing this before matplotlib.backends stuff
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    matplotlib.use('WXAgg') # Tells matplotlib to use WxWidgets for dialogs
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
# Text rendering with matplotlib
from matplotlib import rcParams
import unicodedata

# For finding latex tools
from .misc import findprogram
from . import models as mdls


def greek2tex(char):
    """ Converts greek UTF-8 letters to latex """
    #decchar = codecs.decode(char, "UTF-8")
    decchar = char
    repres = unicodedata.name(decchar).split(" ")
    # GREEK SMALL LETTER ALPHA
    if repres[0] == "GREEK" and len(repres) == 4:
        letter = repres[3].lower()
        if repres[1] != "SMALL":
            letter = letter[0].capitalize() + letter[1:]
        return "\\"+letter
    else:
        return char


def escapechars(string):
    """ For latex output, some characters have to be escaped with a "\\" """
    #string = codecs.decode(string, "UTF-8")
    escapechars = ["#", "$", "%", "&", "~", "_", "\\", "{", "}"] 
    retstr = ur""
    for char in string:
        if char in escapechars:
            retstr += "\\"
            retstr += char
        elif char == "^":
            # Make a hat in latex without $$?
            retstr += "$\widehat{~}$"
        else:
            retstr += char
    return retstr


def latexmath(string):
    """ Format given parameters to nice latex. """
    if string == "offset":
        # prohibit the very often "offset" to be displayed as variables
        return r"\mathrm{offset}"
    elif string == "SP":
        return r"\mathrm{SP}"
    #string = codecs.decode(string, "UTF-8")
    unicodechars = dict()
    #unicodechars[codecs.decode("τ", "UTF-8")] = r"\tau"
    #unicodechars[codecs.decode("µ", "UTF-8")] = r"\mu"
    unicodechars[codecs.decode("²", "UTF-8")] = r"^2"
    unicodechars[codecs.decode("³", "UTF-8")] = r"^3"
    unicodechars[codecs.decode("₁", "UTF-8")] = r"_1"
    unicodechars[codecs.decode("₂", "UTF-8")] = r"_2"
    unicodechars[codecs.decode("₀", "UTF-8")] = r"_0"
    #unicodechars[codecs.decode("α", "UTF-8")] = r"\alpha"
    # We need lambda in here, because unicode names it lamda sometimes.
    unicodechars[codecs.decode("λ", "UTF-8")] = r"\lambda"
    #unicodechars[codecs.decode("η", "UTF-8")] = r'\eta'
    unitchars = dict()
    unitchars[codecs.decode("µ", "UTF-8")] = r"\micro "
    items = string.split(" ", 1)
    a = items[0]
    if len(items) > 1:
        b = items[1]
        if b.count(u"µ"):
            # Use siunitx with the upright µ
            bnew = ur"[\SI{}{"
            for char in b.strip("[]"):
                if char in unitchars.keys():
                    bnew += unitchars[char]
                else:
                    bnew += char
            b = bnew+ur"}]"
    else:
        b = ""
    anew = ur""
    for char in a:
        if char in unicodechars.keys():
            anew += unicodechars[char]
        elif char != greek2tex(char):
            anew += greek2tex(char)
        else:
            anew += char
    # lower case
    lcitems = anew.split("_",1)
    if len(lcitems) > 1:
        anew = lcitems[0]+"_{\\text{"+lcitems[1]+"}}"
    return anew + r" \hspace{0.3em} \mathrm{"+b+r"}"


def savePlotCorrelation(parent, dirname, Page, uselatex=False,
                        verbose=False, show_weights=True):
    """ Save plot from Page into file        
        Parameters:
        *parent*    the parent window
        *dirname*   directory to set on saving
        *Page*      Page containing all variables
        *uselatex*  Whether to use latex for the ploting or not.
        This function uses a hack in misc.py to change the function
        for saving the final figure. We wanted save in the same directory
        as PyCorrFit was working and the filename should be the tabtitle.
    """
    # Close all other plots before commencing
    try:
        plt.close()
    except:
        pass
    # get data
    corr = Page.corr
    dataexp = corr.correlation_plot
    resid = corr.residuals_plot
    fit = corr.modeled_plot

    weights = Page.weights_plot_fill_area
    tabtitle = Page.tabtitle.GetValue()
    #fitlabel = ur"Fit model: "+str(mdls.modeldict[Page.modelid][0])
    fitlabel = Page.corr.fit_model.name
    labelweights = ur"Weights of fit"
    labels, parms = mdls.GetHumanReadableParms(Page.modelid,
                                               corr.fit_parameters)
    if dataexp is None:
        if tabtitle.strip() == "":
            fitlabel = Page.corr.fit_model.name
        else:
            fitlabel = tabtitle
    else:
        if tabtitle.strip() == "":
            tabtitle = "page"+str(Page.counter).strip().strip(":")
    if Page.corr.normparm is not None:
        fitlabel += ur", normalized to "+Page.corr.fit_model.parameters[0][Page.corr.normparm]

    ## Check if we can use latex for plotting:
    r1 = findprogram("latex")[0]
    r2 = findprogram("dvipng")[0]
    # Ghostscript
    r31 = findprogram("gs")[0]
    r32 = findprogram("mgs")[0] # from miktex
    r3 = max(r31,r32)
    if r1+r2+r3 < 3:
        uselatex = False
    if uselatex == True:
        rcParams['text.usetex']=True
        rcParams['text.latex.unicode']=True
        rcParams['font.family']='serif'
        rcParams['text.latex.preamble']=[r"""\usepackage{amsmath}
                                            \usepackage[utf8x]{inputenc}
                                            \usepackage{amssymb}
                                            \usepackage{siunitx}"""] 
        fitlabel = ur"{\normalsize "+escapechars(fitlabel)+r"}"
        tabtitle = ur"{\normalsize "+escapechars(tabtitle)+r"}"
        labelweights = ur"{\normalsize "+escapechars(labelweights)+r"}"
    else:
        rcParams['text.usetex']=False
    # create plot
    # plt.plot(x, y, '.', label = 'original data', markersize=5)
    fig=plt.figure()
    fig.canvas.set_window_title("Correlation - "+Page.title)
    if resid is not None:
        gs = gridspec.GridSpec(2, 1, height_ratios=[5,1])
        ax = plt.subplot(gs[0])
    else:
        ax = plt.subplot(111)
        #    ax = plt.axes()
    ax.semilogx()
    # plot fit first
    plt.plot(fit[:,0], fit[:,1], '-', label=fitlabel, lw=1.5,
             color="blue")
    if dataexp is not None:
        plt.plot(dataexp[:,0], dataexp[:,1], '-', color="black",
                 alpha=.7, label=tabtitle, lw=1)
    else:
        plt.xlabel(ur'lag time $\tau$ [ms]')
    
    if weights is not None and show_weights is True:
        plt.fill_between(weights[0][:,0],weights[0][:,1],weights[1][:,1],
                         color='cyan')
        # fake legend:
        p = plt.Rectangle((0, 0), 0, 0, color='cyan',
                          label=labelweights)
        ax.add_patch(p)
    plt.ylabel('correlation')
    if dataexp is not None:
        mind = np.min([ dataexp[:,1], fit[:,1]])
        maxd = np.max([ dataexp[:,1], fit[:,1]])
    else:
        mind = np.min(fit[:,1])
        maxd = np.max(fit[:,1])
    ymin = mind - (maxd - mind)/20.
    ymax = maxd + (maxd - mind)/20.
    ax.set_ylim(bottom=ymin, top=ymax)
    xmin = np.min(fit[:,0])
    xmax = np.max(fit[:,0])
    ax.set_xlim(xmin, xmax)
    # Add some nice text:
    if uselatex == True and len(parms) != 0:
        text = r""
        text += r'\['            #every line is a separate raw string...
        text += r'\begin{split}' # ...but they are all concatenated
        #                          by the interpreter :-)
        for i in np.arange(len(parms)):
            text += ur' {} &= {:.3g} \\'.format(latexmath(labels[i]), parms[i])
        ## According to issue #54, we remove fitting errors from plots
        #if errparms is not None:
        #    keys = errparms.keys()
        #    keys.sort()
        #    for key in keys:
        #        text += r' \Delta '+latexmath(key)+r" &= " + str(errparms[key]) +r' \\ '
        text += r' \end{split} '
        text += r' \] '
    else:
        text = ur""
        for i in np.arange(len(parms)):
            text += u"{} = {:.3g}\n".format(labels[i], parms[i])
        ## According to issue #54, we remove fitting errors from plots
        #if errparms is not None:
        #    keys = errparms.keys()
        #    keys.sort()
        #    for key in keys:
        #        text += "Err "+key+" = " + str(errparms[key]) +"\n"



    logmax = np.log10(xmax)
    logmin = np.log10(xmin)
    logtext = 0.6*(logmax-logmin)+logmin
    xt = 10**(logtext)
    yt = 0.3*ymax
    plt.text(xt,yt,text, size=12)
    if resid is not None:
        ax2 = plt.subplot(gs[1])
        #ax2 = plt.axes()
        ax2.semilogx()
        if Page.corr.is_weighted_fit:
            if uselatex == True:
                lb = r"\newline \indent "
            else:
                lb = "\n"
            yLabelRes = "weighted "+ lb +"residuals"
        else:
            yLabelRes = "residuals"
        minx = np.min(resid[:,0])
        maxx = np.max(resid[:,0])
        miny = np.min(resid[:,1])
        maxy = np.max(resid[:,1])
        plt.hlines(0, minx, maxx, colors="orange")
        plt.plot(resid[:,0], resid[:,1], '-', color="black",
                 alpha=.85, label=yLabelRes, lw=1)
        plt.xlabel(r'lag time $\tau$ [ms]')
        plt.ylabel(yLabelRes, multialignment='center')

        ax2.set_xlim(minx, maxx)
        maxy = max(abs(maxy), abs(miny))
        ax2.set_ylim(-maxy, maxy)
        ticks = ax2.get_yticks()
        ax2.set_yticks([ticks[0], ticks[-1], 0])
    ## Hack
    # We need this for hacking. See edclasses.
    fig.canvas.HACK_parent = parent
    fig.canvas.HACK_fig = fig
    fig.canvas.HACK_Page = Page
    fig.canvas.HACK_append = ".png"
    

    # Legend outside of plot
    # Decrease size of plot to fit legend
    box = ax.get_position()
    
    ax.set_position([box.x0, box.y0 + box.height * 0.2,
                     box.width, box.height * 0.9])
    
    if resid is not None:
        box2 = ax2.get_position()
        ax2.set_position([box2.x0, box2.y0 + box.height * 0.2,
                     box2.width, box2.height])
    
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.55),
              prop={'size':9})
    
    
    if verbose == True:
        plt.show()
    else:
        # If WXAgg is not used for some reason, then our hack does not work
        # and we must use e.g. TkAgg
        try:
            fig.canvas.toolbar.save()
        except AttributeError:
            fig.canvas.toolbar.save_figure()
        # Close all other plots before commencing
        try:
            plt.close()
        except:
            pass


def savePlotTrace(parent, dirname, Page, uselatex=False, verbose=False):
    """ Save trace plot from Page into file        
        Parameters:
        *parent*    the parent window
        *dirname*   directory to set on saving
        *Page*      Page containing all variables
        *uselatex*  Whether to use latex for the ploting or not.
        This function uses a hack in misc.py to change the function
        for saving the final figure. We wanted save in the same directory
        as PyCorrFit was working and the filename should be the tabtitle.
    """
    # Close all other plots before commencing
    try:
        plt.close()
    except:
        pass
    # Trace must be displayed in s
    timefactor = 1e-3
    tabtitle = Page.tabtitle.GetValue()
    if tabtitle.strip() == "":
        tabtitle = "page"+str(Page.counter).strip().strip(":")
    # Intensity trace in kHz may stay the same
    if len(Page.corr.traces) == 0:
        return
    
    traces = Page.corr.traces
    labels = list()
    for ii, tr in enumerate(traces):
        labels.append("Channel {}: {}".format(ii+1, tr.name))

    ## Check if we can use latex for plotting:
    r1 = findprogram("latex")[0]
    r2 = findprogram("dvipng")[0]
    # Ghostscript
    r31 = findprogram("gs")[0]
    r32 = findprogram("mgs")[0]
    r3 = max(r31,r32)
    if r1+r2+r3 < 3:
        uselatex = False
    if uselatex == True:
        rcParams['text.usetex']=True
        rcParams['text.latex.unicode']=True
        rcParams['font.family']='serif'
        rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"] 
        for i in np.arange(len(labels)):
            labels[i] = ur"{\normalsize "+escapechars(labels[i])+r"}"
    else:
        rcParams['text.usetex']=False
    # create plot
    # plt.plot(x, y, '.', label = 'original data', markersize=5)
    fig=plt.figure(figsize=(10,3))
    fig.canvas.set_window_title("Trace - "+Page.title)
    ax = plt.subplot(111)
    for i in np.arange(len(traces)):
        # Columns
        time = traces[i][:,0]*timefactor
        intensity = traces[i][:,1]
        plt.plot(time, intensity, '-', 
                 label = labels[i],
                 lw=1)
    # set plot boundaries
    maxy = -np.infty
    miny = np.infty
    for tr in traces:
        maxy = max(np.max(tr[:,1]), maxy)
        miny = min(np.min(tr[:,1]), miny)
    ax.set_ylim(miny, maxy)

    plt.ylabel('count rate [kHz]')
    plt.xlabel('time [s]')
    
    # Legend outside of plot
    # Decrease size of plot to fit legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.2,
                     box.width, box.height * 0.9])
    plt.legend(loc='upper center', 
               bbox_to_anchor=(0.5, -0.35),
               prop={'size':9},
               )
    
    ## Hack
    # We need this for hacking. See edclasses.
    fig.canvas.HACK_parent = parent
    fig.canvas.HACK_fig = fig
    fig.canvas.HACK_Page = Page
    fig.canvas.HACK_append = "_trace.png"

    plt.tight_layout(rect=(.001,.34,.999,1.0))

    if verbose == True:
        plt.show()
    else:
        # If WXAgg is not used for some reason, then our hack does not work
        # and we must use e.g. TkAgg
        try:
            fig.canvas.toolbar.save()
        except AttributeError:
            fig.canvas.toolbar.save_figure()
        # Close all other plots before commencing
        try:
            plt.close()
        except:
            pass

# set dpi to 300
matplotlib.rcParams['savefig.dpi'] = 300