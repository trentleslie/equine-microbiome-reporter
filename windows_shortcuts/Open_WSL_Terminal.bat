@echo off
:: Open WSL Terminal in the project directory
:: For advanced users who want command line access

wsl -d Ubuntu -e bash -c "cd ~/equine-microbiome-reporter && conda activate equine-microbiome && exec bash"