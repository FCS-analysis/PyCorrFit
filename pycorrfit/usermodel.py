# -*- coding: utf-8 -*-
"""
PyCorrFit

Module: user model:
When the user wants to use his own functions.
We are using sympy as function parser instead of writing our own,
which might be safer.
We only parse the function with sympy and test it once during
import. After that, the function is evaluated using eval()!
"""

import codecs
import numpy as np
import scipy.special as sps
import sys
import warnings
try:
    import sympy
    import sympy.functions
    from sympy.core import S
    from sympy.core.function import Function
    from sympy import sympify
except ImportError:
    warnings.warn("Importing sympy failed."+\
                  " Reason: {}.".format(sys.exc_info()[1].message))
    # Define Function, so PyCorrFit will start, even if sympy is not there.
    # wixi needs Function.
    Function = object
import wx

from . import models as mdls


class CorrFunc(object):
    """
        Check the input code of a proposed user model function and
        return a function for fitting via GetFunction.
    """
    def __init__(self, labels, values, substitutes, funcstring):
        self.values = values
        # a --> a
        # b [ms] --> b
        self.variables = list()
        for item in labels:
            self.variables.append(item.split(" ")[0].strip())
        self.funcstring = funcstring
        for key in substitutes.keys():
            # Don't forget to insert the "(" and ")"'s
            self.funcstring = self.funcstring.replace(key, 
                                                       "("+substitutes[key]+")")
            for otherkey in substitutes.keys():
                substitutes[otherkey] = substitutes[otherkey].replace(key, 
                                                       "("+substitutes[key]+")")
        # Convert the function string to a simpification object
        self.simpification = sympify(self.funcstring, sympyfuncdict)
        self.simstring = str(self.simpification)
        self.vardict = evalfuncdict


    def GetFunction(self):
        # Define the function that will be calculated later
        def G(parms, tau):
            tau = np.atleast_1d(tau)
            for i in np.arange(len(parms)):
                self.vardict[self.variables[i]] = float(parms[i])
            self.vardict["tau"] = tau
            # Function called with array/list
            # The problem here might be 
            #for key in vardict.keys():
            #    symstring = symstring.replace(key, str(vardict[key]))
            #symstring = symstring.replace("####", "tau")
            g = eval(self.funcstring, self.vardict)
            ## This would be a safer way to do this, but it is too slow!
            # Once simpy supports arrays, we can use these.
            #
            # g = np.zeros(len(tau))
            # for i in np.arange(len(tau)):
            # vardict["tau"] = tau[i]
            # g[i] = simpification.evalf(subs=vardict)
            return g
        return G


    def TestFunction(self):
        """ Test the function for parsibility with the given parameters.
        """
        vardict = dict()
        for i in np.arange(len(self.variables)):
            vardict[self.variables[i]] = sympify(float(self.values[i]))
        for tau in np.linspace(0.0001, 10000, 10):
            vardict["tau"] = tau
            Number = self.simpification.evalf(subs=vardict)
            if Number.is_Number is False:
                raise SyntaxError("Function could not be parsed!")


