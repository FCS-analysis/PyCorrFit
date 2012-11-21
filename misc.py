# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module misc
"""
# Generic modules
from distutils.version import LooseVersion # For version checking
import numpy as np
import os
import sys
import tempfile
import urllib2
import webbrowser
import wx                               # GUI interface wxPython
import wx.html

import doc                          # Documentation/some texts

import platform
if platform.system() == 'Linux':
    from IPython.Shell import IPythonShellEmbed
    ipshell = IPythonShellEmbed()
   #ipshell()


class UpdateDlg(wx.Frame):
    def __init__(self, parent, description, homepage, changelog):
        pos = parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Update", 
                          size=(250,160), pos=pos)
        self.changelog = changelog
        # Fill html content
        html = wxHTML(self)
        string =             '' +\
            "<b> PyCorrFit <br></b>" +\
            description[0]+"<br>" +\
            description[1]+"<br>" +\
            description[2]+"<br>"

        if len(homepage) != 0:
            string = string + '<p><b><a href="'+homepage+'">Homepage</a>'

        if len(changelog) != 0:
            string = string + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + '<a href="'+changelog+'">Change Log</a>'
        string = string+'</b></p>'
        html.SetPage(string)
        self.Bind(wx.EVT_CLOSE, self.Close)


    def Close(self, event):
        if len(self.changelog) != 0:
            # Cleanup downloaded file
            os.remove(self.changelog)
        self.Destroy()

class wxHTML(wx.html.HtmlWindow):
    def OnLinkClicked(parent, link):
         webbrowser.open(link.GetHref())




def findprogram(program):
    """ Uses the systems PATH variable find executables"""
    path = os.environ['PATH']
    paths = path.split(os.pathsep)
    for d in paths:
        if os.path.isdir(d):
            fullpath = os.path.join(d, program)
            if sys.platform[:3] == 'win':
                for ext in '.exe', '.bat':
                    program_path = fullpath + ext
                    if os.path.isfile(fullpath + ext):
                        return (1, program_path)
            else:
                if os.path.isfile(fullpath):
                    return (1, fullpath)
    return (0, None)





def Update(parent):
        changelog = ""
        # I created this TXT record to keep track of the current web presence.
        try:
            urlopener = urllib2.urlopen(doc.HomePage, timeout=2)
            homepage = urlopener.geturl()
        except:
            homepage = doc.HomePage
        try:
            response = urllib2.urlopen(homepage+doc.ChangeLog, timeout=2)
        except:
            newversion = "unknown"
            action = "(check internet connection)"
        else:
            changelog = response.read()
            newversion = changelog.splitlines()[0]
            new = LooseVersion(newversion)
            old = LooseVersion(parent.version)
            if new > old:
                action = "(update available)"
            elif new < old:
                action = "(whoop you rock!)"
            else:
                action = "(state of the art)"

        description = ["Your version: "+parent.version,
                       "Newest version: "+newversion,
                       action]

        if len(changelog) != 0:
            changelogfile = tempfile.mktemp()+"_PyCorrFit_ChangeLog"+".txt"
            clfile = open(changelogfile, 'wb')
            clfile.write(changelog)
            clfile.close()            
        else:
            changelogfile=""

        dlg = UpdateDlg(parent, description, homepage, changelogfile)
        dlg.Show()


