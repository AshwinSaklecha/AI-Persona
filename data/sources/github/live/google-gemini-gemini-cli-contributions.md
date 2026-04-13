# google-gemini/gemini-cli Contributions

Source URL: https://github.com/google-gemini/gemini-cli
Contributor: AshwinSaklecha

## PR #22418 - Reject positional prompt when --prompt-interactive is provided

Pull request URL: https://github.com/google-gemini/gemini-cli/pull/22418
State: open
Merged at: None

## Summary

<!-- Concisely describe what this PR changes and why. Focus on impact and
urgency. -->
Reject conflicting CLI input when a positional prompt and `--prompt-interactive` are provided together. This makes the behavior consistent with the existing `positional prompt + --prompt` validation and prevents the prompt value from being overwritten or handled inconsistently.

## Details

<!-- Add any extra context and design decisions. Keep it brief but complete. -->
This change adds a parser check for `positional prompt + --prompt-interactive` and adds a regression test covering that case.

## Related Issues

<!-- Use keywords to auto-close issues (Closes #123, Fixes #456). If this PR is
only related to an issue or is a partial fix, simply reference the issue number
without a keyword (Related to #123). -->
Closes #22417
## How to Validate
1. Run:
 ```bash
   npm run test --workspace @google/gemini-cli -- src/config/config.test.ts --testNamePattern="positional prompt and the --prompt-interactive flag|positional prompt and the --prompt flag"
```
2. Confirm the targeted tests pass.
3. Optionally verify the CLI behavior manually by running:
```bash

gemini hello --prompt-interactive "from-flag"
```
4. Confirm the CLI now rejects the conflicting input instead of accepting it.

<!-- List exact steps for reviewers to validate the change. Include commands,
expected results, and edge cases. -->

## Pre-Merge Checklist

<!-- Check all that apply before requesting review or merging. -->

- [ ] Updated relevant documentation and README (if needed)
- [x] Added/updated tests (if needed)
- [ ] Noted breaking changes (if any)
- [ ] Validated on required platforms/methods:
  - [ ] MacOS
    - [ ] npm run
    - [ ] npx
    - [ ] Docker
    - [ ] Podman
    - [ ] Seatbelt
  - [ ] Windows
    - [ ] npm run
    - [ ] npx
    - [ ] Docker
  - [x] Linux
    - [x] npm run
    - [ ] npx
    - [ ] Docker

## PR #22259 - fix(core): preserve ask_user payload in CoreToolScheduler

Pull request URL: https://github.com/google-gemini/gemini-cli/pull/22259
State: closed
Merged at: None

## Summary

<!-- Concisely describe what this PR changes and why. Focus on impact and
urgency. -->
Fixes a regression in `CoreToolScheduler.handleConfirmationResponse()` where confirmation payloads were not forwarded to the wrapped `onConfirm` callback. This caused `ask_user` answers to be dropped for non-TUI integrations.


## Details

<!-- Add any extra context and design decisions. Keep it brief but complete. -->
Forward the optional `payload` argument to `originalOnConfirm()` inside `handleConfirmationResponse()`.

Add a regression test covering the `ask_user` confirmation path through the scheduler's wrapped `onConfirm` callback so submitted answers are preserved.


## Related Issues

<!-- Use keywords to auto-close issues (Closes #123, Fixes #456). If this PR is
only related to an issue or is a partial fix, simply reference the issue number
without a keyword (Related to #123). -->
Fixes #22120

## How to Validate

<!-- List exact steps for reviewers to validate the change. Include commands,
expected results, and edge cases. -->
Run:

```bash
npm run test --workspace @google/gemini-cli-core -- src/core/coreToolScheduler.test.ts src/tools/ask-user.test.ts
```

## Pre-Merge Checklist

<!-- Check all that apply before requesting review or merging. -->

- [ ] Updated relevant documentation and README (if needed)
- [x] Added/updated tests (if needed)
- [ ] Noted breaking changes (if any)
- [x] Validated on required platforms/methods:
  - [ ] MacOS
    - [ ] npm run
    - [ ] npx
    - [ ] Docker
    - [ ] Podman
    - [ ] Seatbelt
  - [ ] Windows
    - [ ] npm run
    - [ ] npx
    - [ ] Docker
  - [x] Linux
    - [x] npm run
    - [ ] npx
    - [ ] Docker
