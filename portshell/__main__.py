#!/usr/bin/python

import sys
from curses import wrapper

import portage
from portage.dep import Atom

from .app import App
from .portage import PackageVersion, Portage


def initialize():
    q = sys.argv[1] if len(sys.argv) > 1 else 'dev-lang/python'
    atom = Atom(q)
    mylist = Portage.porttree().match(atom)
    return PackageVersion(portage.best(mylist))


def main(stdscr, mainpkg):
    app = App(stdscr, mainpkg)
    app.runloop()


if __name__ == '__main__':
    wrapper(main, initialize())
