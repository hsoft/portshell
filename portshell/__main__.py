#!/usr/bin/python

import sys
from curses import wrapper

import portage
from portage.dep import Atom

from .ui import UI
from .portage import Package, Portage


def initialize():
    q = sys.argv[1] if len(sys.argv) > 1 else 'dev-lang/python'
    atom = Atom(q)
    mylist = Portage.porttree().match(atom)
    return Package(portage.best(mylist))


def main(stdscr, mainpkg):
    ui = UI(stdscr, mainpkg)
    ui.runloop()


if __name__ == '__main__':
    wrapper(main, initialize())
