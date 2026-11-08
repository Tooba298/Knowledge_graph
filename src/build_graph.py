import pandas as pd
import re
from urllib.parse import quote
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, RDF

# Define the knowledge graph namespace
KG = Namespace("http://example.org/kg/24p-0030/")

# Create an RDF graph
graph = Graph()

# Load ontology
graph.parse("ontology.ttl", format="turtle")

# Read extracted triples
df = pd.read_csv("out/triples.csv")

# Check required CSV columns
required_columns = ["subject", "predicate", "object"]

for column in required_columns:
    if column not in df.columns:
        raise ValueError(f"Missing column in triples.csv: {column}")


# Convert entity names into valid URI identifiers
def create_uri(name):
    name = str(name).strip()
    name = re.sub(r"\s+", "_", name)
    return URIRef(str(KG) + quote(name, safe="_-"))


# Map predicates to their object classes
object_classes = {
    "bornIn": KG.Place,
    "educatedAt": KG.Organization,
    "receivedAward": KG.Award,
    "worksAt": KG.Organization,
    "doctoralAdvisor": KG.Person
}


# Add extracted relationships
for _, row in df.iterrows():

    subject = create_uri(row["subject"])
    predicate_name = row["predicate"]
    predicate = KG[predicate_name]
    obj = create_uri(row["object"])

    # Check whether the predicate is supported
    if predicate_name not in object_classes:
        print("Unknown predicate skipped:", predicate_name)
        continue

    # Every subject is a Person
    graph.add((subject, RDF.type, KG.Person))

    # Assign the correct class to the object
    graph.add((obj, RDF.type, object_classes[predicate_name]))

    # Add the relationship
    graph.add((subject, predicate, obj))


# Save the RDF knowledge graph
Path("out").mkdir(exist_ok=True)

graph.serialize(destination="out/kg.ttl", format="turtle")

print("RDF knowledge graph created successfully.")
print("Total RDF statements:", len(graph))
print("Saved to: out/kg.ttl")