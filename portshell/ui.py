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
        self.offset = 0

    def _adjust_offset(self):
        height, *_ = self.list_coords()
        count = self.selectable_item_count()
        if count > height:
            if self.selected_index - self.offset > height - 2:
                self.offset = self.selected_index - height + 2
            elif self.selected_index < self.offset:
                self.offset = self.selected_index - 1
            self.offset = max(min(self.offset, count - height), 0)

    def draw_list(self, lines):
        height, width, y, x = self.list_coords()
        if self.offset > 0:
            lines = ['...'] + lines[self.offset+1:]
        if len(lines) > height:
            del lines[height-1:]
            lines.append('...')

        attrmap = {self.selected_index - self.offset: curses.A_STANDOUT}
        win = self.stdscr.subwin(height, width, y, x)
        win.clear()
        for i, line in enumerate(lines[:height]):
            mode = attrmap.get(i, 0)
            win.addstr(i, 0, line, mode)
        win.refresh()

    def interpret_keystroke(self, key, c):
        if key == curses.KEY_DOWN:
            self.down()
        elif key == curses.KEY_NPAGE:
            self.down(10)
        elif key == curses.KEY_UP:
            self.up()
        elif key == curses.KEY_PPAGE:
            self.up(10)
        else:
            return False
        return True

    def list_coords(self):
        # (height, width, y, x)
        # LINES - 3: two header lines, 1 footer line
        return (curses.LINES - 3, curses.COLS, 2, 0)

    def selectable_item_count(self):
        return 0

    def down(self, count=1):
        self.selected_index = min(
            self.selected_index + count,
            self.selectable_item_count() - 1)
        self._adjust_offset()

    def up(self, count=1):
        self.selected_index = max(self.selected_index - count, 0)
        self._adjust_offset()


class DependencyScreen(SelectableScreen):
    STATUS_ORDER = [
        PackageStatus.NotVisible,
        PackageStatus.New,
        PackageStatus.Updated,
        PackageStatus.Unchanged,
        PackageStatus.Deselected,
    ]
    STATUS_ORDER_MAP = {v: i for i, v in enumerate(STATUS_ORDER)}

    def _get_deps(self):
        def sort_key(dep):
            return self.STATUS_ORDER_MAP[dep.status]

        pkg = self.app.current
        return sorted(pkg.deps, key=sort_key)

    def _get_row(self, dep):
        bv = dep.best.version if dep.best else ''
        iv = dep.installed.version if dep.installed else ''
        if bv:
            deps = dep.best.affected_deep_deps
            depcount = str(len(deps)) if deps is not None else '?'
        else:
            depcount = ''
        return (dep.status.value, dep.cps, iv, bv, depcount)

    def draw(self):
        active = self._get_deps()
        rows = [("S", "Package", "Installed", "Best", "Aff deps")]
        rows.extend(map(self._get_row, active))
        rows = list(tableize(rows))
        self.stdscr.addstr(2, 0, rows[0])
        del rows[0]
        self.draw_list(rows)

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

    def list_coords(self):
        (h, w, y, x) = super().list_coords()
        return (h - 1, w, y + 1, x)

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
