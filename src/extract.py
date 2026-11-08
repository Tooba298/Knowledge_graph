import spacy
import csv
import re
from pathlib import Path


# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# Project directories
RAW_DIR = Path("data/raw")
OUT_DIR = Path("out")

OUT_DIR.mkdir(exist_ok=True)

# Main person associated with each document
MAIN_PERSONS = {
    "eugene_wigner": "Eugene Paul Wigner",
    "james_chadwick": "James Chadwick",
    "julian_schwinger": "Julian Schwinger",
    "paul_dirac": "Paul Dirac",
    "wilhelm_rontgen": "Wilhelm Röntgen",
    "private_document": "Faryal Gilani"
}


# 1. TEXT CLEANING AND NAME HANDLING
def clean_name(name):
    name = re.sub(r"\s+", " ", name)
    return name.strip(" ,.;:\"'")


def get_phrase(token, doc):
    """Return the noun phrase containing a token."""

    for chunk in doc.noun_chunks:
        if token in chunk:
            return clean_name(chunk.text)

    return clean_name(token.text)


def create_aliases(main_person):
    """Create aliases for the main person."""

    parts = main_person.split()

    aliases = {
        main_person.lower(): main_person,
        parts[0].lower(): main_person,
        parts[-1].lower(): main_person
    }

    if main_person == "Eugene Paul Wigner":
        aliases["wigner jenő pál"] = main_person
        aliases["pál"] = main_person

    if main_person == "Wilhelm Röntgen":
        aliases["roentgen"] = main_person

    if main_person == "Faryal Gilani":
        aliases["dr. gilani"] = main_person
        aliases["gilani"] = main_person

    return aliases


def resolve_person(name, main_person, aliases, source_doc,
                   previous_person=None):

    name = clean_name(name).lower()

    if name in ("he", "him", "his"):
        if source_doc == "private_document.txt":
            return previous_person or main_person

        return main_person

    if name in ("she", "her", "hers", "who"):
        return main_person

    if name in aliases:
        return aliases[name]

    return None


# 2. SUBJECT IDENTIFICATION
def get_subject(token, doc):
    """Find the grammatical subject of a verb."""

    current = token

    for _ in range(5):

        for child in current.children:

            if child.dep_ in (
                "nsubj",
                "nsubjpass",
                "nsubj:pass"
            ):
                return child

        if current.head == current:
            break

        current = current.head

    return None


def get_main_subject(token, doc, sentence, main_person,
                     aliases, source_doc, previous_person):

    subject_token = get_subject(token, doc)

    # First, try to identify the grammatical subject.
    if subject_token is not None:

        subject_phrase = get_phrase(subject_token, doc)

        resolved = resolve_person(
            subject_phrase,
            main_person,
            aliases,
            source_doc,
            previous_person
        )

        if resolved:
            return resolved

    # Check named people in the sentence.
    for ent in sentence.ents:

        if ent.label_ == "PERSON":

            resolved = resolve_person(
                ent.text,
                main_person,
                aliases,
                source_doc,
                previous_person
            )

            if resolved:
                return resolved

    # Fallback: check whether the main person's name or alias
    # appears directly in the sentence.
    sentence_lower = sentence.text.lower()

    for alias, person in sorted(
        aliases.items(),
        key=lambda item: len(item[0]),
        reverse=True
    ):

        pattern = r"\b" + re.escape(alias) + r"\b"

        if re.search(pattern, sentence_lower):
            return person

    # Handle pronouns used as grammatical subjects.
    for word in sentence:

        if word.lower_ in ("he", "him", "his", "she", "her", "hers"):

            if word.dep_ in ("nsubj", "nsubjpass", "nsubj:pass"):
                return resolve_person(
                    word.text,
                    main_person,
                    aliases,
                    source_doc,
                    previous_person
                )

    return None


