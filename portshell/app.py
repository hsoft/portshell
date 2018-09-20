import curses
import time

from .ui import UseFlagScreen, DependencyScreen


class App:
    def __init__(self, stdscr, pkg):
        stdscr.nodelay(True)
        self.stdscr = stdscr
        self.stack = [pkg]
        self.screen = DependencyScreen(self.stdscr, self)

    def draw(self):
        maxy, _ = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, f"Current package: {self.current}")
        self.screen.draw()
        self.stdscr.addstr(maxy-1, 0, self.screen.statusline)
        self.stdscr.refresh()

    def enter(self, dep):
        self.stack.append(dep.best)

    def go_back(self):
        if len(self.stack) > 1:
            self.stack.pop()

    def interpret_keystroke(self, key):
        c = chr(key).lower()
        if self.screen.interpret_keystroke(key, c):
            return
        if c == 'q':
            raise StopIteration()
        elif c == 'u':
            self.screen = UseFlagScreen(self.stdscr, self)
        elif c == 'd':
            self.screen = DependencyScreen(self.stdscr, self)

    def pulse(self):
        # Instead of doing threading and having to deal with race conditions, we "pulse" small
        # units of work at each runloop iteration.
        if self.current.pulse_deps():
            time.sleep(0.1)

    def runloop(self):
        self.draw()
        while True:
            try:
                key = self.stdscr.getch()
                if key != curses.ERR:
                    self.interpret_keystroke(key)
                    self.draw()
            except StopIteration:
                break
            self.pulse()

    @property
    def current(self):
        return self.stack[-1]
