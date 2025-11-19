# Liquid Pressure Chess

**Liquid Pressure Chess** is a terminal-based chess opponent designed for Termux/Android and desktop systems. It accepts algebraic (SAN) moves like `e4`, `Nf3`, `hxe5`, `O-O`, etc., and plays back using the Stockfish engine while applying a creative "liquid pressure" decision model to vary strength and style.

## Features 
- **Liquid Pressure Style**: Mimics human decision-making with flowing, adaptive gameplay
- **Time Management**: Intelligent 10-minute game clock awareness
- **Anti-Detection**: Natural imperfections and human-like thinking patterns
- **Android Optimized**: Built for Termux and mobile devices
- **Real-time Analysis**: Live board display and move recommendations

## 🚀 Quick Start

### Prerequisites
- Android device with [Termux](https://termux.com/)
- Python 3.8+
- Stockfish Android ARMv8 binary

### Installation

1. **Install Termux** from F-Droid or Play Store

2. **Update packages**:
   ```bash
   pkg update && pkg upgrade
   pkg install python python-pip git wget
   pkg install tar
   pip install --uograde pip
   pip install chess stockfish
   ```

3. **Download & Setup**:
   ```bash
   wget https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-android-armv8.tar
   ```
   **Extract it**
   ```bash
   tar -xf stockfish-android-armv8.tar
   ```
   **Navigate to the Stockfish Directory**
   ```bash
   cd stockfish
   ```
   **Make Stockfish Executable**
   ```bash
   chmod +x stockfish-android-armv8
   ```
   **Test Stockfish**
   ```bash
   ./stockfish-android-armv8
   ```
   And Type "quit"

   **Run**
   ```bash
   python3 chess_liquid_pressure.py
   ```


**🎯 Playing Tips**

1. Input moves in UCI format (e.g., e2e4, g1f3)
2. Monitor time pressure indicators
3. Follow liquid pressure phases for strategic guidance
4. Use recommended moves as learning opportunities

**⚠️ Disclaimer**

This tool is intended for:

· Chess improvement and analysis
· Understanding engine thought processes
· Educational purposes

Use responsibly and in accordance with platform rules. The authors are not responsible for account penalties from inappropriate use.

**🤝 Contributing**

Contributions welcome! Please feel free to submit pull requests or open issues for:

· Bug fixes
· New features
· Improved anti-detection patterns
· Additional playing styles
