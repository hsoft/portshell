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


class SelectableScreen(Screen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_index = 0

    def interpret_keystroke(self, key, c):
        if key == curses.KEY_DOWN:
            self.down()
        elif key == curses.KEY_UP:
            self.up()
        else:
            return False
        return True

    def selectable_item_count(self):
        return 0

    def down(self):
        if self.selected_index < self.selectable_item_count() - 1:
            self.selected_index += 1

    def up(self):
        if self.selected_index > 0:
            self.selected_index -= 1


class DependencyScreen(SelectableScreen):
    def draw(self):
        pkg = self.cursor.current
        active = [d for d in pkg.deps if d.active]
        inactive_count = len(pkg.deps) - len(active)
        for i, dep in enumerate(active):
            mode = curses.A_STANDOUT if i == self.selected_index else 0
            self.stdscr.addstr(i + 2, 0, f"{dep}", mode)
        self.statusline = f"{inactive_count} inactive package(s)"

    def interpret_keystroke(self, key, c):
        if super().interpret_keystroke(key, c):
            return True
        if key == curses.KEY_RIGHT:
            self.cursor.enter(self.selected_index)
        elif key == curses.KEY_LEFT:
            self.cursor.go_back()
        else:
            return False
        return True

    def selectable_item_count(self):
        pkg = self.cursor.current
        return len([d for d in pkg.deps if d.active])


class UseFlagScreen(SelectableScreen):
    def draw(self):
        pkg = self.cursor.current
        maxlen = 0
        for i, flag in enumerate(pkg.IUSE):
            mode = curses.A_BOLD if flag.is_enabled else 0
            if i == self.selected_index:
                mode |= curses.A_STANDOUT
            s = str(flag)
            maxlen = max(len(s), maxlen)
            self.stdscr.addstr(i + 2, 0, s, mode)
        if pkg.IUSE:
            deps = pkg.deps_affected_by_flag(pkg.IUSE[self.selected_index])
            for i, dep in enumerate(deps):
                self.stdscr.addstr(i + 2, maxlen + 1, str(dep))

    def selectable_item_count(self):
        return len(self.cursor.current.IUSE)


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

