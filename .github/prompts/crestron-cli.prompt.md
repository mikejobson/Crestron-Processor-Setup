---
description: Look up Crestron processor CLI commands, syntax, and parameters
---

# Crestron CLI Command Reference

You have access to a comprehensive Crestron CP4 command reference database at [crestron_command_reference.md](../../crestron_command_reference.md).

## When to Use

Use this skill when the user needs to:

- Look up the syntax or parameters for a Crestron CLI command
- Find which command performs a specific function on a Crestron processor
- Understand available commands by role (Administrator, Operator, Programmer, Connect)
- Write or modify `expect` scripts that interact with the Crestron CLI
- Troubleshoot command usage or errors on a Crestron processor

## How to Use

1. Read the command reference file to find the relevant command(s).
2. The reference contains:
   - **Command Index** — table of all 414 commands with role and description
   - **Command Details** — detailed syntax, parameters, and usage for each command
3. Commands are organized alphabetically. Use the index to find commands by description, or search the details for parameter syntax.

## Key Context

- The Crestron CLI uses a `MODEL>` prompt (e.g., `CP4>`, `MC4>`). It is **not** a standard Unix shell.
- Commands are case-insensitive but conventionally shown in mixed case (e.g., `ADDPUBKEYtouser`).
- Roles determine access level: Connect < Operator < Programmer < Administrator.
- Some commands return `ERROR:` when prerequisites aren't met (e.g., BACnet not running, AD not configured).
- Use `COMMAND ?` to get help for any command on a live processor.
