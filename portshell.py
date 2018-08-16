#!/usr/bin/python

import sys
import curses
from curses import wrapper

import portage
from portage.dep import Atom
from gentoolkit.dependencies import Dependencies


class PackageCursor:
    def __init__(self, root):
        self.stack = [root]
        self._update_deps()

    def _update_deps(self):
        deps = Dependencies(str(self.current))
        self.deps = [dep for _, dep in deps.graph_depends()]
        self.selindex = 0

    @property
    def current(self):
        return self.stack[-1]

    @property
    def selection(self):
        if self.selindex < len(self.deps):
            return self.deps[self.selindex]
        else:
            return None

    def down(self):
        if self.selindex < len(self.deps) - 1:
            self.selindex += 1

    def up(self):
        if self.selindex > 0:
            self.selindex -= 1

    def right(self):
        self.stack.append(self.selection)
        self._update_deps()

    def left(self):
        if len(self.stack) > 1:
            to_select = self.stack.pop()
            self._update_deps()
            self.selindex = self.deps.index(to_select)


def initialize():
    q = sys.argv[1] if len(sys.argv) > 1 else 'dev-lang/python'
    db = portage.db['/']['porttree'].dbapi
    atom = Atom(q)
    mylist = db.match(atom)
    pkg = portage.best(mylist)
    return PackageCursor(pkg)


def draw(win, cursor):
    win.clear()
    win.addstr(0, 0, f"Current package: {cursor.current}")
    for i, dep in enumerate(cursor.deps):
        mode = curses.A_STANDOUT if i == cursor.selindex else 0
        win.addstr(i + 2, 0, str(dep), mode)
    win.refresh()

def main(stdscr, cursor):
    while True:
        draw(stdscr, cursor)
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == curses.KEY_DOWN:
            cursor.down()
        elif c == curses.KEY_UP:
            cursor.up()
        elif c == curses.KEY_RIGHT:
            cursor.right()
        elif c == curses.KEY_LEFT:
            cursor.left()


if __name__ == '__main__':
    wrapper(main, initialize())
