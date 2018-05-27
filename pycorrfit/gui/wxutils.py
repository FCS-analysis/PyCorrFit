"""Module wxutils"""
import re
import string

import numpy as np
import wx


def float2string_nsf(fval, n=7):
    """
    Truncate a float to n significant figures and return nice string.
    Arguments:
      q : a float
      n : desired number of significant figures
    Returns:
    String with only n s.f. and trailing zeros.
    """
    #sgn=np.sign(fval)
    try:
        if fval == 0:
            npoint=n
        else:
            q=abs(fval)
            k=int(np.ceil(np.log10(q/n)))
            # prevent negative significant digits
            npoint = max(0, n-k)
        string="{:.{}f}".format(fval, npoint)
    except:
        string="{}".format(fval)
    return string

def nice_string(string):
    """
    Convert a string of a float created by `float2string_nsf`
    to something nicer.

    i.e.
    - 1.000000 -> 1
    - 1.010000 -> 1.010
    """
    if string.count(".") and len(string.split(".")[1].replace("0", "")) == 0:
        return "{:d}".format(int(float(string)))
    else:
        olen = len(string)
        newstring = string.rstrip("0")
        if olen > len(newstring):
            string=newstring+"0"
        return string

class PCFFloatValidator(wx.PyValidator):
    def __init__(self, flag=None, pyVar=None):
        wx.PyValidator.__init__(self)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return PCFFloatValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        for x in val:
            if x not in string.digits:
                return False

        return True

    def OnChar(self, event):
        """
        Filter the characters that are put in the control.

        TODO:
        - check for strings that do not make sense
          - 2e-4.4
          - 2e--3
          - 3-1+5
        """
        key = event.GetKeyCode()
        ctrl = event.GetEventObject()
        # Get the actual string from the object
        curval = wx.TextCtrl.GetValue(ctrl)

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        char = chr(key)
        char = char.replace(",", ".")

        onlyonce = [".", "e", "i", "n", "f"]
        if char in onlyonce and curval.count(char):
            # not allowed
            return

        if ( char in string.digits or
             char in ["+", "-"]+onlyonce):
            event.Skip()
            return

        if not wx.Validator_IsSilent():
            wx.Bell()

        # Returning without calling event.Skip eats the event before it
        # gets to the text control
        return


class PCFFloatTextCtrl(wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, validator=PCFFloatValidator(), size=(110,-1),
                             style=wx.TE_PROCESS_ENTER, **kwargs)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self._PCFvalue = 0.0

    def OnMouseEnter(self, e):
        self.SetFocus()
        self.SetSelection(-1,0)

    def OnMouseLeave(self, e):
        self.SetSelection(0,0)
        self.SetInsertionPoint(0)

    def SetValue(self, value):
        self._PCFvalue = value
        string = PCFFloatTextCtrl.float2string(value)
        wx.TextCtrl.SetValue(self, string)

    def GetValue(self):
        string = wx.TextCtrl.GetValue(self)
        if string == PCFFloatTextCtrl.float2string(self._PCFvalue):
            # use internal value: more accurate
            #print("internal", self._PCFvalue)
            return self._PCFvalue
        else:
            # new value
            #print("external", string)
            return PCFFloatTextCtrl.string2float(string)

    @staticmethod
    def float2string(value):
        """
        inverse of string2float with some tweaks
        """
        value = float2string_nsf(value)
        value = nice_string(value)
        return value

    @staticmethod
    def string2float(string):
        """
        Remove any characters that are not in
        [+-{0-9},.] and show a decent float
        value.
        """
        if string.count("inf"):
            if string[0]=="-":
                return -np.inf
            else:
                return np.inf
        # allow comma
        string = string.replace(",", ".")
        # allow only one decimal point
        string = string[::-1].replace(".", "", string.count(".")-1)[::-1]
        try:
            string = "{:.12f}".format(float(string))
        except:
            pass
        # remove letters
        string = re.sub(r'[^\d.-]+', '', string)
        if len(string) == 0:
            string = "0"
        return float(string)
