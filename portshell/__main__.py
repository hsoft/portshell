#!/usr/bin/python

import sys
from curses import wrapper

import portage
from portage.dep import Atom

from .app import App
from .portage import PackageVersion, Portage, World


app = None

def initialize():
    q = sys.argv[1] if len(sys.argv) > 1 else '@world'
    if q == '@world':
        return World()
    else:
        atom = Atom(q)
        mylist = Portage.porttree().match(atom)
        return PackageVersion(portage.best(mylist))


def main(stdscr, mainpkg):
    global app
    app = App(stdscr, mainpkg)
    app.runloop()


if __name__ == '__main__':
    try:
        wrapper(main, initialize())
    except Exception:
        import pdb
        pdb.set_trace()
        raise
