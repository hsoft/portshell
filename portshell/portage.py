# Convenience layer over portage API and gentoolkit
import portage
from gentoolkit.dependencies import Dependencies
from gentoolkit.query import Query

class Portage:
    @staticmethod
    def porttree():
        return portage.db['/']['porttree'].dbapi


class Package:
    def __init__(self, cpv):
        self.cpv = cpv
        self._deps = None
        self._IUSE = None

    @classmethod
    def from_atom(cls, atom):
        return Query(atom).find_best()

    @property
    def deps(self):
        if self._deps is None:
            deps = Dependencies(self.cpv).get_all_depends()
            deps = (Dependency(Package.from_atom(d.atom), d.use_conditional) for d in deps)
            self._deps = sorted(deps, key=lambda d: (d.use_conditional, d.pkg.cpv))
        return self._deps

    @property
    def IUSE(self):
        if self._IUSE is None:
            self._IUSE = Portage.porttree().aux_get(self.cpv, ['IUSE'])[0].split()
        return self._IUSE


class Dependency:
    def __init__(self, pkg, use_conditional):
        self.pkg = pkg
        self.use_conditional = use_conditional or ''

    def __str__(self):
        return str(self.pkg)


