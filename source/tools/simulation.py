# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - simulation
    Enables the user to change plotting parameters and replotting fast.
    Might be useful for better understanding.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""

# We may import different things from throughout the program:
import wx
import numpy as np

import edclasses                    # Cool stuf like better floatspin

import platform






class Slide(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
        # parent is the main frame of PyCorrFit
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Simulation",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)

        # Starting positions/factors for spinctrls and sliders
        self.slidemax = 1000
        self.slidestart = 500
        self.spinstartfactor = 0.1
        self.spinendfactor = 1.9

        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None

        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()



        ## Content
        self.panel = wx.Panel(self)

        self.rbtnB = wx.RadioButton (self.panel, -1, 'Fix parameter B', 
                                        style = wx.RB_GROUP)
        self.rbtnOp = wx.RadioButton (self.panel, -1, 'Fix operation result')

        # Set starting variables
        self.SetStart()

        dropsizer = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)

        dropsizer.Add( wx.StaticText(self.panel, label="Parameter A"))
        dropsizer.Add( wx.StaticText(self.panel, label="Operator"))
        dropsizer.Add( wx.StaticText(self.panel, label="Parameter B"))

        self.droppA = wx.ComboBox(self.panel, -1, self.labelA, (15, 20),
                     wx.DefaultSize, self.parmAlist,
                     wx.CB_DROPDOWN|wx.CB_READONLY)
        self.droppA.SetSelection(0)
        self.Bind(wx.EVT_COMBOBOX, self.Ondrop, self.droppA)
        self.dropop = wx.ComboBox(self.panel, -1, "", (10, 20),
                     wx.DefaultSize, self.oplist,
                     wx.CB_DROPDOWN|wx.CB_READONLY)
        self.dropop.SetSelection(0)
        self.opfunc = self.opdict[self.opdict.keys()[0]]
        self.Bind(wx.EVT_COMBOBOX, self.Ondrop, self.dropop)
        self.droppB = wx.ComboBox(self.panel, -1, self.labelB, (15, 30),
                     wx.DefaultSize, self.parmBlist,
                     wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.Ondrop, self.droppB)
        self.droppB.SetSelection(1)
        dropsizer.Add(self.droppA)
        dropsizer.Add(self.dropop)
        dropsizer.Add(self.droppB)

        textfix = wx.StaticText(self.panel,
                                label="\nSelect intervals and slide.\n")

        # Parameter A
        slidesizer = wx.FlexGridSizer(rows=3, cols=5, vgap=5, hgap=5)

        self.textstartA = wx.StaticText(self.panel, label=self.labelA)
        slidesizer.Add(self.textstartA)
        self.startspinA = edclasses.FloatSpin(self.panel, digits=7,
                                            increment=.1)
        slidesizer.Add(self.startspinA)
        self.sliderA = wx.Slider(self.panel, -1, self.slidestart, 0,
                                 self.slidemax, wx.DefaultPosition, (250, -1),
                                 wx.SL_HORIZONTAL)
        slidesizer.Add(self.sliderA)
        self.endspinA = edclasses.FloatSpin(self.panel, digits=7,
                                            increment=.1)
        slidesizer.Add(self.endspinA)
        self.textvalueA = wx.StaticText(self.panel, label= "%.5e" % self.valueA)
        slidesizer.Add(self.textvalueA)
        # Parameter B
        self.textstartB = wx.StaticText(self.panel, label=self.labelB)
        slidesizer.Add(self.textstartB)
        self.startspinB = edclasses.FloatSpin(self.panel, digits=7,
                                            increment=.1)
        slidesizer.Add(self.startspinB)
        self.sliderB = wx.Slider(self.panel, -1, self.slidestart, 0,
                                 self.slidemax, wx.DefaultPosition, (250, -1),
                                 wx.SL_HORIZONTAL)
        slidesizer.Add(self.sliderB)
        self.endspinB = edclasses.FloatSpin(self.panel, digits=7,
                                            increment=.1)
        slidesizer.Add(self.endspinB)
        self.textvalueB = wx.StaticText(self.panel, label= "%.5e" % self.valueB)
        slidesizer.Add(self.textvalueB)
        # Result of operation
        self.textstartOp = wx.StaticText(self.panel, label=self.labelOp)
        slidesizer.Add(self.textstartOp)
        self.startspinOp = edclasses.FloatSpin(self.panel, digits=7,
                                            increment=.1)
        slidesizer.Add(self.startspinOp)
        self.sliderOp = wx.Slider(self.panel, -1, self.slidestart, 0,
                                  self.slidemax, wx.DefaultPosition, (250, -1),
                                  wx.SL_HORIZONTAL)
        slidesizer.Add(self.sliderOp)
        self.endspinOp = edclasses.FloatSpin(self.panel, digits=7,
                                        increment=.1)
        slidesizer.Add(self.endspinOp)
        self.textvalueOp = wx.StaticText(self.panel,
                                         label= "%.5e" % self.valueOp)
        slidesizer.Add(self.textvalueOp)


        self.Bind(wx.EVT_SLIDER, self.OnSlider, self.sliderA)
        self.Bind(wx.EVT_SLIDER, self.OnSlider, self.sliderB)
        self.Bind(wx.EVT_SLIDER, self.OnSlider, self.sliderOp)

        # Bindings for radiobuttons
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.rbtnB)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.rbtnOp)

        # Our self-made spin controls alread have wx_EVT_SPINCTRL bound to
        # the increment function. We will call that function manually here.
        self.startspinA.Unbind(wx.EVT_SPINCTRL)
        self.startspinB.Unbind(wx.EVT_SPINCTRL)
        self.startspinOp.Unbind(wx.EVT_SPINCTRL)
        self.endspinA.Unbind(wx.EVT_SPINCTRL)
        self.endspinB.Unbind(wx.EVT_SPINCTRL)
        self.endspinOp.Unbind(wx.EVT_SPINCTRL)


        self.Bind(wx.EVT_SPINCTRL, self.OnSlider, self.startspinA)
        self.Bind(wx.EVT_SPINCTRL, self.OnSlider, self.startspinB)
        self.Bind(wx.EVT_SPINCTRL, self.OnSlider, self.startspinOp)
        self.Bind(wx.EVT_SPINCTRL, self.OnSlider, self.endspinA)
        self.Bind(wx.EVT_SPINCTRL, self.OnSlider, self.endspinB)
        self.Bind(wx.EVT_SPINCTRL, self.OnSlider, self.endspinOp)
     
        self.SetValues()
        ## Sizers
        self.topSizer = wx.BoxSizer(wx.VERTICAL)

        self.topSizer.Add(dropsizer)

        self.topSizer.Add(self.rbtnB)
        self.topSizer.Add(self.rbtnOp)

        self.topSizer.Add(textfix)

        self.topSizer.Add(slidesizer)

        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)

        #self.size = self.topSizer.GetMinSizeTuple()
        #newsize = (xmin1, ymin1)
        #self.panel.SetSize(newsize)
        #self.SetSize(newsize)

        self.Show(True)
        wx.EVT_SIZE(self, self.OnSize)
        # Disable lowest slieder
        self.OnRadio()

    def CalcFct(self, A, B, C):
        if self.rbtnB.Value == True:
            func = self.opfunc[0]
            try:
                C = func(A,B)
            except ZeroDivisionError:
                a = 0
            else:
                return B, C
        else:
            func = self.opfunc[1]
            try:
                B = func(A,C)
            except ZeroDivisionError:
                a = 0
            else:
                return B, C


    def Increment(self):
        # Set the correct increment for each spinctrl
        self.startspinA.increment()
        self.startspinB.increment()
        self.startspinOp.increment()
        self.endspinA.increment()
        self.endspinB.increment()
        self.endspinOp.increment()

    def FillOpDict(self):
        # Dictionaries: [Calculate C, Calculate B)
        self.opdict["A/B"] = [lambda A,B: A/B, lambda A,C: A/C]
        self.opdict["B/A"] = [lambda A,B: B/A, lambda A,C: C*A]
        self.opdict["A*B"] = [lambda A,B: A*B, lambda A,C: C/A]
        self.opdict["A+B"] = [lambda A,B: A+B, lambda A,C: C-A]
        self.opdict["A-B"] = [lambda A,B: A-B, lambda A,C: A-C]
        self.opdict["A*exp(B)"] = [lambda A,B: A*np.exp(B),
                                   lambda A,C: np.log(C/A)]
        self.opdict["B*exp(A)"] = [lambda A,B: B*np.exp(A),
                                   lambda A,C: C/np.exp(A)]


    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()

    def Ondrop(self, event=None):
        self.labelOp = self.oplist[self.dropop.GetSelection()]
        self.labelA = self.parmAlist[self.droppA.GetSelection()]
        self.labelB = self.parmBlist[self.droppB.GetSelection()]

        self.textstartOp.SetLabel(self.labelOp)
        self.textstartA.SetLabel(label=self.labelA)
        self.textstartB.SetLabel(self.labelB)

        self.sliderB.SetValue(self.slidestart)
        self.sliderOp.SetValue(self.slidestart)
        self.sliderA.SetValue(self.slidestart)
        self.SetValues()
        self.OnSize()

    def OnPageChanged(self, page):
        # When parent changes
        # This is a necessary function for PyCorrFit.
        # This is stuff that should be done when the active page
        # of the notebook changes.
        if page.counter != self.Page.counter:
            self.Page = page
            self.SetStart()
            self.droppA.SetItems(self.parmAlist)
            self.droppB.SetItems(self.parmBlist)
            self.droppA.SetSelection(0)
            self.droppB.SetSelection(1)
            self.dropop.SetSelection(0)
            # Set labels
            self.Ondrop()

    def OnRadio(self, event=None):
        if self.rbtnB.Value == True:
            # Parameter B is vaiable
            self.sliderOp.Enable(False)
            self.startspinOp.Enable(False)
            self.endspinOp.Enable(False)
            self.sliderB.Enable(True)
            self.startspinB.Enable(True)
            self.endspinB.Enable(True)
        else:
            # Operation result is vaiable
            self.sliderOp.Enable(True)
            self.startspinOp.Enable(True)
            self.endspinOp.Enable(True)
            self.sliderB.Enable(False)
            self.startspinB.Enable(False)
            self.endspinB.Enable(False)
        self.Ondrop()

    def OnSize(self, event=None):
        #(x,y) = self.GetSize()
        #self.size = ( max(self.size[0], y), max(self.size[1], y))
        #print self.size
        #print x,y
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.panel.SetSize(self.GetSize())

    def OnSlider(self, event=None):
        ## Set the slider vlaues
        idmax = self.sliderA.GetMax()
        slideA = self.sliderA.GetValue()
        startA = self.startspinA.GetValue()
        endA = self.endspinA.GetValue()
        self.valueA = startA + (endA-startA)*slideA/idmax
        self.textvalueA.SetLabel( "%.5e" % self.valueA)

        if self.rbtnB.Value == True:
            slideB = self.sliderB.GetValue()
            startB = self.startspinB.GetValue()
            endB = self.endspinB.GetValue()
            self.valueB = startB + (endB-startB)*slideB/idmax
        else:
            # Same thing
            slideOp = self.sliderOp.GetValue()
            startOp = self.startspinOp.GetValue()
            endOp = self.endspinOp.GetValue()
            self.valueOp = startOp + (endOp-startOp)*slideOp/idmax

        self.valueB, self.valueOp = self.CalcFct(self.valueA, self.valueB,
                                                 self.valueOp)
        self.textvalueB.SetLabel( "%.5e" % self.valueB)
        self.textvalueOp.SetLabel( "%.5e" % self.valueOp)

        self.Increment()
        self.SetResult()
        self.OnSize()



    def SetResult(self, event=None):
        # And Plot
        idA = self.droppA.GetSelection()
        idB = self.droppB.GetSelection()
        self.Page.active_parms[1][idA] = self.valueA
        self.Page.active_parms[1][idB] = self.valueB

        self.Page.apply_parameters_reverse()
        self.Page.PlotAll()

    def SetStart(self):
        # Sets first and second variable of a page to
        # Parameters A and B respectively.
        self.parmAlist = self.Page.active_parms[0]
        self.parmBlist = self.Page.active_parms[0]
        # Operators
        # Calculation of variable A with fixed B
        self.opdict = dict()
        self.FillOpDict()
        self.oplist = self.opdict.keys()
        self.oplist.sort()

        self.labelA = self.parmAlist[0]
        self.labelB = self.parmBlist[1]
        self.labelOp = self.oplist[0]
        self.opfunc = self.opdict[self.labelOp]
        self.valueA = self.Page.active_parms[1][0]
        self.valueB = self.Page.active_parms[1][1]
        self.valueB, self.valueOp = self.CalcFct(self.valueA, self.valueB, 0)


    def SetValues(self, event=None):
        # Set the values for spin and slider
        idA = self.droppA.GetSelection()
        self.valueA = self.Page.active_parms[1][idA]

        idB = self.droppB.GetSelection()
        self.valueB = self.Page.active_parms[1][idB]

        idop = self.dropop.GetSelection()
        keys = self.opdict.keys()
        opkey = self.oplist[idop]
        self.opfunc = self.opdict[opkey]


        # Parameter A
        startA = self.valueA*self.spinstartfactor
        endA = self.valueA*self.spinendfactor
        self.startspinA.SetValue(startA)
        self.endspinA.SetValue(endA)

        # Parameter B
        startB = self.valueB*self.spinstartfactor
        endB = self.valueB*self.spinendfactor
        self.startspinB.SetValue(startB)
        self.endspinB.SetValue(endB)

        # Operation result

        self.valueOp = self.opfunc[0](self.valueA, self.valueB)
        startOp = self.valueOp*self.spinstartfactor
        endOp = self.valueOp*self.spinendfactor
        self.startspinOp.SetValue(startOp)
        self.endspinOp.SetValue(endOp)

        self.textvalueA.SetLabel( "%.5e" % self.valueA)
        self.textvalueB.SetLabel( "%.5e" % self.valueB)
        self.textvalueOp.SetLabel( "%.5e" % self.valueOp)

        self.Increment()

        self.SetResult()

        


