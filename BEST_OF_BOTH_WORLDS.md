# Nova CI-Rescue: Best of Both Worlds Implementation

## Overview

This enhanced implementation combines the best features from both our clean modern approach and the production-ready CLI specification. It provides a powerful, flexible, and user-friendly system for automatically fixing failing tests.

## ✨ Key Features

### From Our Implementation
- ✅ **Docker Sandbox**: Complete isolation for safe test execution
- ✅ **Modern @tool Decorators**: Clean LangChain integration
- ✅ **Comprehensive Documentation**: Detailed guides and examples
- ✅ **Modular Architecture**: Clean separation of concerns

### From Their Implementation
- ✅ **YAML Configuration**: User-friendly external configuration
- ✅ **Multi-LLM Support**: GPT-4, Claude, Llama models
- ✅ **Pre-Agent Test Discovery**: Better user feedback before AI starts
- ✅ **GitHub Integration**: PR comments and check runs
- ✅ **Fault Localization**: Advanced test failure analysis
- ✅ **Class-Based Tools**: More flexible tool architecture

### Hybrid Advantages
- ✅ **Dual Tool Support**: Works with both class-based and function-based tools
- ✅ **Flexible Configuration**: YAML files with CLI overrides
- ✅ **Smart Defaults**: Works out-of-the-box with sensible defaults
- ✅ **Production Ready**: Enterprise-grade features with clean design

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install langchain langchain-openai langchain-anthropic openai anthropic pyyaml

# Build Docker sandbox
cd docker/
bash build.sh

# Set API keys
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Basic Usage

```bash
# Fix tests in current directory (uses defaults)
python src/nova/cli_enhanced.py fix

# Use a specific model
python src/nova/cli_enhanced.py fix --model claude-3

# Use configuration file
python src/nova/cli_enhanced.py fix -c nova.config.yml

# Verbose mode with custom limits
python src/nova/cli_enhanced.py fix -v --max-iters 10 --timeout 1800
```

### 3. Configuration File

Create `nova.config.yml`:

```yaml
default_llm_model: gpt-4
max_iterations: 8
timeout_seconds: 1500

safety:
  max_lines_changed: 1000
  max_files_modified: 15
  denied_paths:
    - "*.min.js"
    - "vendor/*"

docker_image: nova-ci-rescue-sandbox:latest
use_docker: true
```

## 📦 Architecture

### Tool System

The hybrid implementation supports both approaches:

#### Class-Based Tools (Production Style)
```python
from nova.tools.run_tests import RunTestsTool

tool = RunTestsTool(repo_path="/path/to/repo")
result = tool._run(max_failures=5)
```

#### Function-Based Tools (Modern Style)
```python
from nova.agent.tools import run_tests

@tool("run_tests", return_direct=True)
def run_tests() -> str:
    # Docker-based execution
    return json.dumps(result)
```

#### Automatic Conversion
The `NovaDeepAgent` automatically normalizes both types:
```python
agent = NovaDeepAgent(
    tools=[class_tool, function_tool],  # Mix and match!
    ...
)
```

### Configuration System

Three-level configuration hierarchy:

1. **Defaults**: Built-in sensible defaults
2. **YAML File**: External configuration file
3. **CLI Arguments**: Command-line overrides

```python
# Priority: CLI > YAML > Defaults
settings = NovaSettings()  # Defaults
settings.merge_with_yaml(Path("nova.config.yml"))  # YAML
if cli_arg:
    settings.field = cli_arg  # CLI override
```

### LLM Support

Multi-model support with automatic fallbacks:

```python
# Automatic model detection and initialization
if "gpt" in model_name:
    llm = ChatOpenAI(model=model_name)
elif "claude" in model_name:
    llm = ChatAnthropic(model=model_name)
elif "llama" in model_name:
    llm = HuggingFacePipeline.from_model_id(model_name)
else:
    llm = ChatOpenAI(model="gpt-4")  # Fallback
```

## 🛠️ Advanced Features

### Pre-Agent Test Discovery

Tests are run before the agent starts for better user feedback:

```python
# Pre-discovery for user feedback
runner = TestRunner(repo_path)
failing_tests = runner.run_tests()

# Display to user
show_failing_tests_table(failing_tests)

# Then pass to agent
agent.run(failures_summary=format_tests(failing_tests))
```

