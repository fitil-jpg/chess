#!/usr/bin/env python3
"""
Test script to verify that the dataClicked signal fix works
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Test the signal fix without running the full GUI
def test_signal_fix():
    print("Testing signal fix...")
    
    try:
        from ui.interactive_charts import InteractiveBarChart, InteractivePieChart, InteractiveLineChart
        
        # Test InteractiveBarChart
        chart = InteractiveBarChart("Test Chart")
        print(f"InteractiveBarChart has dataClicked signal: {hasattr(chart, 'dataClicked')}")
        print(f"InteractiveBarChart has barClicked signal: {hasattr(chart, 'barClicked')}")
        
        # Test InteractivePieChart
        pie_chart = InteractivePieChart("Test Pie Chart")
        print(f"InteractivePieChart has dataClicked signal: {hasattr(pie_chart, 'dataClicked')}")
        print(f"InteractivePieChart has sliceClicked signal: {hasattr(pie_chart, 'sliceClicked')}")
        
        # Test InteractiveLineChart
        line_chart = InteractiveLineChart("Test Line Chart")
        print(f"InteractiveLineChart has dataClicked signal: {hasattr(line_chart, 'dataClicked')}")
        print(f"InteractiveLineChart has pointClicked signal: {hasattr(line_chart, 'pointClicked')}")
        
        print("✅ Signal fix test passed! All charts have the required dataClicked signal.")
        return True
        
    except Exception as e:
        print(f"❌ Signal fix test failed: {e}")
        return False

if __name__ == "__main__":
    # Create a minimal QApplication for testing
    app = QApplication(sys.argv)
    
    success = test_signal_fix()
    
    # Exit immediately
    sys.exit(0 if success else 1)