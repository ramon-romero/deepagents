# Fork Protocol (Read First)

This fork contains critical Bedrock support not present in upstream.

## Non-Negotiable Rules
- **Always use the local forked CLI** at `~/src/deepagents/libs/cli`.
- **Do not install from PyPI** unless explicitly told to do so.
- The only override is: `DEEPAGENTS_LOCAL=0` (forces PyPI).

## Why
Bedrock support lives only in this fork. Using PyPI will drop that support and break workflows.

## When Upstream Changes
- Keep Bedrock commits isolated on the `bedrock-patches` branch.
- Rebase those commits onto upstream when updating.
- Resolve conflicts in `libs/cli/deepagents_cli/config.py` and `libs/cli/pyproject.toml`.

## Summary
Default = **local fork**. Only deviate with explicit instruction.
