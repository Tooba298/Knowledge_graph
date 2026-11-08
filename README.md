# From Text to Knowledge Graph

## Course information

- **Course:** AI3001 – Knowledge Representation and Reasoning
- **Semester:** Fall 2026
- **Student:** Tooba Ali Asghar
- **Roll number:** 24P-0030

## Project overview

This project extracts five kinds of relationships from six text files, represents the results as RDF, validates the graph with SHACL, and provides SPARQL queries and an evaluation against prepared Wikidata results.

The source set contains five biographical articles (Eugene Paul Wigner, James Chadwick, Julian Schwinger, Paul Dirac, and Wilhelm Röntgen) and a private test document about Faryal Gilani. The private document exercises aliases, pronouns, and negation.

## Requirements

- Python 3.10 or newer
- spaCy and its English model `en_core_web_sm`
- RDFLib, pySHACL, and requests
- Apache Jena Fuseki and Java 17 or newer, if you want to load and query the graph through Fuseki
- Git, for the required version-control history

`requests` is included to meet the assignment's dependency requirement. The current pipeline reads the supplied Wikidata reference CSV and does not make HTTP requests.

## Setup

Run commands from the repository root.

1. Check that Python is 3.10 or newer:

   ```bash
   python3 --version
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell, activate it with:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. Install the Python packages and spaCy model:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install spacy rdflib pyshacl requests
   python -m spacy download en_core_web_sm
   ```

4. If using Fuseki, check Java and install/download Apache Jena Fuseki. The Java version must be 17 or newer:

   ```bash
   java -version
   ```

## Run the Python pipeline

Run each command from the project root and in this order:

```bash
python src/extract.py
python src/build_graph.py
python src/validate.py
python src/evaluate.py
```

Each stage reads files relative to the project root, so running scripts from inside `src/` may cause file-not-found errors.

1. **Extract text relationships** — `src/extract.py` reads every `data/raw/*.txt` file and writes `out/triples.csv`. Each row includes the subject, predicate, object, source filename, and source sentence.
2. **Build the RDF graph** — `src/build_graph.py` reads the CSV and `ontology.ttl`, then writes `out/kg.ttl` in Turtle format. It expects `subject`, `predicate`, and `object` columns. Predicates outside the five supported relationship names are reported and skipped.
3. **Validate the graph** — `src/validate.py` reads `out/kg.ttl`, `ontology.ttl`, and `shapes.ttl`, runs pySHACL with RDFS inference, prints whether the graph conforms, and writes the report to `eval/shacl_report.txt`.
4. **Evaluate extraction** — `src/evaluate.py` compares extracted triples with `eval/wikidata_values.csv`. It writes predicate-level precision/recall and false-positive/false-negative lists to `eval/metrics.csv`, `eval/false_positives.csv`, and `eval/false_negatives.csv`. The reference CSV must be present and have the expected `personLabel`, `predicate`, and `value`/`valueLabel` columns.

The scripts create their output directories when needed. Running a stage again overwrites its corresponding generated output files.

## Extraction rules

The rules below describe the implemented behavior in `src/extract.py`. They are heuristic rules built on spaCy's English dependency parser and named-entity recognition; they do not cover every way a relationship can be expressed.

### Shared subject, alias, and negation rules

- Each input filename is mapped to a canonical main person. For example, `eugene_wigner.txt` maps to Eugene Paul Wigner and `private_document.txt` maps to Faryal Gilani.
- The main person's full name, first name, and surname are aliases. There are additional explicit aliases for Wigner, Röntgen, and Gilani, including “Dr. Gilani”.
- For each candidate verb, the extractor searches the verb and up to five dependency ancestors for a grammatical subject. It resolves recognized aliases and pronouns to the document's main person. If that fails, it tries recognized PERSON entities and then a matching main-person alias in the sentence.
- In the private document, masculine pronouns can resolve to the most recently tracked person; otherwise they resolve to the main person. Feminine pronouns and “who” resolve to the main person. The previous-person value is updated from PERSON entities at the end of each sentence. This is intentionally a small, document-specific heuristic, not general coreference resolution.
- A candidate verb is skipped if a `neg` dependency is found on it or within up to five ancestor steps. This prevents straightforward negated clauses from generating triples (for example, “never studied”). It is not a full semantic treatment of negation.
- Noun phrases are used as entity values when spaCy can identify them; whitespace and surrounding punctuation are cleaned. Coordinated direct objects and selected prepositional objects can produce multiple candidates.

### Relationship-by-relationship rules

