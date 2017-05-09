from aiosparql.syntax import IRI, Namespace, PrefixedName, RDF

__all__ = """
    rdf swarmui mu ext dct doap w3vocab foaf auth session
    """.split()


class SwarmUI(Namespace):
    __iri__ = IRI("http://swarmui.semte.ch/vocabularies/core/")

    PidsStats = PrefixedName
    SectorsRecursive = PrefixedName
    CpuUsage = PrefixedName
    ThrottlingData = PrefixedName
    CpuStats = PrefixedName
    CpuUsage = PrefixedName
    ThrottlingData = PrefixedName
    PrecpuStats = PrefixedName
    Stats = PrefixedName
    MemoryStats = PrefixedName
    Network = PrefixedName
    Stats = PrefixedName


class Mu(Namespace):
    __iri__ = IRI("http://mu.semte.ch/vocabularies/core/")


class Ext(Namespace):
    __iri__ = IRI("http://mu.semte.ch/vocabularies/ext/")


class Dct(Namespace):
    __iri__ = IRI("http://purl.org/dc/terms/")


class Doap(Namespace):
    __iri__ = IRI("http://usefulinc.com/ns/doap#")


class Foaf(Namespace):
    __iri__ = IRI("http://xmlns.com/foaf/0.1/")


class Auth(Namespace):
    __iri__ = IRI("http://mu.semte.ch/vocabularies/authorization/")


class Session(Namespace):
    __iri__ = IRI("http://mu.semte.ch/vocabularies/session/")


class W3Vocab(Namespace):
    __iri__ = IRI("https://www.w3.org/1999/xhtml/vocab#")
