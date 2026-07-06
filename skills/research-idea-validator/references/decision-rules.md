# Decision Rules

Choose one decision. Do not hedge with multiple labels.

## Pursue

Use `pursue` when:

- the problem is clear and important enough for the intended audience
- there is a plausible novelty gap
- the core assumption is falsifiable
- a minimum viable project can produce signal before heavy investment
- required evidence is feasible with available resources
- likely reviewer attacks are known and not fatal

`pursue` output must include:

- first implementation or analysis target
- killer experiment or proof
- primary baseline
- kill criteria
- next skill or action

## Revise

Use `revise` when the direction may be valuable but the current form is wrong.

Common reasons:

- contribution type is mismatched
- claim is too broad
- method mechanism is underspecified
- evaluation does not test the claim
- baseline or closest work changes the novelty story
- target venue or audience is wrong

`revise` output must say what to revise:

- framing
- problem scope
- method
- evaluation
- literature positioning
- paper shape

Then give the smallest revision that could turn the decision into `pursue`.

## Park

Use `park` when the idea may be good but is blocked right now.

Common reasons:

- needs unavailable compute, data, or collaborators
- novelty depends on a literature review not yet done
- timing is bad relative to deadlines
- implementation cost is too high for current stage
- another project has higher expected value

`park` output must include:

- what new evidence or resource would reopen the idea
- what memory should be saved
- a date, milestone, or trigger for reconsideration if known

## Kill

Use `kill` when the idea is unlikely to become a worthwhile project or paper.

Common reasons:

- closest work already covers the contribution
- problem is not important enough
- claim is not falsifiable
- evaluation cannot support the claim
- required evidence is infeasible
- success would still be too incremental
- the idea is a technique without a motivating problem

`kill` output must preserve useful residue:

- what was learned
- whether any sub-idea should be reused
- which related direction might be better
- why not to revisit without new information

## Confidence

Use:

- `high`: decision follows from clear evidence or obvious structural issue.
- `medium`: enough information for a practical next step, but some uncertainty remains.
- `low`: decision is provisional; next action should reduce uncertainty.

Low confidence should usually route to literature review, feasibility check, or advisor discussion.
