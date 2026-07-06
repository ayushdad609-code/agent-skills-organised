# Paper Shapes

Pick the paper shape that the idea can actually support. Do not force every idea into a method paper.

## Method Paper

Best when:

- there is a new algorithm, objective, architecture, training procedure, inference method, or optimization strategy
- improvements can be isolated against strong baselines
- ablations can show why the method works

Must show:

- performance gain
- fair baselines
- ablations
- cost and limitations
- mechanism evidence if claiming a specific reason

Common failure: small tweak with weak motivation and no mechanism.

## Theory Paper

Best when:

- the main contribution is a theorem, bound, formal explanation, or principled framework
- assumptions are meaningful and connected to real methods or phenomena
- the theory predicts something observable or clarifies a known puzzle

Must show:

- clear assumptions
- nontrivial result
- relation to existing theory
- examples or empirical diagnostics when useful

Common failure: theorem about an artificial setting with unclear relevance.

## Empirical Analysis Paper

Best when:

- the idea is to explain, diagnose, or characterize an important phenomenon
- the contribution is insight rather than a new method
- careful experimental design can change community understanding

Must show:

- systematic study
- strong controls
- multiple settings
- actionable conclusions

Common failure: collection of observations without a thesis.

## Benchmark or Dataset Paper

Best when:

- existing evaluation misses an important capability, failure mode, or real-world constraint
- the dataset or benchmark changes what can be measured

Must show:

- clear evaluation gap
- data quality
- task design
- baseline suite
- reproducibility
- limitations and ethics

Common failure: dataset exists but does not answer an important question.

## Systems Paper

Best when:

- the contribution is infrastructure, scaling, efficiency, reliability, deployment, or tooling
- the work changes what is practical to run

Must show:

- real bottleneck
- strong engineering comparison
- throughput, latency, cost, memory, reliability, or usability evidence
- reproducible setup

Common failure: engineering effort without a research claim.

## Application Paper

Best when:

- the novelty is applying methods to a domain with real constraints
- domain validity matters as much as algorithmic novelty

Must show:

- domain problem importance
- domain-appropriate evaluation
- comparison to current practice
- expert or real-world validation if needed

Common failure: standard model on standard data with no domain insight.

## Negative Result Paper

Best when:

- a plausible community assumption fails under careful study
- the negative result prevents wasted effort or corrects misleading belief

Must show:

- why the hypothesis was plausible
- rigorous controls
- broad enough conditions
- useful explanation or guidance

Common failure: failed implementation presented as a general negative result.

## Position or Interpretation Paper

Best when:

- the contribution is a new framing, taxonomy, critique, or synthesis
- evidence can support a shift in how people think

Must show:

- precise thesis
- broad coverage
- concrete implications
- fair treatment of alternatives

Common failure: opinion without evidence.
