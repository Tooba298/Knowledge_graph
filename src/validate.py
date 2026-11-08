from rdflib import Graph
from pyshacl import validate
from pathlib import Path

# Load the knowledge graph
data_graph = Graph()
data_graph.parse("out/kg.ttl", format="turtle")

# Load the ontology
ontology_graph = Graph()
ontology_graph.parse("ontology.ttl", format="turtle")

# Load SHACL shapes
shapes_graph = Graph()
shapes_graph.parse("shapes.ttl", format="turtle")

# Validate the knowledge graph
conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    ont_graph=ontology_graph,
    inference="rdfs",
    abort_on_first=False
)

# Display validation results
print("SHACL Validation Results")
print("Conforms:", conforms)
print(results_text)

# Create eval directory if it does not exist
Path("eval").mkdir(exist_ok=True)

# Save the validation report
with open("eval/shacl_report.txt", "w") as file:
    file.write("----------SHACL Validation Report----------\n")
    file.write("Conforms: " + str(conforms) + "\n\n")
    file.write(results_text)

print("\nReport saved to eval/shacl_report.txt")