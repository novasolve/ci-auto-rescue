# The ACTUAL Simple Fix

## What We Discovered

The patch corruption is due to **incorrect hunk line counts** in the LLM-generated patches.

## The Simple Fix That Would Work

### Option 1: Don't Use Python Fallback (Simplest)

```python
# In fs.py, just fail if git apply fails instead of using buggy Python fallback
if not success:
    return []  # Don't use apply_unified_diff fallback
```

### Option 2: Fix the LLM Prompt (Best)

Tell the LLM to be more careful with line counts:

```python
prompt += "\nIMPORTANT: Count the exact number of lines in each hunk. "
prompt += "The hunk header @@ -X,N +Y,M @@ must have N and M match the actual line count."
prompt += "Remember that each context line, removed line, and added line counts as 1."
```

### Option 3: Keep SimpleFixer (Pragmatic)

For demo purposes, SimpleFixer actually works fine. It's not elegant but it's reliable.

## Why Our Current Fix Partially Works But Breaks Things

1. We fix the hunk headers (good!)
2. Git apply still fails for unknown reasons
3. Python fallback tries to apply but has bugs
4. File ends up with syntax errors

## The Lesson

Sometimes the simple hack (SimpleFixer) is better than the "proper" solution when the proper solution has too many edge cases.

For production, fixing the LLM prompt to generate correct patches in the first place is the best approach.
