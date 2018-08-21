# Convenience layer over portage API
import portage
from portage.dep import use_reduce, extract_affecting_use, isvalidatom, dep_getkey

class Portage:
    @staticmethod
    def porttree():
        return portage.db['/']['porttree'].dbapi

    @staticmethod
    def get_depstring(cpv):
        dbapi = Portage.porttree()
        raw = dbapi.aux_get(cpv, ('DEPEND', 'PDEPEND', 'RDEPEND'))
        return ' '.join(raw)

    @staticmethod
    def find_best(atom):
        dbapi = Portage.porttree()
        return dbapi.xmatch('bestmatch-visible', atom)

    @staticmethod
    def system_use_flags():
        return set(portage.settings['USE'].split())

    @staticmethod
    def enabled_use_flags(cpv):
        settings = Portage.porttree().settings
        try:
            settings.unlock()
            settings.setcpv(cpv, mydb=portage.portdb)
            return set(portage.settings['PORTAGE_USE'].split())
        finally:
            settings.reset()
            settings.lock()


class Package:
    def __init__(self, cpv):
        self.cpv = cpv
        self._deps = None
        self._IUSE = None

    @classmethod
    def from_atom(cls, atom):
        return cls(Portage.find_best(atom))

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
            IUSE = Portage.porttree().aux_get(self.cpv, ['IUSE'])[0].split()
            enabled_flags = Portage.enabled_use_flags(self.cpv)
            self._IUSE = [Flag.from_iuse(f, enabled_flags) for f in IUSE]
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


class Flag:
    def __init__(self, name, is_defaulted, is_enabled):
        self.name = name
        self.is_defaulted = is_defaulted
        self.is_enabled = is_enabled

    @classmethod
    def from_iuse(cls, iuse_str, enabled_flags):
        is_defaulted = iuse_str.startswith('+')
        if is_defaulted:
            iuse_str = iuse_str[1:]
        is_enabled = iuse_str in enabled_flags
        return cls(iuse_str, is_defaulted, is_enabled)

    def __str__(self):
        return self.name

