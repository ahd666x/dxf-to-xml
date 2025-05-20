"""Terminal user interface for DXF to XML converter."""
import os
import sys
import subprocess

class TerminalUI:
    """Handles user interaction in the terminal."""
    def __init__(self, config):
        self.config = config

    def run(self):
        """Runs the terminal UI for selecting and converting a single DXF file."""
        self._clear_screen()
        print("=========================================")
        print("  DXF to XML Converter for Wood Panels")
        print("=========================================")

        dxf_files = self._get_dxf_files_in_current_directory()

        if not dxf_files:
            print("\n❌ No DXF files found in the current directory.")
            print("Please place DXF files next to the script.")
            input("\nPress Enter to exit...")
            sys.exit()

        print("\nDXF files in current directory:")
        for i, file_name in enumerate(dxf_files, 1):
            print(f"{i}. {file_name}")

        print("\n0. Exit")
        
        while True:
            try:
                choice = input("Please enter the file number (1-{}) or 0 to exit: ".format(len(dxf_files)))
                if not choice.strip():  # Handle empty input
                    continue
                    
                choice = int(choice)
                if choice == 0:
                    print("\nExiting program.")
                    sys.exit(0)
                elif 1 <= choice <= len(dxf_files):
                    selected_file = dxf_files[choice - 1]
                    print(f"\n✅ Selected file: {selected_file}")
                    return selected_file
                else:
                    print(f"⚠️ Please enter a number between 0 and {len(dxf_files)}")
            except ValueError:
                print("⚠️ Please enter a valid number")

        choice = self._get_user_choice(len(dxf_files))
        return self._handle_user_choice(choice, dxf_files)

    def _get_dxf_files_in_current_directory(self):
        """Lists all files with .dxf extension in the current directory."""
        return [f for f in os.listdir('.') if os.path.isfile(f) and f.lower().endswith('.dxf')]

    def _get_user_choice(self, num_files):
        """Gets valid user input for file selection."""
        while True:
            try:
                user_input = input(f"Please enter the file number (1-{num_files}) or 0 to exit: ")
                choice = int(user_input)
                if 0 <= choice <= num_files:
                    return choice
                print("⚠️ Invalid number. Please enter a number from the list.")
            except ValueError:
                print("⚠️ Invalid input. Please enter a number.")

    def _handle_user_choice(self, choice, dxf_files):
        """Handles the user's file choice."""
        if choice == 0:
            print("\nExiting program.")
            sys.exit()
        
        selected_file = dxf_files[choice - 1]
        print(f"\n✅ Selected file: {selected_file}")
        return selected_file

    def _clear_screen(self):
        """Clears the terminal screen using subprocess or a fallback method."""
        try:
            command = 'cls' if os.name == 'nt' else 'clear'
            subprocess.run(command, shell=True, check=True, 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            print("\n" * 100)
