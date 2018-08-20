class PackageCursor:
    def __init__(self, root):
        self.stack = [root]
        self._update_info()

    def _update_info(self):
        self.selindex = 0

    @property
    def current(self):
        return self.stack[-1]

    @property
    def selection(self):
        if self.selindex < len(self.current.deps):
            return self.current.deps[self.selindex]
        else:
            return None

    def down(self):
        if self.selindex < len(self.current.deps) - 1:
            self.selindex += 1

    def up(self):
        if self.selindex > 0:
            self.selindex -= 1

    def right(self):
        self.stack.append(self.selection)
        self._update_info()

    def left(self):
        if len(self.stack) > 1:
            to_select = self.stack.pop()
            self._update_info()
            self.selindex = self.current.deps.index(to_select)

