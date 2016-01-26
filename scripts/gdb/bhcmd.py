import gdb
import re

# {{{ Utility functions --------------------------------------------------------

def clean_remaining(remaining):
    return re.sub(r"^[,]?\s*", "", remaining)

# }}}

# {{{ GDB Library --------------------------------------------------------------

class BHBp(gdb.Breakpoint):
    def __init__(self, spec, callback, location, remaining):
        super(BHBp, self).__init__(spec, gdb.BP_BREAKPOINT, internal=False)
        self.callback = callback
        self.location = location
        self.remaining = remaining

    def stop(self):
        callback(self.location, clean_remaining(self.remaining))
        return False

class BHCmd(gdb.Command):

    def __init__(self, name, callback, verbose=False):
        super(BHCmd, self).__init__(name, gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL)
        self.callback = callback
        self.verbose = verbose

    def invoke(self, arg, from_tty):
        (remaining, locations) = gdb.decode_line(arg)
        if self.verbose:
            print("-> Argument: %s"  % (arg,))
            print("-> Remaining: %s" % (remaining,))
        if len(locations) != 1:
            gdb.GdbError("The command `BHCmd` supports just one location.")
        location = locations[0]
        if self.verbose:
            print("-> Location %s" % (location,))
        spec = "*0x%s" % (location.pc,)
        BHBp(spec, callback, location, remaining)

# }}}

# {{{ Custom commands ----------------------------------------------------------

c_examine = BHCmd("c_examine", lambda _, r: gdb.execute("x/%s" % (r,)))

# }}}
