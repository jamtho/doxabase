from pathlib import Path

from rdflib import Dataset, Graph

from tools.validate_rdf import (
    BASE_SHAPES,
    CORE_ONTOLOGY,
    EXAMPLES,
    combined_data_graph,
    parse_core,
    parse_example,
    parse_shapes,
    rc_terms_defined_in_core,
    rc_terms_used_in_dataset,
    validate_example,
)


def test_core_ontology_parses() -> None:
    graph = Graph()
    graph.parse(CORE_ONTOLOGY, format="turtle")
    assert len(graph) > 0


def test_base_shapes_parse() -> None:
    graph = Graph()
    graph.parse(BASE_SHAPES, format="turtle")
    assert len(graph) > 0


def test_examples_parse_as_trig() -> None:
    for path in EXAMPLES:
        dataset = Dataset()
        dataset.parse(path, format="trig")
        assert sum(len(graph) for graph in dataset.graphs()) > 0


def test_examples_only_use_defined_rc_terms() -> None:
    defined = rc_terms_defined_in_core(parse_core())
    for path in EXAMPLES:
        dataset = parse_example(path)
        missing = rc_terms_used_in_dataset(dataset) - defined
        assert not missing, f"{Path(path).name} uses undefined rc terms: {sorted(missing)}"


def test_combined_graph_includes_core_and_example() -> None:
    core = parse_core()
    dataset = parse_example(EXAMPLES[0])
    combined = combined_data_graph(dataset, core)
    assert len(combined) > len(core)


def test_examples_conform_to_base_shapes() -> None:
    parse_shapes()
    for path in EXAMPLES:
        conforms, report_text = validate_example(path)
        assert conforms, report_text
