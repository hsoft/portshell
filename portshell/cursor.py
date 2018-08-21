class PackageCursor:
    def __init__(self, root):
        self.stack = [root]

    @property
    def current(self):
        return self.stack[-1]

    def enter(self, selected_index):
        if selected_index < len(self.current.deps):
            dep = self.current.deps[selected_index]
        else:
            return
        pkg = dep.get_package()
        self.stack.append(pkg)

    def go_back(self):
        if len(self.stack) > 1:
            self.stack.pop()

