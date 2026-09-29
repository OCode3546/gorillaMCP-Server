# Builder Agent — Example Invoke Prompts

Purpose: Short, copy-paste prompts to invoke the workspace-scoped Builder Agent skill.

1. Implement a feature (small)

- Prompt: "Implement a settings page under `src/ui/settings`. Keep changes minimal, add unit tests with pytest, and run only tests impacted by the change. Use project's test runner if present."

2) Refactor a module

- Prompt: "Refactor `service/auth.py` to remove duplication and improve readability. Keep behavior identical; add unit tests for any changed logic. Run `ruff` and `pytest`."

3. Lint and fix straightforward issues

- Prompt: "Audit the repository for `ruff`/`flake8` errors and automatically fix trivial style issues. Report any non-trivial warnings for approval."

4. Add a test for a bug
- Prompt: "Reproduce failing behavior in `tests/test_user_flow.py::test_login` and add a regression test that captures the correct behavior. Run pytest and provide failing output if the bug reproduces."

5) Quick audit before PR
- Prompt: "Prepare a pre-PR checklist for `feature/new-reports`: lint, run unit tests, run type checks, and list any risky changes that need manual review."

Guidance: include the target file/folder path, desired depth (quick/complete), and whether to run tests or only static checks.
