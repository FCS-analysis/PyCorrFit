import wx
from wx.lib import sized_controls
import wx.lib.agw.hyperlink as hl


class ContributeDialog(sized_controls.SizedDialog):

    def __init__(self, *args, **kwargs):
        super(ContributeDialog, self).__init__(title="Contribute to PyCorrFit",
                                               *args, **kwargs)
        pane = self.GetContentsPane()

        pane_btns = sized_controls.SizedPanel(pane)
        pane_btns.SetSizerType('vertical')
        pane_btns.SetSizerProps(align="center")

        wx.StaticText(pane_btns, label=contribute_text)
        wx.StaticText(pane_btns, label="\nLinks:")
        for ii, link in enumerate(contribute_links):
            hl.HyperLinkCtrl(pane_btns,
                             -1,
                             "[{}]  {}".format(ii+1, link),
                             URL=link)
        wx.StaticText(pane_btns, label="\n")

        button_ok = wx.Button(pane_btns, label='OK')
        button_ok.Bind(wx.EVT_BUTTON, self.on_button)
        button_ok.SetFocus()
        button_ok.SetSizerProps(expand=True)

        self.Fit()

    def on_button(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()


contribute_text = """
PyCorrFit has no funding and a vanishingly small developer community.
My personal objective is to keep PyCorrFit operational on Linux and
Windows which is currently limited by the free time I have available.

An active community is very important for an open source project such
as PyCorrFit. You can help this community grow (and thus help improve
PyCorrFit) in numerous ways:

1. \tTell your colleagues and peers about PyCorrFit. One of them might
   \tbe able to contribute to the project.

2. \tIf you need a new feature in PyCorrFit, publicly announce a bounty
   \tfor its implementation.

3. \tIf your research heavily relies on FCS, please consider diverting
   \tsome of your resources to the development of PyCorrFit.

4. \tYou don't have to be a Python programmer to contribute. If you are
   \tfamiliar with reStrucuredText or LaTeX, you might be able to help
   \tout with the online documentation.

5. \tPlease cite: Müller et al. Bioinformatics 30(17): 2532–2533, 2014 [1].

6. \tSponsor me on GitHub [2] or donate via Liberapay [3].

If you are planning to contribute to PyCorrFit, please contact me via
the PyCorrFit issue page on GitHub such that we may coordinate a pull
request.

Thank you!
Paul Müller (October 2019)
"""


contribute_links = [
    "https://dx.doi.org/10.1093/bioinformatics/btu328",
    "https://github.com/sponsors/paulmueller",
    "https://liberapay.com/paulmueller,"
    ]
