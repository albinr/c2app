import tkinter as tk
import platform
from tkinter import ttk, messagebox
import requests
import subprocess


SERVER_URL = 'http://localhost:5000'

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("C2 Client")

        self.device_name = platform.node()
        self.os_version = f"{platform.system()} {platform.release()}"


        ttk.Label(root, text=f"Device Name: {self.device_name}").grid(column=0, row=0, padx=10, pady=5)
        ttk.Label(root, text=f"OS Version: {self.os_version}").grid(column=0, row=1, padx=10, pady=5)

        ttk.Button(root, text="Add Device", command=self.add_device).grid(column=0, row=2, columnspan=2, pady=10)

        ttk.Button(root, text="Ping Server", command=self.check_server).grid(column=0, row=3, columnspan=2, pady=10)

        ttk.Button(root, text="Quit", command=root.quit).grid(column=0, row=4, columnspan=2, pady=10)

    def add_device(self):
        try:
            data = {'device_name': self.device_name, 'os_version': self.os_version}
            response = requests.post(f"{SERVER_URL}/device", json=data)
            if response.status_code == 201:
                messagebox.showinfo("Success", "Device added successfully!")
            else:
                messagebox.showerror("Error", f"Failed to add device: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to the server: {e}")

    def check_server(self):
        try:
            response = requests.get(f"{SERVER_URL}/ping")
            if response.status_code == 200:
                messagebox.showinfo("Server Status", "Server is running")
            else:
                messagebox.showerror("Server Status", "Server is not available")
        except Exception as e:
            messagebox.showerror("Server Status", f"Error connecting to server: {e}")

    def get_installed_apps():
        try:
            result = subprocess.run(['wmic', 'product', 'get', 'name'], stdout=subprocess.PIPE)
            installed_apps = result.stdout.decode('utf-8').split('\n')
            print(installed_apps)
            return installed_apps
        except Exception as e:
            return [f"Error retrieving installed applications: {e}"]
    
    def get_geolocation():
        try:
            response = requests.get('https://ipinfo.io')
            location_data = response.json()
            return location_data['loc']  # Returns latitude, longitude as a string
        except Exception as e:
            return f"Error retrieving location: {e}"
        
    def send_heartbeat(self):
        try:
            response = requests.post(f"{SERVER_URL}/device/{self.device_id}/heartbeat")
            if response.status_code == 200:
                print("Heartbeat sent")
            else:
                print("Failed to send heartbeat")
        except:
            print("Server not available")

        # Send a heartbeat every 60 seconds
        self.root.after(60000, self.send_heartbeat)


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    app.check_server()
    app.get_installed_apps
    root.mainloop()
