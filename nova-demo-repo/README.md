# Nova CI-Rescue Demo Repository

This repository demonstrates Nova's self-healing CI/CD capabilities through a realistic workflow:

1. ✅ **Working Code**: Initial calculator with passing tests
2. ❌ **Breaking Change**: A "bad PR" introduces bugs
3. 🤖 **Auto-Fix**: Nova detects and fixes the failures automatically
4. ✅ **Green Pipeline**: Tests pass again without human intervention

## Demo Workflow

### Step 1: Initial Setup (Working State)
```bash
# Clone and setup
git clone <this-repo>
cd nova-demo-repo

# Install dependencies
pip install -r requirements.txt

# Run tests - they should pass!
pytest -v
```

### Step 2: Introduce Breaking Changes
```bash
# Apply the breaking changes (simulating a bad PR)
git apply breaking-changes.patch
git add -A
git commit -m "feat: optimize calculator performance"
git push

# Watch GitHub Actions fail ❌
```

### Step 3: Nova Auto-Fix
GitHub Actions will automatically:
1. Detect the test failures
2. Run Nova CI-Rescue
3. Fix the bugs
4. Create a PR with the fixes
5. All tests pass again ✅

## Repository Structure

```
nova-demo-repo/
├── src/
│   └── calculator.py      # Main calculator module
├── tests/
│   └── test_calculator.py # Comprehensive test suite
├── .github/
│   └── workflows/
│       └── ci.yml         # CI/CD with Nova integration
├── requirements.txt       # Python dependencies
├── breaking-changes.patch # The "bad PR" changes
└── demo-script.sh        # Automated demo runner
```

## Running the Full Demo

```bash
# Run the automated demo script
./demo-script.sh
```

This will:
1. Show the working state
2. Apply breaking changes
3. Push to trigger CI
4. Show Nova fixing the issues
5. Display the auto-generated PR

## Key Features Demonstrated

- **Autonomous Detection**: Nova identifies failing tests without human input
- **Intelligent Fixes**: AI understands the test failures and generates appropriate fixes
- **PR Generation**: Creates professional pull requests with GPT-5
- **Zero Human Intervention**: Complete automation from failure to fix

## Technologies Used

- **Nova CI-Rescue**: AI-powered test fixing
- **GitHub Actions**: CI/CD automation
- **GPT-5**: Intelligent code analysis and PR generation
- **Python + pytest**: Test framework

## Watch It In Action

Check the [Actions tab](../../actions) to see Nova in action fixing broken tests!
