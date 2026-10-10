# arXiv scientific-literature relations: annotation guide

You will label sentences from arXiv abstracts (computer science / machine learning). For each sentence decide whether it expresses
one of the six relations below between two entities **that appear in the sentence**.

| relation | head entity | tail entity | definition |
|---|---|---|---|
| `evaluated_on` | method / model | dataset / benchmark | A method or model is tested or evaluated on a dataset or benchmark. |
| `outperforms` | method | baseline / earlier method | A method achieves better results than a baseline or an earlier method. |
| `achieves_result` | method | score / metric value | A method obtains a specific performance result, such as a score or a metric value. |
| `builds_on` | new method | earlier method | A method is built on, extends or modifies an earlier method. |
| `applied_to_task` | method | task / problem / domain | A method is applied to a task, a problem or an application domain. |
| `uses_component` | method | technique / module / resource | A method uses a technique, a module or a resource as one of its parts. |

## How to fill in a row

1. Read `sentence`. If it expresses one of the relations, copy the **exact words** of the head entity into `head_entity` and of the tail entity into `tail_entity` (as they appear in the sentence), and write the relation name in `relation` (e.g. `evaluated_on`). The head is always the entity named in the *head entity* column above, wherever it appears in the sentence.
2. If the sentence expresses none of the six relations, write `none` in `relation` and leave both entity cells empty. Do not leave `relation` blank: blank rows are skipped by the agreement script.
3. One relation per sentence. If a sentence contains several, label the most prominent one and mention the others in `notes`.
4. Write your name or initials in `annotator`. Use `notes` for anything unclear. Do not look at the other annotator's sheet until both are finished.

## Disambiguation

- `builds_on` is for a whole earlier *method* that the new method extends. `uses_component` is for a part, technique or resource inside the method. If unsure, pick `uses_component` and note it.
- `achieves_result` needs a concrete score or metric value as the tail (e.g. `84.5% accuracy`, `state-of-the-art F1`). 'Improves performance' without a value is `none`.
- `outperforms` needs an explicit comparison with a named or clearly identified baseline/earlier method.
- Relations must be stated or clearly implied by the sentence itself, not by your outside knowledge.

## Illustrative examples (made up for this guide, not from the annotation sheet)

| sentence | head | tail | relation |
|---|---|---|---|
| We evaluate FooNet on the BarBench benchmark. | FooNet | BarBench | `evaluated_on` |
| FooNet outperforms the strongest baseline, BazNet, by 3 points. | FooNet | BazNet | `outperforms` |
| FooNet reaches 91.2% accuracy. | FooNet | 91.2% accuracy | `achieves_result` |
| FooNet extends the earlier QuxNet architecture. | FooNet | QuxNet | `builds_on` |
| We apply FooNet to protein folding. | FooNet | protein folding | `applied_to_task` |
| FooNet uses a contrastive loss. | FooNet | contrastive loss | `uses_component` |
| Large models are expensive to train. | | | `none` |
