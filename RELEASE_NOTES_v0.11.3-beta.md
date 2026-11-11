# Atlas.ai v0.11.3-beta — Engineering Adviser hotfix

- Fixed a keyword-argument collision between the harness execution context and the Engineering Adviser's retrieved knowledge context.
- The harness now receives its own `harness_context` argument while the adviser receives its expected `context` argument.
- Added a regression test proving retrieved knowledge context reaches the adviser tool.
- No engineering calculation methods or design rules were changed.
