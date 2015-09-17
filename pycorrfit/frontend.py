# -*- coding: utf-8 -*-
"""
PyCorrFit - Module "frontend"

The frontend displays the GUI (Graphic User Interface). All necessary 
functions and modules are called from here.
"""

from distutils.version import LooseVersion # For version checking
import os
import webbrowser
import wx.lib.agw.flatnotebook as fnb   # Flatnotebook (Tabs)
import wx.py.shell
import numpy as np                      # NumPy
import platform
import sys                              # System stuff
import traceback                        # for Error handling
import warnings

try:
    # contains e.g. update and icon, but no vital things.
    import misc
except ImportError:
    print " Some modules are not available."
    print " Update function will not work."

# PyCorrFit modules
from . import doc                          # Documentation/some texts
from . import edclasses

from . import models as mdls
from . import openfile as opf              # How to treat an opened file
from . import page
try:
    from . import plotting
except ImportError:
    warnings.warn("Submodule `pycorrfit.plotting` will not be "+\
             "available. Reason: {}.".format(sys.exc_info()[1].message))
from . import readfiles
from . import tools                        # Some tools
from . import usermodel


########################################################################
class ExceptionDialog(wx.MessageDialog):
    """"""
    def __init__(self, msg):
        """Constructor"""
        wx.MessageDialog.__init__(self, None, msg, "Error",
                                          wx.OK|wx.ICON_ERROR)   


########################################################################
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


class MyApp(wx.App):
    def __init__(self, args):
        wx.App.__init__(self, args)
        # Suppress WXDEBUG assertions, as happens by default with wx2.8.
        # http://anonscm.debian.org/cgit/collab-maint/wx-migration-tools.git/tree/README#n30
        self.SetAssertMode(wx.PYAPP_ASSERT_SUPPRESS)
        
    def MacOpenFile(self,filename):
        """
        """
        if filename.endswith(".pcfs"):
            stri = self.frame.OnClearSession()
            if stri == "clear":
                self.frame.OnOpenSession(sessionfile=filename)
        elif filename.endswith(".txt"):
            self.frame.OnAddModel(modfile=filename)
        else:
            self.frame.OnLoadBatch(dataname=filename)


