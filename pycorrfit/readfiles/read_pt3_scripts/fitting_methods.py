import numpy as np
import copy
"""FCS Bulk Correlation Software

    Copyright (C) 2015  Dominic Waithe

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""


def initialise_fcs(int_obj):
        # default options for the fitting.
    int_obj.def_options = {}

    int_obj.def_options['Diff_eq'] = 1
    int_obj.def_options['Diff_species'] = 1
    int_obj.def_options['Triplet_eq'] = 1
    int_obj.def_options['Triplet_species'] = 1

    int_obj.def_options['Dimen'] = 1

    A1 = {'alias': 'A1', 'value': 1.0, 'minv': 0.0, 'maxv': 1.0,
          'vary': False, 'to_show': True, 'stdev': False, 'calc': False}
    A2 = {'alias': 'A2', 'value': 1.0, 'minv': 0.0, 'maxv': 1.0,
          'vary': False, 'to_show': True, 'calc': False}
    A3 = {'alias': 'A3', 'value': 1.0, 'minv': 0.0, 'maxv': 1.0,
          'vary': False, 'to_show': True, 'calc': False}
    # The offset
    offset = {'alias': 'offset', 'value': 0.01, 'minv': -1.0,
              'maxv': 1.0, 'vary': True, 'to_show': True, 'calc': False}
    #int_obj.defin.add('offset', value=0.0, min=-1.0,max=5.0,vary=False)
    # The amplitude
    GN0 = {'alias': 'GN0', 'minv': 0.001, 'value': 1,
           'maxv': 1.0, 'vary': True, 'to_show': True, 'calc': False}
    #int_obj.def_param.add('GN0', value=1.0, vary=True)
    # The alpha value
    #int_obj.def_param.add('alpha', value=1.0, min=0,max=1.0, vary=True)
    # lateral diffusion coefficent
    txy1 = {'alias': 'txy1', 'value': 0.01, 'minv': 0.001,
            'maxv': 2000.0, 'vary': True, 'to_show': True, 'calc': False}
    txy2 = {'alias': 'txy2', 'value': 0.01, 'minv': 0.001,
            'maxv': 2000.0, 'vary': True, 'to_show': True, 'calc': False}
    txy3 = {'alias': 'txy3', 'value': 0.01, 'minv': 0.001,
            'maxv': 2000.0, 'vary': True, 'to_show': True, 'calc': False}

    alpha1 = {'alias': 'alpha1', 'value': 1.0, 'minv': 0.0,
              'maxv': 2.0, 'vary': True, 'to_show': True, 'calc': False}
    alpha2 = {'alias': 'alpha2', 'value': 1.0, 'minv': 0.0,
              'maxv': 2.0, 'vary': True, 'to_show': True, 'calc': False}
    alpha3 = {'alias': 'alpha3', 'value': 1.0, 'minv': 0.0,
              'maxv': 2.0, 'vary': True, 'to_show': True, 'calc': False}

    tz1 = {'alias': 'tz1', 'value': 1.0, 'minv': 0.0,
           'maxv': 1.0, 'vary': True, 'to_show': True, 'calc': False}
    tz2 = {'alias': 'tz2', 'value': 1.0, 'minv': 0.0,
           'maxv': 1.0, 'vary': True, 'to_show': True, 'calc': False}
    tz3 = {'alias': 'tz3', 'value': 1.0, 'minv': 0.0,
           'maxv': 1.0, 'vary': True, 'to_show': True, 'calc': False}

    # Axial ratio coefficient

    AR1 = {'alias': 'AR1', 'value': 1.0, 'minv': 0.001,
           'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}
    AR2 = {'alias': 'AR2', 'value': 1.0, 'minv': 0.001,
           'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}
    AR3 = {'alias': 'AR3', 'value': 1.0, 'minv': 0.001,
           'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}

    B1 = {'alias': 'B1', 'value': 1.0, 'minv': 0.001,
          'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}
    B2 = {'alias': 'B2', 'value': 1.0, 'minv': 0.001,
          'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}
    B3 = {'alias': 'B3', 'value': 1.0, 'minv': 0.001,
          'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}

    T1 = {'alias': 'T1', 'value': 1.0, 'minv': 0.0, 'maxv': 1000.0,
          'vary': True, 'to_show': True, 'calc': False}
    T2 = {'alias': 'T2', 'value': 1.0, 'minv': 0.0, 'maxv': 1000.0,
          'vary': True, 'to_show': True, 'calc': False}
    T3 = {'alias': 'T3', 'value': 1.0, 'minv': 0.0, 'maxv': 1000.0,
          'vary': True, 'to_show': True, 'calc': False}

    tauT1 = {'alias': 'tauT1', 'value': 0.055, 'minv': 0.001,
             'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}
    tauT2 = {'alias': 'tauT2', 'value': 0.055, 'minv': 0.001,
             'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}
    tauT3 = {'alias': 'tauT3', 'value': 0.005, 'minv': 0.001,
             'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': False}

    N_FCS = {'alias': 'N (FCS)', 'value': 0.0, 'minv': 0.001,
             'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}
    cpm = {'alias': 'cpm (kHz)', 'value': 0.0, 'minv': 0.001,
           'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}
    N_mom = {'alias': 'N (mom)', 'value': 0.0, 'minv': 0.001,
             'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}
    bri = {'alias': 'bri (kHz)', 'value': 0.0, 'minv': 0.001,
           'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}
    CV = {'alias': 'Coincidence', 'value': 0.0, 'minv': 0.001,
          'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}
    f0 = {'alias': 'PBC f0', 'value': 0.0, 'minv': 0.001,
          'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}
    overtb = {'alias': 'PBC tb', 'value': 0.0, 'minv': 0.001,
              'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}

    ACAC = {'alias': 'ACAC', 'value': 0.0, 'minv': 0.001,
            'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}
    ACCC = {'alias': 'ACCC', 'value': 0.0, 'minv': 0.001,
            'maxv': 1000.0, 'vary': True, 'to_show': True, 'calc': True}

    int_obj.def_param = {'A1': A1, 'A2': A2, 'A3': A3, 'txy1': txy1, 'txy2': txy2, 'txy3': txy3, 'offset': offset, 'GN0': GN0, 'alpha1': alpha1, 'alpha2': alpha2, 'alpha3': alpha3,
                         'tz1': tz1, 'tz2': tz2, 'tz3': tz3, 'AR1': AR1, 'AR2': AR2, 'AR3': AR3, 'B1': B1, 'B2': B2, 'B3': B3, 'T1': T1, 'T2': T2, 'T3': T3, 'tauT1': tauT1, 'tauT2': tauT2, 'tauT3': tauT3}
    int_obj.def_param['N_FCS'] = N_FCS
    int_obj.def_param['cpm'] = cpm
    int_obj.def_param['N_mom'] = N_mom
    int_obj.def_param['bri'] = bri
    int_obj.def_param['CV'] = CV
    int_obj.def_param['f0'] = f0
    int_obj.def_param['overtb'] = overtb

    int_obj.def_param['ACAC'] = ACAC
    int_obj.def_param['ACCC'] = ACCC

    int_obj.order_list = ['offset', 'GN0', 'N_FCS', 'cpm', 'A1', 'A2', 'A3', 'txy1', 'txy2', 'txy3', 'tz1', 'tz2', 'tz3', 'alpha1', 'alpha2', 'alpha3',
                          'AR1', 'AR2', 'AR3', 'B1', 'B2', 'B3', 'T1', 'T2', 'T3', 'tauT1', 'tauT2', 'tauT3', 'N_mom', 'bri', 'CV', 'f0', 'overtb', 'ACAC', 'ACCC']


def decide_which_to_show(int_obj):

    for art in int_obj.objId_sel.param:
        if int_obj.objId_sel.param[art]['to_show'] == True:
            int_obj.objId_sel.param[art]['to_show'] = False

        int_obj.objId_sel.param['offset']['to_show'] = True
        int_obj.objId_sel.param['GN0']['to_show'] = True

        int_obj.def_options['Diff_species'] = int_obj.diffNumSpecSpin.value()
        int_obj.def_options['Triplet_species'] = int_obj.tripNumSpecSpin.value()

        # Optional parameters
        for i in range(1, int_obj.def_options['Diff_species']+1):
            int_obj.objId_sel.param['A'+str(i)]['to_show'] = True
            int_obj.objId_sel.param['txy'+str(i)]['to_show'] = True
            int_obj.objId_sel.param['alpha'+str(i)]['to_show'] = True
            # 2 in this case corresponds to 3D:
            if int_obj.def_options['Dimen'] == 2:
                if int_obj.def_options['Diff_eq'] == 1:
                    int_obj.objId_sel.param['tz'+str(i)]['to_show'] = True

                if int_obj.def_options['Diff_eq'] == 2:
                    int_obj.objId_sel.param['AR'+str(i)]['to_show'] = True

        if int_obj.def_options['Triplet_eq'] == 2:
                # Triplet State equation1
            for i in range(1, int_obj.tripNumSpecSpin.value()+1):
                int_obj.objId_sel.param['B'+str(i)]['to_show'] = True
                int_obj.objId_sel.param['tauT'+str(i)]['to_show'] = True

        if int_obj.def_options['Triplet_eq'] == 3:
            # Triplet State equation2
            for i in range(1, int_obj.tripNumSpecSpin.value()+1):
                int_obj.objId_sel.param['T'+str(i)]['to_show'] = True
                int_obj.objId_sel.param['tauT'+str(i)]['to_show'] = True
        calc_param_fcs(int_obj, objId=int_obj.objId_sel)


def update_each(int_obj, text):
    """Will try and populate paramaters with what is present in the inteface, but if new option will goto the default"""
    try:
        exec("valueV = int_obj."+text+"_value.value()")
        exec("minV = int_obj."+text+"_min.value()")
        exec("maxV = int_obj."+text+"_max.value()")
        exec("varyV = int_obj."+text+"_vary.isChecked()")

        int_obj.objId_sel.param[text]['value'] = valueV
        int_obj.objId_sel.param[text]['minv'] = minV
        int_obj.objId_sel.param[text]['maxv'] = maxV
        int_obj.objId_sel.param[text]['vary'] = varyV
    except:

        int_obj.objId_sel.param[text] = copy.deepcopy(int_obj.def_param[text])


def update_param_fcs(int_obj):
    """Depending on the menu options this function will update the params of the current data set. """
    if int_obj.objId_sel == None:
        return
    decide_which_to_show(int_obj)
    # Set all the parameters to not show.

    for art in int_obj.objId_sel.param:
        if int_obj.objId_sel.param[art]['to_show'] == True:
            update_each(int_obj, art)

    calc_param_fcs(int_obj, objId=int_obj.objId_sel)


def calc_param_fcs(int_obj, objId):
    # Calculated parameters.
    try:
        objId.param['N_FCS']['value'] = 1/objId.param['GN0']['value']
        objId.param['N_FCS']['to_show'] = True
    except:
        objId.param['N_FCS']['value'] = 1
        objId.param['N_FCS']['to_show'] = False

    try:
        objId.param['cpm']['value'] = float(
            objId.kcount)/(1/objId.param['GN0']['value'])
        objId.param['cpm']['to_show'] = True
    except:
        objId.param['cpm']['value'] = 1
        objId.param['cpm']['to_show'] = False
    try:
        objId.param['N_mom']['value'] = float(objId.numberNandB)
        objId.param['N_mom']['to_show'] = True
    except:
        objId.param['N_mom']['value'] = 1
        objId.param['N_mom']['to_show'] = False
    try:
        objId.param['bri']['value'] = float(objId.brightnessNandB)
        objId.param['bri']['to_show'] = True
    except:
        objId.param['bri']['value'] = 1
        objId.param['bri']['to_show'] = False
    try:
        objId.param['CV']['value'] = float(objId.CV)
        objId.param['CV']['to_show'] = True
    except:
        pass
    try:
        objId.param['f0']['value'] = float(objId.pbc_f0)
        objId.param['f0']['to_show'] = True
        objId.param['overtb']['value'] = float(objId.pbc_tb)
        objId.param['overtb']['to_show'] = True
    except:
        pass

    if int_obj.objIdArr != [] and objId.siblings != None and objId.ch_type != 2:

        if objId.siblings[0].fitted == True:

            objId.param['ACAC']['value'] = float(
                objId.param['GN0']['value'])/float(objId.siblings[0].param['GN0']['value'])
            objId.param['ACAC']['to_show'] = True
            objId.param['ACCC']['value'] = float(
                objId.param['GN0']['value'])/float(objId.siblings[1].param['GN0']['value'])
            objId.param['ACCC']['to_show'] = True


def equation_(param, tc, options):
    """This is equation for fitting"""

    # A1 is relative component of fluorescent species
    # tc is tau.
    # txy1 is xy difusion   for fluorescent species one.
    # alpha1 is
    # tz1 is z diffusion for fluorescent species one.
    offset = param['offset'].value
    GN0 = param['GN0'].value

    if(options['Dimen'] == 2):
        if(options['Diff_eq'] == 1):
            # Equation 1A with 3D term.
            if (options['Diff_species'] == 1):
                A1 = param['A1'].value
                txy1 = param['txy1'].value
                alpha1 = param['alpha1'].value
                tz1 = param['tz1'].value
                # For one diffusing species
                GDiff = (A1*(((1+((tc/txy1)**alpha1))**-1)*((1+(tc/tz1))**-0.5)))
            elif (options['Diff_species'] == 2):
                A1 = param['A1'].value
                txy1 = param['txy1'].value
                alpha1 = param['alpha1'].value
                tz1 = param['tz1'].value
                A2 = param['A2'].value
                txy2 = param['txy2'].value
                alpha2 = param['alpha2'].value
                tz2 = param['tz2'].value
                param['A2'].value = 1.0-A1
                A2 = param['A2'].value
                # For two diffusing species
                GDiff = (A1*(((1+((tc/txy1)**alpha1))**-1)*((1+(tc/tz1))**-0.5))) + \
                    (A2*(((1+((tc/txy2)**alpha2))**-1)*((1+(tc/tz2))**-0.5)))
            elif (options['Diff_species'] == 3):
                A1 = param['A1'].value
                txy1 = param['txy1'].value
                alpha1 = param['alpha1'].value
                tz1 = param['tz1'].value
                A2 = param['A2'].value
                txy2 = param['txy2'].value
                alpha2 = param['alpha2'].value
                tz2 = param['tz2'].value
                A3 = param['A3'].value
                txy3 = param['txy3'].value
                alpha3 = param['alpha3'].value
                tz3 = param['tz3'].value
                param['A2'].value = 1.0-A1-A3
                A2 = param['A2'].value
                param['A3'].value = 1.0-A2-A1
                A3 = param['A3'].value
                # For three diffusing species
                GDiff = (A1*(((1+((tc/txy1)**alpha1))**-1)*((1+(tc/tz1))**-0.5))) + (A2*(((1+((tc/txy2)**alpha2))
                                                                                          ** -1)*((1+(tc/tz2))**-0.5))) + (A3*(((1+((tc/txy3)**alpha3))**-1)*((1+(tc/tz3))**-0.5)))
        elif(options['Diff_eq'] == 2):
            if (options['Diff_species'] == 1):
                A1 = param['A1'].value
                txy1 = param['txy1'].value
                alpha1 = param['alpha1'].value
                AR1 = param['AR1'].value
                # For one diffusing species
                GDiff = (A1*(((1+((tc/txy1)**alpha1))**-1) *
                             (((1+(tc/((AR1**2)*txy1)))**-0.5))))
            elif (options['Diff_species'] == 2):
                A1 = param['A1'].value
                txy1 = param['txy1'].value
                alpha1 = param['alpha1'].value
                AR1 = param['AR1'].value
                A2 = param['A2'].value
                txy2 = param['txy2'].value
                alpha2 = param['alpha2'].value
                AR2 = param['AR2'].value
                param['A2'].value = 1.0-A1
                A2 = param['A2'].value
                # For two diffusing species
                GDiff = (A1*(((1+((tc/txy1)**alpha1))**-1)*(((1+(tc/((AR1**2)*txy1)))**-0.5)))) + \
                    (A2*(((1+((tc/txy2)**alpha2))**-1) *
                         (((1+(tc/((AR2**2)*txy2)))**-0.5))))
            elif (options['Diff_species'] == 3):
                A1 = param['A1'].value
                txy1 = param['txy1'].value
                alpha1 = param['alpha1'].value
                AR1 = param['AR1'].value
                A2 = param['A2'].value
                txy2 = param['txy2'].value
                alpha2 = param['alpha2'].value
                AR2 = param['AR2'].value
                A3 = param['A3'].value
                txy3 = param['txy3'].value
                alpha3 = param['alpha3'].value
                AR3 = param['AR3'].value
                # For two diffusing species
                param['A2'].value = 1.0-A1-A3
                A2 = param['A2'].value
                param['A3'].value = 1.0-A2-A1
                A3 = param['A3'].value
                # For three diffusing species
                GDiff = (A1*(((1+((tc/txy1)**alpha1))**-1)*(((1+(tc/((AR1**2)*txy1)))**-0.5))))+(A2*(((1+((tc/txy2)**alpha2))**-1)
                                                                                                     * (((1+(tc/((AR2**2)*txy2)))**-0.5))))+(A3*(((1+((tc/txy3)**alpha3))**-1)*(((1+(tc/((AR3**2)*txy3)))**-0.5))))

    if(options['Dimen'] == 1):
        # Equation 1A with 2D term.
        if (options['Diff_species'] == 1):
            A1 = param['A1'].value
            txy1 = param['txy1'].value
            alpha1 = param['alpha1'].value
            # For one diffusing species
            GDiff = (A1*(((1+((tc/txy1)**alpha1))**-1)))
        elif (options['Diff_species'] == 2):
            A1 = param['A1'].value
            txy1 = param['txy1'].value
            alpha1 = param['alpha1'].value
            A2 = param['A2'].value
            txy2 = param['txy2'].value
            alpha2 = param['alpha2'].value
            # For two diffusing species

            param['A2'].value = 1.0-A1
            A2 = param['A2'].value

            GDiff = (A1*(((1+(tc/txy1)**alpha1)**-1))) + \
                (A2*(((1+(tc/txy2)**alpha2)**-1)))

            # if A1 +A2 != 1.0:
            #    GDiff = 99999999999
        elif (options['Diff_species'] == 3):
            A1 = param['A1'].value
            txy1 = param['txy1'].value
            alpha1 = param['alpha1'].value
            A2 = param['A2'].value
            txy2 = param['txy2'].value
            alpha2 = param['alpha2'].value
            A3 = param['A3'].value
            txy3 = param['txy3'].value
            alpha3 = param['alpha3'].value
            # For two diffusing species
            param['A2'].value = 1.0-A1-A3
            A2 = param['A2'].value
            param['A3'].value = 1.0-A2-A1
            A3 = param['A3'].value
            # For three diffusing species
            GDiff = (A1*(((1+(tc/txy1)**alpha1)**-1)))+(A2 *
                                                        (((1+(tc/txy2)**alpha2)**-1)))+(A3*(((1+(tc/txy3)**alpha3)**-1)))

    if(options['Triplet_eq'] == 1):
        # For no triplets.
        GT = 1
    elif(options['Triplet_eq'] == 2):
        # Equation (2) 1st equation.
        if (options['Triplet_species'] == 1):
            B1 = param['B1'].value
            tauT1 = param['tauT1'].value
            # For one dark state.
            GT = 1 + (B1*np.exp(-tc/tauT1))
        elif (options['Triplet_species'] == 2):
            B1 = param['B1'].value
            tauT1 = param['tauT1'].value
            B2 = param['B2'].value
            tauT2 = param['tauT2'].value
            # For two dark state
            GT = 1 + (B1*np.exp(-tc/tauT1))+(B2*np.exp(-tc/tauT2))
        elif (options['Triplet_species'] == 3):
            B1 = param['B1'].value
            tauT1 = param['tauT1'].value
            B2 = param['B2'].value
            tauT2 = param['tauT2'].value
            B3 = param['B3'].value
            tauT3 = param['tauT3'].value
            # For three dark state
            GT = 1 + (B1*np.exp(-tc/tauT1)) + \
                (B2*np.exp(-tc/tauT2))+(B3*np.exp(-tc/tauT3))

    elif(options['Triplet_eq'] == 3):
        # Equation (2) 2nd equation.
        if (options['Triplet_species'] == 1):
            T1 = param['T1'].value
            tauT1 = param['tauT1'].value
            # For one dark state.
            GT = 1 - T1 + (T1*np.exp(-tc/tauT1))
        elif (options['Triplet_species'] == 2):
            T1 = param['T1'].value
            tauT1 = param['tauT1'].value
            T1 = param['T2'].value
            tauT1 = param['tauT2'].value
            # For two dark state.
            GT = 1 - (T1+T2) + ((T1*np.exp(-tc/tauT1))+(T2*np.exp(-tc/tauT2)))
        elif (options['Triplet_species'] == 3):
            T1 = param['T1'].value
            tauT1 = param['tauT1'].value
            T2 = param['T2'].value
            tauT1 = param['tauT2'].value
            T3 = param['T3'].value
            tauT1 = param['tauT3'].value
            # For three dark state.
            GT = 1 - (T1+T2+T3) + ((T1*np.exp(-tc/tauT1)) +
                                   (T2*np.exp(-tc/tauT2))+(T3*np.exp(-tc/tauT3)))

    return offset + (GN0*GDiff*GT)
