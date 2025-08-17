# Nova Git Branching Guide

## Overview

Nova CI-Rescue uses Git branches to safely isolate automated fixes from your main development work. This guide explains how Nova's branching works and how to customize it.

## Default Branching Behavior

By default, Nova creates a new branch for every `nova fix` run with a unique timestamped name:

```bash
nova fix .
# Creates branch: nova-fix/20250817_105520
```

### Why Timestamped Branches?

1. **Safety**: Your main/development branch remains untouched
2. **Isolation**: Each fix attempt is isolated in its own branch
3. **Uniqueness**: Timestamps prevent naming conflicts
4. **Review**: You can review fixes before merging
5. **Rollback**: Easy to abandon unsuccessful fixes

### Branch Lifecycle

1. Nova creates a new branch from your current HEAD
2. All fixes are committed to this branch
3. On success: Branch remains for review/merge
4. On failure/interrupt: Branch is deleted, original state restored

## Customizing Branch Names

### Using NOVA_FIX_BRANCH_NAME

You can override the default timestamped branches by setting the `NOVA_FIX_BRANCH_NAME` environment variable:

```bash
# Use a consistent branch name
export NOVA_FIX_BRANCH_NAME="nova-fixes"
nova fix .

# Or inline for a single run
NOVA_FIX_BRANCH_NAME="development" nova fix .
```

### In .env File

Add to your `.env` file for persistent configuration:

```bash
# .env
NOVA_FIX_BRANCH_NAME=nova-fixes
```

### Behavior with Custom Branch Names

When using a custom branch name:
- Nova uses `git checkout -B <branch>` (creates or resets the branch)
- Existing branch is reset to current HEAD
- All previous commits on that branch are lost
- Useful for CI/CD where you want consistent branch names

## Use Cases

### Development Workflow

Keep the default timestamped branches:
```bash
nova fix .
# Creates: nova-fix/20250817_105520
# Review and merge if successful
```

### CI/CD Pipeline

Use a consistent branch name:
```bash
# In CI script
export NOVA_FIX_BRANCH_NAME="automated-fixes"
nova fix .
```

### Working on Current Branch

To work on your current branch (be careful!):
```bash
# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)
NOVA_FIX_BRANCH_NAME="$CURRENT_BRANCH" nova fix .
```

**Warning**: This will reset your branch to HEAD, losing any uncommitted changes!

## Model Configuration

Nova now supports multiple ways to configure the LLM model, in order of precedence:

### 1. CLI Option (Highest Priority)

```bash
nova fix . --model gpt-4
nova fix . -m gpt-3.5-turbo
```

### 2. Configuration File

Create `nova.config.yml`:
```yaml
model: gpt-4
# or
default_llm_model: gpt-4
```

### 3. Environment Variables

```bash
export NOVA_MODEL=gpt-4
# or
export NOVA_LLM_MODEL=gpt-4
# or
export MODEL=gpt-4
```

### 4. Default

If no configuration is provided, Nova defaults to `gpt-4`.

## Supported Models

Nova supports these OpenAI models:
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4-0613`
- `gpt-4-32k`
- `gpt-3.5-turbo`
- `gpt-3.5-turbo-16k`

And Anthropic models:
- `claude-3-opus`
- `claude-3-sonnet`
- `claude-3-haiku`
- `claude-3.5-sonnet`

## Model Fallback Behavior

Nova includes intelligent fallback for invalid or unavailable models:

1. **Unknown models**: Automatically fallback to `gpt-4`
2. **GPT-5 references**: Fallback to `gpt-4` (until GPT-5 is available)
3. **GPT-4.1 aliases**: Map to `gpt-4`
4. **Runtime errors**: If a model fails at runtime, Nova retries with `gpt-4`

Example:
```bash
# These all safely fallback to gpt-4:
nova fix . --model gpt-5
nova fix . --model gpt-4.1alias
nova fix . --model unknown-model
```

## Best Practices

1. **Development**: Use default timestamped branches for safety
2. **CI/CD**: Use `NOVA_FIX_BRANCH_NAME` for consistent branch names
3. **Model Selection**: Start with `gpt-4` for best results
4. **Testing**: Use `gpt-3.5-turbo` for faster/cheaper testing
5. **Review**: Always review Nova's fixes before merging

## Troubleshooting

### "Working tree not clean" Error

Nova requires a clean working tree. Commit or stash changes:
```bash
git add .
git commit -m "WIP"
# or
git stash
```

### Model Not Found Errors

If you see model errors, check:
1. API key is set (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
2. Model name is valid (see supported models above)
3. Your API key has access to the model

### Branch Already Exists

With custom branch names, Nova will reset the branch. To preserve it:
```bash
git branch backup-branch nova-fixes
NOVA_FIX_BRANCH_NAME="nova-fixes" nova fix .
```
