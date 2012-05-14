import time, logging
log = logging.getLogger()

def logTime(func):
    def inner(*args, **kw):
        t1 = time.time()
        try:
            ret = func(*args, **kw)
        finally:
            log.info("Call to %s took %.1f ms" % (
                func.__name__, 1000 * (time.time() - t1)))
        return ret
    return inner

def debug():
    from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
    shell = TerminalInteractiveShell(user_ns=vars())
    shell.mainloop()
