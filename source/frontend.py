# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

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
"""

# Generic modules
import os
import wx                               # GUI interface wxPython
import wx.lib.agw.flatnotebook as fnb   # Flatnotebook (Tabs)
import numpy as np                      # NumPy
import platform
import sys                              # System stuff
import traceback                        # for Error handling

# PyCorrFit modules
import doc                          # Documentation/some texts
import edclasses
try:
    import misc
except ImportError:
    print " Some modules are not available."
    print " Update function will not work."
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
        self.fnb = fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY,
        style=fnb.FNB_SMART_TABS|fnb.FNB_NO_NAV_BUTTONS|\
              fnb.FNB_DROPDOWN_TABS_LIST|fnb.FNB_NODRAG|\
              fnb.FNB_TABS_BORDER_SIMPLE)



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
        initial_size = (768,586)
        self.SetSize(initial_size)
        self.SetMinSize(initial_size)

        # Set this, so we know in which directory we are working in.
        # This will change, when we load a session or data file.
        self.dirname = os.curdir
        self.filename = None

        # Session Comment - may be edited and saved later
        self.SessionComment = "You may enter some information here."

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
        self.tabcounter = 0

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

        # If user hits the "x", ask if he wants to save
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        


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
            self.tabcounter = max(int(counter[1:len(counter)-2]), 
                                  self.tabcounter)
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
        self.notebook.AddPage(Newtab, counter+model, select=True)
        self.tabcounter = self.tabcounter + 1
        # Enable the "Current" Menu
        self.EnableToolCurrent(True)
        return Newtab



    def EnableToolCurrent(self, enabled):
        """ Independent on order of menus, enable or disable tools and
            current menu.
        """
        tid = self.menuBar.FindMenu("&Tools")
        self.menuBar.EnableTop(tid, enabled)
        cid = self.menuBar.FindMenu("Current &Page")
        self.menuBar.EnableTop(cid, enabled)
        if enabled == False:
            # Close all the dialogs
            keys = self.ToolsOpen.keys()
            for key in keys:
                # Close it
                self.ToolsOpen[key].Close()
            # Uncheck all the tool menu items
            for item in self.toolmenu.GetMenuItems():
                if item.IsCheckable() is True:
                    # This means, that we hit a separator
                    self.toolmenu.Check(item.GetId(), False)

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
        #menuLoadSingle = self.filemenu.Append(wx.ID_ANY, 
        #                          "&Load single data file", "Load a data file")
        menuLoadBatch = self.filemenu.Append(wx.ID_ANY, 
                         "&Load data files", "Loads one or multiple data files")
        menuAddModel = self.filemenu.Append(wx.ID_ANY, 
                          "&Import model function", "Add a user defined model.")
        self.filemenu.AppendSeparator()
        self.menuComm = self.filemenu.Append(wx.ID_ANY, "Co&mment session", 
                           "Add a comment to this session", kind=wx.ITEM_CHECK)
        self.filemenu.Check(self.menuComm.GetId(), False)
        menuClear = self.filemenu.Append(wx.ID_CLEAR, "&Clear session", 
                                "Deletes all progress made during this session")
        menuOpen = self.filemenu.Append(wx.ID_OPEN, "&Open session", 
                                           "Restore a previously saved session")
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

        # toolmenu
        for ttype in tools.ToolDict:
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
                                     "&Save trace view as image",
                                     "Export current trace as image.")

        self.curmenu.AppendSeparator()
        menuClPa = self.curmenu.Append(wx.ID_ANY, "&Close Page",
                                       "Close Current Page")
        # Model menu
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
                menuentry = submenu.Append(model[0], model[1], model[2])
                self.Bind(wx.EVT_MENU, self.add_fitting_tab, menuentry)

        menuSoftw = helpmenu.Append(wx.ID_ANY, "&Software used",
                                    "Information about the software used")
        menuAbout = helpmenu.Append(wx.ID_ABOUT, "&About",
                                    "Information about this program")
        menuUpdate = helpmenu.Append(wx.ID_ANY, "&Update",
                                    "Check for new version of PyCorrFit"+
                                     " (Web access required)")


        # Creating the menubar.
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



    #Help
    def OnAbout(self, event):
        # Show About Information
        description = doc.description()
        licence = doc.licence()
        info = wx.AboutDialogInfo()
        #info.SetIcon(wx.Icon('hunter.png', wx.BITMAP_TYPE_PNG))
        info.SetName('PyCorrFit')
        info.SetVersion(self.version)
        info.SetDescription(description)
        info.SetCopyright('(C) 2011 - 2012 Paul Müller')
        info.SetWebSite(doc.HomePage)
        info.SetLicence(licence)
        info.AddDeveloper('Paul Müller')
        info.AddDocWriter('Paul Müller')
        wx.AboutBox(info)

    def OnAddModel(self, event=None):
        """ Import a model from an external .txt file. See example model
            functions available on the web.
        """
        # Add a model using the dialog.
        filters = "text file (*.txt)|*.txt"
        dlg = wx.FileDialog(self, "Choose a model file", 
                            self.dirname, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            NewModel = usermodel.UserModel(self)
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
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
                dlg3 = wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                dlg3.ShowModal() == wx.ID_OK
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
            result = dial.ShowModal()
            dial.Destroy()
            if result == wx.ID_CANCEL:
                return "abort"      # stop this function - do nothing.
            elif result == wx.ID_YES:
                self.OnSaveSession()
        # Close all the dialogs and disable menus
        self.EnableToolCurrent(False)
        # Delete all the pages
        for i in np.arange(numtabs):
            idp = numtabs-i-1
            self.notebook.DeletePage(idp)
        self.EnableToolCurrent(False)
        self.tabcounter = 0
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
        self.notebook.DeletePage(self.notebook.GetSelection())


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
            # Disable Current Menu and close their dialogs
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
        dlg = wx.FileDialog(self, "Choose a data file", 
            self.dirname, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # The filename the page will get
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
          #  filterindex = dlg.GetFilterIndex()
          #  Filetype = SupFiletypes[filterindex]
          #  # This is the function we will use to import the data
          #  # opf.Filetypes is a dictionary with that has a key *self.Filetype*
          #  # which points to our import function:
          #  OpenFile = opf.Filetypes[Filetype]
            try:
                Stuff = readfiles.openAny(self.dirname, self.filename)
            except:
                # The file does not seem to be what it seems to be.
                info = sys.exc_info()
                errstr = "Unknown file format:\n"
                errstr += str(self.filename)+"\n\n"
                errstr += str(info[0])+"\n"
                errstr += str(info[1])+"\n"
                for tb_item in traceback.format_tb(info[2]):
                    errstr += tb_item
                dlg = wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                dlg.ShowModal() == wx.ID_OK
                return
            else:
                dataexp = Stuff["Correlation"]
                trace = Stuff["Trace"]
                curvelist = Stuff["Type"]
                filename = Stuff["Filename"]
                
                # If curvelist is a list with more than one item, we are
                # importing more than one curve per file. Therefore, we
                # need to create more pages for this file.
                
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
                dlg = wx.ProgressDialog("Import", "Loading pages..."
                , maximum = num, parent=self, style=style)
                
                CurPage = self.notebook.GetCurrentPage()
                for i in np.arange(num):
                    # Fill Page with data
                 #   #if i == 0:
                 #   #    # The tab title still holds the old filename
                 #   #    # We do not want this:
                 #   #    # *filename* is always a string
                 #   ##    M = len(CurPage.filename)
                 #   #    text = CurPage.tabtitle.GetValue()
                 #   #    if text[0:M] == CurPage.filename:
                 #   #        CurPage.tabtitle.SetValue(text[M:])
                 #   # Now we may change the filename.
                 #   #CurPage.filename = str(filename[i])+" "+str(curvelist[i])
                 #   # Strip leading or trailing white spaces.
                 #   #CurPage.filename = CurPage.filename.strip()
                    self.ImportData(CurPage, dataexp[i], trace[i],
                                    curvelist[i], filename[i])
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


    def ImportData(self, Page, dataexp, trace, curvetype="", filename=""):
        CurPage = Page
        # Import traces. Traces are usually put into a list, even if there
        # is only on trace. The reason is, that for cross correlation, we 
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
   #     # Set Title
   #    # N = len(CurPage.modelname)
   #    # M = len(CurPage.filename)
   #    # text = CurPage.tabtitle.GetValue()
        # Set new tabtitle value and strip leading or trailing
        # white spaces.
        title = filename+" "+curvetype
        CurPage.tabtitle.SetValue(title.strip())
   #    # if text[0:N] == CurPage.modelname:
   #    #     CurPage.tabtitle.SetValue(CurPage.filename+" "+
   #    #                               CurPage.modelname+text[N:-1].strip())
   #    # elif text[0:M] == CurPage.filename:
   #    #     CurPage.tabtitle.SetValue(CurPage.filename+text[M:].strip())
   #    # else:
   #    #     CurPage.tabtitle.SetValue(CurPage.filename+" "+text.strip())
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
        dlg = wx.FileDialog(self, "Choose data files", 
            self.dirname, "", filters, wx.OPEN|wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            Datafiles = dlg.GetFilenames()
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
        Filename = list() # there might be zipfiles with additional name info
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

        # If *Type* is a list with more than one item, we are
        # importing more than one curve per file. Therefore, we
        # need to create more pages for this file.
        
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
        # Now we have a dictionary curvetypes with keys that name
        # items in *Type* and which point to indices in *Type*.
        # We will display a dialog that let's the user choose what
        # to import.
        keys = curvetypes.keys()
        # Start the dialog for choosing types and model functions
        Chosen = tools.ChooseImportTypesModel(self, curvetypes)
        newCorrelation = list()
        newTrace = list()
        newType = list()
        newFilename = list()
        modelList = list()
        if Chosen.ShowModal() == wx.ID_OK:
            keys = Chosen.keys
            # modelids is a dictionary with chosen modelids.
            # The keys of modelids are indices in the *Type* etc. lists.
            modelids = Chosen.modelids
            if len(keys) == 0:
                # do not do anything
                return
            for key in keys:
                # create a new curvelist with the selected curves
                for index in curvetypes[key]:
                    newCorrelation.append(Correlation[index])
                    newTrace.append(Trace[index])
                    newType.append(Type[index])
                    newFilename.append(Filename[index])
                    modelList.append(modelids[index])
            Correlation = newCorrelation
            Trace = newTrace
            Type = newType
            Filename = newFilename
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
                            Type[i], Filename[i])
            # Let the user abort, if he wants to:
            # We want to do this here before an empty page is added
            # to the notebok.
            if dlg.Update(i+1, "Loading pages...")[0] == False:
                dlg.Destroy()
                return        


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
        Function_parms, Function_array, Function_trace, Background, \
         Preferences, Comments, ExternalFunctions, self.dirname, filename = \
         opf.OpenSession(self, self.dirname, sessionfile=sessionfile)
        # Check, if a file has been opened
        if filename is not None:
            # Reset all Pages. We already gave the user the possibility to
            # save his session.
            # self.OnClearSession()
            self.filename = filename
            self.SetTitleFCS(self.filename)
            ## Background traces
            self.Background = Background
            ## Preferences
            ## if Preferences is Not None:
            ## add them!
            # External functions
            for key in ExternalFunctions.keys():
                NewModel = usermodel.UserModel(self)
                # NewModel.AddModel(self, code)
                # code is a list with strings
                # each string is one line
                NewModel.AddModel(ExternalFunctions[key].splitlines())
                NewModel.ImportModel()

            # Internal functions:
            N = len(Function_parms)
            # Reset tabcounter
            self.tabcounter = 0
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
                # As of v.0.2.0
                # Import dataexp:
                [tau, dataexp] = Function_array[i]
                # Add a new page to the notebook. This page is created with
                # variables from models.py. We will write our data to
                # the page later.
                counter = Function_parms[i][0]
                modelid = Function_parms[i][1]
                self.add_fitting_tab(modelid=modelid, counter=counter)
                # Get New Page, so we can add our stuff.
                Newtab = self.notebook.GetCurrentPage()
                # Add experimental Data
                if dataexp is not None:
                    # Write experimental data
                    Newtab.dataexpfull = dataexp
                    Newtab.dataexp = True
                    # Enable fitting button

                self.UnpackParameters(Function_parms[i], Newtab)

                # Set Title of the Page
                if Comments is not None:
                    Newtab.tabtitle.SetValue(Comments[i])

                # Import the intensity trace
                trace = Function_trace[i]
                if trace is not None:
                    if Newtab.IsCrossCorrelation is False:
                        Newtab.trace = trace[0]
                        Newtab.traceavg = trace[0][:,1].mean()
                    else:
                        Newtab.tracecc = trace
                # Plot everything
                Newtab.PlotAll()
            # Set Session Comment
            if Comments is not None:
                self.SessionComment = Comments[-1]

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
        Page = self.notebook.GetCurrentPage()
        plotting.savePlotCorrelation(self, self.dirname, Page, uselatex,
                                     verbose)
        
    def OnSavePlotTrace(self, e=None):
        """ make some output """
        # Saving dialog box.
        uselatex = 1*self.MenuUseLatex.IsChecked()
        verbose = 1*self.MenuVerbose.IsChecked()
        Page = self.notebook.GetCurrentPage()
        plotting.savePlotTrace(self, self.dirname, Page, uselatex, verbose)


    def OnSaveSession(self,e=None):
        """Save a session for later continuation."""
        # Save each Page
        N = self.notebook.GetPageCount()
        # Create two lists: One for internal and one for external (user added)
        # functions:
        Function_parms = list()
        Function_array = list()
        Function_trace = list()
        Function_prefs = list()
        # Reserved for future versions of PyCorrFit:
        Preferences = None
        # User edited Comments
        Comments = list()
        # External functions
        ExternalFunctions = dict()
        for usermodelid in mdls.modeltypes["User"]:
            # Those models belong to external user functions.
            doc = mdls.modeldict[usermodelid][-1].func_doc
            doc = doc.splitlines()
            docnew=""
            for line in doc:
                docnew = docnew+line.strip()+"\r\n"
            ExternalFunctions[usermodelid] = docnew
        for i in np.arange(N):
            # Set Page 
            Page = self.notebook.GetPage(i)
            # Apply currently set parameters
            Page.apply_parameters()
            # Get experimental data
            dataexp = Page.dataexpfull    # 2D Array or None
            # Get parameters
            tau = Page.tau            # Array
            Array = [tau, dataexp]
            Parms = self.PackParameters(Page)
            Function_parms.append(Parms)
            Function_array.append(Array)
            # Also save the trace
            if Page.IsCrossCorrelation is False:
                Function_trace.append(Page.trace)
            else:
                Function_trace.append(Page.tracecc)
            # Append title to Comments
            Comments.append(Page.tabtitle.GetValue())
        # Append Session Comment:
        Comments.append(self.SessionComment)
        # Save everything
        # If no file has been selected, self.filename will be set to 'None'.
        self.dirname, self.filename = opf.SaveSession(self, self.dirname,
          Function_parms, Function_array, Function_trace, self.Background,
          Preferences, Comments, ExternalFunctions)
        # Set title of our window
        self.SetTitleFCS(self.filename)


    #Help
    def OnSoftware(self, event=None):
        # Show About Information
        text = doc.SoftwareUsed()
        dlg = wx.MessageBox(text, 'Software', 
            wx.OK | wx.ICON_INFORMATION)


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


    def PackParameters(self, Page):
        """ Gets all parameters from a page and returns a list object,
            that can be used to save as e.g. a safe YAML file 
        """
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
        knots = Page.Fitbox[1].GetValue()
        knots = filter(lambda x: x.isdigit(), knots)
        if len(knots) == 0:
            knots = None
        else:
            knots = int(knots)
        weighted = Page.Fitbox[1].GetSelection()
        weights = Page.Fitbox[5].GetValue()
        Parms.append([weighted, weights, knots])
        # Additional parameters as of v.0.2.9
        # Which Background signal is selected?
        # The Background information is in the list *self.Background*.
        Parms.append([Page.bgselected])
        # Additional parameters as of v.0.5.8
        # Is the Experimental data (if it exists) AC or CC?
        Parms.append(Page.IsCrossCorrelation)
        return Parms

    def UnpackParameters(self, Parms, Page):
        """ Apply the given parameters to the Page in question.
        """
        modelid = Parms[1]
        if Page.modelid != modelid:
            print "Wrong model: "+str(Page.modelid)+" vs. "+str(modelid)
            return
        active_values = Parms[2]
        active_fitting = Parms[3]
        
        # As of version 0.7.0, square pinhole TIR-FCS models
        # use sigma instead of lambda, NA and sigma_0. This
        # is for backwards compatibility:
        changeTIRF = False
        if modelid in [6000, 6010]:
            lindex = 1
            changeTIRF = True
        elif modelid in [6020, 6021, 6022, 6023]:
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
        Page.apply_parameters_reverse()
        # Cropping
        Page.startcrop = cropstart
        Page.endcrop = cropend
        # Weighted fitting
        if len(Parms) >= 6:
            if len(Parms[5]) == 2:
                [weighted, weights] = Parms[5]
                knots = None
            else:
                # We have knots as of v. 0.6.5
                [weighted, weights, knots] = Parms[5]
            if weighted is False or weighted == 0:
                Page.Fitbox[1].SetSelection(0)
            if weighted is True or weighted == 1:
                Page.Fitbox[1].SetSelection(1)
            else:
                Page.Fitbox[1].SetSelection(weighted)
            if knots is not None:
                text = Page.Fitbox[1].GetValue()
                text = filter(lambda x: x.isalpha(), text)
                Page.Fitbox[1].SetValue(text+str(knots))
            Page.Fitbox[5].SetValue(weights)
        if Page.dataexp is not None:
            Page.Fit_enable_fitting()
        Page.Fit_WeightedFitCheck()

        # Set which background correction the Page uses:
        if len(Parms) >= 7:
            if len(self.Background) > Parms[6][0]:
                Page.bgselected = Parms[6][0]
        # Set if Newtab is of type cross-correlation:
        if len(Parms) >= 8:
            Page.IsCrossCorrelation = Parms[7]
        ## If we want to add more stuff, we should do something like:
        ##   if len(Parms) >= 6:
        ##       nextvalue = Parms[5]
        ## Such that we are compatible to earlier versions of 
        ## PyCorrFit sessions.


    def SetTitleFCS(self, title):
        if title is not None and len(title) != 0:
            title = " {"+title+"}"
            self.SetTitle('PyCorrFit ' + self.version + title)
        else:
            self.SetTitle('PyCorrFit ' + self.version)



