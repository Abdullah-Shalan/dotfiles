# Run this script when running stow for the first time on new machine.
rm ~/.oh-my-zsh/custom/plugins/example/example.plugin.zsh
rm ~/.oh-my-zsh/custom/themes/example.zsh-theme
rm ~/.oh-my-zsh/custom/example.zsh
cp ~/.zshrc ~/.zshrc.before-stow
rm ~/.zshrc