### Safety Configuration

Comprehensive safety checks with customization:

```yaml
safety:
  max_lines_changed: 500
  denied_paths:
    - "test_*.py"
    - ".github/*"
  suspicious_patterns:
    - "exec("
    - "eval("
```

### Docker Sandbox

Full isolation with resource limits:

```bash
docker run --rm \
  -v $REPO:/workspace:ro \
  --memory 1g \
  --cpus 1.0 \
  --network none \
  --pids-limit 256 \
  nova-ci-rescue-sandbox --pytest
```

## 📊 Comparison with Single Approaches

| Feature | Our Original | Their Spec | **Hybrid** |
|---------|-------------|------------|------------|
| Tools | @tool functions | BaseTool classes | **Both** ✅ |
| Config | Python only | YAML only | **Both** ✅ |
| Docker | Full | Not shown | **Full** ✅ |
| LLMs | GPT, Claude | GPT, Claude, Llama | **All Three** ✅ |
| Test Discovery | Agent does it | Pre-agent | **Pre-agent** ✅ |
| GitHub | Basic | Full | **Full** ✅ |
| Fault Localization | No | Yes | **Yes** ✅ |
| Documentation | Extensive | Minimal | **Extensive** ✅ |

## 🔄 Migration Path

### From Our Original Implementation

```python
# Old
from nova_deep_agent import DeepAgent
agent = DeepAgent(config)

# New
from nova.agent.nova_deep_agent import NovaDeepAgent
agent = NovaDeepAgent(settings=NovaSettings())
```

### From Their Specification

```python
# Their way still works
from nova.tools.run_tests import RunTestsTool
tools = [RunTestsTool(...)]

# But can also use our way
from nova.agent.tools import run_tests
tools = [run_tests]
```

## 📝 File Structure

```
src/nova/
├── agent/
│   ├── nova_deep_agent.py    # Hybrid agent (new)
│   ├── deep_agent.py          # Original agent
│   └── tools.py               # Function-based tools
├── tools/
│   ├── run_tests.py           # Class-based tool (new)
│   ├── apply_patch.py         # Class-based tool (new)
│   └── critic_review.py       # Class-based tool (new)
├── cli_enhanced.py            # Enhanced CLI (new)
├── config.py                  # Configuration system (enhanced)
└── orchestrator.py            # Pipeline orchestration

docker/
├── Dockerfile                 # Sandbox container
├── run_python.py             # Test runner script
└── build.sh                  # Build script

nova.config.example.yml       # Example configuration
```

## 🎯 Usage Examples

### Example 1: Simple Fix
```bash
nova fix
```

### Example 2: Custom Model with Config
```bash
nova fix -c my-config.yml --model claude-3 -v
```

### Example 3: Programmatic Usage
```python
from nova.agent.nova_deep_agent import NovaDeepAgent
from nova.config import NovaSettings

settings = NovaSettings.from_yaml("config.yml")
agent = NovaDeepAgent(settings=settings)
success = agent.run(failing_tests="test_calc failed")
```

### Example 4: Custom Tools
```python
# Mix class and function tools
tools = [
    RunTestsTool(repo_path),         # Class-based
    apply_patch,                      # Function-based
    CriticReviewTool(),              # Class-based
]

agent = NovaDeepAgent(tools=tools)
```

## ✅ Benefits of This Hybrid Approach

1. **Flexibility**: Use either tool style based on preference
2. **Compatibility**: Works with existing code from both approaches
3. **User-Friendly**: YAML config for non-programmers
4. **Developer-Friendly**: Full programmatic control when needed
5. **Production-Ready**: GitHub integration, fault localization, etc.
6. **Modern**: Clean @tool decorators and LangChain best practices
7. **Safe**: Docker sandbox and comprehensive safety checks
8. **Extensible**: Easy to add new tools and features

## 🚦 Next Steps

1. **Test with real repositories**
2. **Add more LLM providers** (Gemini, Cohere, etc.)
3. **Implement caching** for faster iterations
4. **Add web UI** for non-technical users
5. **Create plugin system** for custom tools

## 📄 License

This hybrid implementation combines the best of open-source patterns with production-grade features, available under the project's license.

---

*The best of both worlds: Clean design meets production features.*
