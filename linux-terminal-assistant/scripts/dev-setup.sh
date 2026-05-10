#!/bin/bash
# Development setup script for Linux Terminal Assistant (LTA)
# This script sets up a development environment with all dependencies

set -e

echo "🐧 Linux Terminal Assistant - Development Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "  Python: $python_version"

# Verify Python >= 3.10
major=$(echo "$python_version" | cut -d'.' -f1)
minor=$(echo "$python_version" | cut -d'.' -f2)

if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ is required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Detect package manager
echo -e "${BLUE}Detecting package manager...${NC}"
if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    PKG_INSTALL="sudo apt install -y"
    DISTRO="Debian/Ubuntu"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    PKG_INSTALL="sudo dnf install -y"
    DISTRO="Fedora/RHEL"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    PKG_INSTALL="sudo pacman -S --noconfirm"
    DISTRO="Arch"
elif command -v zypper &> /dev/null; then
    PKG_MANAGER="zypper"
    PKG_INSTALL="sudo zypper install -y"
    DISTRO="openSUSE"
else
    echo -e "${YELLOW}Warning: Unknown package manager, skipping system dependencies${NC}"
    PKG_MANAGER=""
fi

if [ -n "$PKG_MANAGER" ]; then
    echo "  Distribution: $DISTRO"
    echo "  Package Manager: $PKG_MANAGER"
    echo -e "${GREEN}✓ Package manager detected${NC}"
fi
echo ""

# Install system dependencies (optional tools for full functionality)
if [ -n "$PKG_MANAGER" ]; then
    echo -e "${BLUE}Checking optional system tools...${NC}"
    
    TOOLS_TO_INSTALL=()
    
    # Check yt-dlp
    if ! command -v yt-dlp &> /dev/null; then
        TOOLS_TO_INSTALL+=("yt-dlp")
    fi
    
    # Check fzf
    if ! command -v fzf &> /dev/null; then
        TOOLS_TO_INSTALL+=("fzf")
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        TOOLS_TO_INSTALL+=("jq")
    fi
    
    # Check ripgrep
    if ! command -v rg &> /dev/null; then
        TOOLS_TO_INSTALL+=("ripgrep")
    fi
    
    # Check bat
    if ! command -v bat &> /dev/null; then
        TOOLS_TO_INSTALL+=("bat")
    fi
    
    if [ ${#TOOLS_TO_INSTALL[@]} -gt 0 ]; then
        echo "  Missing tools: ${TOOLS_TO_INSTALL[*]}"
        read -p "Install missing tools? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Installing system tools...${NC}"
            $PKG_INSTALL ${TOOLS_TO_INSTALL[@]}
            echo -e "${GREEN}✓ System tools installed${NC}"
        else
            echo -e "${YELLOW}Skipping system tools installation${NC}"
        fi
    else
        echo -e "${GREEN}✓ All optional tools already installed${NC}"
    fi
    echo ""
fi

# Create virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip wheel setuptools > /dev/null 2>&1
echo -e "${GREEN}✓ Pip upgraded${NC}"
echo ""

# Install LTA in development mode
echo -e "${BLUE}Installing LTA in development mode...${NC}"
pip install -e ".[dev]" > /dev/null 2>&1
echo -e "${GREEN}✓ LTA installed${NC}"
echo ""

# Install pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    echo -e "${BLUE}Installing pre-commit hooks...${NC}"
    pre-commit install > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ Pre-commit hooks configured${NC}"
    echo ""
fi

# Create config directory
echo -e "${BLUE}Setting up configuration...${NC}"
mkdir -p ~/.config/lta
if [ ! -f ~/.config/lta/config.yaml ]; then
    cp config/defaults.yaml ~/.config/lta/config.yaml
    echo -e "${GREEN}✓ Default configuration copied to ~/.config/lta/config.yaml${NC}"
else
    echo -e "${YELLOW}Configuration already exists at ~/.config/lta/config.yaml${NC}"
fi
echo ""

# Run tests
echo -e "${BLUE}Running tests...${NC}"
if python -m pytest src/lta/tests -v 2>/dev/null; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${YELLOW}No tests found or tests skipped${NC}"
fi
echo ""

# Show summary
echo "================================================"
echo -e "${GREEN}✅ Development setup complete!${NC}"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run LTA:"
echo "     lta                    # Interactive mode"
echo "     lta --help             # Show all commands"
echo "     lta ip                 # Show public IP"
echo "     lta status             # Quick system status"
echo "     lta monitor            # System dashboard"
echo ""
echo "  3. Run tests:"
echo "     pytest src/lta/tests"
echo ""
echo "  4. Run linting:"
echo "     ruff check src/"
echo "     black --check src/"
echo ""
echo -e "${YELLOW}Note: Some features require external tools (yt-dlp, fzf, jq, etc.)${NC}"
echo "      Run 'lta check' to see what's available."
echo ""
