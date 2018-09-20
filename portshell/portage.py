# Convenience layer over portage API
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from enum import Enum

import portage
import portage._sets
from portage.dep import use_reduce, isvalidatom, dep_getkey, dep_getslot
from portage.versions import catpkgsplit

class Portage:
    SETTINGS_LOCK = threading.Lock()

    @staticmethod
    def trees():
        return portage.db['/']

    @staticmethod
    def porttree():
        return Portage.trees()['porttree'].dbapi

    @staticmethod
    def vartree():
        return Portage.trees()['vartree'].dbapi

    @staticmethod
    def sets():
        config = portage._sets.load_default_config(
            portage.settings, Portage.trees())
        return config.getSets()

    @staticmethod
    def get_depstring(cpv):
        dbapi = Portage.porttree()
        raw = dbapi.aux_get(cpv, ('DEPEND', 'PDEPEND', 'RDEPEND'))
        return ' '.join(raw)

    @staticmethod
    def find_best(atom):
        dbapi = Portage.porttree()
        with Portage.acquire_settings():
            return dbapi.xmatch('bestmatch-visible', atom)

    @staticmethod
    def find_installed(atom):
        dbapi = Portage.vartree()
        with Portage.acquire_settings():
            matches = dbapi.match(atom)
        return matches[-1] if matches else None

    @staticmethod
    def system_use_flags():
        return set(portage.settings['USE'].split())

    @classmethod
    @contextmanager
    def acquire_settings(cls):
        with cls.SETTINGS_LOCK:
            settings = Portage.porttree().settings
            settings.unlock()
            yield settings
            settings.reset()
            settings.lock()

    @staticmethod
    def available_use_flags(cpv):
        return Portage.porttree().aux_get(cpv, ['IUSE'])[0].split()

    @staticmethod
    def installed_use_flags(cpv):
        return Portage.vartree().aux_get(cpv, ['USE'])[0].split()

    @staticmethod
    def enabled_use_flags(cpv):
        with Portage.acquire_settings() as settings:
            settings.setcpv(cpv, mydb=portage.portdb)
            return set(portage.settings['PORTAGE_USE'].split())


def resolve_deps_anyof(deplist):
    """Dependency list from portage is a simple list of cpv... with a twist.

    When the dependency list want "any packages among those", it will look
    like this: ['a', '||', ['b', 'c']]

    That means "a and (b or c)". Resolve this into either ['a', 'b'] or
    ['a', 'c'].
    """
    def do_yield(elem):
        # if, in a || list, there's *another* embedded list, it means we have
        # something like || ( ( a b ) c d ). If we end up selecting the first
        # element, we must yield *both* elements.
        if isinstance(elem, str):
            yield elem
        else:
            yield from iter(elem)

    def check(elem, func):
        if isinstance(elem, str):
            return func(elem)
        else:
            return all(func(x) for x in elem)

    for elem, next_elem in zip(deplist, deplist[1:]):
        if not isinstance(elem, str):
            continue
        if elem == '||':
            # first, try to find first installed
            for x in next_elem:
                if check(x, Portage.find_installed):
                    do_yield(x)
                    break
            else:
                # if none, try with first installable
                for x in next_elem:
                    if check(x, Portage.find_best):
                        do_yield(x)
                        break
                else:
                    # fallback on first of list
                    do_yield(next_elem[0])
        else:
            yield elem


def deps_from_depstring(depstring, use_flags=None):
    # match all if use flags are empty
    matchall = not bool(use_flags)
    use_flags = use_flags or []
    deps = use_reduce(depstring, uselist=use_flags, matchall=matchall)
    # ignore blocker deps
    deps = (d for d in resolve_deps_anyof(deps) if not d.startswith('!'))
    return list(deps)


def extract_cps(atom):
    cp = dep_getkey(atom)
    slot = dep_getslot(atom) or ''
    if slot.endswith('='):
        slot = slot[:-1]
    if slot and slot not in {'*', '0'}:
        return f'{cp}:{slot}'
    else:
        return cp


class PackageStatus(Enum):
    Unchanged = ''
    New = 'N'
    Updated = 'U'
    NeedsRebuild = 'R'
    NotVisible = '~'
    # De-selected by use flags
    Deselected = 'H'


