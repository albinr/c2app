import tkinter as tk
import threading
import platform
import os
import uuid
from tkinter import ttk, messagebox, filedialog
import requests
import subprocess

SERVER_URL = 'http://localhost:5000'

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("C2 Client")

        self.device_name = platform.node()
        self.os_version = f"{platform.system()} {platform.release()}"
        self.hardware_id = self.load_hardware_id()
        self.geo_location = self.get_geolocation()
        self.installed_apps = self.get_installed_apps()

        self.status_frame = ttk.Frame(root)
        self.status_frame.grid(column=0, row=0, padx=10, pady=5)

        self.server_status_label = ttk.Label(self.status_frame, text="Server status:")
        self.server_status_label.grid(column=0, row=0)
        self.server_status_indicator = tk.Canvas(self.status_frame, width=20, height=20)
        self.server_status_indicator.grid(column=1, row=0, padx=5)

        self.device_status_label = ttk.Label(self.status_frame, text="Device connection:")
        self.device_status_label.grid(column=0, row=1)
        self.device_status_indicator = tk.Canvas(self.status_frame, width=20, height=20)
        self.device_status_indicator.grid(column=1, row=1, padx=5)

        ttk.Button(root, text="Run in background", command=self.minimize_in_background).grid(column=0, row=2, columnspan=2, padx=20, pady=10)
        ttk.Button(root, text="Upload a file", command=self.upload_file).grid(column=0, row=3, columnspan=2, padx=20, pady=10)
        ttk.Button(root, text="Quit", command=root.quit).grid(column=0, row=4, columnspan=2, padx=20, pady=10)

        self.print_all()
        self.check_server()
        self.add_device()
        self.send_heartbeat()

        threading.Thread(target=self.terminal_input_listener, daemon=True).start()

    def terminal_input_listener(self):
        while True:
            user_input = input("Type 'show' to restore the window: ")
            if user_input.lower() == "show":
                self.restore_window()

    def minimize_in_background(self):
        self.root.withdraw()
        print("Window is minimized. Type 'show' in the terminal to restore it.")

    def restore_window(self):
        self.root.deiconify()

    def add_device(self):
        try:
            data = {
                'device_name': self.device_name,
                'os_version': self.os_version,
                'hardware_id': self.hardware_id,
                'geo_location': self.geo_location,
                'installed_apps': self.installed_apps
            }
            response = requests.post(f"{SERVER_URL}/device", json=data)

            if response.status_code == 201:
                print("Device added!")
            elif response.status_code == 400 and 'already exists' in response.text:
                print("Device already exists.")
            else:
                messagebox.showerror("Error", f"Failed to add device: {response.text}")
        except Exception as e:
            print(f"Could not connect to the server: {e}")

    def execute_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error executing command: {e}"

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    files = {'file': file}
                    data = {'hardware_id': self.hardware_id}
                    response = requests.post(f"{SERVER_URL}/upload", files=files, data=data)

                    if response.status_code == 200:
                        messagebox.showinfo("Success", "File uploaded successfully!")
                    else:
                        messagebox.showerror("Error", f"Failed to upload file: {response.text}")
            except Exception as e:
                messagebox.showerror("Error", f"Error uploading file: {e}")

    def get_installed_apps(self):
        if platform.system() == 'Windows':
            try:
                result = subprocess.run(['wmic', 'product', 'get', 'name'], stdout=subprocess.PIPE, check=True)
                installed_apps = result.stdout.decode('utf-8').split('\n')
                return [app.strip() for app in installed_apps if app.strip()]
            except subprocess.CalledProcessError as e:
                return [f"Error getting apps from Windows: {e}"]
            except Exception as e:
                return [f"Unexpected error on Windows: {e}"]

        elif platform.system() == 'Linux':
            try:
                result = subprocess.run(['dpkg', '--get-selections'], stdout=subprocess.PIPE, check=True)
                installed_apps = result.stdout.decode('utf-8').split('\n')
                installed_apps = [app.split()[0] for app in installed_apps if "install" in app]
                return installed_apps[:10]
            except subprocess.CalledProcessError as e:
                return [f"Error getting apps from Linux: {e}"]
            except Exception as e:
                return [f"Unexpected error on Linux: {e}"]
        else:
            return ["Installed apps retrieval is not supported on this OS."]

    def get_geolocation(self):
        try:
            response = requests.get('https://ipinfo.io')
            location_data = response.json()
            return location_data['loc']
        except Exception as e:
            return f"Error retrieving location: {e}"

    def get_device_id(self):
        device_id = uuid.uuid1()
        return str(device_id)

    def load_hardware_id(self):
        hardware_id_file = 'hardware_id.txt'
        if os.path.exists(hardware_id_file):
            with open(hardware_id_file, 'r') as file:
                return file.read().strip()
        else:
            new_hardware_id = self.get_device_id()
            with open(hardware_id_file, 'w') as file:
                file.write(new_hardware_id)
            return new_hardware_id

    def send_heartbeat(self):
        def background_heartbeat():
            try:
                response = requests.post(f"{SERVER_URL}/device/heartbeat", json={"hardware_id": self.hardware_id})
                if response.status_code == 200:
                    print("Heartbeat sent")
                    self.root.after(0, lambda: self.update_device_status("green"))
                else:
                    print("Failed to send heartbeat")
                    self.root.after(0, lambda: self.update_device_status("red"))
            except:
                print("Server not available")
                self.root.after(0, lambda: self.update_device_status("red"))

        threading.Thread(target=background_heartbeat).start()
        self.root.after(30000, self.send_heartbeat)

    def check_server(self):
        def background_check():
            try:
                response = requests.get(f"{SERVER_URL}/ping")
                print("Server pinged")
                if response.status_code == 200:
                    self.root.after(0, lambda: self.update_server_status("green"))
                else:
                    self.root.after(0, lambda: self.update_server_status("red"))
            except Exception as e:
                self.root.after(0, lambda: self.update_server_status("red"))

        threading.Thread(target=background_check).start()
        self.root.after(60000, self.check_server)

    def update_server_status(self, color):
        self.server_status_indicator.delete("all")
        self.server_status_indicator.create_oval(5, 5, 20, 20, fill=color)

    def update_device_status(self, color):
        self.device_status_indicator.delete("all")
        self.device_status_indicator.create_oval(5, 5, 20, 20, fill=color)

    def print_all(self):
        print("Device name:       ", self.device_name)
        print("Device os:         ", self.os_version)
        print("Device hardware_id:", self.hardware_id)
        print("Device coordinates:", self.geo_location)
        print("Installed apps:    ", self.installed_apps)


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
