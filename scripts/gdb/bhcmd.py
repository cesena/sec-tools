# {{{ Imports ------------------------------------------------------------------

import gdb
import sys
from re import sub
from itertools import tee
try:
    from itertools import izip
except ImportError: # Python 3.x
    izip = zip

# }}} --------------------------------------------------------------------------
# {{{ Utility functions --------------------------------------------------------

def clean_remaining(remaining):
    return remaining and sub(r"^[,]?\s*", "", remaining)

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
            print("Can't parse the line: {}: skipping..".format(breakpoint_str))
    return info

class BHBp(gdb.Breakpoint):
    def __init__(self, spec, callback, location, remaining, go_on=False):
        super(BHBp, self).__init__(spec, gdb.BP_BREAKPOINT, internal=False)
        self._go_on = go_on
        self._callback = callback
        self._location = location
        self._remaining = remaining

    def stop(self):
        callback = lambda: self._callback(self._location,
                                          clean_remaining(self._remaining))
        if self._go_on:
            callback = lambda: (callback(), gdb.execute("continue"))
        gdb.post_event(callback)
        return True

class BHCmd(gdb.Command):

    @staticmethod
    def create(name, callback, verbose=False, go_on=False, prefix="c"):
        cmd_name = "{prefix}_{name}".format(prefix=prefix, name=name)
        cmd_name_loop = "{name}_loop".format(name=cmd_name)

        cmd      = BHCmd(cmd_name,      callback, verbose, go_on)
        cmd_loop = BHCmd(cmd_name_loop, callback, verbose, go_on)

        setattr(sys.modules[__name__], cmd_name,      cmd)
        setattr(sys.modules[__name__], cmd_name_loop, cmd_loop)

        return [cmd, cmd_loop]

    def __init__(self, name, callback, verbose=False, go_on=False):
        super(BHCmd, self).__init__(name, gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL)
        self._callback = callback
        self._verbose  = verbose
        self._go_on    = go_on

    def invoke(self, arg, from_tty):
        (remaining, locations) = gdb.decode_line(arg)
        if self._verbose:
            print("-> Argument: {}".format(arg))
            print("-> Remaining: {}".format(remaining))
        if len(locations) != 1:
            gdb.GdbError("The command `BHCmd` supports just one location.")
        location = locations[0]
        if self._verbose:
            print("-> Location {}".format(location))
        spec = remaining and arg[0:-len(remaining)] or arg[:]
        BHBp(spec, self._callback, location, remaining, self._go_on)

# }}} --------------------------------------------------------------------------
# {{{ Custom commands ----------------------------------------------------------

BHCmd.create("examine", lambda _,   r:  gdb.execute("x/{}".format(r)))
BHCmd.create("printf",  lambda _,   r:  gdb.execute("printf {}".format(r)))
BHCmd.create("where",   lambda _l, _r: (gdb.execute("stepi"),
                                        gdb.execute("where")))

# }}}

# vim: set filetype=python foldmethod=marker :
