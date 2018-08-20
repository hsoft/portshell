import curses
from itertools import groupby

from .cursor import PackageCursor


class DependencyScreen:
    def __init__(self, stdscr, cursor):
        self.stdscr = stdscr
        self.cursor = cursor

    def draw(self):
        pkg = self.cursor.current
        max_flag_length = max(len(d.use_conditional) for d in pkg.deps)
        for key, group in groupby(enumerate(pkg.deps), key=lambda t: t[1].use_conditional):
            group = list(group)
            self.stdscr.addstr(group[0][0] + 2, 0, key)
            for i, dep in group:
                mode = curses.A_STANDOUT if i == self.cursor.selindex else 0
                self.stdscr.addstr(i + 2, max_flag_length + 1, f"{dep}", mode)

    def interpret_keystroke(self, key, c):
        if key == curses.KEY_DOWN:
            self.cursor.down()
        elif key == curses.KEY_UP:
            self.cursor.up()
        elif key == curses.KEY_RIGHT:
            self.cursor.right()
        elif key == curses.KEY_LEFT:
            self.cursor.left()
        else:
            return False
        return True


class UseFlagScreen:
    def __init__(self, stdscr, cursor):
        self.stdscr = stdscr
        self.cursor = cursor

    def draw(self):
        pkg = self.cursor.current
        for i, flag in enumerate(pkg.IUSE):
            self.stdscr.addstr(i + 2, 0, flag)

    def interpret_keystroke(self, key, c):
        return False


class UI:
    def __init__(self, stdscr, pkg):
        self.stdscr = stdscr
        self.cursor = PackageCursor(pkg)
        self.screen = DependencyScreen(self.stdscr, self.cursor)

    def draw(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, f"Current package: {self.cursor.current}")
        self.screen.draw()
        self.stdscr.refresh()

    def interpret_keystroke(self, key):
        c = chr(key).lower()
        if self.screen.interpret_keystroke(key, c):
            return
        if c == 'q':
            raise StopIteration()
        elif c == 'u':
            self.screen = UseFlagScreen(self.stdscr, self.cursor)
        elif c == 'd':
            self.screen = DependencyScreen(self.stdscr, self.cursor)

    def runloop(self):
        while True:
            self.draw()
            key = self.stdscr.getch()
            try:
                self.interpret_keystroke(key)
            except StopIteration:
                break

