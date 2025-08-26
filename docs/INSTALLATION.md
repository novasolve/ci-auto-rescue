# Installation

Requirements: Python 3.10+ and an API key for either OpenAI or Anthropic.

## Steps

1. Clone the repo

```bash
git clone https://github.com/novasolve/ci-auto-rescue
cd ci-auto-rescue
```

2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install Nova in editable mode

```bash
pip install -e .
```

4. Configure API keys

```bash
cp env.example .env
# Edit .env with OPENAI_API_KEY or ANTHROPIC_API_KEY
```

5. Verify install

```bash
nova version
```

You are ready to run Nova.