###########################################################
class MyFrame(wx.Frame):
    def __init__(self, parent, anid, version):

        sys.excepthook = MyExceptionHook
        ## Set initial variables that make sense
        self.version = version
        wx.Frame.__init__(self, parent, anid, "PyCorrFit " + self.version)
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

        # Tab Counter
        self.tabcounter = 1

        # Background Correction List
        # Contains instances of `Trace`
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

        self.Centre()
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


    def add_fitting_tab(self, event=None, modelid=None, counter=None,
                        select=False):
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
            # Give the new page focus
            select = True
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
        Newtab = page.FittingPanel(self, counter, modelid, active_parms)
        #self.Freeze()
        self.notebook.AddPage(Newtab, counter+model, select=select)
        if select:
            # A hack to have the last page displayed in the tab menu:
            Npag = self.notebook.GetPageCount()
            for i in range(int(Npag)):
                self.notebook.SetSelection(i)

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
        #toolkeys = self.ToolsOpen.keys()
        #for key in toolkeys:
        #    tool = self.ToolsOpen[key]
        #    try:
        #        if tool.MyName=="STATISTICS":
        #            # Call the function properly.
        #            tool.OnPageChanged(Newtab)
        #    except:
        #        pass
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
        # Preferences
        self.Bind(wx.EVT_MENU, self.OnLatexCheck, self.MenuUseLatex)
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
        info.SetCopyright(u'(C) 2011 - 2012 Paul Müller')
        info.SetWebSite(doc.HomePage)
        info.SetLicence(licence)
        info.SetIcon(misc.getMainIcon(pxlength=64))
        info.AddDeveloper(u'Paul Müller')
        info.AddDocWriter(u'Thomas Weidemann, Paul Müller')
        wx.AboutBox(info)
        

    def OnAddModel(self, event=None, modfile=None):
        """ Import a model from an external .txt file. See example model
            functions available on the web.
        """
        # Add a model using the dialog.
        filters = "text file (*.txt)|*.txt"
        if modfile is None:
            dlg = wx.FileDialog(self, "Open model file", 
                            self.dirname, "", filters, wx.FD_OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                # Workaround since 0.7.5
                (dirname, filename) = os.path.split(dlg.GetPath())
                #filename = dlg.GetFilename()
                #dirname = dlg.GetDirectory()
                self.dirname = dirname
                # Try to import a selected .txt file
            else:
                self.dirname = dlg.GetDirectory()
                dlg.Destroy()
                return
        else:
            dirname, filename = os.path.split(modfile)
            self.dirname = dirname

        NewModel = usermodel.UserModel(self)
        try:
            NewModel.GetCode( os.path.join(dirname, filename) )
        except NameError:
            # sympy is probably not installed
            # Warn the user
            text = ("SymPy not found.\n"+
                    "In order to import user defined model\n"+
                    "functions, please install Sympy\n"+
                    "version 0.7.2 or higher.\nhttp://sympy.org/")
            if platform.system().lower() == 'linux':
                text += ("\nSymPy is included in the package:\n"+
                         "   'python-sympy'")
            dlg = wx.MessageDialog(None, text, 'SymPy not found', 
                            wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            return
        except:
            # The file does not seem to be what it seems to be.
            info = sys.exc_info()
            errstr = "Unknown file format:\n"
            errstr += str(filename)+"\n\n"
            errstr += str(info[0])+"\n"
            errstr += str(info[1])+"\n"
            for tb_item in traceback.format_tb(info[2]):
                errstr += tb_item
            dlg = wx.MessageDialog(self, errstr, "Error", 
                style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
            dlg.ShowModal()
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
                return
        else:
            # The model was loaded correctly
            NewModel.ImportModel()
               

        self.dirname = dirname
            

    def OnClearSession(self, e=None, clearmodels=False):
        """
            Clear the entire session
        
            Returns:
            "abort" if the user did not want to clear the session
            "clear" if the session has been cleared and the user did
                    or did not save the session
        """
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
                filename = self.OnSaveSession()
                if filename is None:
                    return "abort"
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
        return "clear"


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
        """
            Kindly asks the user if he wants to save the session and
            then exit the program.
        """
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
                filename = self.OnSaveSession()
                if filename is None:
                    # Do not exit. The user pressed abort in the session
                    # saving dialog.
                    return
        # Exit the Program
        self.Destroy()


    def OnFNBClosedPage(self,e=None):
        """ Called, when a page has been closed """
        if self.notebook.GetPageCount() == 0:
            # Grey out tools
            self.EnableToolCurrent(False)



    def OnFNBPageChanged(self, e=None, Page=None, trigger=None):
        """ Called, when 
            - Page focus switches to another Page
            - Page with focus changes significantly:
                - experimental data is loaded
                - weighted fit was done
            - trigger is a string. For more information read the
              doc strings of the `tools` submodule.
        """
        
        if (e is not None and
            e.GetEventType()==fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED.typeId
            and trigger is None):
            trigger = "tab_browse"
        # Get the Page
        if Page is None:
            Page = self.notebook.GetCurrentPage()
        keys = list(self.ToolsOpen.keys())
        for key in keys:
            # Update the information
            self.ToolsOpen[key].OnPageChanged(Page, trigger=trigger)
        # parameter range selection tool for page.
        if self.RangeSelector is not None:
            try:
                self.RangeSelector.OnPageChanged(Page, trigger=trigger)
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
        """Import experimental data from all filetypes specified in 
           *opf.Filetypes*.
           Is called by the curmenu and applies to currently opened model.
           Calls self.ImportData.
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
            self.dirname, "", filters, wx.FD_OPEN)
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
                if "Weight" in Stuff:
                    Weight = Stuff["Weight"]
                    WeightName = Stuff["Weight Name"]
                else:
                    Weight = [None] * len(Stuff["Type"])
                    WeightName = [None] * len(Stuff["Type"])
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
                    newWeight = list()
                    newWeightName = list()
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
                                newWeight.append(Weight[index])
                                newWeightName.append(WeightName[index])
                        curvelist = newcurvelist
                        filename = newfilename
                        dataexp = newdataexp
                        trace = newtrace
                        Weight = newWeight
                        WeightName = newWeightName
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
                                   weights=Weight[i], weight_type=WeightName[i],
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
                                             modelid=CurPage.corr.fit_model.id,
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
        where = pc.HitTest(event.GetPosition())[0]
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
                   filename="", curveid="", run="0", 
                   weights=None, weight_type=None, trigger=None):
        """
            Import data into the current page.
            
            `trigger` is passed to PlotAll. For more info see the
            submodule `tools`.
        """
        CurPage = Page
        # Set name of correlation
        CurPage.corr.filename = filename
        # Import traces. Traces are usually put into a list, even if there
        # is only one trace. The reason is, that for cross correlation, we 
        # have two traces and thus we have to import both.
        if trace is not None:
            CurPage.corr.traces = trace
        # Import correlation function
        CurPage.corr.correlation = dataexp
        CurPage.corr.corr_type = curvetype
        CurPage.OnAmplitudeCheck()
        # It might be possible, that we want the channels to be
        # fixed to some interval. This is the case if the 
        # checkbox on the "Channel selection" dialog is checked.
        #self.OnFNBPageChanged()
        # Enable Fitting Button
        CurPage.Fit_enable_fitting()
        # Set new tabtitle value and strip leading or trailing
        # white spaces.
        if run != "":
            title = "{} r{:03d}-{}".format(filename, int(run), curvetype)
        else:
            title = "{} id{:03d}-{}".format(filename, int(curveid), curvetype)
        CurPage.title = title
        # set weights
        if weights is not None:
            CurPage.corr.set_weights(weight_type, weights)
            List = CurPage.Fitbox[1].GetItems()
            if not weight_type in List:
                List.append(weight_type)
                CurPage.Fitbox[1].SetItems(List)
                CurPage.Fitbox[1].SetSelection(len(List)-1)
            else:
                listid = List.index(weight_type)
                CurPage.Fitbox[1].SetSelection(listid)
            
        # Plot everything
        CurPage.OnAmplitudeCheck()
        CurPage.PlotAll(trigger=trigger)
        # Call this function to allow the "Channel Selection" window that
        # might be open to update itself.
        # We are aware of the fact, that we just did that
        #self.OnFNBPageChanged()


    def OnLatexCheck(self,e):
        """ Checks if we can use latex. If not, create a pop-up window
            stating so.
        """
        uselatex = self.MenuUseLatex.IsChecked()
        if uselatex == False:
            # do nothing
            return
        ## Check if we can use latex for plotting:
        r1 = misc.findprogram("latex")[0]
        r2 = misc.findprogram("dvipng")[0]
        # Ghostscript
        r31 = misc.findprogram("gs")[0]
        r32 = misc.findprogram("mgs")[0] # from miktex
        r3 = max(r31,r32)
        if r1+r2+r3 < 3:
            # Warn the user
            if platform.system().lower() == 'windows':
                text = ("Latex plotting features will not work.\n"+
                        "Please install MiKTeX.\n"+
                        "http://miktex.org/")
            elif platform.system().lower() == 'darwin':
                text = ("Latex plotting features will not work.\n"+
                        "Please install MacTeX.\n"+
                        "http://tug.org/mactex/")
            else:
                text = ("Latex plotting features will not work.\n"+
                        "Make sure you have these packages installed:\n"+
                        "  - latex\n"+
                        "  - dvipng\n"+
                        "  - ghostscript\n"+
                        "  - texlive-latex-base\n"+
                        "  - texlive-math-extra\n")
            dlg = wx.MessageDialog(None, text, 'Latex not found', 
                            wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            

    def OnLoadBatch(self, e=None, dataname=None):
        """ Open multiple data files and apply a single model to them
            We will create a new window where the user may decide which
            model to use.
        """
        if dataname is None:
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
                self.dirname, "", filters, wx.FD_OPEN|wx.FD_MULTIPLE)
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
        else:
            Datafiles = list()
            if isinstance(dataname, list):
                for item in dataname:
                    Datafiles.append(os.path.split(item)[1])
                self.dirname = os.path.split(Datafiles[0])[0]
            else:
                Datafiles.append(os.path.split(dataname)[1])
                self.dirname = os.path.split(dataname)[0]
            Datafiles.sort()

        ## Get information from the data files and let the user choose
        ## which type of curves to load and the corresponding model.
        # List of filenames that could not be opened
        BadFiles = list()
        Exceptions = list()
        # Lists for correlation, trace, type and names
        Correlation = list()
        Trace = list()
        Type = list()
        Filename = list()   # there might be zipfiles with additional name info
        #Run = list()        # Run number connecting AC1 AC2 CC12 CC21
        Curveid = list()    # Curve ID of each curve in a file
        Weight = list()
        WeightName = list()
        
        # Display a progress dialog for file import
        N = len(Datafiles)
        style = wx.PD_REMAINING_TIME|wx.PD_SMOOTH|wx.PD_AUTO_HIDE|\
                wx.PD_CAN_ABORT
        dlgi = wx.ProgressDialog("Import", "Loading data...",
                                maximum = N, parent=self, style=style)
        for j in np.arange(N):
            afile=Datafiles[j]
            # Let the user abort, if he wants to:
            if dlgi.Update(j, "Loading data: "+afile)[0] == False:
                dlgi.Destroy()
                return
            #Stuff = readfiles.openAny(self.dirname, afile)
            try:
                Stuff = readfiles.openAny(self.dirname, afile)
            except Exception as excpt:
                # The file does not seem to be what it seems to be.
                BadFiles.append(afile)
                Exceptions.append(excpt)
                # Print exception
                trb = traceback.format_exc(excpt)
                trb = "..." + trb.replace("\n", "\n...")
                warnings.warn("Problem processing a file."+\
                  " Reason:\n{}".format(trb))
            else:
                for i in np.arange(len(Stuff["Type"])):
                    Correlation.append(Stuff["Correlation"][i])
                    Trace.append(Stuff["Trace"][i])
                    Type.append(Stuff["Type"][i])
                    Filename.append(Stuff["Filename"][i])
                    if "Weight" in Stuff:
                        Weight.append(Stuff["Weight"][i])
                        WeightName.append(Stuff["Weight Name"][i])
                    else:
                        Weight.append(None)
                        WeightName.append(None)
                        #Curveid.append(str(i+1))                    
        dlgi.Destroy()
        
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
            for item, excpt in zip(BadFiles, Exceptions):
                trb = traceback.format_exc(excpt)
                trb = "   " + trb.replace("\n", "\n   ")
                errstr += " " + item + "\n" + trb 
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
        newWeight = list()
        newWeightName = list()
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
                        newWeight.append(Weight[index])
                        newWeightName.append(WeightName[index])
            Correlation = newCorrelation
            Trace = newTrace
            Type = newType
            Filename = newFilename
            Curveid = newCurveid
            Run = newRun
            Weight = newWeight
            WeightName = newWeightName
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
                            curveid=str(Curveid[i]), run=str(Run[i]),
                            weights=Weight[i], weight_type=WeightName[i],
                            trigger="page_add_batch")
            # Let the user abort, if he wants to:
            # We want to do this here before an empty page is added
            # to the notebok.
            if dlg.Update(i+1, "Loading pages...")[0] == False:
                break
        self.OnFNBPageChanged(trigger="page_add_finalize")
        # If the user did not select curves but chose a model, destroy
        # the dialog.
        dlg.Destroy()


    def OnOpenSession(self, e=None, sessionfile=None):
        """ Displays a dialog for opening PyCorrFit sessions
        
        Optional parameter sessionfile defines the file that shall be
        automatically loaded (without a dialog).
        
        
        See Also
        --------
        `pycorrfit.openfile.LoadSessionData`
        """
        # We need to clear the session before opening one.
        # This will also ask, if user wants to save the current session.
        clear = self.OnClearSession(clearmodels=True)
        if clear == "abort":
            # User pressed abort when he was asked if he wants to save
            # the session. Therefore, we cannot open a new session.
            return "abort"
        
        ## Create user dialog
        wc = opf.session_wildcards
        wcstring = "PyCorrFit session (*.pcfs)|*{};*{}".format(
                                                           wc[0], wc[1])
        if sessionfile is None:
            dlg = wx.FileDialog(self, "Open session file",
                                self.dirname, "", wcstring, wx.FD_OPEN)
            # user cannot do anything until he clicks "OK"
            if dlg.ShowModal() == wx.ID_OK:
                sessionfile = dlg.GetPath()
                (self.dirname, self.filename) = os.path.split(
                                                            sessionfile)
            else:
                # User did not press OK
                # stop this function
                self.dirname = dlg.GetDirectory()
                return "abort"
            dlg.Destroy()
        Infodict = opf.LoadSessionData(sessionfile)
        
        ## Check for correct version
        try:
            arcv = LooseVersion(Infodict["Version"])
            thisv = LooseVersion(self.version.strip())
            if arcv > thisv:
                errstring = "Your version of Pycorrfit ("+str(thisv)+\
                       ") is too old to open this session ("+\
                       str(arcv).strip()+").\n"+\
                       "Please download the lates version of "+\
                       " PyCorrFit from \n"+doc.HomePage+".\n"+\
                       "Continue opening this session?"
                dlg = edclasses.MyOKAbortDialog(self, errstring, "Warning")
                returns = dlg.ShowModal()
                if returns == wx.ID_OK:
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return "abort"
        except:
            pass
        
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
        dlg = wx.ProgressDialog("Import", "Loading pages...",
                                maximum = N, parent=self, style=style)
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
            Newtab = self.add_fitting_tab(modelid=modelid,
                                          counter=counter)
            # Add experimental Data
            # Import dataexp:
            number = counter.strip().strip(":").strip("#")
            pageid = int(number)
            dataexp = Infodict["Correlations"][pageid][1]

            if Infodict["Parameters"][0][7]:
                curvetype = "cc"
            else:
                curvetype = "ac"

            # As of 0.7.3: Add external weights to page
            try:
                for key in Infodict["External Weights"][pageid].keys():
                    Newtab.corr.set_weights(key, Infodict["External Weights"][pageid][key])
            except KeyError:
                pass

            if len(Infodict["Parameters"][i]) >= 6:
                if Infodict["Parameters"][i][5][0] >= 3:
                    # we have a weighted fit with external weights
                    # these are usually averages.
                    keys = Infodict["External Weights"][pageid].keys()
                    keys = list(keys)
                    keys.sort()
                    key = keys[Infodict["Parameters"][i][5][0]-3]
                    weights = Infodict["External Weights"][pageid][key]
                    weight_type = key
                else:
                    weight_type = None
                    weights = None

            self.ImportData(Newtab, 
                            dataexp, 
                            trace=Infodict["Traces"][pageid],
                            curvetype=curvetype,
                            weights=weights,
                            weight_type=weight_type)
           
            # Set Title of the Page
            try:
                Newtab.tabtitle.SetValue(Infodict["Comments"][pageid])
            except:
                pass # no page title

            # Parameters
            self.UnpackParameters(Infodict["Parameters"][i], Newtab,
                                  init=True)
            # Supplementary data
            fit_results = dict()
            fit_results["weighted fit"] = Infodict["Parameters"][i][5][0] > 0
            try:
                Sups = Infodict["Supplements"][pageid]
            except KeyError:
                pass
            else:
                if Sups.has_key("FitErr"):
                    ervals = list()
                    for errInfo in Sups["FitErr"]:
                        ervals.append(float(errInfo[1]))
                    fit_results["fit error estimation"] = ervals
                try:
                    if len(Sups["Global Share"]) > 0: 
                        fit_results["global pages"] = Sups["Global Share"]
                except KeyError:
                    pass
                try:
                    fit_results["chi2"] = Sups["Chi sq"]
                except:
                    pass
                # also set fit parameters
                fit_results["fit parameters"] = np.where(Infodict["Parameters"][i][3])[0]
                # set fit weights for plotting
                if fit_results["weighted fit"]:
                    # these were already imported:
                    try:
                        weights = Infodict["External Weights"][pageid]
                        for w in weights.keys():
                            fit_results["weighted fit type"] = w
                            fit_results["fit weights"] = weights[w]
                    except KeyError:
                        pass
            Newtab.corr.fit_results = fit_results

            # Plot everything
            Newtab.PlotAll(trigger="page_add_batch")
        # Set Session Comment
        dlg.Destroy()
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
            self.OnFNBPageChanged(trigger="page_add_finalize")
        else:
            # There are no pages in the session.
            # Disable some menus and close some dialogs
            self.EnableToolCurrent(False)


    def OnSaveData(self,e=None):
        """ Opens a dialog for saving correlation data of a Page
        
        Also saves the parameters that are accessible in the Info
        dialog and the trace(s).
        """
        # What Data do we wish to save?
        Page = self.notebook.GetCurrentPage()
        # Export CSV data
        filename = Page.tabtitle.GetValue().strip()+Page.counter[:2]+".csv"
        dlg = wx.FileDialog(self, "Save curve", self.dirname, filename, 
              "Correlation with trace (*.csv)|*.csv;*.*"+\
              "|Correlation only (*.csv)|*.csv;*.*",
               wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        # user cannot do anything until he clicks "OK"
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()            # Workaround since 0.7.5
            if not path.lower().endswith(".csv"):
                path += ".csv"
            (self.dirname, self.filename) = os.path.split(path)


            if dlg.GetFilterIndex() == 0:
                savetrace = True
            else:
                savetrace = False
            opf.ExportCorrelation(path, Page, tools.info,
                                  savetrace=savetrace)
        
        dlg.Destroy()


    def OnSavePlotCorr(self, e=None):
        """ make some output """
        # Saving dialog box.
        uselatex = self.MenuUseLatex.IsChecked()
        verbose = self.MenuVerbose.IsChecked()
        show_weights = self.MenuShowWeights.IsChecked()
        Page = self.notebook.GetCurrentPage()
        try:
            plotting.savePlotCorrelation(self, self.dirname, Page, uselatex,
                                     verbose, show_weights)
        except NameError as excpt:
            trb = traceback.format_exc(excpt)
            trb = "   " + trb.replace("\n", "\n   ")
            raise NameError("Please make sure matplotlib is installed:\n"+trb)


    def OnSavePlotTrace(self, e=None):
        """ make some output """
        # Saving dialog box.
        uselatex = 1*self.MenuUseLatex.IsChecked()
        verbose = 1*self.MenuVerbose.IsChecked()
        Page = self.notebook.GetCurrentPage()
        try:
            plotting.savePlotTrace(self, self.dirname, Page, uselatex, verbose)
        except NameError as excpt:
            trb = traceback.format_exc(excpt)
            trb = "   " + trb.replace("\n", "\n   ")
            raise NameError("Please make sure matplotlib is installed:\n"+trb)


    def OnSaveSession(self,e=None):
        """ Displays a dialog for saving PyCorrFit sessions
        
        
        Returns
        -------
        - the filename of the session if it was saved
        - None, if the user canceled the action
        
        
        See Also
        --------
        `pycorrfit.openfile.SaveSessionData`
        """
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
            corr = Page.corr
            # Set supplementary information, such as errors of fit
            if hasattr(corr, "fit_results"):
                Infodict["Supplements"][counter] = dict()
                if corr.fit_results.has_key("chi2"):
                    Infodict["Supplements"][counter]["Chi sq"] = float(corr.fit_results["chi2"])
                else:
                    Infodict["Supplements"][counter]["Chi sq"] = 0
                PageList = list()
                for pagei in Page.GlobalParameterShare:
                    PageList.append(int(pagei))
                Infodict["Supplements"][counter]["Global Share"] = PageList

                # optimization error
                Alist = list()
                if (corr.fit_results.has_key("fit error estimation") and 
                    len(corr.fit_results["fit error estimation"]) != 0):
                    for ii, fitpid in enumerate(corr.fit_results["fit parameters"]):
                        Alist.append([ int(fitpid),
                                   float(corr.fit_results["fit error estimation"][ii]) ])
                Infodict["Supplements"][counter]["FitErr"] = Alist
                
            # Set exp data
            Infodict["Correlations"][counter] = [corr.lag_time, corr.correlation]
            # Also save the trace
            Infodict["Traces"][counter] = corr.traces
            # Append title to Comments
            # #Comments.append(Page.tabtitle.GetValue())
            Infodict["Comments"][counter] = Page.tabtitle.GetValue()
            # Add additional weights to Info["External Weights"]
            external_weights = dict()
            for key in corr._fit_weight_memory.keys():
                if isinstance(corr._fit_weight_memory[key], np.ndarray):
                    external_weights[key] = corr._fit_weight_memory[key]
            # also save current weights
            if hasattr(corr, "fit_results"):
                if corr.fit_results.has_key("weighted fit type"):
                    fittype = corr.fit_results["weighted fit type"]
                    fitweight = corr.fit_results["fit weights"]
                    external_weights[fittype] = fitweight
            Infodict["External Weights"][counter] = external_weights
        # Append Session Comment:
        Infodict["Comments"]["Session"] = self.SessionComment
        # File dialog
        dlg = wx.FileDialog(self, "Save session file", self.dirname, "",
                            "PyCorrFit session (*.pcfs)|*.pcfs|All files (*.*)|*.*",
                            wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            # Save everything
            path = dlg.GetPath()            # Workaround since 0.7.5
            (self.dirname, self.filename) = os.path.split(path)
            opf.SaveSessionData(path, Infodict)
        else:
            self.dirname = dlg.GetDirectory()
            self.filename = None
            # Set title of our window
        if (self.filename is not None and
            not self.filename.endswith(".pcfs")):
            self.filename += ".pcfs"
        dlg.Destroy()
        self.SetTitleFCS(self.filename)
        return self.filename


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
        modelid = Page.corr.fit_model.id
        # Get Page number
        counter = Page.counter
        active_numbers = Page.corr.fit_parameters   # Array, Parameters
        active_fitting = Page.corr.fit_parameters_variable
        crop = Page.corr.fit_ival
        Parms = [counter, modelid, active_numbers, active_fitting, crop]
        # Weighting:
        # Additional parameters as of v.0.2.0
        # Splines and model function:
        # Additional parameters as of v.6.4.0
        #self.Fitbox=[ fitbox, weightedfitdrop, fittext, fittext2, 
        #              fittextvar, fitspin, buttonfit ]
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
        algorithm = Page.corr.fit_algorithm
        Parms.append([weighted, weights, knots, algorithm])
        # Additional parameters as of v.0.2.9
        # Which Background signal is selected?
        # The Background information is in the list *self.Background*.
        Parms.append([Page.bgselected, Page.bg2selected])
        # Additional parameter as of v.0.5.8
        # Is the Experimental data (if it exists) AC or CC?
        Parms.append(Page.IsCrossCorrelation)
        # Additional parameter as of v.0.7.8
        # The selection of a normalization parameter (None or integer)
        Parms.append(Page.corr.normparm)
        # Parameter ranges
        Parms.append(Page.corr.fit_parameters_range)
        return Parms


    def UnpackParameters(self, Parms, Page, init=False):
        """ Apply the given parameters to the Page in question.
            This function contains several *len(Parms) >= X* statements.
            These are used for opening sessions that were saved using
            earlier versions of PyCorrFit.
            The `init` variable can be set if fundamental changes
            are made (loading data). This e.g. might change the type
            (Autocorrelation/Cross-Correlation) of the page.
        """
        modelid = Parms[1]
        if Page.corr.fit_model.id != modelid:
            print "Wrong model: "+str(Page.corr.fit_model.id)+" vs. "+str(modelid)
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
        elif (modelid == 6022 and
              len(Parms[2]) == len(mdls.valuedict[modelid][0]) + 1):
            # Change in verson 0.8.7: TIRF_2D2D model remove d_eva
            active_values = np.delete(active_values, 4)
            active_fitting = np.delete(active_fitting, 4)
           
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
        # Cropping: What part of the correlation should be displayed.
        Page.corr.fit_ival = Parms[4]
        # Add parameters and fitting to the created page.
        # We need to run Newtab.apply_parameters_reverse() in order
        # for the data to be displayed in the user interface.
        Page.corr.fit_parameters = active_values
        Page.corr.fit_parameters_variable = active_fitting
        # Weighted fitting
        if len(Parms) >= 6:
            if len(Parms[5]) == 2:
                [weighted, weights] = Parms[5]
                knots = None
            elif len(Parms[5]) == 3:
                # We have knots as of v. 0.6.5
                [weighted, weights, knots] = Parms[5]
            else:
                # We have different fitting algorithms as of v. 0.8.3
                [weighted, weights, knots, algorithm] = Parms[5]
                Page.corr.fit_algorithm = algorithm
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

        if Page.corr.correlation is not None:
            Page.Fit_enable_fitting()
            Page.Fit_WeightedFitCheck()
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
            if Parms[7]:
                Page.corr.corr_type = "cc"
            else:
                Page.corr.corr_type = "ac"
            Page.OnAmplitudeCheck()
        if len(Parms) >= 9:
            # New feature in 0.7.8 includes normalization to a fitting
            # parameter.
            Page.corr.normparm = Parms[8]
            Page.OnAmplitudeCheck("init")
        if len(Parms) >= 10:
            Page.corr.fit_parameters_range = np.array(Parms[9])
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


def MyExceptionHook(etype, value, trace):
    """
    Handler for all unhandled exceptions.
 
    :param `etype`: the exception type (`SyntaxError`, `ZeroDivisionError`, etc...);
    :type `etype`: `Exception`
    :param string `value`: the exception error message;
    :param string `trace`: the traceback header, if any (otherwise, it prints the
     standard Python header: ``Traceback (most recent call last)``.
    """
    wx.GetApp().GetTopWindow()
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join(tmp)
 
    dlg = ExceptionDialog(exception)
    dlg.ShowModal()
    dlg.Destroy()     
    wx.EndBusyCursor()
