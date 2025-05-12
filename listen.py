import win32file
import win32con
import os
import subprocess


# Start the subprocess
subprocess_args = ['./backend.exe']  # Replace with your own command and arguments
subprocess_instance = subprocess.Popen(subprocess_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

# Define the path to the file you want to monitor
file_path = "input.txt"

# Open the file
file_handle = win32file.CreateFile(
    file_path,
    win32con.GENERIC_READ,
    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
    None,
    win32con.OPEN_EXISTING,
    win32con.FILE_ATTRIBUTE_NORMAL,
    None,
)

# Read the initial content of the file
previous_content = win32file.ReadFile(file_handle, 4096)[1].decode("utf-8")

# Start monitoring the file for changes
change_detected = False

while True:
    # Read the current content of the file
    current_content = win32file.ReadFile(file_handle, 4096)[1].decode("utf-8")

    # Normalize line endings for comparison
    previous_content = previous_content.replace(os.linesep, "\n")
    current_content = current_content.replace(os.linesep, "\n")

    # Compare the current content with the previous content
    if current_content != previous_content and not change_detected:
        print("File content changed")
        print(current_content)
        # Send input to the subprocess
        user_input = f"{(current_content)}\n"
        subprocess_instance.stdin.write(user_input.encode())
        subprocess_instance.stdin.flush()
        
        change_detected = True
    elif current_content == previous_content:
        change_detected = False

    # Update the previous content with the current content
    previous_content = current_content

# Close the file handle
win32file.CloseHandle(file_handle)