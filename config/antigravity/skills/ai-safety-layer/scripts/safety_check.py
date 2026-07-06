import sys
import os
import re
from datetime import datetime

# Define blocked patterns (regex)
BLOCKED_PATTERNS = [
    r'rm\s+-(rf|fr|r|f)\s+/',          # Dangerous rm on root
    r'drop\s+table',                   # SQL drop table
    r'delete\s+from\s+\w+$',           # SQL delete without WHERE (approx)
    r'mkfs',                            # Format filesystem
    r'shred',                           # Secure deletion
    r'shutdown',                        # System shutdown
    r'reboot',                          # System reboot
    r'>\s+/dev/sd[a-z]',               # Direct disk writing
    r'chmod\s+777\s+/',                 # Global permissions on root
]

AUDIT_LOG = "ai_safety_audit.log"

def check_commands(commands_raw):
    # Split by newline or semicolon
    commands = re.split(r'\n|;', commands_raw)
    commands = [c.strip() for c in commands if c.strip()]
    
    violations = []
    for cmd in commands:
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                violations.append((cmd, pattern))
                break
                
    # Log to audit file
    with open(AUDIT_LOG, 'a') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"--- {timestamp} ---\n")
        f.write(f"Commands: {commands_raw}\n")
        if violations:
            f.write(f"STATUS: BLOCKED\n")
            for cmd, p in violations:
                f.write(f"Violation: {cmd} (matched {p})\n")
        else:
            f.write(f"STATUS: PASSED\n")
        f.write("\n")

    if violations:
        print("❌ SAFETY ALERT: Blocked dangerous command(s) detected!")
        for cmd, p in violations:
            print(f"  - Blocked: '{cmd}'")
        print(f"\nAudit details logged to {AUDIT_LOG}")
        sys.exit(1)
    else:
        print("✅ Safety check passed. Commands are within safe boundaries.")
        print(f"Execution logged to {AUDIT_LOG}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python safety_check.py \"<command_string>\"")
    else:
        check_commands(sys.argv[1])
