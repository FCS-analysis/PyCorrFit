# -*- coding: utf-8 -*-
""" PyCorrFit

    Module frontend
    The frontend displays the GUI (Graphic User Interface). All necessary 
    functions and modules are called from here.

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


import os
import webbrowser
import wx                               # GUI interface wxPython
import wx.lib.agw.flatnotebook as fnb   # Flatnotebook (Tabs)
import wx.lib.delayedresult as delayedresult
import wx.py.shell
import numpy as np                      # NumPy
import platform
import sys                              # System stuff
import traceback                        # for Error handling

try:
    # contains e.g. update and icon, but no vital things.
    import misc
except ImportError:
    print " Some modules are not available."
    print " Update function will not work."

# PyCorrFit modules
import doc                          # Documentation/some texts
import edclasses

import models as mdls
import openfile as opf              # How to treat an opened file
import page
import plotting
import readfiles
import tools                        # Some tools
import usermodel


## On Windows XP I had problems with the unicode Characters.
# I found this at 
# http://stackoverflow.com/questions/5419/python-unicode-and-the-windows-console
# and it helped:
if platform.system() == 'Windows':
    reload(sys)
    sys.setdefaultencoding('utf-8')
# ~paulmueller


###########################################################
class FlatNotebookDemo(fnb.FlatNotebook):
    """
    Flatnotebook class
    """
    def __init__(self, parent):
        """Constructor"""
        style = fnb.FNB_SMART_TABS|fnb.FNB_NO_NAV_BUTTONS|\
              fnb.FNB_DROPDOWN_TABS_LIST|fnb.FNB_NODRAG|\
              fnb.FNB_TABS_BORDER_SIMPLE|\
              fnb.FNB_X_ON_TAB|fnb.FNB_NO_X_BUTTON
        # Bugfix for Mac
        if platform.system().lower() in ["windows", "linux"]:
            style = style|fnb.FNB_HIDE_ON_SINGLE_TAB
        self.fnb = fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY,
        agwStyle=style)


###########################################################
class MyFrame(wx.Frame):
    def __init__(self, parent, id, version):
        ## Set initial variables that make sense
        tau = 10**np.linspace(-6,8,1001)

        self.version = version
        wx.Frame.__init__(self, parent, id, "PyCorrFit " + self.version)
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        self.StatusBar.SetStatusText("Find help and updates online:"+
                                     " 'Help > Update'")
        ## Properties of the Frame
        initial_size = (768,700)
        self.SetSize(initial_size)
        self.SetMinSize(initial_size)

        # Set this, so we know in which directory we are working in.
        # This will change, when we load a session or data file.
        self.dirname = os.curdir
        self.filename = None

        # Session Comment - may be edited and saved later
        self.SessionComment = "This is a session comment. It will be saved" +\
                              " as the session is saved."

        ## Set variables
        # The model module that can be changed by importing user defined
        # functions.
        # These are only for compatibility.
        
        # value_set and valuedict only for compatibility!
        # I should use mdls for anything, since it's globally imported
        # and modified by this program (e.g. adding new function)
        self.value_set = mdls.values
        self.valuedict = mdls.valuedict

        # Some standard time scale
        # We need this for the functions inside the "FittingPanel"s
        self.tau = tau 

        # Tab Counter
        self.tabcounter = 1

        # Background Correction List
        # Here, each item is a list containing three elements:
        # [0] average signal [kHz]
        # [1] signal name (edited by user)
        # [2] signal trace (tuple) ([ms], [kHz])
        self.Background = list()

        # A dictionary for all the opened tool windows
        self.ToolsOpen = dict()
        # A dictionary for all the tools
        self.Tools = dict()

        # Range selector (None if inactive)
        # Fitting parameter range selection
        # New as of 0.7.9
        self.RangeSelector = None
        
        ## Setting up the menus.
        # models, modeldict, modeltypes only for compatibility!
        # I should use mdls for anything, since it's globally imported
        # and modified by this program (e.g. adding new function)
        self.models = mdls.models
        self.modeldict = mdls.modeldict
        self.modeltypes = mdls.modeltypes

        self.modelmenudict = dict()
        self.MakeMenu()

        ## Create the Flatnotebook (Tabs Tabs Tabs!)
        panel = wx.Panel(self)
        self.panel = panel

        self.notebook = FlatNotebookDemo(panel)
        self.notebook.SetRightClickMenu(self.curmenu)

        #self.notebook.SetAGWWindowStyleFlag(FNB_X_ON_TAB)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        self.Layout()

        self.Show()
        
        # Notebook Handler
        self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSED, 
                           self.OnFNBClosedPage)
        self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, 
                           self.OnFNBPageChanged)
        # This is a hack since version 0.7.7:
        # When the "X"-button on a page is pressed, ask the user
        # if he really wants to close that page.
        self.notebook._pages.Unbind(wx.EVT_LEFT_UP)
        self.notebook._pages.Bind(wx.EVT_LEFT_UP, self.OnMyLeftUp)

        # If user hits the "x", ask if he wants to save the session
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        # Set window icon
        try:
            self.MainIcon = misc.getMainIcon()
            wx.Frame.SetIcon(self, self.MainIcon)
        except:
            self.MainIcon = None


    def add_fitting_tab(self, event=None, modelid=None, counter=None):
        """ This function creates a new page inside the notebook.
            If the function is called from a menu, the modelid is 
            known by the event. If not, the modelid should be specified by 
            *modelid*. 
            *counter* specifies which page number we should use for our 
            new page. If it is None, we will simply use *self.tabcounter*.
            
            *event*   - An event that has event.GetId() equal to a modelid
            *modelid* - optional, directly set the modelid
            *counter* - optional, set the "#" value of the page
        """
        if modelid is None:
            # Get the model id from the menu
            modelid = event.GetId()
        if counter is not None:
            # Set the tabcounter right, so the tabs are counted continuously.
            counterint = int(counter.strip().strip(":").strip("#"))
            self.tabcounter = max(counterint, self.tabcounter)
        modelid = int(modelid)
        counter = "#"+str(self.tabcounter)+": "
        # Get the model for the page together
        valuepack = mdls.valuedict[modelid]
        active_labels = valuepack[0]
        active_values = 1*valuepack[1]
        active_fitting = 1*valuepack[2]
        active_parms = [active_labels, active_values, active_fitting]
        model = mdls.modeldict[modelid][1]
        # Create New Tab
        Newtab = page.FittingPanel(self, counter, modelid, active_parms,
                                   self.tau)
        #self.Freeze()
        self.notebook.AddPage(Newtab, counter+model, select=True)
        #self.Thaw()
        self.tabcounter = self.tabcounter + 1
        # Enable the "Current" Menu
        self.EnableToolCurrent(True)
        #
        #######
        #
        # This is a work-around to prevent a weird bug in version 0.7.8:
        # The statistics OnPageChanged function is called but the parameters
        # are displayed double if a new page is created and the statistics
        # window is open.
        # Find Tool Statistics
        # Get open tools
        toolkeys = self.ToolsOpen.keys()
        for key in toolkeys:
            tool = self.ToolsOpen[key]
            try:
                if tool.MyName=="STATISTICS":
                    # Call the function properly.
                    tool.OnPageChanged(Newtab)
            except:
                pass
        #
        #######
        #
        return Newtab


    def EnableToolCurrent(self, enabled):
        """ Independent on order of menus, enable or disable tools and
            current menu.
        """
        # Tools menu is now always enabled
        # tid = self.menuBar.FindMenu("&Tools")
        # self.menuBar.EnableTop(tid, enabled)
        cid = self.menuBar.FindMenu("Current &Page")
        self.menuBar.EnableTop(cid, enabled)


    def MakeMenu(self):
        self.filemenu = wx.Menu()
        # toolmenu and curmenu are public, because they need to be enabled/
        # disabled when there are tabs/notabs.
        self.toolmenu = wx.Menu()
        # curmenu needs to be public, because we want to call it from the right
        # click menu of a Page in fnb
        self.curmenu = wx.Menu()
        modelmenu = wx.Menu()
        prefmenu = wx.Menu()
        helpmenu = wx.Menu()
        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        # self.filemenu
        menuAddModel = self.filemenu.Append(wx.ID_ANY, 
                          "&Import model", "Add a user defined model.")
        menuLoadBatch = self.filemenu.Append(wx.ID_ANY, 
                         "&Load data", "Loads one or multiple data files")
        menuOpen = self.filemenu.Append(wx.ID_OPEN, "&Open session", 
                                           "Restore a previously saved session")
        self.filemenu.AppendSeparator()
        self.menuComm = self.filemenu.Append(wx.ID_ANY, "Co&mment session", 
                           "Add a comment to this session", kind=wx.ITEM_CHECK)
        self.filemenu.Check(self.menuComm.GetId(), False)
        menuClear = self.filemenu.Append(wx.ID_ANY, "&Clear session", 
                          "Remove all pages but keep imported model functions.")
        menuSave = self.filemenu.Append(wx.ID_SAVE, "&Save session", 
                                   "Save entire Session")
        self.filemenu.AppendSeparator()
        menuExit = self.filemenu.Append(wx.ID_EXIT,"E&xit",
                                                        "Terminate the program")
        # prefmenu
        self.MenuUseLatex = prefmenu.Append(wx.ID_ANY, "Use Latex",
                            "Enables/Disables usage of Latex for image saving.",
                            kind=wx.ITEM_CHECK)
        self.MenuVerbose = prefmenu.Append(wx.ID_ANY, "Verbose mode",
                           "Enables/Disables output of additional information.",
                            kind=wx.ITEM_CHECK)
        self.MenuShowWeights = prefmenu.Append(wx.ID_ANY, "Show weights",
                           "Enables/Disables displaying weights of fit.",
                            kind=wx.ITEM_CHECK)
        self.MenuShowWeights.Check()
        # toolmenu
        toolkeys = tools.ToolDict.keys()
        toolkeys.sort()
        for ttype in toolkeys:
            for tool in np.arange(len(tools.ToolDict[ttype])):
                menu = self.toolmenu.Append(wx.ID_ANY, 
                       tools.ToolName[ttype][tool][0],
                       tools.ToolName[ttype][tool][1], kind=wx.ITEM_CHECK)
                self.toolmenu.Check(menu.GetId(), False)
                # Append tool to list of tools with menu ID
                self.Tools[menu.GetId()] = tools.ToolDict[ttype][tool]
                # Bindings
                # On tool only needs the Id of the wx.EVT_MENU
                self.Bind(wx.EVT_MENU, self.OnTool, menu)
            if ttype != toolkeys[-1]:
                self.toolmenu.AppendSeparator()
        # curmenu
        menuImportData = self.curmenu.Append(wx.ID_ANY, "&Import Data",
                                             "Import experimental FCS curve")

        menuSaveData = self.curmenu.Append(wx.ID_ANY, "&Save data (*.csv)",
                                           "Save data (comma separated values)")

        menuSavePlotCorr = self.curmenu.Append(wx.ID_ANY, 
                                     "&Save correlation as image",
                                     "Export current plot as image.")

        menuSavePlotTrace = self.curmenu.Append(wx.ID_ANY, 
                                     "&Save trace as image",
                                     "Export current trace as image.")
        self.curmenu.AppendSeparator()
        menuClPa = self.curmenu.Append(wx.ID_ANY, "&Close Page",
                                       "Close Current Page")
        # model menu
        # Integrate models into menu
        keys = mdls.modeltypes.keys()
        keys.sort()
        for modeltype in keys:
            # Now we have selected a type of model
            # Create a submenu
            submenu = wx.Menu()
            modelmenu.AppendMenu(wx.ID_ANY, modeltype, submenu)
            # Append to menulist
            self.modelmenudict[modeltype] = submenu
            for modelid in mdls.modeltypes[modeltype]:
                # Now we add every model that belongs to that type
                model = mdls.modeldict[modelid]
                if platform.system().lower() == "darwin" and hasattr(sys, 'frozen'):
                    ###
                    ### Work-around for freezed mac version
                    ###
                    ### (strange UTF-8 decoding error,
                    ###  would work with misc.removewrongUTF8)
                    b = model[1].split("(")[0].strip()
                    c = misc.removewrongUTF8(model[2])
                    menuentry = submenu.Append(model[0],b,c)
                else:
                    menuentry = submenu.Append(model[0], model[1], model[2])
                self.Bind(wx.EVT_MENU, self.add_fitting_tab, menuentry)
        # help menu
        menuDocu = helpmenu.Append(wx.ID_ANY, "&Documentation",
                                    "PyCorrFit documentation")
        menuWiki = helpmenu.Append(wx.ID_ANY, "&Wiki",
                          "PyCorrFit wiki pages by users for users (online)")
        menuUpdate = helpmenu.Append(wx.ID_ANY, "&Update",
                                    "Check for new version"+
                                     " (Web access required)")
        helpmenu.AppendSeparator()
        menuShell = helpmenu.Append(wx.ID_ANY, "S&hell",
                                    "A Python shell")
        helpmenu.AppendSeparator()
        menuSoftw = helpmenu.Append(wx.ID_ANY, "&Software",
                                    "Information about the software used")
        menuAbout = helpmenu.Append(wx.ID_ABOUT, "&About",
                                    "Information about this program")
        # Create the menubar.
        self.menuBar = wx.MenuBar()
        # Adding all the menus to the MenuBar
        self.menuBar.Append(self.filemenu,"&File") 
        self.menuBar.Append(self.toolmenu,"&Tools") 
        self.menuBar.Append(self.curmenu,"Current &Page") 
        self.menuBar.Append(modelmenu,"&Model") 
        self.menuBar.Append(prefmenu,"&Preferences") 
        self.menuBar.Append(helpmenu,"&Help")
        self.SetMenuBar(self.menuBar) # Adding the MenuBar to the Frame content.
        self.EnableToolCurrent(False)
        ## Set events
        #File
        #self.Bind(wx.EVT_MENU, self.OnLoadSingle, menuLoadSingle)
        self.Bind(wx.EVT_MENU, self.OnLoadBatch, menuLoadBatch)
        self.Bind(wx.EVT_MENU, self.OnAddModel, menuAddModel)
        self.Bind(wx.EVT_MENU, self.OnCommSession, self.menuComm)
        self.Bind(wx.EVT_MENU, self.OnClearSession, menuClear)
        self.Bind(wx.EVT_MENU, self.OnOpenSession, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnSaveSession, menuSave)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        # Current
        self.Bind(wx.EVT_MENU, self.OnImportData, menuImportData)
        self.Bind(wx.EVT_MENU, self.OnSaveData, menuSaveData)
        self.Bind(wx.EVT_MENU, self.OnSavePlotCorr, menuSavePlotCorr)
        self.Bind(wx.EVT_MENU, self.OnSavePlotTrace, menuSavePlotTrace)
        self.Bind(wx.EVT_MENU, self.OnDeletePage, menuClPa)
        # Help
        self.Bind(wx.EVT_MENU, self.OnSoftware, menuSoftw)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnUpdate, menuUpdate)
        self.Bind(wx.EVT_MENU, self.OnDocumentation, menuDocu)
        self.Bind(wx.EVT_MENU, self.OnWiki, menuWiki)
        self.Bind(wx.EVT_MENU, self.OnShell, menuShell)


    def OnAbout(self, event=None):
        # Show About Information
        description =  ("PyCorrFit is a data displaying, fitting "+
            "and evaluation tool \nfor fluorescence correlation "+
            "spectroscopy. \nPyCorrFit is written in Python.")
        licence = doc.licence()
        info = wx.AboutDialogInfo()
        #info.SetIcon(wx.Icon('hunter.png', wx.BITMAP_TYPE_PNG))
        info.SetName('PyCorrFit')
        info.SetVersion(self.version)
        info.SetDescription(description)
        info.SetCopyright('(C) 2011 - 2012 Paul Müller')
        info.SetWebSite(doc.HomePage)
        info.SetLicence(licence)
        info.SetIcon(misc.getMainIcon(pxlength=64))
        info.AddDeveloper('Paul Müller')
        info.AddDocWriter('Thomas Weidemann, Paul Müller')
        wx.AboutBox(info)
        

    def OnAddModel(self, event=None):
        """ Import a model from an external .txt file. See example model
            functions available on the web.
        """
        # Add a model using the dialog.
        filters = "text file (*.txt)|*.txt"
        dlg = wx.FileDialog(self, "Open model file", 
                            self.dirname, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            NewModel = usermodel.UserModel(self)
            # Workaround since 0.7.5
            (dirname, filename) = os.path.split(dlg.GetPath())
            #filename = dlg.GetFilename()
            #dirname = dlg.GetDirectory()
            self.dirname = dirname
            # Try to import a selected .txt file
            try:
                NewModel.GetCode( os.path.join(dirname, filename) )
            except:
                # The file does not seem to be what it seems to be.
                info = sys.exc_info()
                errstr = "Unknown file format:\n"
                errstr += str(filename)+"\n\n"
                errstr += str(info[0])+"\n"
                errstr += str(info[1])+"\n"
                for tb_item in traceback.format_tb(info[2]):
                    errstr += tb_item
                wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                del NewModel
                return
            # Test the code for sympy compatibility.
            # If you write your own parser, this might be easier.
            try:
                NewModel.TestFunction()
            except:
                # This means that the imported model file could be
                # contaminated. Ask the user how to proceed.
                text = "The model parsing check raised an Error.\n"+\
                       "This could be the result of a wrong Syntax\n"+\
                       "or an error of the parser.\n"+\
                       "This might be dangerous. Procceed\n"+\
                       "only, if you trust the source of the file.\n"+\
                       "Try and import offensive file: "+filename+"?"
                dlg2 = wx.MessageDialog(self, text, "Unsafe Operation",
                        style=wx.ICON_EXCLAMATION|wx.YES_NO|wx.STAY_ON_TOP)
                if dlg2.ShowModal() == wx.ID_YES:
                    NewModel.ImportModel()
                else:
                    del NewModel
                    return
            else:
                # The model was loaded correctly
                NewModel.ImportModel()
               
        else:
            dirname = dlg.GetDirectory()
            dlg.Destroy()
        self.dirname = dirname
            

    def OnClearSession(self,e=None,clearmodels=False):
        """Open a previously saved session. """
        numtabs = self.notebook.GetPageCount()
        # Ask, if user wants to save current session.
        if numtabs > 0:
            dial = wx.MessageDialog(self, 
                'Do you wish to save this session first?', 
                'Save current session?', 
                 wx.ICON_QUESTION | wx.CANCEL | wx.YES_NO | wx.NO_DEFAULT )
#            dial = edclasses.MyYesNoAbortDialog(self, 
#                    'Do you wish to save this session first?',
#                    'Save current session?')
            result = dial.ShowModal()
            dial.Destroy()
            if result == wx.ID_CANCEL:
                return "abort"      # stop this function - do nothing.
            elif result == wx.ID_YES:
                self.OnSaveSession()
            elif result == wx.ID_NO:
                pass
        # Delete all the pages
        self.notebook.DeleteAllPages()
        # Disable all the dialogs and menus
        self.EnableToolCurrent(False)
        self.OnFNBPageChanged()
        self.tabcounter = 1
        self.filename = None
        self.SetTitleFCS(None)
        self.SessionComment = "You may enter some information here."
        self.Background = list()
        ## Do we want to keep user defined models after session clearing?
        if clearmodels == True:
            # Also reset user defined models
            for modelid in mdls.modeltypes["User"]:    
                mdls.values.remove(mdls.valuedict[modelid])
                del mdls.valuedict[modelid]
                mdls.models.remove(mdls.modeldict[modelid])
                del mdls.modeldict[modelid]
            mdls.modeltypes["User"] = list()
            # Model Menu
            menu=self.modelmenudict["User"]
            for item in  menu.GetMenuItems():
                menu.RemoveItem(item)


    def OnCommSession(self,e=None):
        """ Dialog for commenting on session. """
        try:
            self.EditCommentDlg.IsEnabled()
        except AttributeError:
            # Dialog is not opened
            self.EditCommentDlg = tools.EditComment(self)
            self.EditCommentDlg.Bind(wx.EVT_CLOSE, self.EditCommentDlg.OnClose)
            self.filemenu.Check(self.menuComm.GetId(), True)
        else:
            # Close Dialog
            self.EditCommentDlg.OnClose()


    def OnDeletePage(self, event=None):
        """
        This method is based on the flatnotebook demo
 
        It removes a page from the notebook
        """
        # Ask the user if he really wants to delete the page.
        title = self.notebook.GetCurrentPage().tabtitle.GetValue()
        numb = self.notebook.GetCurrentPage().counter.strip().strip(":")
        text = "This will close page "+numb+"?\n"+title
        dlg = edclasses.MyOKAbortDialog(self, text, "Warning")
        if dlg.ShowModal() == wx.ID_OK:
            self.notebook.DeletePage(self.notebook.GetSelection())
            self.OnFNBClosedPage()
            if self.notebook.GetPageCount() == 0:
                self.OnFNBPageChanged()


    def OnDocumentation(self, e=None):
        """ Get the documentation and view it with browser"""
        filename = doc.GetLocationOfDocumentation()
        if filename is None:
            # Now we have to tell the user that there is no documentation
            self.StatusBar.SetStatusText("...documentation not found.")
        else:
            self.StatusBar.SetStatusText("...documentation: "+filename)
            if platform.system().lower() == 'windows':
                os.system("start /b "+filename)
            elif platform.system().lower() == 'linux':
                os.system("xdg-open "+filename+" &")
            elif platform.system().lower() == 'darwin':
                os.system("open "+filename+" &")
            else:
                # defaults to linux style:
                os.system("xdg-open "+filename+" &")
        

    def OnExit(self,e=None):
        numtabs = self.notebook.GetPageCount()
        # Ask, if user wants to save current session.
        if numtabs > 0:
            dial = wx.MessageDialog(self, 
                'Do you wish to save this session first?', 
                'Save current session?', 
                 wx.ICON_QUESTION | wx.CANCEL | wx.YES_NO | wx.NO_DEFAULT )
            result = dial.ShowModal()
            dial.Destroy()
            if result == wx.ID_CANCEL:
                return # stop this function - do nothing.
            elif result == wx.ID_YES:
                self.OnSaveSession()
        # Exit the Program
        self.Destroy()


    def OnFNBClosedPage(self,e=None):
        """ Called, when a page has been closed """
        if self.notebook.GetPageCount() == 0:
            # Grey out tools
            self.EnableToolCurrent(False)



    def OnFNBPageChanged(self,e=None, Page=None):
        """ Called, when 
            - Page focus switches to another Page
            - Page with focus changes significantly:
                - experimental data is loaded
                - weighted fit was done
        """
        # Get the Page
        if Page is None:
            Page = self.notebook.GetCurrentPage()
        keys = self.ToolsOpen.keys()
        for key in keys:
            # Update the information
            self.ToolsOpen[key].OnPageChanged(Page)
        # parameter range selection tool for page.
        if self.RangeSelector is not None:
            try:
                self.RangeSelector.OnPageChanged(Page)
            except:
                pass
        # Bugfix-workaround for mac:
        # non-existing tabs are still displayed upon clearing session
        if platform.system().lower() == "darwin":
            if self.notebook.GetPageCount() == 0:
                self.notebook.Hide()
            else:
                self.notebook.Show()
            


    def OnImportData(self,e=None):
        """Import experimental data from a all filetypes specified in 
           *opf.Filetypes*.
           Is called by the curmenu and applies to currently opened model.
        """
        # Open a data file
        # Get Data
        SupFiletypes = opf.Filetypes.keys()
        SupFiletypes.sort()
        filters = ""
        for i in np.arange(len(SupFiletypes)):
            # Add to the filetype filter
            filters = filters+SupFiletypes[i]
            if i+1 != len(SupFiletypes):
                # Add a separator, but not behind the last entry
                # This is wx widgets stuff.
                filters = filters+"|"
        dlg = wx.FileDialog(self, "Open data file", 
            self.dirname, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # The filename the page will get
            path = dlg.GetPath()            # Workaround since 0.7.5
            (self.dirname, self.filename) = os.path.split(path)
            #self.filename = dlg.GetFilename()
            #self.dirname = dlg.GetDirectory()
            try:
                Stuff = readfiles.openAny(self.dirname, self.filename)
            except:
                # The file format is not supported.
                info = sys.exc_info()
                errstr = "Unknown file format:\n"
                errstr += str(self.filename)+"\n\n"
                errstr += str(info[0])+"\n"
                errstr += str(info[1])+"\n"
                for tb_item in traceback.format_tb(info[2]):
                    errstr += tb_item
                wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                return
            else:
                dataexp = Stuff["Correlation"]
                trace = Stuff["Trace"]
                curvelist = Stuff["Type"]
                filename = Stuff["Filename"]
                # If curvelist is a list with more than one item, we are
                # importing more than one curve per file. Therefore, we
                # need to create more pages for this file.
                #
                # We want to give the user the possibility to choose from
                # several types of input functions. If curvelist contains
                # more than one type of data, like "AC1", "AC2", "CC1", ...
                # then the user may wish to only import "AC1" or "AC2"
                # functions.
                curvetypes = dict()
                for i in np.arange(len(curvelist)):
                    try:
                        curvetypes[curvelist[i]].append(i)
                    except KeyError:
                        curvetypes[curvelist[i]] = [i]
                # Now we have a dictionary curvetypes with keys that name
                # items in curvelist and which point to indices in curvelist.
                # We will display a dialog that let's the user choose what
                # to import.
                keys = curvetypes.keys()
                if len(keys) > 1:
                    Chosen = tools.ChooseImportTypes(self, curvetypes)
                    newcurvelist = list()
                    newfilename = list()
                    newdataexp = list()
                    newtrace = list()
                    if Chosen.ShowModal() == wx.ID_OK:
                        keys = Chosen.keys
                        if len(keys) == 0:
                            # do not do anything
                            return
                        for key in keys:
                            # create a new curvelist with the selected curves
                            for index in curvetypes[key]:
                                newcurvelist.append(curvelist[index])
                                newfilename.append(filename[index])
                                newdataexp.append(dataexp[index])
                                newtrace.append(trace[index])
                        curvelist = newcurvelist
                        filename = newfilename
                        dataexp = newdataexp
                        trace = newtrace
                    else:
                        return
                    Chosen.Destroy()
                # curvelist is a list of numbers or labels that correspond
                # to each item in dataexp or trace. Each curvelist/filename
                # item will be converted to a string and then added to the
                # pages title.
                num = len(curvelist) 
                # Show a nice progress dialog:
                style = wx.PD_REMAINING_TIME|wx.PD_SMOOTH|wx.PD_AUTO_HIDE|\
                        wx.PD_CAN_ABORT
                dlg = wx.ProgressDialog("Import", "Loading pages...",
                                        maximum = num, parent=self, style=style)
                # Get current page and populate
                CurPage = self.notebook.GetCurrentPage()
                for i in np.arange(num):
                    # Fill Page with data
                    self.ImportData(CurPage, dataexp[i], trace[i],
                                   curvetype=curvelist[i], filename=filename[i],
                                   curveid=i)
                    # Let the user abort, if he wants to:
                    # We want to do this here before an empty page is added
                    # to the notebok.
                    if dlg.Update(i+1, "Loading pages...")[0] == False:
                        dlg.Destroy()
                        return
                    if i+1 != num:
                        # Create new page.
                        # (Add n-1 pages while importing.)
                        CurPage = self.add_fitting_tab(event=None, 
                                             modelid=CurPage.modelid,
                                             counter=None)
                # We are finished here:
                return
        else:
            # User pressed "Abort" - do nothing.
            self.dirname = dlg.GetDirectory()
            dlg.Destroy()
            return


    def OnMyLeftUp(self, event):
        """
        Wrapper for LeftUp:
        We want to have a wrapper for the page closing event.
        The code was copied from "flatnotebook.py"        
        Handles the ``wx.EVT_LEFT_UP`` event for L{PageContainer}.
        :param `event`: a `wx.MouseEvent` event to be processed.
        """
        # Get the page container
        pc = self.notebook._pages
        # forget the zone that was initially clicked
        self._nLeftClickZone = fnb.FNB_NOWHERE
        where, tabIdx = pc.HitTest(event.GetPosition())
        FNB_X = 2
        FNB_TAB_X = 3
        if not pc.HasAGWFlag(fnb.FNB_NO_TAB_FOCUS):
            # Make sure selected tab has focus
            self.SetFocus()
        if where == FNB_X:
            # Make sure that the button was pressed before
            if pc._nXButtonStatus != fnb.FNB_BTN_PRESSED:
                return
            pc._nXButtonStatus = fnb.FNB_BTN_HOVER
            self.OnDeletePage(self.notebook.GetCurrentPage())
        elif where == FNB_TAB_X:
            # Make sure that the button was pressed before
            if pc._nTabXButtonStatus != fnb.FNB_BTN_PRESSED:
                return 
            pc._nTabXButtonStatus = fnb.FNB_BTN_HOVER
            self.OnDeletePage(self.notebook.GetCurrentPage())
        else:
            # Call what should have been called.
            pc.OnLeftUp(event)


    def ImportData(self, Page, dataexp, trace, curvetype="",
                   filename="", curveid="", run=""):
        CurPage = Page
        # Import traces. Traces are usually put into a list, even if there
        # is only one trace. The reason is, that for cross correlation, we 
        # have two traces and thus we have to import both.
        # In case of cross correlation, save that list of (two) traces
        # in the page.tracecc variable. Else, save the trace for auto-
        # correlations directly into the page.trace variable. We are
        # doing this in order to keep data types clean.
        if curvetype[0:2] == "CC":
            # For cross correlation, the trace has two components
            CurPage.IsCrossCorrelation = True
            CurPage.tracecc = trace
            CurPage.trace = None
        else:
            CurPage.IsCrossCorrelation = False
            CurPage.tracecc = None
            if trace is not None:
                CurPage.trace = trace
                CurPage.traceavg = trace[:,1].mean()
        # Import correlation function
        CurPage.dataexpfull = dataexp
        # We need this to be able to work with the data.
        # It actually does nothing to the data right now.
        CurPage.startcrop = None
        CurPage.endcrop = None
        # It might be possible, that we want the channels to be
        # fixed to some interval. This is the case if the 
        # checkbox on the "Channel selection" dialog is checked.
        self.OnFNBPageChanged()
        # Enable Fitting Button
        CurPage.Fit_enable_fitting()
        # Set new tabtitle value and strip leading or trailing
        # white spaces.
        if run != "":
            title = "{} r{:03d}-{}".format(filename, int(run), curvetype)
        else:
            title = "{} id{:03d}-{}".format(filename, int(curveid), curvetype)
        CurPage.tabtitle.SetValue(title.strip())
        # Plot everything
        CurPage.PlotAll()
        # Call this function to allow the "Channel Selection" window that
        # might be open to update itself.
        # We are aware of the fact, that we just did that
        self.OnFNBPageChanged()


    def OnLoadBatch(self, e):
        """ Open multiple data files and apply a single model to them
            We will create a new window where the user may decide which
            model to use.
        """
        ## Browse the file system
        SupFiletypes = opf.Filetypes.keys()
        # Sort them so we have "All suported filetypes" up front
        SupFiletypes.sort()
        filters = ""
        for i in np.arange(len(SupFiletypes)):
            # Add to the filetype filter
            filters = filters+SupFiletypes[i]
            if i+1 != len(SupFiletypes):
                # Add a separator if item is not last item
                filters = filters+"|"
        dlg = wx.FileDialog(self, "Open data files", 
            self.dirname, "", filters, wx.OPEN|wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            Datafiles = dlg.GetFilenames()
            # We rely on sorted filenames
            Datafiles.sort()
            # Workaround since 0.7.5
            paths = dlg.GetPaths()
            if len(paths) != 0:
                self.dirname = os.path.split(paths[0])[0]
            else:
                self.dirname = dlg.GetDirectory()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        ## Get information from the data files and let the user choose
        ## which type of curves to load and the corresponding model.
        # List of filenames that could not be opened
        BadFiles = list()
        # Lists for correlation, trace, type and names
        Correlation = list()
        Trace = list()
        Type = list()
        Filename = list()   # there might be zipfiles with additional name info
        #Run = list()        # Run number connecting AC1 AC2 CC12 CC21
        Curveid = list()    # Curve ID of each curve in a file
        for afile in Datafiles:
            try:
                Stuff = readfiles.openAny(self.dirname, afile)
            except:
                # The file does not seem to be what it seems to be.
                BadFiles.append(afile)
            else:
                for i in np.arange(len(Stuff["Type"])):
                    Correlation.append(Stuff["Correlation"][i])
                    Trace.append(Stuff["Trace"][i])
                    Type.append(Stuff["Type"][i])
                    Filename.append(Stuff["Filename"][i])
                    #Curveid.append(str(i+1))
        # Add number of the curve within a file.
        nameold = None
        counter = 1
        for name in Filename:
            if name == nameold:
                Curveid.append(counter)
                counter += 1
            else:
                counter = 1
                nameold = name
                Curveid.append(counter)
                counter += 1
        # If there are any BadFiles, we will let the user know.
        if len(BadFiles) > 0:
            # The file does not seem to be what it seems to be.
            errstr = "The following files could not be processed:\n"
            for item in BadFiles:
                errstr += " "+item
            dlg = wx.MessageDialog(self, errstr, "Error", 
                style=wx.ICON_WARNING|wx.OK|wx.CANCEL|wx.STAY_ON_TOP)
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
        # Abort, if there are no curves left
        if len(Type) == 0:
            return
        # We want to give the user the possibility to choose from
        # several types of input functions. If curvelist contains
        # more than one type of data, like "AC1", "AC2", "CC1", ...
        # then the user may wish to only import "AC1" or "AC2"
        # functions.
        curvetypes = dict()
        for i in np.arange(len(Type)):
            try:
                curvetypes[Type[i]].append(i)
            except KeyError:
                curvetypes[Type[i]] = [i]
        # Fill in the Run information
        keys = curvetypes.keys()
        # This part is a little tricky. We assume at some point, that different
        # types of curves (AC1, AC2) belong to the same run. The only possible
        # chek/assumtion that we can make is:
        # If all curvetypes have the same amount of curves, then the curves
        # from different curvetypes belong together.
        # Unfortunately, we do not know how the curves are ordered. It could
        # be like this:
        # AC1-r1, AC2-r1, CC12-r1, CC21-r1, AC1-r2, AC1-r2, ...
        # or otherwise interlaced like this:
        # AC1-r1, AC2-r1, AC1-r2, AC1-r2, ... ,  CC12-r1, CC21-r1, ...
        # What we do know is that the first occurence of AC1 matches up with
        # the first occurences of AC2, CC12, etc.
        # We create the list/array *Run* whose elements are the run-number
        # at the position of the curves in *Types*.
        # Check if the type of curves have equal length
        lentypes = np.zeros(len(keys), dtype=int)
        for i in range(len(keys)):
            lentypes[i] = len(curvetypes[keys[i]])
        if len(np.unique(np.array(lentypes))) == 1 and lentypes[0] != 0:
            # Made sure that AC1 AC2 CC12 CC21 have same length
            # Create Runs such that they are matched.
            # We assume that the curves are somehow interlaced and that
            # the Nth occurence of the keys in Types correspond to the
            # matching curves.
            # Also make sure that number starts at one for each selected file.
            coords = np.zeros(len(keys), dtype=np.int)
            Run = np.zeros(len(Curveid), dtype=np.int)
            WorkType = 1*Type
            for fname in np.unique(Filename):
                # unique returns sorted file names.
                for i in range(Filename.count(fname)/len(keys)):
                    for k in range(len(keys)):
                        coords[k] = WorkType.index(keys[k])
                        WorkType[coords[k]] = None
                    Run[coords] = i + 1
                #del WorkType
        else:
            Run = [""] * len(Curveid)
        # Now we have a dictionary curvetypes with keys that name
        # items in *Type* and which point to indices in *Type*.
        # We will display a dialog that lets the user choose what
        # to import.
        keys = curvetypes.keys()
        # Start the dialog for choosing types and model functions
        labels=list()
        for i in np.arange(len(Filename)):
            if Run[i] != "":
                labels.append("{} r{:03d}-{}".format(Filename[i],
                                                     Run[i], Type[i]))
            else:
                labels.append("{} id{:03d}-{}".format(Filename[i],
                                                      Curveid[i], Type[i]))
        Chosen = tools.ChooseImportTypesModel(self, curvetypes, Correlation,
                                              labels=labels)
        newCorrelation = list()
        newTrace = list()
        newType = list()
        newFilename = list()
        modelList = list()
        newCurveid = list()
        newRun = list()
        if Chosen.ShowModal() == wx.ID_OK:
            keys = Chosen.typekeys
            # Keepdict is a list of indices pointing to Type or Correlation
            # of curves that are supposed to be kept.
            keepcurvesindex = Chosen.keepcurvesindex
            # modelids is a dictionary with chosen modelids.
            # The keys of modelids are indices in the *Type* etc. lists.
            modelids = Chosen.modelids
            if len(keys) == 0:
                # do not do anything
                return
            for key in keys:
                # create a new curvelist with the selected curves
                for index in curvetypes[key]:
                    if keepcurvesindex.count(index) == 1:
                        newCorrelation.append(Correlation[index])
                        newTrace.append(Trace[index])
                        newType.append(Type[index])
                        newFilename.append(Filename[index])
                        modelList.append(modelids[index])
                        newCurveid.append(Curveid[index])
                        newRun.append(Run[index])
            Correlation = newCorrelation
            Trace = newTrace
            Type = newType
            Filename = newFilename
            Curveid = newCurveid
            Run = newRun
        else:
            return
        Chosen.Destroy()
        ## Import the data into new pages
        # curvelist is a list of numbers or labels that correspond
        # to each item in dataexp or trace. Each curvelist/filename
        # item will be converted to a string and then added to the
        # pages title.
        num = len(Type)
        # Show a nice progress dialog:
        style = wx.PD_REMAINING_TIME|wx.PD_SMOOTH|wx.PD_AUTO_HIDE|\
                wx.PD_CAN_ABORT
        dlg = wx.ProgressDialog("Import", "Loading pages..."
        , maximum = num, parent=self, style=style)
        for i in np.arange(num):
            # create a new page
            CurPage = self.add_fitting_tab(event=None, 
                                     modelid=modelList[i],
                                     counter=None)
            # Fill Page with data
            self.ImportData(CurPage, Correlation[i], Trace[i],
                            curvetype=Type[i], filename=Filename[i],
                            curveid=str(Curveid[i]), run=str(Run[i]))
            # Let the user abort, if he wants to:
            # We want to do this here before an empty page is added
            # to the notebok.
            if dlg.Update(i+1, "Loading pages...")[0] == False:
                dlg.Destroy()
                return
        # If the user did not select curves but chose a model, destroy
        # the dialog.
        dlg.Destroy()


    def OnOpenSession(self,e=None,sessionfile=None):
        """Open a previously saved session. 
           Optional parameter sessionfile defines the file that shall be
           automatically loaded (without a dialog)
        """
        # We need to clear the session before opening one.
        # This will also ask, if user wants to save the current session.
        clear = self.OnClearSession(clearmodels=True)
        if clear == "abort":
            # User pressed abort when he was asked if he wants to save the
            # session.
            return "abort"
        Infodict, self.dirname, filename = \
         opf.OpenSession(self, self.dirname, sessionfile=sessionfile)
        # Check, if a file has been opened
        if filename is not None:
            # Reset all Pages. We already gave the user the possibility to
            # save his session.
            # self.OnClearSession()
            self.filename = filename
            self.SetTitleFCS(self.filename)
            ## Background traces
            try:
                self.Background = Infodict["Backgrounds"]
            except:
                pass
            ## Preferences
            ## if Preferences is Not None:
            ## add them!
            # External functions
            for key in Infodict["External Functions"].keys():
                NewModel = usermodel.UserModel(self)
                # NewModel.AddModel(self, code)
                # code is a list with strings
                # each string is one line
                NewModel.AddModel(
                    Infodict["External Functions"][key].splitlines())
                NewModel.ImportModel()
            # Internal functions:
            N = len(Infodict["Parameters"])
            # Reset tabcounter
            self.tabcounter = 1
            # Show a nice progress dialog:
            style = wx.PD_REMAINING_TIME|wx.PD_SMOOTH|wx.PD_AUTO_HIDE|\
                    wx.PD_CAN_ABORT
            dlg = wx.ProgressDialog("Import", "Loading pages..."
            , maximum = N, parent=self, style=style)
            for i in np.arange(N):
                # Let the user abort, if he wants to:
                if dlg.Update(i+1, "Loading pages...")[0] == False:
                    dlg.Destroy()
                    return
                # Add a new page to the notebook. This page is created with
                # variables from models.py. We will write our data to
                # the page later.
                counter = Infodict["Parameters"][i][0]
                modelid = Infodict["Parameters"][i][1]
                self.add_fitting_tab(modelid=modelid, counter=counter)
                # Get New Page, so we can add our stuff.
                Newtab = self.notebook.GetCurrentPage()
                # Add experimental Data
                # Import dataexp:
                number = counter.strip().strip(":").strip("#")
                pageid = int(number)
                [tau, dataexp] = Infodict["Correlations"][pageid]
                if dataexp is not None:
                    # Write experimental data
                    Newtab.dataexpfull = dataexp
                    Newtab.dataexp = True # not None
                # As of 0.7.3: Add external weights to page
                try:
                    Newtab.external_std_weights = \
                                   Infodict["External Weights"][pageid]
                except KeyError:
                    # No data
                    pass
                else:
                    # Add external weights to fitbox
                    WeightKinds = Newtab.Fitbox[1].GetItems()
                    wkeys = Newtab.external_std_weights.keys()
                    wkeys.sort()
                    for wkey in wkeys:
                        WeightKinds += [wkey]
                    Newtab.Fitbox[1].SetItems(WeightKinds)
                self.UnpackParameters(Infodict["Parameters"][i], Newtab)
                # Supplementary data
                try:
                    Sups = Infodict["Supplements"][pageid]
                except KeyError:
                    pass
                else:
                    errdict = dict()
                    for errInfo in Sups["FitErr"]:
                        for ierr in np.arange(len(errInfo)):
                            errkey = mdls.valuedict[modelid][0][int(errInfo[0])]
                            errval = float(errInfo[1])
                            errdict[errkey] = errval
                    Newtab.parmoptim_error = errdict
                    try:
                        Newtab.GlobalParameterShare = Sups["Global Share"]
                    except:
                        pass
                    try:
                        Newtab.chi2 = Sups["Chi sq"]
                    except:
                        pass
                # Set Title of the Page
                try:
                    Newtab.tabtitle.SetValue(Infodict["Comments"][pageid])
                except:
                    pass # no page title
                # Import the intensity trace
                try:
                    trace = Infodict["Traces"][pageid]
                except:
                    trace = None
                if trace is not None:
                    if Newtab.IsCrossCorrelation is False:
                        Newtab.trace = trace[0]
                        Newtab.traceavg = trace[0][:,1].mean()
                    else:
                        Newtab.tracecc = trace
                # Plot everything
                Newtab.PlotAll()
            # Set Session Comment
            try:
                self.SessionComment = Infodict["Comments"]["Session"]
            except:
                pass
            try:
                Infodict["Preferences"] # not used yet
            except:
                pass
            if self.notebook.GetPageCount() > 0:
                # Enable the "Current" Menu
                self.EnableToolCurrent(True)
                self.OnFNBPageChanged()
            else:
                # There are no pages in the session.
                # Disable some menus and close some dialogs
                self.EnableToolCurrent(False)


    def OnSaveData(self,e=None):
        # Save the Data
        """ Save calculated Data including optional fitted exp. data. """
        # What Data do we wish to save?
        Page = self.notebook.GetCurrentPage()
        # Export CSV
        # If no file has been selected, self.filename will be set to 'None'.
        self.dirname, self.filename = opf.saveCSV(self, self.dirname, Page)


    def OnSavePlotCorr(self, e=None):
        """ make some output """
        # Saving dialog box.
        uselatex = self.MenuUseLatex.IsChecked()
        verbose = self.MenuVerbose.IsChecked()
        show_weights = self.MenuShowWeights.IsChecked()
        Page = self.notebook.GetCurrentPage()
        plotting.savePlotCorrelation(self, self.dirname, Page, uselatex,
                                     verbose, show_weights)


    def OnSavePlotTrace(self, e=None):
        """ make some output """
        # Saving dialog box.
        uselatex = 1*self.MenuUseLatex.IsChecked()
        verbose = 1*self.MenuVerbose.IsChecked()
        Page = self.notebook.GetCurrentPage()
        plotting.savePlotTrace(self, self.dirname, Page, uselatex, verbose)


    def OnSaveSession(self,e=None):
        """Save a session for later continuation."""
        # Parameters are all in one dictionary:
        Infodict = dict()
        Infodict["Backgrounds"] = self.Background # Background list
        Infodict["Comments"] = dict() # Session comment "Session" and Pages int
        Infodict["Correlations"] = dict() # all correlation curves
        Infodict["External Functions"] = dict() # external model functions
        Infodict["External Weights"] = dict() # additional weights for the pages
        Infodict["Parameters"] = dict() # all parameters of all pages
        Infodict["Preferences"] = dict() # not used
        Infodict["Supplements"] = dict() # error estimates for fitting
        Infodict["Traces"] = dict() # all traces
        # Save each Page
        N = self.notebook.GetPageCount()
        # External functions
        for usermodelid in mdls.modeltypes["User"]:
            # Those models belong to external user functions.
            doc = mdls.modeldict[usermodelid][-1].func_doc
            doc = doc.splitlines()
            docnew=""
            for line in doc:
                docnew = docnew+line.strip()+"\r\n"
            Infodict["External Functions"][usermodelid] = docnew
        for i in np.arange(N):
            # Set Page 
            Page = self.notebook.GetPage(i)
            counter = int(Page.counter.strip().strip(":").strip("#"))
            # Apply currently set parameters
            Page.apply_parameters()
            # Set parameters
            Infodict["Parameters"][counter] = self.PackParameters(Page)
            # Set supplementary information, such as errors of fit
            if Page.parmoptim_error is not None: # == if Page.chi2 is not None
                Infodict["Supplements"][counter] = dict()
                Infodict["Supplements"][counter]["Chi sq"] = float(Page.chi2)
                PageList = list()
                for pagei in Page.GlobalParameterShare:
                    PageList.append(int(pagei))
                Infodict["Supplements"][counter]["Global Share"] = PageList
                                                
                Alist = list()
                for key in Page.parmoptim_error.keys():
                    position = mdls.GetPositionOfParameter(Page.modelid, key)
                    Alist.append([ int(position),
                                   float(Page.parmoptim_error[key]) ])
                    Infodict["Supplements"][counter]["FitErr"] = Alist
            # Set exp data
            Infodict["Correlations"][counter] = [Page.tau, Page.dataexpfull]
            # Also save the trace
            if Page.IsCrossCorrelation is False:
                Infodict["Traces"][counter] = Page.trace
                # #Function_trace.append(Page.trace)
            else:
                # #Function_trace.append(Page.tracecc)
                Infodict["Traces"][counter] = Page.tracecc
            # Append title to Comments
            # #Comments.append(Page.tabtitle.GetValue())
            Infodict["Comments"][counter] = Page.tabtitle.GetValue()
            # Add additional weights to Info["External Weights"]
            if len(Page.external_std_weights) != 0:
                Infodict["External Weights"][counter] = Page.external_std_weights
        # Append Session Comment:
        Infodict["Comments"]["Session"] = self.SessionComment
        # Save everything
        # If no file has been selected, self.filename will be set to 'None'.
        self.dirname, self.filename = opf.SaveSession(self, self.dirname,
          Infodict)
        #Function_parms, Function_array, Function_trace, self.Background,
        #Preferences, Comments, ExternalFunctions, Info)
        # Set title of our window
        self.SetTitleFCS(self.filename)


    def OnShell(self, e=None):
        Shell = wx.py.shell.ShellFrame(self, title="PyCorrFit Shell",
                 style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT,
                 locals=locals())
        # Set window icon
        if self.MainIcon is not None:
            wx.Frame.SetIcon(Shell, self.MainIcon)
        Shell.Show(True)


    def OnSoftware(self, event=None):
        # Show About Information
        text = doc.SoftwareUsed()
        wx.MessageBox(text, 'Software', wx.OK | wx.ICON_INFORMATION)


    def OnTool(self, event):
        eid = event.GetId()
        try:
            # Check if a tool is open
            self.ToolsOpen[eid]
        except KeyError:
            # eid is not on self.ToolOpen
            # So we open the dialog and add it to the list
            self.ToolsOpen[eid] = self.Tools[eid](self)
            self.ToolsOpen[eid].MyID = eid
            self.ToolsOpen[eid].Bind(wx.EVT_CLOSE, self.ToolsOpen[eid].OnClose)
            self.toolmenu.Check(eid, True)
        else:
            # We close it then
            self.ToolsOpen[eid].OnClose()


    def OnUpdate(self, event):
        misc.Update(self)


    def OnWiki(self, e=None):
        """ Go to the GitHub Wiki page"""
        webbrowser.open(doc.GitWiki)
        

    def PackParameters(self, Page):
        """ Gets all parameters from a page and returns a list object,
            that can be used to save as e.g. a safe YAML file 
        """
        Page.apply_parameters()
        # Get Model ID
        modelid = Page.modelid
        # Get Page number
        counter = Page.counter
        active_numbers = Page.active_parms[1]       # Array, Parameters
        active_fitting = Page.active_parms[2]
        crop = [Page.startcrop, Page.endcrop]
        Parms = [counter, modelid, active_numbers, active_fitting, crop]
        # Weighting:
        # Additional parameters as of v.0.2.0
        # Splines and model function:
        # Additional parameters as of v.6.4.0
        #self.Fitbox=[ fitbox, weightedfitdrop, fittext, fittext2, fittextvar,
        #                fitspin, buttonfit ]
        # Some fits like Spline have a number of knots of the spline
        # that is important for fitting. If there is a number in the
        # Dropdown, save it.
        #
        knots = str(Page.FitKnots)
        knots = filter(lambda x: x.isdigit(), knots)
        if len(knots) == 0:
            knots = None
        else:
            knots = int(knots)
        weighted = Page.weighted_fittype_id
        weights = Page.weighted_nuvar
        Parms.append([weighted, weights, knots])
        # Additional parameters as of v.0.2.9
        # Which Background signal is selected?
        # The Background information is in the list *self.Background*.
        Parms.append([Page.bgselected, Page.bg2selected])
        # Additional parameter as of v.0.5.8
        # Is the Experimental data (if it exists) AC or CC?
        Parms.append(Page.IsCrossCorrelation)
        # Additional parameter as of v.0.7.8
        # The selection of a normalization parameter (None or integer)
        if Page.normparm is not None:
            # We need to do this because yaml export would not work
            # in safe mode.
            Page.normparm=int(Page.normparm)
        Parms.append(Page.normparm)
        # Parameter ranges
        Parms.append(Page.parameter_range)
        return Parms


    def UnpackParameters(self, Parms, Page):
        """ Apply the given parameters to the Page in question.
            This function contains several *len(Parms) >= X* statements.
            These are used for opening sessions that were saved using
            earlier versions of PyCorrFit.
        """
        modelid = Parms[1]
        if Page.modelid != modelid:
            print "Wrong model: "+str(Page.modelid)+" vs. "+str(modelid)
            return
        active_values = Parms[2]
        active_fitting = Parms[3]
        # As of version 0.7.0: square pinhole TIR-FCS models
        # use sigma instead of lambda, NA and sigma_0. This
        # is for backwards compatibility:
        changeTIRF = False
        if modelid in [6000, 6010]:
            if len(Parms[2]) > len(mdls.valuedict[modelid][0]):
                lindex = 1
                changeTIRF = True
        elif modelid in [6020, 6021, 6022, 6023]:
            if len(Parms[2]) > len(mdls.valuedict[modelid][0]):
                lindex = 2
                changeTIRF = True
        if changeTIRF:
            lamb = active_values[lindex]
            NA = active_values[lindex+1]
            sigma = 0.21*lamb/NA
            active_values[lindex] = sigma
            active_values = np.delete(active_values,lindex+1)
            active_fitting = np.delete(active_fitting, lindex+1)
        # Cropping: What part of dataexp should be displayed.
        [cropstart, cropend] = Parms[4]
        # Add parameters and fitting to the created page.
        # We need to run Newtab.apply_parameters_reverse() in order
        # for the data to be displayed in the user interface.
        Page.active_parms[1] = active_values
        Page.active_parms[2] = active_fitting
        # Cropping
        Page.startcrop = cropstart
        Page.endcrop = cropend
        Page.crop_data()
        # Weighted fitting
        if len(Parms) >= 6:
            if len(Parms[5]) == 2:
                [weighted, weights] = Parms[5]
                knots = None
            else:
                # We have knots as of v. 0.6.5
                [weighted, weights, knots] = Parms[5]
            if knots is not None:
                # This is done with apply_paramters_reverse:
                #       text = Page.Fitbox[1].GetValue()
                #       text = filter(lambda x: x.isalpha(), text)
                #       Page.Fitbox[1].SetValue(text+str(knots))
                Page.FitKnots = int(knots)
            if weighted is False:
                weighted = 0
            elif weighted is True:
                weighted = 1
            elif len(Page.Fitbox[1].GetItems())-1 < weighted:
                # Is the case, e.g. when we have an average std,
                # but this page is not an average.
                weighted = 0
            Page.weighted_fittype_id = weighted
            Page.weighted_nuvar = weights
        Page.apply_parameters_reverse()

        if Page.dataexp is not None:
            Page.Fit_enable_fitting()
            Page.Fit_WeightedFitCheck()
            Page.Fit_create_instance()
        if Page.weighted_fit_was_performed:
            # We need this to plot std-dev
            Page.calculate_corr()
            Page.data4weight = 1.*Page.datacorr
        # Set which background correction the Page uses:
        if len(Parms) >= 7:
            # causality check:
            if len(self.Background) > Parms[6][0]:
                Page.bgselected = Parms[6][0]
                if len(Parms[6]) == 2:
                    # New in 0.8.1: CC background correction
                    Page.bg2selected = Parms[6][1]
                # New feature since 0.7.8: BG selection on Page panel
                Page.OnAmplitudeCheck("init")
        # Set if Newtab is of type cross-correlation:
        if len(Parms) >= 8:
            Page.IsCrossCorrelation = Parms[7]
        if len(Parms) >= 9:
            # New feature in 0.7.8 includes normalization to a fitting
            # parameter.
            Page.normparm = Parms[8]
            Page.OnAmplitudeCheck("init")
        if len(Parms) >= 10:
            Page.parameter_range = np.array(Parms[9])
        ## If we want to add more stuff, we should do something like:
        ##   if len(Parms) >= 11:
        ##       nextvalue = Parms[10]
        ## Such that we are compatible to earlier versions of 
        ## PyCorrFit sessions.
        


    def SetTitleFCS(self, title):
        if title is not None and len(title) != 0:
            title = " {"+title+"}"
            self.SetTitle('PyCorrFit ' + self.version + title)
        else:
            self.SetTitle('PyCorrFit ' + self.version)
