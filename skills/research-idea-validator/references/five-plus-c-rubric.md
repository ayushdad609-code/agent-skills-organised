# FIVE+C Rubric

Use FIVE+C to decide whether a rough idea can become a researchable project and publishable paper.

## Framing

Ask:

- What exact problem does the idea solve?
- Who experiences this problem: researchers, practitioners, benchmark users, theorists, system builders?
- What is the paper's best one-sentence claim?
- Is the idea a new problem, new method, new explanation, new benchmark, or new application?
- What is out of scope?

Ratings:

- `strong`: problem, setting, baseline, and claim are all specific.
- `medium`: problem is plausible but the claim or target setting is fuzzy.
- `weak`: the idea is a technique looking for a problem.
- `unknown`: there is not enough context to judge.

Failure sign: the idea can only be described as "try X on Y" without a reason why Y needs X.

## Importance

Ask:

- Why would the target community care if this works?
- Does it address a known bottleneck, failure mode, cost, correctness issue, or evaluation gap?
- Is the problem central enough for the target venue?
- Would the result change how people build, evaluate, or understand systems?

Ratings:

- `strong`: success would affect a visible problem or active debate.
- `medium`: useful for a meaningful subcommunity.
- `weak`: mostly a convenience improvement or narrow tweak.
- `unknown`: importance depends on literature or user context not yet checked.

Failure sign: the only motivation is that the combination has not been tried.

## Validity

Ask:

- What core assumption makes the idea plausible?
- What would be true in the world if the idea works?
- What would falsify the idea quickly?
- Are there obvious reasons the mechanism should fail?
- Is the claim causal, empirical, theoretical, or interpretive?

Ratings:

- `strong`: core mechanism is plausible and falsifiable.
- `medium`: plausible intuition exists but needs sharpening.
- `weak`: mechanism is vague, circular, or only post-hoc.
- `unknown`: missing technical details prevent judgment.

Failure sign: no possible negative result would change the user's belief.

## Evidence

Ask:

- What is the smallest evidence package that would convince a skeptical reviewer?
- Which baseline matters most?
- What metric actually measures the claim?
- Are ablations, proofs, diagnostics, human studies, or scaling evidence required?
- Can the evidence distinguish the proposed mechanism from easier explanations?

Ratings:

- `strong`: evidence path is concrete, feasible, and aligned with the claim.
- `medium`: evidence path exists but contains major design questions.
- `weak`: evidence would be too indirect, too expensive, or easy to dismiss.
- `unknown`: benchmark, metric, or baseline is not yet identified.

Failure sign: the intended evidence would not answer the paper's main claim.

## Execution

Ask:

- Can the user run the minimum viable project with available code, data, compute, and time?
- Is there a fast time-to-signal?
- Are dependencies and implementation complexity bounded?
- Does the project require unavailable proprietary data or excessive compute?
- Can failures be interpreted?

Ratings:

- `strong`: first signal is obtainable in days to a few weeks.
- `medium`: feasible but needs careful scoping.
- `weak`: likely to consume large time before any interpretable signal.
- `unknown`: resources or implementation path are unclear.

Failure sign: the project requires full implementation before any learning is possible.

## Competition

Ask:

- What closest classic work must be checked?
- What recent or concurrent work is most dangerous?
- Is the idea already done under another name?
- Is the contribution incremental relative to a strong baseline?
- What is the irreducible difference from closest work?

Ratings:

- `strong`: clear gap relative to known close work.
- `medium`: plausible gap, but closest work must be checked.
- `weak`: likely covered or only a small variant.
- `unknown`: literature is insufficiently mapped.

Failure sign: novelty depends on not having looked carefully.

## Overall Judgment Pattern

- Strong framing + strong importance + medium/strong validity + medium/strong evidence + feasible execution + manageable competition can be `pursue`.
- Any fatal weakness in importance, evidence, or competition usually means `revise`, `park`, or `kill`.
- Multiple `unknown` ratings should not produce `pursue`; use `revise` or `park` with literature and feasibility checks.
