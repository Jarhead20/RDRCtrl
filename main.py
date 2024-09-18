import tkinter as tk
from tkinter import ttk
import socket
import threading

# Define unique IP addresses for each Pi
PI1_IP = '192.168.0.211'  # Replace with the actual IP address of Pi 1
PI2_IP = '192.168.0.19'   # Replace with the actual IP address of Pi 2
PORT = 5005
SERVER_IP = '192.168.0.225'
BUFFER_SIZE = 1024

class ScriptManager:
    def __init__(self, master, script_name, pi_ip):
        self.master = master
        self.pi_ip = pi_ip
        self.status = tk.StringVar(value="Unknown")
        self.script_name = tk.StringVar(value=script_name)
        self.refresh_interval = tk.IntVar(value=5)  # Default refresh interval in seconds

        # Frame for each script
        self.frame = ttk.Frame(master)
        self.frame.pack(pady=5, fill='x')

        # Entry for the script name (editable)
        self.script_entry = ttk.Entry(self.frame, textvariable=self.script_name, width=50)
        self.script_entry.grid(row=0, column=0, padx=5, columnspan=4)

        # Status display (initial color is black)
        self.status_label = ttk.Label(self.frame, textvariable=self.status, width=50)
        self.status_label.grid(row=1, column=0, padx=5, columnspan=4)

        # Buttons (placed below the script name)
        self.start_button = ttk.Button(self.frame, text="Start", command=self.start_script)
        self.start_button.grid(row=2, column=0, padx=5, pady=5)

        self.stop_button = ttk.Button(self.frame, text="Stop", command=self.stop_script)
        self.stop_button.grid(row=2, column=1, padx=5, pady=5)

        self.refresh_button = ttk.Button(self.frame, text="Refresh", command=self.refresh_script)
        self.refresh_button.grid(row=2, column=2, padx=5, pady=5)

        # Refresh interval configuration
        self.interval_entry = ttk.Entry(self.frame, textvariable=self.refresh_interval, width=5)
        self.interval_entry.grid(row=2, column=3, padx=5, pady=5)

        self.refresh_button = ttk.Button(self.frame, text="Set Interval", command=self.set_interval)
        self.refresh_button.grid(row=2, column=4, padx=5, pady=5)

        # Separator between each script section
        self.separator = ttk.Separator(master, orient='horizontal')
        self.separator.pack(fill='x', pady=5)

        # Start the status update loop
        self.update_status()

    def send_command(self, command):
        """Send a command to the server using the text from the input field and return the response."""
        script_command = self.script_name.get()  # Retrieve the latest script command from the input field
        print(f"Sending command: {command} with script command: {script_command}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # Set a timeout for socket operations
                s.connect((self.pi_ip, PORT))
                s.sendall(f"{command}:{script_command}".encode())  # Use the current script command
                response = s.recv(BUFFER_SIZE).decode()
                return response
        except Exception as e:
            error_message = f"Error: {e}"
            print(error_message)
            return error_message

    def start_script(self):
        threading.Thread(target=self._run_command_in_thread, args=('start',)).start()

    def stop_script(self):
        threading.Thread(target=self._run_command_in_thread, args=('stop',)).start()

    def refresh_script(self):
        threading.Thread(target=self._run_command_in_thread, args=('status',)).start()

    def _run_command_in_thread(self, command):
        """Runs the command in a separate thread to avoid blocking the GUI."""
        response = self.send_command(command)
        self.update_status_label(response)
        self.status.set(response)

    def update_status_label(self, status_text):
        """Update the status label color based on the status."""
        if status_text.endswith("Not Running"):
            self.status_label.config(foreground="red")
        elif status_text.endswith("Running"):
            self.status_label.config(foreground="green")
        else:
            self.status_label.config(foreground="black")  # Default color for unknown status

    def update_status(self):
        """Periodically update the script status in a separate thread."""
        threading.Thread(target=self._run_command_in_thread, args=('status',)).start()
        # Schedule the next status update
        self.master.after(self.refresh_interval.get() * 1000, self.update_status)

    def set_interval(self):
        """Update the refresh interval based on user input."""
        try:
            interval = int(self.interval_entry.get())
            if interval > 0:
                self.refresh_interval.set(interval)
        except ValueError:
            print("Invalid interval, please enter a positive integer.")

# Section for each Pi
class PiSection:
    def __init__(self, master, pi_name, pi_ip, scripts):
        self.master = master
        self.pi_name = pi_name
        self.pi_ip = pi_ip
        self.scripts = scripts

        # Frame for each Pi section
        self.frame = ttk.LabelFrame(master, text=pi_name)
        self.frame.pack(padx=10, pady=10, fill='x')

        # Create ScriptManager instances for each script
        for script_name in scripts:
            ScriptManager(self.frame, script_name, self.pi_ip)

# Main application window
class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Script Manager Dashboard")

        # Define scripts for each Pi with their respective ports
        pi1_scripts = [("python /home/pi/camStreamer.py --ip {0} --port {1}".format(SERVER_IP, 5000)), 
                       ("python /home/pi/motor.py --port {0}".format(5002)),
                       ("python /home/pi/otos.py --ip {0} --port {1}".format(SERVER_IP, 5003))]
        pi2_scripts = [("python /home/rightpi/camStreamer.py --ip {0} --port {1}".format(SERVER_IP, 5001))]

        # Create sections for each Pi
        PiSection(self, "Pi 1", PI1_IP, pi1_scripts)
        PiSection(self, "Pi 2", PI2_IP, pi2_scripts)

if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
