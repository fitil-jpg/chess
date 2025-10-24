#!/bin/bash
# Enhanced Chess Viewer Dependency Installation Script

echo "Installing Enhanced Chess Viewer Dependencies..."
echo "================================================"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install Python and pip first."
    exit 1
fi

# Install core dependencies
echo "📦 Installing core dependencies..."
pip3 install chess numpy PySide6

# Check installation
echo "🔍 Verifying installation..."
python3 -c "import chess; print('✓ chess module installed')" || echo "❌ chess module failed"
python3 -c "import numpy; print('✓ numpy module installed')" || echo "❌ numpy module failed"
python3 -c "import PySide6; print('✓ PySide6 module installed')" || echo "❌ PySide6 module failed"

# Install optional dependencies
echo "📦 Installing optional dependencies..."
pip3 install matplotlib scipy pandas

echo "✅ Installation complete!"
echo ""
echo "To run the enhanced chess viewer:"
echo "  python3 run_enhanced_viewer.py"
echo ""
echo "To test the system:"
echo "  python3 test_enhanced_system.py"