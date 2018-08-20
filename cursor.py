from gentoolkit.dependencies import Dependencies
from gentoolkit.query import Query


class PackageCursor:
    def __init__(self, root):
        self.stack = [root]
        self._update_deps()

    def _update_deps(self):
        deps = Dependencies(str(self.current))
        deps = deps.get_all_depends()
        self.deps = [Query(dep.atom).find_best() for dep in deps]
        self.selindex = 0

    @property
    def current(self):
        return self.stack[-1]

    @property
    def selection(self):
        if self.selindex < len(self.deps):
            return self.deps[self.selindex]
        else:
            return None

    def down(self):
        if self.selindex < len(self.deps) - 1:
            self.selindex += 1

    def up(self):
        if self.selindex > 0:
            self.selindex -= 1

    def right(self):
        self.stack.append(self.selection)
        self._update_deps()

    def left(self):
        if len(self.stack) > 1:
            to_select = self.stack.pop()
            self._update_deps()
            self.selindex = self.deps.index(to_select)



