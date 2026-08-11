# AI-Powered CLI Assistant

An AI-powered command-line assistant for developers that provides code generation, terminal command suggestions, documentation search, git assistance, and API testing capabilities.

> **Mid-pivot:** this project is moving from a local-only Ollama backend to cloud AI providers
> (Anthropic, OpenAI), with a new incident/debugging co-pilot as the flagship feature. The
> architecture and rationale are fully written up in [`docs/adr/`](docs/adr/README.md) and
> [`docs/architecture.md`](docs/architecture.md); the file-by-file build plan is in
> [`docs/implementation-plan.md`](docs/implementation-plan.md). **The provider implementation
> itself has not landed yet** — commands that call an AI model will report "no AI provider
> configured" until it does.

## Features

- **Code Generation**: Generate code snippets from natural language descriptions
- **Terminal Commands**: Get suggestions and explanations for complex terminal operations
- **Documentation Search**: Search and summarize documentation locally
- **Git Assistance**: Generate commit messages and PR descriptions
- **API Testing**: Test and format API requests easily
- **Command Autocompletion**: Tab completion for all commands and options

## Roadmap

For details on upcoming features and development plans, see [docs/roadmap.md](docs/roadmap.md)
and the pivot documentation linked above.

## Architecture

The CLI is built around a pluggable provider/model abstraction
(`cli/ai_agent_models/base_model.py`, `model_factory.py`): each AI provider is a class
implementing a common interface, registered by provider id, and addressed as
`"<provider>:<model_id>"` (e.g. `anthropic:claude-sonnet-5`). See
[`docs/architecture.md`](docs/architecture.md) for diagrams of how commands, the provider layer,
and git-context gathering fit together.

## Installation

### Prerequisites

- Python 3.8+
- Git

### Setup

#### Installation from PyPI (Recommended)

The easiest way to install the AI CLI Assistant is via pip:

```bash
pip install aidev
```

#### Installation from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aidev.git
   cd aidev
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the CLI tool in development mode:
   ```bash
   pip install -e .
   ```

#### Using Clean Install Scripts

If you encounter dependency issues, use our clean install script:

```bash
./scripts/clean_install.sh
```

This script creates a fresh virtual environment and installs minimal dependencies directly from pyproject.toml.

### Command Autocompletion

For an improved CLI experience, you can enable command autocompletion which provides tab completion for all commands and options.

#### Automatic Installation

Run the provided installation script:

```bash
./scripts/install_completion.sh
```

This script will detect your shell (bash, zsh, or fish) and install the appropriate completion script.

#### Manual Installation

You can also install completion manually:

```bash
# Install completion for your current shell
aidev install-completion

# Or specify a shell
aidev install-completion --shell bash
aidev install-completion --shell zsh
aidev install-completion --shell fish
```

After installation, restart your shell or source the appropriate file to enable completion:

```bash
# For bash
source ~/.bash_completion

# For zsh
source ~/.zshrc

# For fish
source ~/.config/fish/completions/aidev.fish
```

## Usage

You can use the CLI tool with the `aidev` command or by running the Python module directly with `python -m cli.main`.

### Basic Commands

```bash
# Show help and available commands
aidev --help

# Test that the CLI is working
aidev hello
```

### Code Generation

```bash
# Generate a Python function to parse JSON
aidev code generate "Create a function that parses a JSON file and returns a dictionary"

# Generate JavaScript code and save to a file
aidev code generate "Create a React component that displays a todo list" --language javascript --output todo.js

# Explain existing code
aidev code explain path/to/file.py
```

### Terminal Command Help

```bash
# Get command suggestions based on what you want to do
aidev terminal suggest "find all files containing a specific text"

# Explain what a command does
aidev terminal explain ls -la
aidev terminal explain "grep -r pattern ."
```

### Git Operations

```bash
# Generate commit messages based on your changes
aidev git generate-commit

# Generate a pull request description
aidev git pr-description
```

### Documentation Search

```bash
# Search documentation for specific terms
aidev docs search list python

# Limit search to a specific language
aidev docs search function --language javascript

# Summarize a documentation file
aidev docs summarize README.md
```

### API Testing

```bash
# Send an ad-hoc prompt to the configured model
aidev api request "Explain how DNS works"

# Send it to a specific model
aidev api request "Summarize quantum computing" --model anthropic:claude-sonnet-5
```

## Choosing a model

Every AI command accepts `--model` (e.g. `--model anthropic:claude-sonnet-5`), or falls back to
the configured default:

```bash
# Use a specific model for one command
aidev terminal suggest --model anthropic:claude-sonnet-5 "find large files"

# Disable streaming output
aidev code generate --no-stream "Create a binary search function"

# Hide model thinking process
aidev terminal explain --no-thinking "grep -r pattern ."
```

Provider/model management (listing detected providers, picking a default) is planned per
[`docs/implementation-plan.md`](docs/implementation-plan.md) and not yet implemented — see the
note at the top of this file.

### Streaming and Thinking Process

Control the output format:

```bash
# Enable real-time streaming (default)
aidev code generate "Create a function to calculate factorial"

# Disable streaming for complete output at once
aidev code generate --no-stream "Create a binary search function"

# Show model reasoning (default)
aidev git generate-commit --show-thinking

# Hide model reasoning
aidev git generate-commit --no-thinking
```

## Development

### Project Structure

```
aidev/
├── cli/                   # CLI interface code
│   ├── commands/          # Command implementations
│   ├── utils/             # Utilities
│   ├── ai_agent_models/   # AI model implementations
│   │   ├── base_model.py  # Base abstract class for models
│   │   └── model_factory.py # Provider/model registry and resolution
│   └── main.py            # Entry point
├── tests/                 # Test suite
├── docs/                  # Documentation
└── scripts/               # Helper scripts
    ├── format_code.sh     # Formats code with black and isort
    ├── clean_install.sh   # Creates a fresh virtual environment and installation
    └── install_completion.sh # Sets up shell autocompletion
```

### Code Formatting and Linting

This project uses several tools to maintain code quality:

- **Black**: For automatic code formatting
- **isort**: To sort and organize imports
- **flake8**: For code linting
- **mypy**: For static type checking

To format your code before committing:

```bash
# Use the formatting script (recommended)
./scripts/format_code.sh

# Or run the tools manually
black .
isort .
```

We also use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run the hooks manually (useful before committing)
pre-commit run --all-files
```

For detailed information on the coding standards and development workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Contributing

Interested in contributing? Check out our [Development Guide](docs/development.md) for details on:

- Setting up a development environment
- Code style and standards
- Running tests
- Creating model implementations
- Submitting pull requests

## Documentation

- [Development Guide](docs/development.md) - Guide for contributors
- [Architecture Decision Records](docs/adr/README.md) - Rationale behind the current pivot
- [Architecture](docs/architecture.md) - System diagrams (components, request flow, config resolution)
- [Implementation Plan](docs/implementation-plan.md) - File-by-file plan for the pivot in progress
- [PyPI Distribution](docs/pypi_distribution.md) - Information on packaging and publishing
