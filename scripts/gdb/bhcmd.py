# {{{ Imports ------------------------------------------------------------------

import gdb
from re import sub
from itertools import tee
try:
    from itertools import izip
except ImportError: # Python 3.x
    izip = zip

# }}} --------------------------------------------------------------------------
# {{{ Utility functions --------------------------------------------------------

def clean_remaining(remaining):
    return sub(r"^[,]?\s*", "", remaining)

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def strip(array):
    return filter(None, array)

# }}} --------------------------------------------------------------------------
# {{{ GDB Library --------------------------------------------------------------

def bp_info():
    info = []
    breakpoints = strip(gdb.execute("i b", False, True).split("\n"))
    header = [title.lower() for title in strip(breakpoints.pop(0).split(" "))]
    bp = None
    for breakpoint_str in breakpoints:
        breakpoint = strip(breakpoint_str.split(" "))
        if len(breakpoint) == len(header): # breakpoint line.
            bp = dict(zip(header, breakpoint))
            bp["uncategorized"] = []
            info.append(bp)
        elif bp is not None:
            if breakpoint_str.find("breakpoint already hit ") > 0:
                bp["hit_count"] = int(breakpoint_str.split(" ")[3])
            elif breakpoint_str.find("ignore next ") > 0:
                bp["ignore_next"] = int(breakpoint_str.split(" ")[2])
            else:
                bp["uncategorized"].append(breakpoint_str)
        else:
            print("Can't parse the line: %s: skipping.." % (breakpoint_str,))
    return info

class BHBp(gdb.Breakpoint):
    def __init__(self, spec, callback, location, remaining):
        super(BHBp, self).__init__(spec, gdb.BP_BREAKPOINT, internal=False)
        self._callback = callback
        self._location = location
        self._remaining = remaining

    def stop(self):
        if self._remaining is not None:
            gdb.post_event(lambda: self._callback(self._location, clean_remaining(self._remaining)))
        else:
            gdb.post_event(lambda: self._callback(self._location, None))
        return False

class BHCmd(gdb.Command):

    def __init__(self, name, callback, verbose=False):
        super(BHCmd, self).__init__(name, gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL)
        self._callback = callback
        self._verbose = verbose

    def invoke(self, arg, from_tty):
        (remaining, locations) = gdb.decode_line(arg)
        if self._verbose:
            print("-> Argument: %s"  % (arg,))
            print("-> Remaining: %s" % (remaining,))
        if len(locations) != 1:
            gdb.GdbError("The command `BHCmd` supports just one location.")
        location = locations[0]
        if self._verbose:
            print("-> Location %s" % (location,))
        if remaining is not None:
            spec = arg[0:-len(remaining)]
        else:
            spec = arg[:]
        BHBp(spec, self._callback, location, remaining)

# }}} --------------------------------------------------------------------------
# {{{ Custom commands ----------------------------------------------------------

c_examine = BHCmd("c_examine", lambda _, r: gdb.execute("x/%s" % (r,)))
c_printf  = BHCmd("c_printf",  lambda _, r: gdb.execute("printf %s" % (r,)))
c_where   = BHCmd("c_where",   lambda _l, _r: (
    gdb.execute("stepi"),
    gdb.execute("where")))

# }}}

# vim: set filetype=python foldmethod=marker :
