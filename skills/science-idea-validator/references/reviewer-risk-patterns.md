# Reviewer Risk Patterns

Use these patterns to forecast how reviewers or advisors may attack an early idea.

## Novelty Risk

Signals:

- idea is a direct combination of two known methods
- closest work has not been checked
- contribution is described only as "first to apply X to Y"
- improvement is a small variant of a standard baseline

Mitigations:

- run a focused literature review
- identify the irreducible difference from closest work
- reframe as analysis, benchmark, or systems contribution if method novelty is weak

## Importance Risk

Signals:

- no clear user or community pain point
- benchmark is obscure and not linked to broader question
- success would not change practice or understanding

Mitigations:

- sharpen the problem
- connect to a known bottleneck or debate
- narrow to a community that truly cares

## Evaluation Risk

Signals:

- no metric directly tests the claim
- baseline is unclear
- success depends on qualitative examples only
- evidence requires resources the user lacks

Mitigations:

- define the minimum viable experiment
- choose an easier falsification test
- change the claim to match measurable evidence

## Mechanism Risk

Signals:

- paper claims why the method works but only measures final performance
- method changes multiple variables at once
- gains could come from tuning, compute, data, or implementation detail

Mitigations:

- separate performance claim from mechanism claim
- define diagnostics
- plan ablations and controls early

## Baseline Risk

Signals:

- comparison is against an old or weak baseline
- baseline has less tuning or compute
- strong prior methods are omitted

Mitigations:

- identify strongest direct competitor
- define tuning fairness
- use baseline-selection audit when available

## Scope Risk

Signals:

- claim is much broader than the planned evidence
- one dataset supports a universal statement
- method depends on narrow assumptions

Mitigations:

- narrow claim
- define target regime
- state limitations early

## Execution Risk

Signals:

- long implementation before any interpretable result
- dependency on unavailable data, GPU, or collaborators
- no fallback if first result is negative

Mitigations:

- create a fast prototype
- choose a smaller proxy setting
- park until prerequisites exist

## Writing/Positioning Risk

Signals:

- method is feasible but story is unclear
- contribution type is mismatched
- target venue expects a different kind of evidence

Mitigations:

- choose paper shape before building too much
- define primary and secondary contributions
- avoid overclaiming early
