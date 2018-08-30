import curses

from .portage import PackageStatus
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
    STATUS_ORDER = [
        PackageStatus.NotVisible,
        PackageStatus.New,
        PackageStatus.Updated,
        PackageStatus.Unchanged,
        PackageStatus.Deselected,
    ]
    STATUS_ORDER_MAP = {v: i for i, v in enumerate(STATUS_ORDER)}
    STATUS_DISPLAY = {
        PackageStatus.Unchanged: '',
        PackageStatus.New: 'N',
        PackageStatus.Updated: 'U',
        PackageStatus.NotVisible: '~',
        PackageStatus.Deselected: 'H',
    }

    def _get_deps(self):
        def sort_key(dep):
            return self.STATUS_ORDER_MAP[dep.status]

        pkg = self.app.current
        return sorted(pkg.deps, key=sort_key)

    def _get_row(self, dep):
        bv = dep.best.version if dep.best else ''
        iv = dep.installed.version if dep.installed else ''
        status = self.STATUS_DISPLAY[dep.status]
        deps = dep.best.affected_deep_deps
        depcount = str(len(deps)) if deps is not None else '?'
        return (status, dep.cps, iv, bv, depcount)

    def draw(self):
        active = self._get_deps()
        rows = [("S", "Package", "Installed", "Best", "Aff deps")]
        rows.extend(map(self._get_row, active))
        for i, line in enumerate(tableize(rows)):
            # first row is header, so we do (i - 1)
            mode = curses.A_STANDOUT if (i - 1) == self.selected_index else 0
            self.stdscr.addstr(i + 2, 0, line, mode)

    def interpret_keystroke(self, key, c):
        if super().interpret_keystroke(key, c):
            return True
        if key == curses.KEY_RIGHT:
            active = self._get_deps()
            if active:
                self.app.enter(active[self.selected_index])
                self.selected_index = 0
        elif key == curses.KEY_LEFT:
            self.app.go_back()
        else:
            return False
        return True

    def selectable_item_count(self):
        return len(self._get_deps())


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
