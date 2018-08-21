import curses

from .cursor import PackageCursor


class Screen:
    def __init__(self, stdscr, cursor):
        self.stdscr = stdscr
        self.cursor = cursor
        self.statusline = ''

    def draw(self):
        raise NotImplementedError()

    def interpret_keystroke(self, key, c):
        return False


class DependencyScreen(Screen):
    def draw(self):
        pkg = self.cursor.current
        active = [d for d in pkg.deps if d.active]
        inactive_count = len(pkg.deps) - len(active)
        for i, dep in enumerate(active):
            mode = curses.A_STANDOUT if i == self.cursor.selindex else 0
            self.stdscr.addstr(i + 2, 0, f"{dep}", mode)
        self.statusline = f"{inactive_count} inactive package(s)"

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


class UseFlagScreen(Screen):
    def draw(self):
        pkg = self.cursor.current
        for i, flag in enumerate(pkg.IUSE):
            mode = curses.A_BOLD if flag.is_enabled else 0
            self.stdscr.addstr(i + 2, 0, str(flag), mode)



class UI:
    def __init__(self, stdscr, pkg):
        self.stdscr = stdscr
        self.cursor = PackageCursor(pkg)
        self.screen = DependencyScreen(self.stdscr, self.cursor)

    def draw(self):
        maxy, _ = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, f"Current package: {self.cursor.current}")
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

