# Linux Terminal Assistant (LTA)

🐧 **A professional CLI/TUI assistant for Linux system administrators and developers.**

LTA centralizes system diagnostics, administration tools, automation utilities, and media downloading in an intuitive terminal interface. Built with Python 3.10+, following "programs, not scripts" philosophy.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

### 🔍 System Monitoring
- Real-time CPU, memory, disk usage dashboard
- Top processes by resource consumption
- Logged-in users tracking
- Disk partition analysis
- Network connections overview

### 🌐 Network Diagnostics
- Public IP detection with multi-backend fallback
- DNS lookup (A, AAAA, MX, NS records)
- Ping with latency statistics
- Traceroute support
- Port availability checking

### 📥 Media Downloader
- YouTube, Vimeo, Twitch, and 1000+ sites via yt-dlp
- Audio/video format selection
- Playlist download support
- Progress tracking with Rich UI
- Rate limiting options

### 🛠️ System Administration
- Package manager detection (apt, dnf, pacman, zypper)
- Service status monitoring (systemd)
- Process management
- User/group information
- Log viewing capabilities

### 🔧 Developer Tools Integration
- fzf for interactive search
- jq for JSON processing
- ripgrep for fast text search
- bat for syntax-highlighted output
- Docker/Podman container management
- Git helpers
- tmux/screen session management

## Installation

### Quick Install (pip)

```bash
pip install linux-terminal-assistant
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/example/linux-terminal-assistant.git
cd linux-terminal-assistant

# Run setup script (recommended)
./scripts/dev-setup.sh

# Or manual setup
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### System Dependencies (Optional but Recommended)

For full functionality, install these tools:

**Ubuntu/Debian:**
```bash
sudo apt install yt-dlp fzf jq ripgrep bat docker.io
```

**Fedora:**
```bash
sudo dnf install yt-dlp fzf jq ripgrep bat docker
```

**Arch Linux:**
```bash
sudo pacman -S yt-dlp fzf jq ripgrep bat docker
```

## Usage

### Interactive Mode

Run without arguments to launch the interactive TUI:

```bash
lta
```

### CLI Commands

```bash
# Show public IP address
lta ip
lta ip --json          # JSON output
lta ip --no-cache      # Force fresh lookup

# System status
lta status
lta status --json

# System monitoring dashboard
lta monitor
lta monitor --no-interactive

# Comprehensive system info
lta info
lta info --full

# Network diagnostics
lta ping google.com
lta ping google.com --count 10
lta dns google.com
lta dns google.com --type MX

# Download media
lta download <URL>
lta download <URL> --audio      # Audio only (mp3)
lta download <URL> --playlist   # Download playlist
lta download <URL> -o ~/Videos  # Custom output dir

# Check tool availability
lta check
lta check yt-dlp    # Check specific tool
```

### Help

```bash
lta --help           # Main help
lta <command> --help # Command-specific help
```

## Configuration

LTA uses YAML configuration files:

- **Default config:** `/path/to/lta/config/defaults.yaml`
- **User config:** `~/.config/lta/config.yaml`

User config overrides defaults automatically.

### Example Configuration

```yaml
# ~/.config/lta/config.yaml

network:
  ip_backends:
    - https://api.ipify.org
    - https://ifconfig.me/ip
  timeout_seconds: 15

downloader:
  default_audio_format: mp3
  default_video_format: mp4
  output_template: "%(title)s.%(ext)s"
  rate_limit: "5M"  # Limit download speed

ui:
  use_colors: true
  use_icons: true
```

### Environment Variables

Override config with environment variables:

```bash
export LTA_NETWORK__TIMEOUT_SECONDS=20
export LTA_DEBUG_MODE=true
export NO_COLOR=1  # Disable colors
```

## Architecture

```
linux-terminal-assistant/
├── src/lta/
│   ├── main.py              # CLI entrypoint (Typer)
│   ├── config.py            # Configuration management (Pydantic)
│   ├── logger.py            # Logging setup
│   ├── utils/
│   │   ├── shell.py         # Safe subprocess wrapper
│   │   ├── network.py       # Network utilities
│   │   └── system.py        # System monitoring
│   ├── modules/
│   │   ├── admin/           # System administration
│   │   ├── downloader/      # yt-dlp integration
│   │   ├── tools/           # External tool wrappers
│   │   └── tui/             # TUI components
│   └── tests/               # Unit tests
├── config/
│   └── defaults.yaml        # Default configuration
└── scripts/
    └── dev-setup.sh         # Development setup
```

## Development

### Running Tests

```bash
pytest src/lta/tests -v --cov=lta
```

### Code Formatting

```bash
black src/
ruff check src/ --fix
```

### Type Checking

```bash
mypy src/lta
```

### Building Distribution

```bash
python -m build
```

## Troubleshooting

### yt-dlp Not Found

```bash
# Install yt-dlp
pip install yt-dlp
# or
sudo apt install yt-dlp
```

### Permission Errors

Some features require root privileges. Run with `sudo` when needed:

```bash
sudo lta monitor
```

### No Colors in Output

Set the `NO_COLOR` environment variable or use `--no-colors`:

```bash
export NO_COLOR=1
lta --no-colors ip
```

### All IP Backends Failed

Check your internet connection and firewall settings. You can also add custom backends in config:

```yaml
network:
  ip_backends:
    - https://your-custom-ip-api.com
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [Typer](https://github.com/tiangolo/typer) - CLI framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Media downloader
- [psutil](https://github.com/giampaolo/psutil) - System monitoring

---

Built with ❤️ for Linux administrators and developers.
