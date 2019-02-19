"""PyCorrFit - update checking"""
from distutils.version import LooseVersion  # For version checking
import os
import tempfile
import traceback
import urllib.request
import webbrowser

import simplejson
import wx.html
import wx.lib.delayedresult as delayedresult

from .. import _version as pcf_version

from . import doc                          # Documentation/some texts
# The icon file was created with
# img2py -i -n Main PyCorrFit_icon.png icon.py
from . import misc


class UpdateDlg(wx.Frame):
    def __init__(self, parent, valuedict):

        description = valuedict["Description"]
        homepage = valuedict["Homepage"]
        githome = valuedict["Homepage_GIT"]
        changelog = valuedict["Changelog"]
        pos = parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Update",
                          size=(230, 240), pos=pos)
        self.changelog = changelog
        # Fill html content
        html = wxHTML(self)
        string = '' \
                 + "<b> PyCorrFit <br></b>" \
                 + "Your version: {}<br>".format(description[0]) \
                 + "Latest version: {}<br>".format(description[1]) \
                 + "({})<br><p><b>".format(description[2])
        if homepage:
            string = string + '<a href="{}">Homepage</a><br>'.format(homepage)
        if githome:
            string = string + '<a href="{}">Repository</a><br>'.format(githome)

        if changelog:
            string = string + \
                '<a href="{}">Change Log</a>'.format(changelog)
        string += '</b></p>'
        html.SetPage(string)
        self.Bind(wx.EVT_CLOSE, self.Close)
        # Set window icon
        ico = misc.getMainIcon()
        wx.Frame.SetIcon(self, ico)

    def Close(self, event):
        if len(self.changelog) != 0:
            # Cleanup downloaded file, if it was downloaded
            if self.changelog != doc.StaticChangeLog:
                os.remove(self.changelog)
        self.Destroy()


class wxHTML(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())


def get_gh_version(ghrepo="user/repo", timeout=20):
    """ Check GitHub repository for latest release
    """
    u = "https://api.github.com/repos/{}/releases/latest".format(ghrepo)
    try:
        data = urllib.request.urlopen(u, timeout=timeout).read()
    except:
        newversion = None
        try:
            with open("check_update_error.log", "w") as fe:
                fe.writelines(str(traceback.format_exc()))
        except:
            pass
    else:
        j = simplejson.loads(data)
        newversion = LooseVersion(j["tag_name"])

    return newversion


def update(parent):
    """ This is a thread for _Update """
    parent.StatusBar.SetStatusText("Connecting to server...")
    delayedresult.startWorker(_update_consumer, _update_worker,
                              wargs=(parent,), cargs=(parent,))


def _update_consumer(delayedresult, parent):
    results = delayedresult.get()
    dlg = UpdateDlg(parent, results)
    dlg.Show()
    parent.StatusBar.SetStatusText(
        "...update status: "+results["Description"][2])


def _update_worker(parent):
    # Online changelog file
    cl_file = doc.GitChLog
    try:
        responseVer = urllib.request.urlopen(cl_file, timeout=2)
    except:
        changelog = ""
    else:
        changelog = responseVer.read()

    ghrepo = "FCS-analysis/PyCorrFit"
    if hasattr(pcf_version, "repo_tag"):
        old = LooseVersion(pcf_version.repo_tag)
    else:
        old = LooseVersion(pcf_version.version)

    new = get_gh_version(ghrepo)

    if new is not None:
        if new > old:
            action = "update available"
        elif new < old:
            action = "ahead of release"
        else:
            action = "state of the art"
    description = [old, new, action]
    if changelog:
        changelogfile = tempfile.mktemp()+"_PyCorrFit_CHANGELOG"+".txt"
        clfile = open(changelogfile, 'wb')
        clfile.write(changelog)
        clfile.close()
    else:
        changelogfile = doc.StaticChangeLog
    results = dict()
    results["Description"] = description
    results["Homepage"] = doc.HomePage
    results["Homepage_GIT"] = doc.GitHome
    results["Changelog"] = changelogfile
    return results
