#!/usr/bin/env bash

set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting dotfiles setup..."

# -----------------------------------------------------------------------------
# 1. OS Detection
# -----------------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    VSCODE_TARGET="$HOME/Library/Application Support/Code/User"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    VSCODE_TARGET="$HOME/.config/Code/User"
else
    echo "⚠️ Unsupported OS: $OSTYPE"
    exit 1
fi

echo "💻 Operating System detected: $OS"

# -----------------------------------------------------------------------------
# 2. Check Dependencies
# -----------------------------------------------------------------------------
for cmd in stow zsh git; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Required command '$cmd' is not installed."
        exit 1
    fi
done

# -----------------------------------------------------------------------------
# 3. Oh My Zsh & Plugin Management
# -----------------------------------------------------------------------------
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "📦 Installing Oh My Zsh..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
else
    echo "✅ Oh My Zsh is already installed."
fi

# Function to clone or update a plugin repo cleanly
install_or_update_plugin() {
    local repo_url="$1"
    local plugin_dir="$2"
    local plugin_name="$3"

    if [ ! -d "$plugin_dir" ]; then
        echo "🔌 Installing $plugin_name..."
        git clone "$repo_url" "$plugin_dir"
    else
        echo "🔄 Updating $plugin_name..."
        git -C "$plugin_dir" pull --quiet
    fi
}

install_or_update_plugin \
    "https://github.com/zsh-users/zsh-autosuggestions" \
    "$ZSH_CUSTOM/plugins/zsh-autosuggestions" \
    "zsh-autosuggestions"

install_or_update_plugin \
    "https://github.com/zsh-users/zsh-syntax-highlighting.git" \
    "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" \
    "zsh-syntax-highlighting"

# -----------------------------------------------------------------------------
# 4. Stow Standard Packages
# -----------------------------------------------------------------------------
cd "$DOTFILES_DIR"

echo "🔗 Stowing Zsh configuration..."
# Backup non-symlinked .zshrc if Oh My Zsh generated one automatically
if [ -f "$HOME/.zshrc" ] && [ ! -L "$HOME/.zshrc" ]; then
    echo "⚠️ Found default .zshrc, backing up to .zshrc.bak..."
    mv "$HOME/.zshrc" "$HOME/.zshrc.bak"
fi

stow -v -R zsh

# -----------------------------------------------------------------------------
# 5. Stow VS Code Configuration
# -----------------------------------------------------------------------------
if [ -d "$DOTFILES_DIR/vscode" ]; then
    echo "🔗 Stowing VS Code settings to: $VSCODE_TARGET"
    mkdir -p "$VSCODE_TARGET"
    stow --target="$VSCODE_TARGET" -v -R vscode

    if command -v code &> /dev/null && [ -f "$VSCODE_TARGET/extensions.txt" ]; then
        echo "💻 Installing VS Code extensions..."
        cat "$VSCODE_TARGET/extensions.txt" | xargs -L 1 code --install-extension --force
    fi
fi

echo "✨ Setup complete! Run: exec zsh"