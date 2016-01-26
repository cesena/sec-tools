import gdb
from re import sub
from itertools import tee
try:
    from itertools import izip
except ImportError: # Python 3.x
    izip = zip

# {{{ Utility functions --------------------------------------------------------

def clean_remaining(remaining):
    return sub(r"^[,]?\s*", "", remaining)

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

# }}}

# {{{ GDB Library --------------------------------------------------------------

class BHBp(gdb.Breakpoint):
    def __init__(self, spec, callback, location, remaining):
        super(BHBp, self).__init__(spec, gdb.BP_BREAKPOINT, internal=False)
        self._callback = callback
        self._location = location
        self._remaining = remaining

    def stop(self):
        self._callback(self._location, clean_remaining(self._remaining))
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
        spec = arg[0:-len(remaining)]
        BHBp(spec, self._callback, location, remaining)

# }}}

# {{{ Custom commands ----------------------------------------------------------

c_examine = BHCmd("c_examine", lambda _, r: gdb.execute("x/%s" % (r,)))
c_printf  = BHCmd("c_printf",  lambda _, r: gdb.execute("printf %s" % (r,)))

# }}}