class UserModel(object):
    """ Class for importing txt files as models into PyCorrFit.
    """
    def __init__(self, parent):
        " Define all important constants and variables. "
        # Current ID is the last model ID we gave away.
        # This will be set using self.SetCurrentID
        self.CurrentID = None
        # The file to be opened. This is a full path like
        # os.path.join(dirname, filename)
        self.filename = None
        # Imported models
        # Modelarray = [model1, model2]
        self.modelarray = []
        # String that contains the executable code
        self.modelcode = None
        # Parent is main PyCorrFit program
        self.parent = parent
        # The string that identifies the user model menu
        self.UserStr="User"


    def GetCode(self, filename=None):
        """ Get the executable code from the file.
            Optional argument filename may be used. If not self.filename will
            be used.
            This automatically sets self.filename
        """
        if filename is not None:
            self.filename = filename
        openedfile = open(self.filename, 'r')
        code = openedfile.readlines()
        # File should start with a comment #.
        # Remove everything before that comment (BOM).
        startfile = code[0].find("#")
        if startfile != -1:
            code[0] = code[0][startfile:]
        else:
            code[0] = "# "+code[0]
        # Returncode: True if model was imported, False if there was a problem.
        # See ModelImported in class CorrFunc
        self.AddModel(code)
        openedfile.close()


    def AddModel(self, code):
        """ *code* is a list with strings
             each string is one line.
        """
        # a = 1
        # b [ms] = 2.5
        # gAlt = 1+tau/b
        # gProd = a*b
        # G = 1/gA * gB
        labels = list()
        values = list()
        substitutes = dict()
        for line in code:
            # We deal with comments and empty lines
            # We need to check line length first and then we look for
            # a hash.
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                var, val = line.split("=")
                var = var.strip()
                if var == "G":
                    # Create a fuction that calculates G
                    funcstring = val.strip()
                    self.FuncClass = CorrFunc(labels, values, substitutes,
                                              funcstring)
                    func = self.FuncClass.GetFunction()
                    doc = code[0].strip()
                    # Add whitespaces in model string (looks nicer)
                    for olin in code[1:]:
                        doc = doc + "\n       "+olin.strip()
                    func.func_doc = codecs.decode(doc, "utf-8")
                elif var[0] == "g":
                    substitutes[var] = val.strip()
                else:
                    # Add value and variable to our lists
                    labels.append(codecs.decode(var, "utf-8"))
                    values.append(float(val))
        # Active Parameters we are using for the fitting
        # [0] labels
        # [1] values
        # [2] bool values to fit
        bools = list([False]*len(values))
        bools[0] = True
        # Create Modelarray
        active_parms = [ labels, values, bools ]
        self.SetCurrentID()
        Modelname = code[0][1:].strip()
        definitions = [self.CurrentID, Modelname, Modelname, func]
        model = dict()
        model["Parameters"] = active_parms
        model["Definitions"] = definitions
        self.modelarray.append(model)


    def ImportModel(self):
        """ Do everything that is necessarry to import the models into
            PyCorrFit.
        """
        # Set the model ids of the new model(s)
        # Normally, there is only one model.
        for i in np.arange(len(self.modelarray)):
            self.SetCurrentID()
            self.modelarray[i]["Definitions"][0] = self.CurrentID
        # We assume that the models have the correct ID for now
        mdls.AppendNewModel(self.modelarray)
        # Set variables and models
        # Is this still necessary? - We are doing this for compatibility!
        self.parent.value_set = mdls.values
        self.parent.valuedict = mdls.valuedict
        self.parent.models = mdls.models
        self.parent.modeldict = mdls.modeldict
        self.parent.modeltypes = mdls.modeltypes
        # Get menu
        menu = self.parent.modelmenudict[self.UserStr]
        # Add menu entrys
        for item in self.modelarray:
            # Get definitions
            Defs = item["Definitions"]
            # This is important if we want to save the session with
            # the imported model.
            mdls.modeltypes[self.UserStr].append(Defs[0])
            menuentry = menu.Append(Defs[0], Defs[1], Defs[2])
            self.parent.Bind(wx.EVT_MENU, self.parent.add_fitting_tab,
                             menuentry)


    def TestFunction(self):
        """ Convenience function to test self.FuncClass """
        self.FuncClass.TestFunction()


    def SetCurrentID(self):
        # Check last item or so of modelarray
        # Imported functions get IDs starting from 7000
        theID = 7000
        for model in mdls.models:
            theID = max(theID, model[0])
        self.CurrentID = theID + 1


class wixi(Function):
    """
        This is a ghetto solution for using wofz in sympy.
        It only returns the real part of the function.
        I am not sure, if the eval's are placed correctly.
        I only made it work for my needs. This might be wrong!
        For true use of wofz, I am not using sympy, anyhow.
    """
    nargs = 1
    is_real = True
    @classmethod
    def eval(self, arg):
        return None

    def as_base_exp(self):
        return self, S.One  # @UndefinedVariable

    def _eval_evalf(self, prec):
        result = sps.wofz(1j*float(self.args[0]))
        return sympy.numbers.Number(sympy.functions.re(result))


def evalwixi(x):
    """ Complex Error Function (Faddeeva/Voigt).
        w(i*x) = exp(x**2) * ( 1-erf(x) )
        This function is called by other functions within this module.
        We are using the scipy.special.wofz module which calculates
        w(z) = exp(-z**2) * ( 1-erf(-iz) )
        z = i*x
    """
    z = x*1j
    result = sps.wofz(z)
    # We should have a real solution. Make sure nobody complains about
    # some zero-value imaginary numbers.
    return np.real_if_close(result)



sympyfuncdict = dict()
sympyfuncdict["wixi"] = wixi

evalfuncdict = dict()
evalfuncdict["wixi"] = evalwixi
evalfuncdict["I"] = 1j

scipyfuncs = ['wofz', 'erf', 'erfc']
numpyfuncs = ['abs', 'arccos', 'arcsin', 'arctan', 'arctan2', 'ceil', 'cos',
              'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp',
              'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'power',
              'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']

for func in scipyfuncs:
    evalfuncdict[func] = eval("sps."+func)

for func in numpyfuncs:
    evalfuncdict[func] = eval("np."+func)