| Predicate | When a candidate is extracted | Object checks and exclusions |
|---|---|---|
| `bornIn` | The token text is exactly `born`; the person has an object attached through the preposition `in`. | The object or a token in its subtree must be recognized by spaCy as a `GPE` or `LOC`. The noun phrase becomes the place. |
| `educatedAt` | The verb lemma is `study`, `attend`, `enroll`, `graduate`, `matriculate`, or `educate`. Institution candidates are attached through `at` or `from`; direct objects are also considered for `attend` and `educate`. | A named ORG span is preferred when it contains the candidate. Otherwise the phrase must contain a school/university/college/institute/academy/polytechnic keyword and not be a generic institution label. “Tried to attend” and “as a visitor” sentences are skipped, as are scholarship phrases. Two coordinated “educate” cases have explicit school-name mappings in the code. |
| `receivedAward` | The verb lemma is `receive`, `win`, `earn`, or `award`. | Later noun chunks in the same sentence are considered. A candidate must contain an award-related keyword such as prize, award, medal, scholarship, fellowship, studentship, or knighthood. The rules exclude money, “New Year Honours”, honorary qualifications, and M.D. phrases. Several descriptions are normalized to award names (for example, “peace award” to “Atoms for Peace Award”). |
| `worksAt` | The verb lemma is `work`, `join`, or `employ`. Objects of `at` and `for` are considered. | Generic organization labels are rejected. A phrase is treated as an organization if it contains one of the configured organization keywords or spaCy labels the token `ORG`. For `join`, direct objects are additionally considered only in `private_document.txt`. A preposition phrase following “instead of” is ignored. |
| `doctoralAdvisor` | A sentence matches either “Person's doctoral advisor was Advisor” or “Advisor supervised [..] Surname's .. thesis”. | The first pattern must name the document's main person or “Dr. Gilani”. The second pattern uses the main person's surname and requires a capitalized advisor name. “Polanyi” is normalized to “Michael Polanyi”. |

After processing all documents, exact duplicate relationships from the same source file are removed. A relationship repeated in different source files is retained. The source sentence is preserved as evidence in the CSV.

## Ontology and SHACL rules

### Ontology (`ontology.ttl`)

The ontology uses the namespace `http://example.org/kg/24p-0030/` and defines four classes:

- `Person`
- `Place`
- `Organization`
- `Award`

It declares the following object properties, their domains, and their ranges:

| Property | Domain | Range | Additional ontology rule |
|---|---|---|---|
| `bornIn` | `Person` | `Place` | Functional property: at most one value is intended for a person. |
| `educatedAt` | `Person` | `Organization` | — |
| `receivedAward` | `Person` | `Award` | — |
| `worksAt` | `Person` | `Organization` | — |
| `doctoralAdvisor` | `Person` | `Person` | — |

`Person` is declared disjoint with each of `Place`, `Organization`, and `Award`. The ontology describes the intended meaning and types of graph terms; the validation rules below check the actual graph structure.

### SHACL shapes (`shapes.ttl`)

`PersonShape` targets every node typed as `kg:Person` and applies these property constraints:

- `bornIn` values must be typed as `kg:Place`; there can be no more than one such value.
- `educatedAt` values must be typed as `kg:Organization`.
- `receivedAward` values must be typed as `kg:Award`.
- `worksAt` values must be typed as `kg:Organization`.
- `doctoralAdvisor` values must be typed as `kg:Person`.

The validator passes the ontology to pySHACL and enables RDFS inference. A successful report says `Conforms: True`; violations are written in `eval/shacl_report.txt` with the shapes' validation messages.

## Apache Jena Fuseki and SPARQL

The Python scripts create a local Turtle file; they do **not** start Fuseki or upload the graph automatically.

1. Start Fuseki with Java 17 or newer. From the extracted Fuseki distribution, a typical Linux/macOS command is:

   ```bash
   ./fuseki-server
   ```

   If `fuseki-server` is on your `PATH`, you can run `fuseki-server` instead.
2. Open [http://localhost:3030](http://localhost:3030).
3. Create a **persistent TDB2** dataset. Use the dataset name specified in your assignment sheet. This project’s namespace and existing Fuseki storage use `kg-24p-0030`; use that name if it matches your sheet.
4. Open the dataset and upload `out/kg.ttl` as Turtle using the Fuseki dataset UI.
5. Run SPARQL queries in the dataset’s query interface. The standard query endpoint for this dataset name is `http://localhost:3030/kg-24p-0030/sparql`; adjust the path if you chose a different name.

The query files in `queries/` are:

| File | Purpose |
|---|---|
| `q1_birthplace.rq` | Lists each person and their birthplace, retaining people for whom a birthplace is absent. |
| `q2_predicate_counts.rq` | Counts graph triples by predicate in the project namespace. |
| `q3_shared_birthplaces.rq` | Finds pairs of different people who share a birthplace; string ordering avoids returning each pair twice. |
| `q4_multiple_birthplaces.rq` | Finds people with at least two distinct birthplace values. |
| `q5_missing_education.rq` | Lists people with no `educatedAt` relationship. |
| `q6_doctoral_ancestors.rq` | Follows one or more `doctoralAdvisor` links to return advisor-chain ancestors. |

Run a query by opening its `.rq` file and pasting its contents into Fuseki's query editor. Save/export results to `results/` if you want to keep a local CSV result.

## Project layout

```text
data/raw/       Input biographies and private test document
src/            Extraction, RDF construction, validation, and evaluation scripts
out/            Extracted CSV triples and generated Turtle knowledge graph
ontology.ttl    OWL/RDFS ontology and property declarations
shapes.ttl      SHACL validation shapes
queries/        SPARQL query files
results/        Saved query result CSVs
eval/           Wikidata reference, validation report, metrics, and error analysis
screenshots/    Project screenshots
predictions.md  Initial predictions before evaluation
reflection.md   Results and project reflection
```
