"""A progress bar with an abort button that works for long running processes"""
import time
import threading
import traceback as tb
import sys

import wx


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
                 messages=None,
                 time_delay=2):
        """ This class implements a progress dialog that can abort during
        a function call, as opposed to the stock wx.ProgressDialog.

        Parameters
        ----------
        parent : wx object
            The parent of the progress dialog.
        targets : list of callables
            The methods that will be called in each step in the progress.
        args : list
            The arguments to the targets. Should match length of targets.
        kwargs : dict or list of dicts
            Keyword arguments to the targets. If dict, then the same dict
            is used for all targets.
        title : str
            The title of the progress dialog.
        messages : list of str
            The message displayed for each target. Should match length of
            targets.
        time_delay : float
            Time after which the dialog should be displayed. The default
            is 2s, which means that a dialog is only displayed after 2s
            or earlier, if the overall progress seems to be taking longer
            than 2s.

        Arguments
        ---------
        aborted : bool
            Whether the progress was aborted by the user.
        index_aborted : None or int
            The index in `targets` at which the progress was aborted.
        finalize : callable
            A method that will be called after fitting. Can be overriden
            by subclasses.

        Notes
        -----
        The progress dialog is only displayed when `time_delay` is or
        seems shorter than the total running time of the progress. If
        the progress is not displayed, then a busy cursor is displayed.

        """
        wx.BeginBusyCursor()

        if hasattr(targets, "__call__"):
            targets = [targets]

        nums = len(targets)

        if not args:
            args = [()]*nums
        elif isinstance(args, list):
            # convenience-convert args to tuples
            if not isinstance(args[0], tuple):
                args = [ (t,) for t in args ]

        if isinstance(kwargs, dict):
            kwargs = [kwargs]*nums

        if not messages:
            messages = [ "item {} of {}".format(a+1, nums) for a in range(nums) ]


        time1 = time.time()
        sty = wx.PD_SMOOTH|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT
        if len(targets) > 1:
            sty = sty|wx.PD_REMAINING_TIME
        dlgargs = [title, "initializing..."]
        dlgkwargs = {"maximum":nums, "parent":parent, "style":sty }
        dlg = None

        self.aborted = False
        self.index_aborted = None

        for jj in range(nums):
            init = True
            worker = WorkerThread(target=targets[jj],
                                  args=args[jj],
                                  kwargs=kwargs[jj])
            while worker.is_alive() or init:
                if (time.time()-time1 > time_delay or
                    (time.time()-time1)/(jj+1)*nums > time_delay
                    ) and not dlg:
                    dlg = wx.ProgressDialog(*dlgargs, **dlgkwargs)
                    wx.EndBusyCursor()

                init=False
                time.sleep(.01)
                if dlg:
                    if len(targets) == 1:
                        # no progress bar but pulse
                        # cont = dlg.UpdatePulse(messages[jj])[0]
                        cont = dlg.Update(0, messages[jj])[0]
                    else:
                        # show progress until end
                        cont = dlg.Update(jj+1, messages[jj])[0]
                    if cont == False:
                        dlg.Destroy()
                        worker.kill()
                        self.aborted = True
                        break

            if self.aborted:
                self.aborted = True
                self.index_aborted = jj
                break

            if worker.traceback:
                dlg.Destroy()
                self.aborted = True
                self.index_aborted = jj
                raise Exception(worker.traceback)

        if dlg:
            dlg.Hide()
            dlg.Destroy()
        wx.EndBusyCursor()
        wx.BeginBusyCursor()
        self.finalize()
        wx.EndBusyCursor()

    def finalize(self):
        """ You may override this method in subclasses.
        """
        pass



if __name__ == "__main__":
    # GUI Frame class that spins off the worker thread
    class MainFrame(wx.Frame):
        """Class MainFrame."""
        def __init__(self, parent, aid):
            """Create the MainFrame."""
            wx.Frame.__init__(self, parent, aid, 'Thread Test')

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