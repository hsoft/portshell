# Convenience layer over portage API
import portage
from portage.dep import use_reduce, extract_affecting_use, isvalidatom, dep_getkey
from gentoolkit.query import Query

class Portage:
    @staticmethod
    def porttree():
        return portage.db['/']['porttree'].dbapi

    @staticmethod
    def get_depstring(cpv):
        dbapi = Portage.porttree()
        raw = dbapi.aux_get(cpv, ('DEPEND', 'PDEPEND', 'RDEPEND'))
        return ' '.join(raw)


class Package:
    def __init__(self, cpv):
        self.cpv = cpv
        self._deps = None
        self._IUSE = None

    @classmethod
    def from_atom(cls, atom):
        return cls(str(Query(atom).find_best()))

    def __str__(self):
        return self.cpv

    @property
    def deps(self):
        if self._deps is None:
            depstring = Portage.get_depstring(self.cpv)
            deps = filter(isvalidatom, use_reduce(depstring, matchall=True, flat=True))
            deps = {Dependency(d, depstring) for d in deps}
            self._deps = sorted(deps, key=lambda d: (d.use_conditional, d.cp))
        return self._deps

    @property
    def IUSE(self):
        if self._IUSE is None:
            self._IUSE = Portage.porttree().aux_get(self.cpv, ['IUSE'])[0].split()
        return self._IUSE


class Dependency:
    def __init__(self, atom, depstring):
        self.cp = dep_getkey(atom)
        self.use_conditional = '/'.join(extract_affecting_use(depstring, atom))

    def __str__(self):
        return self.cp

    def __eq__(self, other):
        return self.cp == other.cp

    def __hash__(self):
        return hash(self.cp)

    def get_package(self):
        return Package.from_atom(self.cp)
