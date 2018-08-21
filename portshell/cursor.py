class PackageCursor:
    def __init__(self, root):
        self.stack = [root]

    @property
    def current(self):
        return self.stack[-1]

    def enter(self, dep):
        pkg = dep.get_package()
        self.stack.append(pkg)

    def go_back(self):
        if len(self.stack) > 1:
            self.stack.pop()

