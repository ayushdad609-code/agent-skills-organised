# Deep Analysis & Problem Solving Frameworks

This reference outlines the methodologies used by the Codebase Investigator for rigorous engineering analysis.

## 1. First Principles Thinking
Break complex problems down into their basic truths.
- **Deconstruction**: Strip away assumptions. What are the immutable constraints of the system (CPU, Memory, Network, I/O)?
- **Reconstruction**: Build the solution from the ground up based on these constraints.

## 2. The Socratic Method (Asking Deep Questions)
Don't just look for answers; look for the right questions.
- **Assumptions**: "What are we assuming to be true that might not be?"
- **Evidence**: "Where is the empirical evidence that this component is the bottleneck?"
- **Consequences**: "If we change this module, what is the 'blast radius' across the system?"
- **Counter-examples**: "In what scenario would this logic fail?"

## 3. Root Cause Analysis (RCA)
- **The 5 Whys**: Drill down into an issue by asking "Why?" five times.
- **Fault Tree Analysis**: Map out all possible causes of a failure systematically.

## 4. Security & Robustness Auditing
- **Trust Boundaries**: Where does data enter the system? Is it validated?
- **State Management**: Are there race conditions? Is the state consistent across async boundaries?
- **Error Handling**: Are we catching exceptions but losing the context? Are we failing open or failing closed?
