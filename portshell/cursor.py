import portage
from gentoolkit.dependencies import Dependencies
from gentoolkit.query import Query


class Dependency:
    def __init__(self, dep):
        self.use_conditional = dep.use_conditional or ''
        self.pkg = Query(dep.atom).find_best()

    def __str__(self):
        return str(self.pkg)


class PackageCursor:
    def __init__(self, root):
        self.stack = [root]
        self._update_info()

    def _update_info(self):
        deps = Dependencies(str(self.current))
        self.deps = sorted(
            map(Dependency, deps.get_all_depends()),
            key=lambda d: (d.use_conditional, str(d))
        )
        self.flags = portage.db['/']['porttree'].dbapi.aux_get(
            self.current.cpv, ['IUSE'])[0].split()
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
        self._update_info()

    def left(self):
        if len(self.stack) > 1:
            to_select = self.stack.pop()
            self._update_info()
            self.selindex = self.deps.index(to_select)

