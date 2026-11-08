import csv
import os
import re
import unicodedata
from urllib.parse import unquote

# File paths
triples_file = "out/triples.csv"
wikidata_file = "eval/wikidata_values.csv"

# Create eval folder
os.makedirs("eval", exist_ok=True)


# Normalize names and values
def normalize(value):
    value = str(value).strip()

    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1]

    if value.startswith("http://") or value.startswith("https://"):
        value = unquote(value.rstrip("/").split("/")[-1])

    value = value.replace("_", " ")
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value).strip().casefold()

    # Ignore articles at the beginning
    value = re.sub(r"^(the|a|an)\s+", "", value)

    return value


# Five assigned Wikipedia people
people = {
    normalize("Eugene Paul Wigner"),
    normalize("James Chadwick"),
    normalize("Julian Schwinger"),
    normalize("Paul Dirac"),
    normalize("Wilhelm Röntgen")
}


# Read extracted triples
with open(triples_file, "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    triples = list(reader)


# Read Wikidata results
with open(wikidata_file, "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    wikidata = list(reader)


# Prepare extracted triples
extracted = set()

for row in triples:
    subject = normalize(row["subject"])

    # Ignore people outside the assigned five
    if subject not in people:
        continue

    predicate = row["predicate"].split("/")[-1].split("#")[-1]
    predicate = normalize(predicate)

    obj = normalize(row["object"])

    extracted.add((subject, predicate, obj))


# Prepare Wikidata triples
reference = set()

for row in wikidata:
    subject = normalize(row["personLabel"])

    # Ignore people outside the assigned five
    if subject not in people:
        continue

    predicate = normalize(row["predicate"])

    value = row.get("valueLabel", "").strip()

    if not value:
        value = row.get("value", "")

    obj = normalize(value)

    if subject and predicate and obj:
        reference.add((subject, predicate, obj))


# Predicates to evaluate
predicates = [
    "bornin",
    "educatedat",
    "receivedaward",
    "worksat",
    "doctoraladvisor"
]


# Calculate evaluation metrics
metrics = []

print("\n---------- EVALUATION RESULTS ----------\n")

for predicate in predicates:

    extracted_p = {
        triple for triple in extracted
        if triple[1] == predicate
    }

    reference_p = {
        triple for triple in reference
        if triple[1] == predicate
    }

    tp = len(extracted_p & reference_p)
    fp = len(extracted_p - reference_p)
    fn = len(reference_p - extracted_p)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    metrics.append({
        "predicate": predicate,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4)
    })

    print(f"Predicate: {predicate}")
    print(f"TP: {tp}")
    print(f"FP: {fp}")
    print(f"FN: {fn}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print("-----------------------------------")


# Save evaluation metrics
with open("eval/metrics.csv", "w", newline="", encoding="utf-8") as file:

    fields = [
        "predicate", "TP", "FP", "FN",
        "precision", "recall"
    ]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(metrics)


# Generate false positives
false_positives = sorted(
    extracted - reference,
    key=lambda x: x
)


with open("eval/false_positives.csv", "w", newline="", encoding="utf-8") as file:

    fields = ["subject", "predicate", "object"]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for subject, predicate, obj in false_positives:
        writer.writerow({
            "subject": subject,
            "predicate": predicate,
            "object": obj
        })


# Generate false negatives
false_negatives = sorted(
    reference - extracted,
    key=lambda x: x
)


with open("eval/false_negatives.csv", "w", newline="", encoding="utf-8") as file:

    fields = ["subject", "predicate", "object"]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for subject, predicate, obj in false_negatives:
        writer.writerow({
            "subject": subject,
            "predicate": predicate,
            "object": obj
        })


# Display summary
print("\n----------- SUMMARY -----------\n")

print("Total extracted triples:", len(extracted))
print("Total Wikidata triples:", len(reference))
print("Total False Positives:", len(false_positives))
print("Total False Negatives:", len(false_negatives))

print("\nFiles saved:")
print("eval/metrics.csv")
print("eval/false_positives.csv")
print("eval/false_negatives.csv")