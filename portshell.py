#!/usr/bin/python

import sys
from curses import wrapper

import portage
from portage.dep import Atom

from ui import UI


def initialize():
    q = sys.argv[1] if len(sys.argv) > 1 else 'dev-lang/python'
    db = portage.db['/']['porttree'].dbapi
    atom = Atom(q)
    mylist = db.match(atom)
    return portage.best(mylist)


def main(stdscr, mainpkg):
    ui = UI(stdscr, mainpkg)
    ui.runloop()


if __name__ == '__main__':
    wrapper(main, initialize())
