#!/usr/bin/env python3
"""
Eye of God - Device Tracker
Main entry point for the project
"""

import sys
import subprocess


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                      👁️ EYE OF GOD                            ║
║                  Device Tracking & Recovery                   ║
╠══════════════════════════════════════════════════════════════╣
║  1. Find Lost Device    - Locate lost/stolen phones          ║
║  2. Device Tracker      - Track your devices (requires API)   ║
║  3. Exit                - Quit the program                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    choice = input("👉 Choose an option (1-3): ").strip()
    
    if choice == '1':
        print("\n🚀 Starting Find Lost Device...")
        import core.find_lost_device
        sys.exit(0)
    
    elif choice == '2':
        print("\n🚀 Starting Device Tracker CLI...")
        import core.device_tracker
        sys.exit(0)
    
    elif choice == '3':
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    else:
        print("\n❌ Invalid option. Please choose 1, 2, or 3.")
        sys.exit(1)


if __name__ == '__main__':
    main()
