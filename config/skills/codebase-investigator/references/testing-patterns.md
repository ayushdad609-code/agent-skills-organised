# Finding Flaws & Testing Patterns

Use these patterns to systematically identify bugs and verify fixes.

## 1. Static Analysis Patterns (Manual Review)
- **Data Flow**: Trace a variable from input to output. Check for unsanitized use, type mismatches, or null pointers.
- **Control Flow**: Look for complex branching logic. Are there unreachable "dead" code paths or infinite loops?
- **Resource Leaks**: Check for unclosed sockets, file handles, or database connections.

## 2. Dynamic Analysis & Testing
- **Edge Cases**: Zero, Negative, Max/Min values, Empty strings, Null objects.
- **Concurrency**: Look for shared mutable state without proper locking/synchronization.
- **Integration**: Verify the "glue" code between modules, not just the modules themselves.

## 3. The "Deep Question" Checklist for Code
- "Why was this chosen over [Alternative]?"
- "How does this scale if the input size increases by 100x?"
- "What happens if this external dependency is down or slow?"
- "Is this logic idempotent?"
- "Where is the single point of failure?"
