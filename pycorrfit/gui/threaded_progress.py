# -*- coding: utf-8 -*-
"""
PyCorrFit

A progress bar with an abort button that works for long running processes.
"""
import time
import threading
import traceback as tb
import wx
import sys
from pycorrfit import Fit



class KThread(threading.Thread):
    """A subclass of threading.Thread, with a kill()
    method.
    
    https://web.archive.org/web/20130503082442/http://mail.python.org/pipermail/python-list/2004-May/281943.html

    The KThread class works by installing a trace in the thread.  The trace
    checks at every line of execution whether it should terminate itself.
    So it's possible to instantly kill any actively executing Python code.
    However, if your code hangs at a lower level than Python, then the
    thread will not actually be killed until the next Python statement is
    executed.
    """
    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run      # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the
        trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True



class WorkerThread(KThread):
    """Worker Thread Class."""
    def __init__(self, target, args, kwargs):
        """Init Worker Thread Class."""
        KThread.__init__(self)
        self.traceback = None
        self.target = target
        self.args = args
        self.kwargs = kwargs
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
        

    def run(self):
        """Run Worker Thread."""
        try:
            self.target(*self.args, **self.kwargs)
        except:
            self.traceback = tb.format_exc()


class ThreadedProgressDlg(object):
    def __init__(self, parent, targets, args=None, kwargs={},
                 title="Dialog title",
                 messages=None):
        if hasattr(targets, "__call__"):
            targets = [targets]

        nums = len(targets)
        
        if args is None:
            args = [()]*nums
        elif isinstance(args, list):
            # convenience-convert args to tuples
            if not isinstance(args[0], tuple):
                args = [ (t,) for t in args ]
        
        if isinstance(kwargs, dict):
            kwargs = [kwargs]*nums
        
        if messages is None:
            messages = [ "item {} of {}".format(a+1, nums) for a in range(nums) ]
        
        sty = wx.PD_REMAINING_TIME|wx.PD_SMOOTH|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT
        dlg = wx.ProgressDialog(title,
                                "initializing...",
                                maximum=nums,
                                parent=parent,
                                style=sty)
        self.aborted = False
        self.index_aborted = None

        for jj in range(nums):
            init = True
            worker = WorkerThread(target=targets[jj],
                                  args=args[jj],
                                  kwargs=kwargs[jj])
            while worker.is_alive() or init:
                init=False
                time.sleep(.01)
                if dlg.Update(jj+1, messages[jj])[0] == False:
                    dlg.Destroy()
                    worker.kill()
                    self.aborted = True
                    break
            if self.aborted:
                self.aborted = True
                self.index_aborted = jj
                break
            
            if worker.traceback is not None:
                dlg.Destroy()
                self.aborted = True
                self.index_aborted = jj
                raise Exception(worker.traceback)

        self.finalize()

    def finalize(self):
        pass



class FitProgressDlg(ThreadedProgressDlg):
    def __init__(self, parent, pages, trigger=None):
        if not isinstance(pages, list):
            pages = [pages]
        self.pages = pages
        self.trigger = trigger
        title = "Fitting data"
        messages = [ "fitting page {}".format(pi.counter.strip("# :")) for pi in pages ]
        targets = [Fit]*len(pages)
        args = [pi.corr for pi in pages]
        super(FitProgressDlg, self).__init__(parent, targets, args,
                                             title=title,
                                             messages=messages)

    
    def finalize(self):
        if self.aborted:
            ## we need to cleanup
            fin_index = max(0,self.index_aborted-1)
            pab = self.pages[self.index_aborted]
            pab.fit_results = None
            pab.apply_parameters()
        else:
            fin_index = len(self.pages)
        
        # finalize fitting
        [ pi.Fit_finalize(trigger=self.trigger) for pi in self.pages[:fin_index] ] 



if __name__ == "__main__":
    # GUI Frame class that spins off the worker thread
    class MainFrame(wx.Frame):
        """Class MainFrame."""
        def __init__(self, parent, id):
            """Create the MainFrame."""
            wx.Frame.__init__(self, parent, id, 'Thread Test')
    
            # Dumb sample frame with two buttons
            but = wx.Button(self, wx.ID_ANY, 'Start Progress', pos=(0,0))
    
            
            self.Bind(wx.EVT_BUTTON, self.OnStart, but)
    
        def OnStart(self, event):
            """Start Computation."""
            # Trigger the worker thread unless it's already busy
            arguments = [ test_class(a) for a in range(10) ]
            def method(x):
                x.arg *= 1.1
                time.sleep(1)
            tp = ThreadedProgressDlg(self, [method]*len(arguments), arguments)
            print(tp.index_aborted)
            print([a.arg for a in arguments])
    
    
    class MainApp(wx.App):
        """Class Main App."""
        def OnInit(self):
            """Init Main App."""
            self.frame = MainFrame(None, -1)
            self.frame.Show(True)
            self.SetTopWindow(self.frame)
            return True
    
    class test_class(object):
        def __init__(self, arg):
            self.arg = arg
    
    
    app = MainApp(0)
    app.MainLoop()