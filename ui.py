import curses

from cursor import PackageCursor


def draw(win, cursor):
    win.clear()
    win.addstr(0, 0, f"Current package: {cursor.current}")
    for i, dep in enumerate(cursor.deps):
        mode = curses.A_STANDOUT if i == cursor.selindex else 0
        win.addstr(i + 2, 0, f"{dep}", mode)
    win.refresh()


class UI:
    def __init__(self, stdscr, pkg):
        self.stdscr = stdscr
        self.cursor = PackageCursor(pkg)

    def interpret_keystroke(self, c):
        if c == ord('q'):
            return False
        elif c == curses.KEY_DOWN:
            self.cursor.down()
        elif c == curses.KEY_UP:
            self.cursor.up()
        elif c == curses.KEY_RIGHT:
            self.cursor.right()
        elif c == curses.KEY_LEFT:
            self.cursor.left()
        return True

    def runloop(self):
        stdscr = self.stdscr
        cursor = self.cursor
        while True:
            draw(stdscr, cursor)
            c = stdscr.getch()
            if not self.interpret_keystroke(c):
                break