class PackageVersion:
    EXECUTOR = ThreadPoolExecutor()

    def __init__(self, cpv):
        self.cpv = cpv
        self.cps = extract_cps(f'={cpv}')
        self._affected_deep_deps = None
        self._affected_deep_deps_res = None
        self._deps = None
        self._IUSE = None

    @classmethod
    def from_atom(cls, atom):
        cpv = Portage.find_best(atom)
        if cpv:
            return cls(cpv)
        else:
            return None

    def __str__(self):
        return self.cpv

    def _get_recursive_deps(self, statuses, seen):
        if self.cps in seen:
            return set()
        result = set()
        filtered_deps = (d for d in self.deps if d.active and d.status in statuses)
        for dep in filtered_deps:
            result.add(dep.cps)
            result |= dep.best._get_recursive_deps(
                statuses, seen=(seen | {self.cps}))
        return result

    def deps_affected_by_flag(self, flag):
        depstring = Portage.get_depstring(self.cpv)
        base_deps = set(filter(isvalidatom, use_reduce(depstring, flat=True)))
        deps = set(filter(isvalidatom, use_reduce(depstring, uselist=[flag.name], flat=True)))
        return sorted(map(Dependency, deps - base_deps))

    def needs_rebuild(self):
        return any(f.is_installed != f.is_enabled for f in self.IUSE)

    @property
    def affected_deep_deps(self):
        # This computation is called concurrently. Returns None if currently
        # computing.
        if self._affected_deep_deps is None:
            if self._affected_deep_deps_res is None:
                FILTER = {PackageStatus.New, PackageStatus.Updated, PackageStatus.NeedsRebuild}
                self._affected_deep_deps_res = self.EXECUTOR.submit(
                    self._get_recursive_deps,
                    statuses=FILTER, seen=set())
                # When the executor is freshly started, we don't want to try
                # fetching results. This method is likely called in batch and
                # this can drag the app down.
                return None
            try:
                self._affected_deep_deps = self._affected_deep_deps_res.result(timeout=0.001)
                self._affected_deep_deps_res = None
            except TimeoutError:
                return None
        return self._affected_deep_deps

    @property
    def deps(self):
        if self._deps is None:
            depstring = Portage.get_depstring(self.cpv)
            enabled_flags = Portage.enabled_use_flags(self.cpv)
            all_deps = deps_from_depstring(depstring)
            active_deps = deps_from_depstring(depstring, use_flags=enabled_flags)
            deps = {Dependency(d, active=(d in active_deps)) for d in all_deps}
            self._deps = sorted(deps)
        return self._deps

    @property
    def IUSE(self):
        if self._IUSE is None:
            IUSE = Portage.available_use_flags(self.cpv)
            enabled_flags = Portage.enabled_use_flags(self.cpv)
            installed_flags = Portage.installed_use_flags(self.cpv)
            self._IUSE = [Flag.from_iuse(f, enabled_flags, installed_flags) for f in IUSE]
        return self._IUSE

    @property
    def version(self):
        _, _, v, r = catpkgsplit(self.cpv)
        return f'{v}-{r}'


class World:
    def __str__(self):
        return '@world'

    @property
    def deps(self):
        if getattr(self, '_deps', None) is None:
            sets = Portage.sets()
            atoms = sets['selected'].getAtoms()
            deps = {Dependency(atom, active=True) for atom in atoms}
            self._deps = sorted(deps)
        return self._deps

    IUSE = []


class Dependency:
    def __init__(self, atom, active=False):
        self.atom = atom
        self.active = active
        self.cps = extract_cps(atom)
        cpv = Portage.find_installed(atom)
        self.installed = PackageVersion(cpv) if cpv else None
        self.best = PackageVersion.from_atom(atom)

    def __str__(self):
        return self.cps

    __repr__ = __str__

    def __eq__(self, other):
        return self.cps == other.cps

    def __lt__(self, other):
        return self.cps < other.cps

    def __hash__(self):
        return hash(self.cps)

    @property
    def status(self):
        if not self.active:
            return PackageStatus.Deselected
        elif not self.best:
            return PackageStatus.NotVisible
        elif not self.installed:
            return PackageStatus.New
        elif self.best.version != self.installed.version:
            return PackageStatus.Updated
        elif self.installed.needs_rebuild():
            return PackageStatus.NeedsRebuild
        else:
            return PackageStatus.Unchanged


class Flag:
    def __init__(self, name, is_defaulted, is_enabled, is_installed):
        self.name = name
        self.is_defaulted = is_defaulted
        self.is_enabled = is_enabled
        self.is_installed = is_installed

    @classmethod
    def from_iuse(cls, iuse_str, enabled_flags, installed_flags):
        is_defaulted = iuse_str.startswith('+')
        if is_defaulted:
            iuse_str = iuse_str[1:]
        is_enabled = iuse_str in enabled_flags
        is_installed = iuse_str in installed_flags
        return cls(iuse_str, is_defaulted, is_enabled, is_installed)

    def __str__(self):
        return self.name

