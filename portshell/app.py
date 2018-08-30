from .ui import UseFlagScreen, DependencyScreen


class App:
    def __init__(self, stdscr, pkg):
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

    def runloop(self):
        while True:
            self.draw()
            key = self.stdscr.getch()
            try:
                self.interpret_keystroke(key)
            except StopIteration:
                break

    def enter(self, dep):
        self.stack.append(dep.best)

    def go_back(self):
        if len(self.stack) > 1:
            self.stack.pop()

    @property
    def current(self):
        return self.stack[-1]
