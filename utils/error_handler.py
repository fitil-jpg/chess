"""Comprehensive error handling utilities for the chess application.

This module provides enhanced error handling, logging, and user-friendly
error messages throughout the application.
"""

import logging
import traceback
from pathlib import Path
from typing import Optional, Any, Dict, List
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for the chess application."""
    
    @staticmethod
    def log_error(error: Exception, context: str = "", details: Dict[str, Any] = None) -> None:
        """Log an error with context and details."""
        details = details or {}
        logger.error(f"Error in {context}: {error}")
        if details:
            logger.error(f"Details: {details}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def show_error_dialog(
        parent: QWidget,
        title: str,
        message: str,
        error_type: str = "Error",
        suggestions: List[str] = None
    ) -> None:
        """Show a user-friendly error dialog."""
        suggestions = suggestions or []
        
        full_message = f"🚨 <b>{error_type}:</b> {message}"
        
        if suggestions:
            full_message += "\n\n<b>💡 Suggestions:</b>\n"
            for i, suggestion in enumerate(suggestions, 1):
                full_message += f"{i}. {suggestion}\n"
        
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(full_message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_warning_dialog(
        parent: QWidget,
        title: str,
        message: str,
        suggestions: List[str] = None
    ) -> None:
        """Show a user-friendly warning dialog."""
        suggestions = suggestions or []
        
        full_message = f"⚠️ <b>Warning:</b> {message}"
        
        if suggestions:
            full_message += "\n\n<b>💡 Suggestions:</b>\n"
            for i, suggestion in enumerate(suggestions, 1):
                full_message += f"{i}. {suggestion}\n"
        
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(full_message)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_info_dialog(
        parent: QWidget,
        title: str,
        message: str
    ) -> None:
        """Show a user-friendly info dialog."""
        full_message = f"ℹ️ <b>Info:</b> {message}"
        
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(full_message)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
    
    @staticmethod
    def handle_import_error(error: ImportError, context: str = "") -> None:
        """Handle import errors with specific suggestions."""
        missing_module = str(error).split("'")[1] if "'" in str(error) else "unknown"
        
        suggestions = [
            f"Install missing module: pip install {missing_module}",
            "Check if you're using the correct Python environment",
            "Verify all dependencies are installed: pip install -r requirements.txt",
            "Try running: pip install --upgrade pip"
        ]
        
        ErrorHandler.log_error(error, f"Import error in {context}")
        print(f"❌ Import Error: {error}")
        print("💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    @staticmethod
    def handle_file_error(error: FileNotFoundError, context: str = "") -> None:
        """Handle file not found errors with specific suggestions."""
        file_path = str(error).split("'")[1] if "'" in str(error) else "unknown file"
        
        suggestions = [
            f"Check if file exists: {file_path}",
            "Verify the file path is correct",
            "Ensure you have read permissions for the file",
            "Try running the application from the correct directory"
        ]
        
        ErrorHandler.log_error(error, f"File error in {context}")
        print(f"❌ File Error: {error}")
        print("💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    @staticmethod
    def handle_permission_error(error: PermissionError, context: str = "") -> None:
        """Handle permission errors with specific suggestions."""
        suggestions = [
            "Check file/folder permissions",
            "Try running as administrator (Windows) or with sudo (Linux/Mac)",
            "Ensure the application has write access to the target directory",
            "Close any applications that might be using the file"
        ]
        
        ErrorHandler.log_error(error, f"Permission error in {context}")
        print(f"❌ Permission Error: {error}")
        print("💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    @staticmethod
    def handle_chess_error(error: Exception, context: str = "") -> None:
        """Handle chess-related errors with specific suggestions."""
        suggestions = [
            "Check if the chess position is valid",
            "Verify the FEN string is correct",
            "Ensure the move is legal",
            "Try resetting the game"
        ]
        
        ErrorHandler.log_error(error, f"Chess error in {context}")
        print(f"❌ Chess Error: {error}")
        print("💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    @staticmethod
    def handle_agent_error(error: Exception, agent_name: str = "Unknown") -> None:
        """Handle AI agent errors with specific suggestions."""
        suggestions = [
            f"Check if {agent_name} agent is properly implemented",
            "Verify agent configuration and dependencies",
            "Try using a different agent",
            "Check agent module files for syntax errors"
        ]
        
        ErrorHandler.log_error(error, f"Agent error for {agent_name}")
        print(f"❌ Agent Error ({agent_name}): {error}")
        print("💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    @staticmethod
    def handle_heatmap_error(error: Exception, context: str = "") -> None:
        """Handle heatmap generation errors with specific suggestions."""
        suggestions = [
            "Install R or Wolfram Engine for heatmap generation",
            "Check if required R packages are installed",
            "Verify heatmap script files are present and valid",
            "Try generating heatmaps manually first"
        ]
        
        ErrorHandler.log_error(error, f"Heatmap error in {context}")
        print(f"❌ Heatmap Error: {error}")
        print("💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")


def safe_execute(func, *args, **kwargs):
    """Safely execute a function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ErrorHandler.log_error(e, f"Error in {func.__name__}")
        return None


def safe_execute_with_fallback(func, fallback_value, *args, **kwargs):
    """Safely execute a function with a fallback value."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ErrorHandler.log_error(e, f"Error in {func.__name__}")
        return fallback_value