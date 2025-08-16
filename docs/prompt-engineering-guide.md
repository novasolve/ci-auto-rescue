# Nova Deep Agent - Prompt Engineering Guide

## Overview

This guide documents the prompt engineering approach for Nova's v1.1 Deep Agent, including system prompts, response formats, validation, and testing frameworks.

## 🎯 Core Objectives

The prompt system is designed to:

1. **Embed core rules** directly into agent behavior
2. **Enforce structured outputs** for reliable parsing
3. **Prevent hallucination** of non-existent tools
4. **Validate all outputs** before execution
5. **Test prompt effectiveness** systematically

## 📋 Core Rules (Never Violate)

### Rule #1: Never Modify Test Files

```python
NEVER edit any file in tests/, test_*.py, or *_test.py
- If a test is wrong, document it but DO NOT change it
- Only fix source code to make tests pass
```

### Rule #2: Minimize Diff Size

```python
Keep changes as small as possible
- Fix only what's necessary for tests to pass
- Don't refactor or improve unrelated code
- Each change should have a clear purpose
```

### Rule #3: No Hallucinating Tools

```python
Only use tools that actually exist:
- open_file: Read source code files
- write_file: Modify source code files
- run_tests: Execute test suite
- apply_patch: Apply unified diff
- critic_review: Review patches
```

### Rule #4: Safety Guardrails

```python
Respect all safety limits:
- Max patch size: 500 lines
- Max files per patch: 10
- Never modify: .env, .git/, secrets, CI/CD configs
```

### Rule #5: Valid Patches Only

```python
Ensure all patches are syntactically valid:
- Preserve indentation (spaces vs tabs)
- Maintain code style consistency
- Ensure no syntax errors introduced
```

## 🏗️ System Prompt Structure

### Main Components

```python
from nova.agent.prompts.system_prompt import NovaSystemPrompt

# Get the full prompt with all rules
full_prompt = NovaSystemPrompt.get_full_prompt()

# Get compact version for token-limited scenarios
compact_prompt = NovaSystemPrompt.get_compact_prompt()
```

### Prompt Sections

1. **Identity**: "You are Nova, an advanced AI software engineer..."
2. **Core Rules**: The 5 inviolable rules
3. **Capabilities**: Available tools and their usage
4. **Workflow**: Step-by-step approach (Analyze → Investigate → Plan → Implement → Verify)
5. **Response Format**: JSON structure specification
6. **Error Handling**: How to handle various error types

## 📊 Structured Response Format

### Response Schema

```json
{
  "reasoning": "Clear explanation of the problem",
  "planned_changes": ["file1.py: fix X", "file2.py: adjust Y"],
  "confidence": 0.95,
  "risks": ["potential side effects"]
}
```

### Using the Response Format

```python
from nova.agent.prompts.system_prompt import ResponseFormat

# Parse agent response
response = ResponseFormat(
    reasoning="The add() function uses subtraction",
    planned_changes=["calculator.py: Change return a - b to return a + b"],
    confidence=0.95,
    risks=[]
)
```

## 🔍 Output Parsing & Validation

### Parser Usage

````python
from nova.agent.prompts.output_parser import AgentOutputParser

parser = AgentOutputParser()

# Parse JSON from agent output
agent_text = "```json\n{...}\n```"
parsed = parser.parse_json_response(agent_text)

# Validate patches
patch_text = "--- a/file.py\n+++ b/file.py\n..."
is_valid, error = parser.validate_patch(patch_text)

# Parse tool responses
tool_result = {"success": True, "result": "Tests passed"}
response = parser.parse_tool_response("run_tests", tool_result)
````

### Validation Rules

The parser enforces:

- No test file modifications
- Patch size limits (500 lines max)
- Protected file restrictions
- Valid diff format
- Proper tool usage

## 🧪 Testing Framework

### Test Categories

1. **Rule Compliance**: Ensures core rules are followed
2. **Output Format**: Validates JSON structure
3. **Hallucination Prevention**: Checks for fake tools
4. **Safety**: Verifies guardrails are respected
5. **Effectiveness**: Tests actual problem-solving

### Running Tests

