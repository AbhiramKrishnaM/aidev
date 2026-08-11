#!/bin/bash
# Script to perform a clean installation of aidev with minimal dependencies
# and setup pre-commit hooks

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'  # No Color

echo -e "${GREEN}Starting clean installation of aidev...${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Create and activate a fresh virtual environment
echo -e "${YELLOW}Creating a new virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip and setuptools...${NC}"
pip install --upgrade pip setuptools wheel

# Install minimal core dependencies first
echo -e "${YELLOW}Installing core dependencies...${NC}"
pip install typer rich click httpx pydantic jinja2 shellingham

# Install aidev in development mode
echo -e "${YELLOW}Installing aidev...${NC}"
pip install -e .

# Set up pre-commit hooks
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
pip install pre-commit black flake8 flake8-docstrings isort mypy
if [ -f .pre-commit-config.yaml ]; then
    pre-commit install
    echo -e "${GREEN}Pre-commit hooks installed.${NC}"
    echo -e "${YELLOW}Running initial pre-commit check...${NC}"
    pre-commit run --all-files || true

    echo -e "${GREEN}The following checks will run on commit:${NC}"
    echo -e "  - Trailing whitespace removal"
    echo -e "  - End of file fixer"
    echo -e "  - YAML syntax checking"
    echo -e "  - Black (code formatting)"
    echo -e "  - isort (import sorting)"
    echo -e "  - flake8 (linting)"
    echo -e "  - mypy (type checking)"
else
    echo -e "${YELLOW}No .pre-commit-config.yaml found. Skipping pre-commit setup.${NC}"
fi

# Install tab completion
echo -e "${YELLOW}Setting up tab completion...${NC}"
if command -v aidev &> /dev/null; then
    # Detect shell
    CURRENT_SHELL=$(basename "$SHELL")
    if [[ "$CURRENT_SHELL" == "bash" || "$CURRENT_SHELL" == "zsh" || "$CURRENT_SHELL" == "fish" ]]; then
        echo -e "${YELLOW}Installing completion for $CURRENT_SHELL...${NC}"
        aidev install-completion --shell "$CURRENT_SHELL" --force
    else
        echo -e "${YELLOW}Unsupported shell: $CURRENT_SHELL. Skipping completion setup.${NC}"
    fi
fi

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
if command -v aidev &> /dev/null; then
    VERSION=$(aidev --version)
    echo -e "${GREEN}aidev installed successfully: $VERSION${NC}"
else
    echo -e "${RED}Installation failed. The 'aidev' command is not available.${NC}"
    exit 1
fi

echo -e "${GREEN}Installation complete!${NC}"
echo -e "To use aidev, make sure the virtual environment is activated:"
echo -e "    source .venv/bin/activate"
echo -e "Try running 'aidev hello' to get started."