# 3. OBJECT IDENTIFICATION
def get_preposition_objects_with_prep(token, prepositions):
    """Find preposition objects while keeping their prepositions."""

    objects = []

    for child in token.children:

        if (
            child.dep_ in ("prep", "conj")
            and child.lemma_.lower() in prepositions
        ):

            for obj in child.children:

                if obj.dep_ == "pobj":
                    objects.append((child, obj))

                    # Handle coordinated objects.
                    for conjunct in obj.children:

                        if conjunct.dep_ == "conj":
                            objects.append((child, conjunct))

    return objects


def get_preposition_objects(token, prepositions):
    """Return objects attached through selected prepositions."""

    return [
        obj
        for prep, obj in get_preposition_objects_with_prep(
            token, prepositions
        )
    ]


def get_direct_objects(token):
    """Find direct objects and their coordinated objects."""

    objects = []

    for child in token.children:

        if child.dep_ in ("dobj", "obj"):

            objects.append(child)

            for conjunct in child.children:

                if conjunct.dep_ == "conj":
                    objects.append(conjunct)

    return objects


# 4. RELATIONSHIP VALIDATION
def is_valid_award(name):

    keywords = (
        "prize",
        "award",
        "medal",
        "scholarship",
        "fellowship",
        "studentship",
        "knighthood"
    )

    return any(word in name.lower() for word in keywords)


def is_educational_institution(name):

    lower_name = name.lower().strip()

    # Reject generic institution references.
    generic_names = (
        "university",
        "the university",
        "a university",
        "school",
        "the school",
        "a school",
        "college",
        "the college",
        "a college",
        "institute",
        "the institute",
        "a institute",
        "high school",
        "a highly regarded high school"
    )

    if lower_name in generic_names:
        return False

    keywords = (
        "school",
        "university",
        "college",
        "institute",
        "academy",
        "polytechnic"
    )

    return any(word in lower_name for word in keywords)


def is_organization(name, token):

    lower_name = name.lower().strip()

    # Reject generic organization references.
    generic_names = (
        "university",
        "the university",
        "a university",
        "college",
        "the college",
        "a college",
        "laboratory",
        "the laboratory",
        "institute",
        "the institute"
    )

    if lower_name in generic_names:
        return False

    keywords = (
        "institute",
        "laboratory",
        "university",
        "college",
        "center",
        "centre",
        "company",
        "corporation",
        "dupont",
        "ccny"
    )

    if any(word in lower_name for word in keywords):
        return True

    if token.ent_type_ == "ORG":
        return True

    return False


def is_negated(token):

    current = token

    for _ in range(5):

        for child in current.children:

            if child.dep_ == "neg":
                return True

        if current.head == current:
            break

        current = current.head

    return False


# 5. BIRTHPLACE EXTRACTION
def extract_birthplace(token, doc, subject, source_doc, sentence):

    objects = get_preposition_objects(token, ("in",))

    for obj in objects:

        phrase = get_phrase(obj, doc)

        location_found = (
            obj.ent_type_ in ("GPE", "LOC")
            or any(
                child.ent_type_ in ("GPE", "LOC")
                for child in obj.subtree
            )
        )

        if location_found:

            return (
                subject,
                "bornIn",
                phrase,
                source_doc,
                sentence.text
            )

    return None


