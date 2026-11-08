# Error Analysis

## False Positives

1. **Wigner – educatedAt – Secondary Grammar School (E1):** The extractor selected a general description instead of the actual institution name, Fasori Evangélikus Gimnázium.

2. **Chadwick – bornIn – Cheshire (E6):** The source mentions Cheshire as his birthplace, while Wikidata provides the more specific location Bollington. This creates a location-granularity mismatch.

3. **Chadwick – receivedAward – 1851 Research Fellowship (E6):** The source confirms that Chadwick received this fellowship, but the exact triple is missing from the Wikidata reference results.

4. **Schwinger – bornIn – New York City (E6):** The source confirms New York City as his birthplace, but the exact triple is missing from the Wikidata reference results.

## False Negatives

1. **Wigner – educatedAt – Fasori Gimnázium (E1):** The extractor identified the generic school description but failed to capture the institution's proper name.

2. **Wigner – receivedAward – Foreign Member of the Royal Society (E7):** This information is not present in the provided source text, so the extractor could not identify it.

3. **Wigner – receivedAward – Josiah Willard Gibbs Lectureship (E4):** The source states that Wigner gave the lecture, not that he received it as an award. This is a relation and role distinction.

4. **Wigner – worksAt – Manhattan Project (E4):** The source describes Wigner's participation in the Manhattan Project. Participation in a project does not necessarily represent an employment relationship.

## Conclusion

The selected errors show that the extractor has difficulty identifying complete institution names and distinguishing between closely related relationships. Some differences also occur because the source text and Wikidata use different levels of detail. Improving entity recognition, relation classification, and handling of missing reference information could improve the evaluation results.