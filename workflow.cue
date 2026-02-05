// workflow.cue
// Canonical workflow rules for the deepagents fork.

package workflow

fork_protocol: {
  summary: "This fork contains critical AWS Bedrock support."

  rules: [
    "Always use the local forked CLI at ~/src/deepagents/libs/cli.",
    "Do not install from PyPI unless explicitly instructed.",
    "Only override via DEEPAGENTS_LOCAL=0.",
  ]

  rationale: "Bedrock support lives only in this fork; using PyPI drops it and breaks workflows."

  upstream_updates: [
    "Keep Bedrock commits isolated on the bedrock-patches branch.",
    "Rebase onto upstream when updating.",
    "Resolve conflicts in libs/cli/deepagents_cli/config.py and libs/cli/pyproject.toml.",
  ]
}