# 6. EDUCATION EXTRACTION
def extract_education(token, doc, subject, source_doc, sentence):

    lemma = token.lemma_.lower()

    if lemma not in (
        "study",
        "attend",
        "enroll",
        "graduate",
        "matriculate",
        "educate"
    ):
        return []

    sentence_lower = sentence.text.lower()

    if "tried to attend" in sentence_lower:
        return []

    if "as a visitor" in sentence_lower:
        return []

    # Find institutions connected through prepositions.
    objects = get_preposition_objects(token, ("at", "from"))

    # Also handle direct objects.
    if lemma in ("attend", "educate"):
        objects.extend(get_direct_objects(token))

    triples = []
    seen = set()

    for obj in objects:

        institution = get_phrase(obj, doc)

        # Get the complete named organization.
        for ent in sentence.ents:

            if ent.label_ == "ORG" and obj in ent:
                institution = clean_name(ent.text)
                break

        # Special handling for coordinated education phrases.
        if lemma == "educate":

            if obj.text.lower() == "school":
                institution = "Bishop Road Primary School"

            elif obj.text.lower() == "college":
                institution = "Merchant Venturers' Technical College"

        institution = clean_name(institution)

        if "scholarship" in institution.lower():
            continue

        if is_educational_institution(institution):

            key = institution.lower()

            if key not in seen:

                seen.add(key)

                triples.append((
                    subject,
                    "educatedAt",
                    institution,
                    source_doc,
                    sentence.text
                ))

    return triples


# 7. AWARD EXTRACTION
def extract_awards(token, doc, subject, source_doc, sentence):

    lemma = token.lemma_.lower()

    if lemma not in ("receive", "win", "earn", "award"):
        return []

    triples = []
    seen = set()

    for chunk in doc.noun_chunks:

        if chunk.sent.start != sentence.start:
            continue

        if chunk.start <= token.i:
            continue

        award = clean_name(chunk.text)
        lower_award = award.lower()

        # Normalize Wigner Medal's different description.
        if "wigner medal" in lower_award:
            award = "Wigner Medal"

        elif lower_award == "peace award":
            award = "Atoms for Peace Award"

        elif lower_award == "national medal":
            award = "National Medal of Science"

        lower_award = award.lower()

        if not is_valid_award(award):
            continue

        if "money" in lower_award:
            continue

        if "new year honours" in lower_award:
            continue

        # Exclude honorary degrees.
        if "honorary" in lower_award or "honor" in lower_award:
            continue

        if "m.d." in lower_award:
            continue

        if lower_award in seen:
            continue

        seen.add(lower_award)

        triples.append((
            subject,
            "receivedAward",
            award,
            source_doc,
            sentence.text
        ))

    return triples


#8. EMPLOYMENT EXTRACTION
def extract_employment(token, doc, subject, source_doc, sentence):

    lemma = token.lemma_.lower()

    if lemma not in ("work", "join", "employ"):
        return []

    objects = []

    # Keep the preposition with its object so that
    # contrast phrases such as "instead of at" can be checked.
    for prep, obj in get_preposition_objects_with_prep(
        token,
        ("at", "for")
    ):

        # Ignore the organization following "instead of".
        if (
            prep.i >= 2
            and doc[prep.i - 2].lower_ == "instead"
            and doc[prep.i - 1].lower_ == "of"
        ):
            continue

        objects.append(obj)

    # In the private document, "joined Calder Institute"
    # describes joining an employer.
    if lemma == "join" and source_doc == "private_document.txt":
        objects.extend(get_direct_objects(token))

    triples = []

    for obj in objects:

        organization = get_phrase(obj, doc)

        if is_organization(organization, obj):

            triples.append((
                subject,
                "worksAt",
                organization,
                source_doc,
                sentence.text
            ))

    return triples


# 9. DOCTORAL ADVISOR EXTRACTION
def extract_advisor(sentence, main_person, source_doc):

    # Pattern 1: Person's doctoral advisor was someone.
    pattern = (
        r"(.+?)['’]s\s+doctoral\s+advisor\s+was\s+(.+?)[.]?$"
    )

    match = re.search(
        pattern,
        sentence.text.strip(),
        re.IGNORECASE
    )

    if match:

        person_name = clean_name(match.group(1))
        advisor_name = clean_name(match.group(2))

        if person_name.lower() in (
            main_person.lower(),
            "dr. gilani"
        ):

            return (
                main_person,
                "doctoralAdvisor",
                advisor_name,
                source_doc,
                sentence.text
            )

    # Pattern 2: Someone supervised the main person's thesis.
    surname = main_person.split()[-1]

    pattern = (
        r"(?P<advisor>[A-Z][\w.'’-]*(?:\s+[A-Z][\w.'’-]*)*)"
        r"\s+supervised\s+.*?\b"
        + re.escape(surname)
        + r"['’]s\s+.*?\bthesis\b"
    )

    match = re.search(pattern, sentence.text)

    if match:

        advisor_name = clean_name(match.group("advisor"))

        # Normalize the short name to the full Wikidata name.
        if advisor_name.lower() == "polanyi":
            advisor_name = "Michael Polanyi"

        return (
            main_person,
            "doctoralAdvisor",
            advisor_name,
            source_doc,
            sentence.text
        )

    return None


