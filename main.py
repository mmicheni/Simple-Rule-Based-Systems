#!/usr/bin/env python3
"""
Main entrypoint for the Personal Finance Advisor Knowledge-Based System (KBS).
Provides routing to CLI, Flask Web GUI, and Knowledge Acquisition modes.
"""

import sys
import argparse
from cli_advisor import run_cli_advisor
from acquisition import run_acquisition_flow

def launch_gui():
    print("Attempting to launch Flask Web GUI...")
    try:
        # Check if flask is installed
        import flask
        import threading
        import webbrowser
        import time
        from app import app

        def open_browser():
            time.sleep(1.2)  # Give the server a moment to start up
            webbrowser.open("http://127.0.0.1:5000")

        print("\n==========================================")
        print("   Flask Server Running on http://127.0.0.1:5000")
        print("==========================================\n")
        print("Opening dashboard in your default browser... (Press Ctrl+C to stop)")
        
        # Start a thread to open the browser automatically
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Run Flask server without reloader to prevent duplicate browser openings
        app.run(port=5000, debug=False)

    except ImportError:
        print("\n❌ Error: Flask is not installed.")
        print("Please install dependencies by running: pip install -r requirements.txt")
        print("Or run the zero-dependency CLI version using: python main.py --cli\n")
    except KeyboardInterrupt:
        print("\nGUI Server stopped.")

def main():
    parser = argparse.ArgumentParser(
        description="Personal Finance Advisor - Rule-Based Expert System",
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--cli", action="store_true", help="Launch the interactive CLI Advisor")
    group.add_argument("--gui", action="store_true", help="Launch the Flask Web Dashboard GUI")
    group.add_argument("--acquire", action="store_true", help="Launch the Knowledge Acquisition CLI")

    args = parser.parse_args()

    # If no flags are provided, show an interactive selection menu
    if not (args.cli or args.gui or args.acquire):
        print("=" * 60)
        print(" Welcome to the Personal Finance Advisor Expert System (KBS) ")
        print("=" * 60)
        print("Please select which mode you would like to run:")
        print(" 1. Command-Line Advisor Interface (CLI)")
        print(" 2. Graphical Dashboard Interface (GUI via Flask)")
        print(" 3. Knowledge Acquisition / Rule Builder (CLI)")
        print(" 4. Exit")
        print("=" * 60)
        
        while True:
            choice = input("Enter choice (1-4): ").strip()
            if choice == "1":
                args.cli = True
                break
            elif choice == "2":
                args.gui = True
                break
            elif choice == "3":
                args.acquire = True
                break
            elif choice == "4":
                print("Goodbye!")
                return
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")

    if args.cli:
        run_cli_advisor()
    elif args.gui:
        launch_gui()
    elif args.acquire:
        run_acquisition_flow()

if __name__ == "__main__":
    main()