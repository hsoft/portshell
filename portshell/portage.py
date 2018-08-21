# Convenience layer over portage API
import portage
from portage.dep import use_reduce, isvalidatom, dep_getkey, dep_getslot

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

    def deps_affected_by_flag(self, flag):
        depstring = Portage.get_depstring(self.cpv)
        base_deps = set(filter(isvalidatom, use_reduce(depstring, flat=True)))
        deps = set(filter(isvalidatom, use_reduce(depstring, uselist=[flag.name], flat=True)))
        return sorted(map(Dependency, deps - base_deps))

    @property
    def deps(self):
        if self._deps is None:
            depstring = Portage.get_depstring(self.cpv)
            enabled_flags = Portage.enabled_use_flags(self.cpv)
            all_deps = filter(isvalidatom, use_reduce(depstring, matchall=True, flat=True))
            active_deps = set(use_reduce(depstring, uselist=enabled_flags, flat=True))
            deps = {Dependency(d, active=(d in active_deps)) for d in all_deps}
            self._deps = sorted(deps)
        return self._deps

    @property
    def IUSE(self):
        if self._IUSE is None:
            IUSE = Portage.porttree().aux_get(self.cpv, ['IUSE'])[0].split()
            enabled_flags = Portage.enabled_use_flags(self.cpv)
            self._IUSE = [Flag.from_iuse(f, enabled_flags) for f in IUSE]
        return self._IUSE


class Dependency:
    def __init__(self, atom, active=False):
        cp = dep_getkey(atom)
        slot = dep_getslot(atom) or ''
        if slot.endswith('='):
            slot = slot[:-1]
        if slot and slot not in {'*', '0'}:
            self.cps = f'{cp}:{slot}'
        else:
            self.cps = cp
        self.active = active

    def __str__(self):
        return self.cps

    __repr__ = __str__

    def __eq__(self, other):
        return self.cps == other.cps

    def __lt__(self, other):
        return self.cps < other.cps

    def __hash__(self):
        return hash(self.cps)

    def get_package(self):
        return Package.from_atom(self.cps)


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

