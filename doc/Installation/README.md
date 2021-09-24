# DiPiDi Installation
### Known Compatibilities
*DiPiDi has been tested on the following Python and OS versions:*
- Python 3.8 & 3.9 (64-bit)

OS versions:
- macOS Big Sur *(including the macOS-11.4-arm64-arm-64bit version)*
- Ubuntu 16, 18, & 20
- Windows Subsystem for Linux  (wsl2)

### Installing required Python packages
Use the following command with the requirements.txt file in the main repository folder.

- make sure Python 3 and `pip` are installed and currently in your PATH variables
- `cd` to the directory where `requirements.txt` is located
- run: `pip install -r requirements.txt` in your shell

### GraphViz is required to export viewable graphs
Use the following command to install GraphViz:
- macOS: `brew install graphviz`
- Ubuntu: `sudo apt install graphviz`
- Others: Install from [GraphViz official website](https://graphviz.org/)