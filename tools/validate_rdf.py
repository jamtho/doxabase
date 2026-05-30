from __future__ import annotations

from pathlib import Path

from pyshacl import validate
from rdflib import Dataset, Graph, URIRef

ROOT = Path(__file__).resolve().parents[1]
RC_NAMESPACE = "https://richcanopy.org/ns/rc#"

CORE_ONTOLOGY = ROOT / "ontology" / "rc_core.ttl"
BASE_SHAPES = ROOT / "ontology" / "rc_shapes.ttl"
EXAMPLES = [
    ROOT / "examples" / "manifest-prototype-rc" / "ais.trig",
    ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig",
]


def parse_core() -> Graph:
    graph = Graph()
    graph.parse(CORE_ONTOLOGY, format="turtle")
    return graph


def parse_shapes() -> Graph:
    graph = Graph()
    graph.parse(BASE_SHAPES, format="turtle")
    return graph


def parse_example(path: Path) -> Dataset:
    dataset = Dataset()
    dataset.parse(path, format="trig")
    return dataset


def rc_terms_defined_in_core(core: Graph) -> set[str]:
    return {
        str(subject)
        for subject in core.subjects()
        if isinstance(subject, URIRef) and str(subject).startswith(RC_NAMESPACE)
    }


def rc_terms_used_in_dataset(dataset: Dataset) -> set[str]:
    used: set[str] = set()
    for graph in dataset.graphs():
        for triple in graph:
            for term in triple:
                if isinstance(term, URIRef) and str(term).startswith(RC_NAMESPACE):
                    used.add(str(term))
    return used


def combined_data_graph(dataset: Dataset, core: Graph) -> Graph:
    graph = Graph()
    for triple in core:
        graph.add(triple)
    for context in dataset.graphs():
        for triple in context:
            graph.add(triple)
    return graph


def validate_example(path: Path) -> tuple[bool, str]:
    core = parse_core()
    shapes = parse_shapes()
    dataset = parse_example(path)
    data = combined_data_graph(dataset, core)
    conforms, _, report_text = validate(
        data_graph=data,
        shacl_graph=shapes,
        inference="rdfs",
        advanced=False,
    )
    return bool(conforms), str(report_text)


def main() -> int:
    core = parse_core()
    shapes = parse_shapes()
    print(f"{CORE_ONTOLOGY.relative_to(ROOT)}: {len(core)} triples")
    print(f"{BASE_SHAPES.relative_to(ROOT)}: {len(shapes)} triples")

    defined = rc_terms_defined_in_core(core)
    failed = False

    for path in EXAMPLES:
        dataset = parse_example(path)
        graph_counts = sorted(
            (str(graph.identifier), len(graph))
            for graph in dataset.graphs()
            if len(graph)
        )
        total = sum(count for _, count in graph_counts)
        print(f"{path.relative_to(ROOT)}: {total} quads")
        for graph_name, count in graph_counts:
            print(f"  {graph_name}: {count}")

        missing = sorted(rc_terms_used_in_dataset(dataset) - defined)
        if missing:
            failed = True
            print("  missing rc definitions:")
            for term in missing:
                print(f"    {term}")

        conforms, report_text = validate_example(path)
        if conforms:
            print("  SHACL: conforms")
        else:
            failed = True
            print("  SHACL: does not conform")
            print(report_text)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
