import curses

from .util import tableize


class Screen:
    def __init__(self, stdscr, app):
        self.stdscr = stdscr
        self.app = app
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
    def _get_active_deps(self):
        pkg = self.app.current
        return [d for d in pkg.deps if d.active]

    def draw(self):
        pkg = self.app.current
        active = self._get_active_deps()
        inactive_count = len(pkg.deps) - len(active)
        rows = [("Package", "Installed", "Best")]
        for dep in active:
            best = dep.get_package()
            installed = dep.get_installed()
            bv = best.version if best else ''
            iv = installed.version if installed else ''
            rows.append((dep.cps, iv, bv))
        for i, line in enumerate(tableize(rows)):
            # first row is header, so we do (i - 1)
            mode = curses.A_STANDOUT if (i - 1) == self.selected_index else 0
            self.stdscr.addstr(i + 2, 0, line, mode)
        self.statusline = f"{inactive_count} inactive package(s)"

    def interpret_keystroke(self, key, c):
        if super().interpret_keystroke(key, c):
            return True
        if key == curses.KEY_RIGHT:
            active = self._get_active_deps()
            if active:
                self.app.enter(active[self.selected_index])
                self.selected_index = 0
        elif key == curses.KEY_LEFT:
            self.app.go_back()
        else:
            return False
        return True

    def selectable_item_count(self):
        return len(self._get_active_deps())


class UseFlagScreen(SelectableScreen):
    def draw(self):
        pkg = self.app.current
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
        return len(self.app.current.IUSE)
