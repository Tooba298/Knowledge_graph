# Initial Predictions

## 1. Expected Number of Triples for Each Predicate

Before running the extraction pipeline, I expect the following approximate number of triples from the six source documents:

| Predicate | Expected Number of Triples |
|---|---:|
| bornIn | 8 |
| educatedAt | 15 |
| receivedAward | 15 |
| worksAt | 12 |
| doctoralAdvisor | 5 |

These are preliminary estimates. The actual numbers may differ depending on how many relationships are explicitly mentioned in the documents and how accurately the extraction rules identify them.

## 2. Predicate Expected to Have the Lowest Precision

I predict that **worksAt** will have the lowest precision.

The reason is that a person may be mentioned in connection with an organization without necessarily working there. For example, visiting an institution, studying there, collaborating with its researchers, or moving to another institution does not always establish an employment relationship. This may cause incorrect relationships to be extracted.

## 3. Expected Challenges in Extracting Information from private_document.txt

I expect the following challenges:

- **Pronoun resolution:** Identifying the correct person referred to by pronouns such as "She" and "He".
- **Alias identification:** Recognizing that "Dr. Gilani" refers to Faryal Gilani.
- **Negation handling:** Avoiding the extraction of an educatedAt relationship for Pendleton University because the document explicitly states that she never studied there.
- **Relationship identification:** Distinguishing between studying at an institution, working at an institution, and moving to an institution.
- **Name identification:** Correctly identifying people, universities, organizations, and awards mentioned in the document.

I expect these challenges to affect the accuracy of the extraction pipeline, particularly when relationships depend on context from earlier sentences.