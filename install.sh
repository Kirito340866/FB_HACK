#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# 🍟♤ ｃ𝓐𝐓Sahdow 🐟🎁
# AUTO INSTALLER — Modules Only
# Installs all required Python modules for Termux
# No file creation — Just pure installation
# ============================================================

# Colors
G='\033[92m'
R='\033[91m'
Y='\033[93m'
W='\033[97m'
X='\033[0m'
B='\033[1m'

clear

# ============================================================
# BANNER
# ============================================================
echo -e "${G}╔══════════════════════════════════════════════════════════════════════╗
║                                                ║
║  AUTO INSTALLER — Modules Only                                      ║
║                 ║
╚══════════════════════════════════════════════════════════════════════╝${X}
"

# ============================================================
# CHECK TERMUX
# ============================================================
if [ ! -d "/data/data/com.termux" ]; then
    echo -e "${R}[❌] This script must run in Termux!${X}"
    echo -e "${Y}[!] Install Termux from F-Droid first.${X}"
    exit 1
fi

# ============================================================
# UPDATE PACKAGES
# ============================================================
echo -e "\n${Y}[1] Updating package lists...${X}"
pkg update -y 2>/dev/null
pkg upgrade -y 2>/dev/null
echo -e "${G}[✅] Packages updated${X}"

# ============================================================
# INSTALL PYTHON
# ============================================================
echo -e "\n${Y}[2] Installing Python...${X}"
pkg install python -y 2>/dev/null

if command -v python &> /dev/null; then
    echo -e "${G}[✅] Python installed: $(python --version)${X}"
else
    echo -e "${R}[❌] Python installation failed${X}"
    exit 1
fi

# ============================================================
# INSTALL PIP
# ============================================================
echo -e "\n${Y}[3] Installing pip...${X}"
python -m ensurepip --upgrade 2>/dev/null
python -m pip install --upgrade pip 2>/dev/null
echo -e "${G}[✅] pip installed${X}"

# ============================================================
# INSTALL PYCRYPTODOMEX
# ============================================================
echo -e "\n${Y}[4] Installing pycryptodomex...${X}"
pip install pycryptodomex --quiet 2>/dev/null

if python -c "import Cryptodome" 2>/dev/null; then
    echo -e "${G}[✅] pycryptodomex installed${X}"
else
    echo -e "${R}[❌] pycryptodomex installation failed${X}"
fi

# ============================================================
# INSTALL CRYPTOGRAPHY (BACKUP)
# ============================================================
echo -e "\n${Y}[5] Installing cryptography (backup engine)...${X}"
pip install cryptography --quiet 2>/dev/null

if python -c "import cryptography" 2>/dev/null; then
    echo -e "${G}[✅] cryptography installed${X}"
else
    echo -e "${R}[❌] cryptography installation failed${X}"
fi

# ============================================================
# SETUP TERMUX STORAGE
# ============================================================
echo -e "\n${Y}[6] Setting up Termux storage...${X}"

if [ -d "/data/data/com.termux/files/home/storage" ]; then
    echo -e "${G}[✅] Storage already configured${X}"
else
    echo -e "${Y}[!] Please grant storage permission when prompted${X}"
    termux-setup-storage 2>/dev/null
    sleep 3
    echo -e "${G}[✅] Storage setup initiated${X}"
fi

# ============================================================
# FINAL CHECK
# ============================================================
echo -e "\n${Y}[7] Verifying installation...${X}"

ALL_GOOD=true

# Check Python
if command -v python &> /dev/null; then
    echo -e "${G}   ✅ Python: $(python --version)${X}"
else
    echo -e "${R}   ❌ Python: Not found${X}"
    ALL_GOOD=false
fi

# Check pip
if command -v pip &> /dev/null; then
    echo -e "${G}   ✅ pip: $(pip --version | cut -d' ' -f2)${X}"
else
    echo -e "${R}   ❌ pip: Not found${X}"
    ALL_GOOD=false
fi

# Check Cryptodome
if python -c "import Cryptodome" 2>/dev/null; then
    echo -e "${G}   ✅ pycryptodomex: Installed${X}"
else
    echo -e "${R}   ❌ pycryptodomex: Not installed${X}"
    ALL_GOOD=false
fi

# Check cryptography
if python -c "import cryptography" 2>/dev/null; then
    echo -e "${G}   ✅ cryptography: Installed${X}"
else
    echo -e "${R}   ❌ cryptography: Not installed${X}"
    ALL_GOOD=false
fi

# ============================================================
# COMPLETE
# ============================================================
if [ "$ALL_GOOD" = true ]; then
    echo -e "\n${G}╔══════════════════════════════════════════════════════════════════════╗
║                                                ║
║  ${G}✅ INSTALLATION COMPLETE!${G}                                              ║
║                                                                      ║
║  ${W}All modules installed successfully!${G}                                ║
║                                                                      ║
║  ${Y}You can now run any Python script that requires:${G}                ║
║  ${W}  - pycryptodomex${G}                                              ║
║  ${W}  - cryptography${G}                                               ║
║                                                                      ║
║  ${W}[!] No file was created. This is pure installation.${G}            ║
╚══════════════════════════════════════════════════════════════════════╝${X}
"
else
    echo -e "\n${R}╔══════════════════════════════════════════════════════════════════════╗
║  ${R}❌ INSTALLATION FAILED${R}                                               ║
║                                                                      ║
║  ${Y}Some modules failed to install. Try manually:${R}                      ║
║  ${W}  pip install pycryptodomex cryptography${R}                         ║
╚══════════════════════════════════════════════════════════════════════╝${X}
"
fi
