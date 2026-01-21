# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="robbyrussell"

export ZSH_COMPDUMP=$ZSH/cache/.zcompdump-$HOST

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
    git
    zsh-syntax-highlighting
    zsh-autosuggestions
    zsh-interactive-cd
)

source $ZSH/oh-my-zsh.sh

# fzf shell integration
source <(fzf --zsh)

# set environment variables 
export EDITOR='nvim'

# Aliases
alias cls=clear
alias path="echo $PATH | tr ':' '\n' && echo $PATH | tr ':' '\n' | wc -l"
alias v='nvim'
