# -*- coding: utf-8 -*-
""" PyCorrFit

    Module plotting
    Everything about plotting with matplotlib is located here.
    Be sure to install texlive-science and texlive-math-extra

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
    
    Copyright (C) 2011-2012  Paul Müller

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License 
    along with this program. If not, see <http://www.gnu.org/licenses/>.
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
    decchar = codecs.decode(char, "UTF-8")
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
    string = codecs.decode(string, "UTF-8")
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
    string = codecs.decode(string, "UTF-8")
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
    items = string.split(" ", 1)
    a = items[0]
    if len(items) > 1:
        b = items[1]
    else:
        b = ""
    anew = r""
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
    # As of version 0.7.8 the user may export data normalized to a certain
    # parameter.
    if Page.dataexp is not None:
        dataexp = 1*Page.dataexp
        resid = 1*Page.resid
        dataexp[:,1] *= Page.normfactor
        resid[:,1] *= Page.normfactor
    else:
        dataexp = Page.dataexp
        resid = Page.resid
    fit = 1*Page.datacorr
    fit[:,1] *= Page.normfactor
    weights = Page.weights_plot_fill_area
    tabtitle = Page.tabtitle.GetValue()
    #fitlabel = ur"Fit model: "+str(mdls.modeldict[Page.modelid][0])
    fitlabel = Page.modelname
    labelweights = ur"Weights of fit"
    labels, parms = mdls.GetHumanReadableParms(Page.modelid,
                                               Page.active_parms[1])
    ## According to issue #54, we remove fitting errors from plots
    ## Error parameters with nice look
    #errparmsblank = Page.parmoptim_error
    #if errparmsblank is None:
    #    errparms = None
    #else:
    #    errparms = dict()
    #    for key in errparmsblank.keys():
    #        newkey, newparm = mdls.GetHumanReadableParameterDict(Page.modelid,
    #                                                    key, errparmsblank[key])
    #        errparms[newkey] = newparm
    #parmids = np.where(Page.active_parms[2])[0]
    #labels = np.array(labels)[parmids]
    #parms = np.array(parms)[parmids]
    if dataexp is None:
        if tabtitle.strip() == "":
            fitlabel = Page.modelname
        else:
            fitlabel = tabtitle
    else:
        if tabtitle.strip() == "":
            tabtitle = "page"+str(Page.counter).strip().strip(":")
    if Page.normparm is not None:
        fitlabel += ur", normalized to "+Page.active_parms[0][Page.normparm]

    ## Check if we can use latex for plotting:
    (r1, path) = findprogram("latex")
    (r2, path) = findprogram("dvipng")
    # Ghostscript
    (r31, path) = findprogram("gs")
    (r32, path) = findprogram("mgs") # from miktex
    r3 = max(r31,r32)
    if r1+r2+r3 < 3:
        uselatex = False
    if uselatex == True:
        rcParams['text.usetex']=True
        rcParams['text.latex.unicode']=True
        rcParams['font.family']='serif'
        rcParams['text.latex.preamble']=[r"""\usepackage{amsmath}
                                            \usepackage[utf8x]{inputenc}
                                            \usepackage{amssymb}"""] 
        fitlabel = ur"{\normalsize "+escapechars(fitlabel)+r"}"
        tabtitle = ur"{\normalsize "+escapechars(tabtitle)+r"}"
        labelweights = ur"{\normalsize "+escapechars(labelweights)+r"}"
    else:
        rcParams['text.usetex']=False
    # create plot
    # plt.plot(x, y, '.', label = 'original data', markersize=5)
    fig=plt.figure()
    if resid is not None:
        gs = gridspec.GridSpec(2, 1, height_ratios=[5,1])
        ax = plt.subplot(gs[0])
    else:
        ax = plt.subplot(111)
        #    ax = plt.axes()
    ax.semilogx()
    if dataexp is not None:
        plt.plot(dataexp[:,0], dataexp[:,1], '-', color="darkgrey",
                 label=tabtitle)
    else:
        plt.xlabel(r'lag time $\tau$ [ms]')
    # Plotting with error bars is very ugly if you have a lot of
    # data points.
    # We will use fill_between instead.
    #plt.errorbar(fit[:,0], fit[:,1], yerr=weights, fmt='-',
    #             label = fitlabel, lw=2.5, color="blue")
    plt.plot(fit[:,0], fit[:,1], '-', label = fitlabel, lw=2.5,
             color="blue")    
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
            text += r' {} &= {:.3g} \\'.format(latexmath(labels[i]), parms[i])
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
            text += "{} = {:.3g}\n".format(labels[i], parms[i])
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
        if Page.weighted_fit_was_performed:
            if uselatex == True:
                lb = r"\newline \indent "
            else:
                lb = "\n"
            yLabelRes = "weighted "+ lb +"residuals"
        else:
            yLabelRes = "residuals"
        plt.plot(resid[:,0], resid[:,1], '-', color="darkgrey", label=yLabelRes)
        plt.xlabel(r'lag time $\tau$ [ms]')
        plt.ylabel(yLabelRes, multialignment='center')
        minx = np.min(resid[:,0])
        maxx = np.max(resid[:,0])
        miny = np.min(resid[:,1])
        maxy = np.max(resid[:,1])
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
    fig.canvas.HACK_append = ""
    

    # Legend outside of plot
    # Decrease size of plot to fit legend
    box = ax.get_position()
    box2 = ax2.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.2,
                     box.width, box.height * 0.9])
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
    if Page.trace is not None:
        # Set trace
        traces = [Page.trace]
        labels = ["{} ({:.2f} kHz)".format(tabtitle, np.average(traces[0][:,1]))]
    elif Page.tracecc is not None:
        # We have some cross-correlation here. Two traces.
        traces = Page.tracecc
        labels = ["{} A ({:.4g} kHz)".format(tabtitle, np.average(traces[0][:,1])),
                  "{} B ({:.4g} kHz)".format(tabtitle, np.average(traces[1][:,1]))]
    else:
        return
    ## Check if we can use latex for plotting:
    (r1, path) = findprogram("latex")
    (r2, path) = findprogram("dvipng")
    # Ghostscript
    (r31, path) = findprogram("gs")
    (r32, path) = findprogram("mgs") # from miktex
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
    fig=plt.figure()
    ax = plt.subplot(111)
    for i in np.arange(len(traces)):
        # Columns
        time = traces[i][:,0]*timefactor
        intensity = traces[i][:,1]
        plt.plot(time, intensity, '-', 
                 label = labels[i],
                 lw=1)
                 
    plt.ylabel('count rate [kHz]')
    plt.xlabel('time [s]')
    
    # Legend outside of plot
    # Decrease size of plot to fit legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.2,
                     box.width, box.height * 0.9])
    plt.legend(loc='upper center', 
               bbox_to_anchor=(0.5, -0.15),
               prop={'size':9})
    
    ## Hack
    # We need this for hacking. See edclasses.
    fig.canvas.HACK_parent = parent
    fig.canvas.HACK_fig = fig
    fig.canvas.HACK_Page = Page
    fig.canvas.HACK_append = "_trace"

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


def savePlotSingle(name, x, dataexp, datafit, dirname = ".", uselatex=False):
    """ CURRENTLY THIS FUNCTION IS NOT USED BY PYCORRFIT
        Show log plot of correlation function without residuals. 
        Parameters:
        *name*      name of curve in legend
        *x*         tau-values to plot
        *dataexp*   correlation data to plot
        *datafit*   fitted curve to correlation data
        *dirname*   initial directory for dialog (not used here)
        *uselatex*  use latex for plotting
        This function uses a hack in misc.py to change the function
        for saving the final figure. We wanted save in the same directory
        as PyCorrFit was working and the filename should be the tabtitle.
    """
    # This is a dirty hack to make sure no plots are opened
    try:
        plt.close()
    except:
        pass
    ## Check if we can use latex for plotting:
    (r1, path) = findprogram("latex")
    (r2, path) = findprogram("dvipng")
    # Ghostscript
    (r31, path) = findprogram("gs")
    (r32, path) = findprogram("mgs") # from miktex
    r3 = max(r31,r32)
    if r1+r2+r3 < 3:
        uselatex = False
    if uselatex == True:
        rcParams['text.usetex']=True
        rcParams['text.latex.unicode']=True
        rcParams['font.family']='serif'
        rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"] 
        name = ur"{\normalsize "+escapechars(name)+r"}"
    else:
        rcParams['text.usetex']=False
    # create plot
    # plt.plot(x, y, '.', label = 'original data', markersize=5)
    plt.figure()
    ax = plt.subplot(111)
    #    ax = plt.axes()
    ax.semilogx()
    plt.plot(x, dataexp,'-', color="darkgrey")
    plt.xlabel(r'lag time $\tau$ [ms]')
    plt.plot(x, datafit, '-', label = name,
             lw=2.5, color="blue")
    plt.ylabel('correlation')
    mind = np.min([ dataexp, datafit])
    maxd = np.max([ dataexp, datafit])
    ymin = mind - (maxd - mind)/20.
    ymax = maxd + (maxd - mind)/20.
    ax.set_ylim(bottom=ymin, top=ymax)
    xmin = np.min(x)
    xmax = np.max(x)
    ax.set_xlim(xmin, xmax)
    # Add some more stuff to the text and append data to a .txt file
    #text = Auswert(parmname, parmoptim, text, savename)
    plt.legend()
    plt.show()
