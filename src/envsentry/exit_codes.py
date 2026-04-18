"""Exit codes for EnvSentry CLI.

This module defines standard exit codes used throughout the application
to communicate execution results to the shell and CI/CD systems.
"""

# Successful execution with no audit findings
EXIT_SUCCESS = 0

# Audit completed successfully but found security issues
# (e.g., exposed secrets, misconfigurations)
EXIT_AUDIT_FAILED = 1

# Execution error occurred (e.g., invalid arguments, parsing failure,
# file access error, configuration error)
EXIT_ERROR = 2
