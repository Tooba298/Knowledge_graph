# Reflection

The initial predictions estimated 8 `bornIn`, 15 `educatedAt`, 15 `receivedAward`, 12 `worksAt`, and 5 `doctoralAdvisor` triples. The final knowledge graph contained 53 extracted triples. The actual counts were 5 `bornIn`, 12 `educatedAt`, 29 `receivedAward`, 5 `worksAt`, and 2 `doctoralAdvisor` triples.

The prediction that `worksAt` would have the lowest precision was correct. Its precision was 0.00, meaning none of its extracted triples matched the reference data. The `doctoralAdvisor` predicate achieved the highest precision of 1.00, but its recall was only 0.20. This means that the extracted advisor relationship was correct, but several expected relationships were missed.

The `receivedAward` predicate produced the highest number of true positives (10), but it also had 18 false positives and 43 false negatives. Its recall was 0.1887. This shows that the extractor still needs improvement in identifying awards and distinguishing them from other information. Overall, the results show that the initial predictions were not fully accurate, especially for the number of award and employment relationships.

During the improvement stage, two changes were made to the extraction logic. First, the subject-identification function was improved to handle passive sentences, named people, aliases, and pronouns. Second, the education extraction logic was improved to identify multiple educational institutions mentioned in the same sentence. The total number of extracted triples increased from 46 to 53 after the improvements.

The Open World Assumption means that missing information is considered unknown rather than false. For example, if the graph does not contain a `worksAt` relationship between a person and an organization, we cannot automatically conclude that the person never worked there. The relationship may simply not have been extracted or recorded.

In conclusion, the assignment helped demonstrate how information can be converted from unstructured text into a knowledge graph. It also showed that relation extraction can produce both false positives and false negatives, so further improvements are needed.