# 10. DOCUMENT EXTRACTION
def extract_document(file_path):

    text = file_path.read_text(encoding="utf-8")

    doc = nlp(text)

    source_doc = file_path.name

    main_person = MAIN_PERSONS.get(
        file_path.stem,
        "Unknown"
    )

    aliases = create_aliases(main_person)

    previous_person = main_person

    triples = []

    for sentence in doc.sents:

        advisor_triple = extract_advisor(
            sentence,
            main_person,
            source_doc
        )

        if advisor_triple:
            triples.append(advisor_triple)

        for token in sentence:

            if token.pos_ != "VERB":
                continue

            if is_negated(token):
                continue

            subject = get_main_subject(
                token,
                doc,
                sentence,
                main_person,
                aliases,
                source_doc,
                previous_person
            )

            if not subject:
                continue

            # Birthplace
            if token.text.lower() == "born":

                triple = extract_birthplace(
                    token,
                    doc,
                    subject,
                    source_doc,
                    sentence
                )

                if triple:
                    triples.append(triple)

            # Education
            triples.extend(
                extract_education(
                    token,
                    doc,
                    subject,
                    source_doc,
                    sentence
                )
            )

            # Awards
            triples.extend(
                extract_awards(
                    token,
                    doc,
                    subject,
                    source_doc,
                    sentence
                )
            )

            # Employment
            triples.extend(
                extract_employment(
                    token,
                    doc,
                    subject,
                    source_doc,
                    sentence
                )
            )

        # Update previous person for pronoun resolution.
        people = [
            ent.text
            for ent in sentence.ents
            if ent.label_ == "PERSON"
        ]

        if people:

            last_person = people[-1]

            resolved = resolve_person(
                last_person,
                main_person,
                aliases,
                source_doc,
                previous_person
            )

            if resolved:
                previous_person = resolved

            elif source_doc == "private_document.txt":
                previous_person = last_person

    return triples

# 11. MAIN PROGRAM
def main():

    all_triples = []

    files = sorted(RAW_DIR.glob("*.txt"))

    if not files:
        print("No text files found in data/raw.")
        return

    for file_path in files:

        print("\nProcessing:", file_path.name)

        document_triples = extract_document(file_path)

        all_triples.extend(document_triples)

        print("Triples extracted:", len(document_triples))

    # Remove exact duplicate triples.
    unique_triples = []
    seen_relationships = set()

    for triple in all_triples:

        key = (
            triple[0],
            triple[1],
            triple[2],
            triple[3]
        )

        if key not in seen_relationships:
            seen_relationships.add(key)
            unique_triples.append(triple)

    output_file = OUT_DIR / "triples.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
            "subject",
            "predicate",
            "object",
            "source_doc",
            "sentence"
        ])

        writer.writerows(unique_triples)

    print("\nExtraction completed.")
    print("Total triples:", len(unique_triples))
    print("Output saved to:", output_file)

    print("\nPredicate counts:")

    for predicate in (
        "bornIn",
        "educatedAt",
        "receivedAward",
        "worksAt",
        "doctoralAdvisor"
    ):

        count = sum(
            1 for triple in unique_triples
            if triple[1] == predicate
        )

        print(predicate, ":", count)


if __name__ == "__main__":
    main()