```python
from nova.agent.prompts.prompt_tester import PromptTestSuite

# Create test suite
suite = PromptTestSuite()

# Provide agent responses for test scenarios
responses = {
    "never_modify_tests": "I cannot modify test files...",
    "minimize_diff": "I'll make a minimal change...",
    # ... more responses
}

# Run all tests
results = suite.run_all_tests(responses)
print(f"Success rate: {results['success_rate']:.1%}")
```

### Prompt Validation

```python
from nova.agent.prompts.prompt_tester import PromptValidator

# Validate a prompt contains required elements
prompt = "Your custom prompt here..."
is_valid, missing = PromptValidator.validate_prompt(prompt)

if not is_valid:
    print(f"Missing elements: {missing}")
```

## 🔧 Integration with Deep Agent

### Using Enhanced Agent

```python
from nova.agent.prompts.enhanced_agent import EnhancedDeepAgent

# Create enhanced agent with structured prompts
agent = EnhancedDeepAgent(
    state=agent_state,
    telemetry=logger,
    verbose=True,
    use_structured_output=True  # Enforce JSON responses
)

# Run the agent
success = agent.run(
    failures_summary="Test failures here",
    error_details="Error details",
    code_snippets="Relevant code"
)
```

### Upgrading Existing Agent

```python
from nova.agent.prompts.enhanced_agent import upgrade_existing_agent

# Upgrade existing agent with enhanced capabilities
enhanced = upgrade_existing_agent(
    existing_agent,
    use_enhanced_prompts=True,
    use_structured_output=True
)
```

## 📈 Prompt Iteration Process

### 1. Baseline Testing

```python
# Test current prompt effectiveness
baseline_results = suite.run_all_tests(current_responses)
```

### 2. Identify Weaknesses

- Which rules are violated?
- Where does hallucination occur?
- What safety issues arise?

### 3. Refine Prompts

- Strengthen weak areas
- Add explicit examples
- Clarify ambiguous instructions

### 4. A/B Testing

```python
# Compare prompt versions
v1_results = test_prompt_version(prompt_v1)
v2_results = test_prompt_version(prompt_v2)
```

### 5. Measure Improvements

- Track success rates
- Monitor rule violations
- Analyze failure patterns

## 🎯 Best Practices

### DO:

- ✅ Be explicit about rules (repeat if necessary)
- ✅ Provide clear examples in prompts
- ✅ Use structured formats for consistency
- ✅ Validate all outputs before execution
- ✅ Test prompts with edge cases

### DON'T:

- ❌ Assume implicit understanding
- ❌ Use ambiguous language
- ❌ Skip validation steps
- ❌ Ignore test results
- ❌ Modify prompts without testing

## 📊 Metrics & Monitoring

### Key Metrics to Track

1. **Rule Compliance Rate**: % of responses following all rules
2. **Hallucination Rate**: Frequency of non-existent tool usage
3. **Patch Success Rate**: % of patches that apply cleanly
4. **Test Fix Rate**: % of test failures successfully fixed
5. **Safety Violation Rate**: Frequency of guardrail breaches

### Telemetry Integration

```python
# Log structured responses
telemetry.log_event("structured_response", {
    "confidence": parsed.confidence,
    "rules_followed": check_rules(parsed),
    "has_risks": len(parsed.risks) > 0
})
```

## 🚀 Implementation Checklist

- [ ] System prompts created with embedded rules
- [ ] Response format specifications defined
- [ ] JSON output parser implemented
- [ ] Tool response validation added
- [ ] Prompt testing framework created
- [ ] Validation rules enforced
- [ ] Integration with Deep Agent complete
- [ ] Documentation updated
- [ ] Metrics tracking enabled
- [ ] A/B testing framework ready

## 📚 Additional Resources

- [System Prompt Module](../src/nova/agent/prompts/system_prompt.py)
- [Output Parser](../src/nova/agent/prompts/output_parser.py)
- [Prompt Tester](../src/nova/agent/prompts/prompt_tester.py)
- [Enhanced Agent](../src/nova/agent/prompts/enhanced_agent.py)

## Success Criteria Met ✅

1. **Reliable agent behavior**: Structured prompts with clear rules
2. **Valid output formats**: JSON schema with Pydantic validation
3. **Guardrails respected**: Validation at multiple levels
4. **Minimal hallucination**: Tool validation and known tool lists
5. **Consistent patch quality**: Patch validation before application
