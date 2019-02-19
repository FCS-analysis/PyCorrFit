""" pycorrfit.models.control

Controls which fitting models are imported an in which order.
"""
import numpy as np

from .classes import Model


def append_model(modelarray):
    """ Append a new model from a modelarray. *Modelarray* has to be a list
        whose elements have two items:
        [0] parameters
        [1] some info about the model
        See separate models for more information
    """
    global values
    global valuedict
    global models
    global modeldict
    global supplement
    global boundaries
    global modeltypes

    if not isinstance(modelarray, list):
        modelarray = [modelarray]

    for datadict in modelarray:
        # We can have many models in one model array
        amod = Model(datadict)

        models.append(amod)
        if amod.id in modeldict:
            raise ValueError("Model with same is already exists: \n {} vs. {}".
                             format(amod, modeldict[amod.id]))
        modeldict[amod.id] = amod

        values.append(amod.parameters)
        valuedict[amod.id] = amod.parameters

        # Supplementary Data might be there
        supplement[amod.id] = amod.func_supplements

        # Check functions - check for correct values
        boundaries[amod.id] = amod.boundaries

        # Add model type to internal type list.
        if amod.type is not None:
            if not amod.type in modeltypes:
                modeltypes[amod.type] = []
            modeltypes[amod.type].append(amod.id)


def model_setup(modelid, name, comp, mtype, fctn, par_labels, par_values,
                par_vary=None, par_boundaries=None, par_constraints=None,
                par_hr_labels=None, par_hr_factors=None,
                supplementary_method=None,
                ):
    u"""
    This helper method does everything that is required to make a model
    available for PyCorrFit. The idea is that this method can be called from
    anywhere and thus we do not need to do the tedious work of adding models
    in the __init__.py file.

    Parameters
    ----------
    modelid : int
        Model identifier.
    name : str
        Name of the Model.
    comp : str
        Description of components of the model, e.g. "T+3D+2D"
    mtype : str
        Type of model, e.g. "Confocal (Gaussian)"
    fctn : callable
        The method that computes the model function. It must take
        two arguments. The first is of shape `par_values` and the
        second is a 2D array containing lag time and correlation.
    par_labels : list-like, strings
        The labels of each parameter in PyCorrFit dimensionless
        representation, i.e.

            unit of time        : 1 ms
            unit of inverse time: 1000 /s
            unit of distance    : 100 nm
            unit of Diff.coeff  : 10 µm²/s
            unit of inverse area: 100 /µm²
            unit of inv. volume : 1000 /µm³
    par_values : list-like, floats
        The parameter values in PyCorrFit dimensionless units.
    par_vary :  list-like, bools or None
        A list describing which parameters should be varied during
        fitting. If not given, only the first element is set to `True`.
    par_boundaries : list-like, floats
        The parameter boundaries - two values for each parameter.
        Examples: [[0, np.inf], [0,1]]
    par_constraints : list of lists
        Constraints between parameters. For example, make sure parameter
        2 is always larger than parameter 1 and parameter 5 is always
        smaller than parameter 1: [[2, ">", 1], [5, "<", 1]]
        Parameter count starts at 0.
    par_hr_labels : list-like, strings
        User-defined human readable labels of the parameters. If this is
        set, `par_hr_factors` is also required.
    par_hr_factors : list-like, floats
        The multiplicative factors to get from `par_labels` to
        `par_hr_labels`.
    supplementary_method : callable
        A method that takes the parameters `par_values` and the countrate
        of the experiment as an argument and returns a dictinoary of
        supplementary information.
    """
    # Checks
    assert len(par_labels) == len(par_values)
    for p in [par_vary,
              par_boundaries,
              par_hr_labels,
              par_hr_factors,
              ]:
        if p is not None:
            assert len(p) == len(
                par_values), "Number of parameters must match!"

    if par_hr_factors is None or par_hr_labels is None:
        assert par_hr_factors is None, "human readable requires two parameter"
        assert par_hr_labels is None, "human readable requires two parameter"

    if par_vary is None:
        # Set par_vary
        par_vary = np.zeros(len(par_values), dtype=bool)
        par_vary[0] = True

    if par_hr_factors is None:
        # Set equal to labels
        par_hr_labels = par_labels
        par_hr_factors = np.ones_like(par_values)

    model = {}

    model["Parameters"] = [par_labels, par_values, par_vary,
                           par_hr_labels, par_hr_factors]

    model["Definitions"] = [modelid, comp, name, fctn, mtype]

    if supplementary_method is not None:
        model["Supplements"] = supplementary_method

    if par_boundaries is not None:
        model["Boundaries"] = par_boundaries

    if par_constraints is not None:
        model["Constraints"] = par_constraints

    append_model(model)


# Pack all variables
values = list()
# Also create a dictionary, key is modelid
valuedict = dict()
# Pack all models
models = list()
# Also create a dictinary
modeldict = dict()
# A dictionary for supplementary data:
supplement = dict()
# A dictionary containing model boundaries
boundaries = dict()

# shorttypes are used by the GUI to abbreviate the model type
shorttype = dict()
shorttype[u"Confocal (Gaussian)"] = u"CFoc"
shorttype[u"Confocal (Gaussian) and triplet"] = u"CFoc"
shorttype[u"Confocal (Gaussian) with double triplet"] = u"CFoc"
shorttype[u"TIR (Gaussian/Exp.)"] = u"TIR CFoc"
shorttype[u"TIR (□xσ/Exp.)"] = u"TIR □xσ"

# Create a list for the differentiation between the models
# This should make everything look a little cleaner
modeltypes = {}
modeltypes[u"User"] = []

# The order of the import matters!
# These models perform the integration by themselves using the `model_setup` method.
from . import model_confocal_3d
from . import model_confocal_3d_3d
from . import model_confocal_2d
from . import model_confocal_2d_2d
from . import model_confocal_3d_2d

from . import model_confocal_t_3d
from . import model_confocal_t_3d_3d
from . import model_confocal_t_2d
from . import model_confocal_t_2d_2d
from . import model_confocal_t_3d_2d
from . import model_confocal_t_3d_3d_3d
from . import model_confocal_t_3d_3d_2d

from . import model_confocal_tt_3d
from . import model_confocal_tt_3d_3d
from . import model_confocal_tt_2d
from . import model_confocal_tt_2d_2d
from . import model_confocal_tt_3d_2d

# These lines can be removed once all models are converted
# from `MODEL_*` to `model_` syntax.
modeltypes[u"TIR (Gaussian/Exp.)"] = [6014, 6034, 6033]
modeltypes[u"TIR (□xσ/Exp.)"] = [6010, 6023, 6000, 6022, 6020, 6021]

# Old models
from . import MODEL_TIRF_gaussian_1C
from . import MODEL_TIRF_gaussian_3D2D
from . import MODEL_TIRF_gaussian_3D3D
from . import MODEL_TIRF_1C
from . import MODEL_TIRF_2D2D
from . import MODEL_TIRF_3D2D
from . import MODEL_TIRF_3D3D
from . import MODEL_TIRF_3D2Dkin_Ries

# Load all models from the imported "MODEL_*" submodules
# These are the models that were not imported using the `model_setup` method.
for g in list(globals().keys()):
    if g.startswith("MODEL_") and hasattr(globals()[g], "Modelarray"):
        append_model(globals()[g].Modelarray)
