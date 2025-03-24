import asyncio
import threading
from bleak import BleakClient, BleakScanner, BleakError
from inputimeout import inputimeout, TimeoutOccurred

import dwarf_python_api.get_config_data
import dwarf_python_api.proto.ble_pb2 as ble
from dwarf_ble_connect.lib.dwarf_lib_ble import discover_dwarf_devices, select_dwarf_device, choice_dwarf_device, connect_to_bluetooth_device
import dwarf_python_api.lib.my_logger as log

import tkinter as tk
from tkinter import simpledialog, messagebox

async def connect_ble_dwarf_test(Bluetooth_PWD = "DWARF_12345678", Wifi_SSID="", Wifi_PWD = ""):
    log.info ("Start of Function connect_ble_dwarf")

    connection_state = None
    dwarf_devices = None
    dwarf_device = None

    # Keep scanning until a device is found or the user exits
    while not dwarf_devices:
        connection_state = await discover_dwarf_devices()
        dwarf_devices = connection_state.get("dwarf_devices")

        if not dwarf_devices:
            restart = input("No devices found. Do you want to restart the scan? (y/n): ").lower()
            if restart != 'y':
                log.info("Exiting...")
                break  # Exit the loop if user chooses not to restart

    if dwarf_devices:
        connection_state = await select_dwarf_device(dwarf_devices)
        dwarf_device = connection_state.get("dwarf_device")

    connection_state = await connect_to_bluetooth_device(dwarf_device,Bluetooth_PWD, Wifi_SSID, Wifi_PWD)
    log.info ("End of Function connect_ble_dwarf")
    log.info (f"{connection_state}")

def connect_ble_direct_dwarf(Bluetooth_PWD = "DWARF_12345678", Wifi_SSID="", Wifi_PWD = "", auto_select = ""):
    try:
        result = asyncio.run(connect_ble_dwarf(Bluetooth_PWD, Wifi_SSID, Wifi_PWD, auto_select))
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("Restarting the event loop...")
            restart_event_loop()
            return asyncio.run(connect_ble_dwarf(Bluetooth_PWD, Wifi_SSID, Wifi_PWD, auto_select))
        else:
            raise
    finally:
        return result  # Return the result to the caller

async def connect_ble_dwarf(Bluetooth_PWD = "DWARF_12345678", Wifi_SSID="", Wifi_PWD = "", auto_select = ""):

    status_bluetooth = False

    log.notice ("Start of Function connect_ble_dwarf")

    connection_state = None
    dwarf_devices = None
    dwarf_device = None

    max_retries = 2
    retry_count = 0

    # Keep scanning until a device is found or the user exits or max tests reached
    while not dwarf_devices and retry_count < max_retries:
        connection_state = await discover_dwarf_devices()
        log.notice (f"{connection_state}")
        dwarf_devices = connection_state.get("dwarf_devices")

        if not dwarf_devices:
            try:
                restart = inputimeout(prompt="No devices found. Do you want to restart the scan? (y/n): ", timeout=5).lower()
            except TimeoutOccurred:
                restart = 'y'

            if restart == 'n':
                log.info("Exiting...")
                break  # Exit the loop if user chooses not to restart

            retry_count += 1
            log.info(f"Retrying scan... Attempt {retry_count}/{max_retries}")
        else:
            break  # Exit loop if devices are found

    if retry_count == max_retries:
        log.info("Max retries reached. Exiting...")

    if dwarf_devices:
        connection_state = await select_dwarf_device(dwarf_devices)
        log.notice (f"{connection_state}")

        # none or one device found
        if connection_state and connection_state.get("step") == "2":
            dwarf_device = connection_state.get("dwarf_device")

        # more than one device found
        elif connection_state and connection_state.get("step") == "3":

            choice = None
            if auto_select :
              dwarf_devices = connection_state.get("dwarf_devices")
              for i, d in enumerate(dwarf_devices):
                  dwarf_device_i = "dwarf_devices"+ str(i+1)
                  if (auto_select == connection_state.get(dwarf_device_i)):
                    choice = i+1
                    log.notice(f"Auto select - {connection_state.get(dwarf_device_i)}")

            if auto_select == 0 or auto_select == "0":
                # Return the list of devices found to be chosen by the user in caller app
                choice = 0

            if choice is None:
                # If multiple devices are found, prompt the user to choose one
                log.notice("Multiple DWARF devices found:")
                dwarf_devices = connection_state.get("dwarf_devices")
                for i, d in enumerate(dwarf_devices):
                    dwarf_device_i = "dwarf_devices"+ str(i+1)
                    log.notice(f"{i+1} - {connection_state.get(dwarf_device_i)}")
        
            # Get the user's choice
            timeout_seconds = 10  # Timeout duration

            while choice is None:
                try:
                    user_input = inputimeout(prompt=f"Select a device (1-{len(dwarf_devices)}) or 0 to exit: ", timeout=timeout_seconds)
                    choice = int(user_input)

                    if choice < 0 or choice > len(dwarf_devices):
                        print("Invalid choice. Please select a valid number.")
                        choice = None
                except TimeoutOccurred:
                    print(f"\nNo input received in {timeout_seconds} seconds. Selecting device 1 automatically.")
                    choice = 1  # Default to selecting the first device
                except ValueError:
                    print("Invalid input. Please enter a number.")

            # Set the selected device
            if choice != 0:
                connection_state = await choice_dwarf_device(dwarf_devices, choice)
                log.notice (f"{connection_state}")
                dwarf_device = connection_state.get("dwarf_device")

        else:
            dwarf_device = None
            log.error ("Error occurs during selecting dwarf devices")

    if dwarf_device:
        connection_state = await connect_to_bluetooth_device(dwarf_device,Bluetooth_PWD, Wifi_SSID, Wifi_PWD)
        log.notice (f"{connection_state}")

    if connection_state.get("is_connected"):
       status_bluetooth = True
       try:
           dwarf_python_api.get_config_data.update_config_data('ip', connection_state.get('ip_address'))
           dwarf_python_api.get_config_data.update_config_data('dwarf_id', connection_state.get('device_dwarf_id'))
       except dwarf_python_api.get_config_data.ConfigFileNotFoundError as e:
           log.warning(f"Warning: {e}")

    log.notice ("End of Function connect_ble_dwarf")

    return status_bluetooth

def connect_ble_dwarf_win(Bluetooth_PWD="DWARF_12345678", Wifi_SSID="", Wifi_PWD=""):
    log.notice("Start of Function connect_ble_dwarf_win")

    connection_state = None
    dwarf_devices = None
    dwarf_device = None
    status_bluetooth = False

    try:
        from bleak.backends.winrt.util import allow_sta
        # tell Bleak we are using a graphical user interface that has been properly configured to work with asyncio
        allow_sta()
    except ImportError:
        pass

    try:

        # Create the root window
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        # Get screen width and height
        width = 380
        height = 100
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate position x and y
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Set the geometry of the window
        # Create a new window 
        new_window = tk.Toplevel(root)
        new_window.geometry(f"{width}x{height}+{x}+{y}")
        new_window.title("Dwarf Device Bluetooth Connection")
        new_window.wm_attributes("-topmost", 1)

        # Add a Label widget to show the message
        status_label = tk.Label(new_window, text="Searching for Dwarf Device...", font=("Arial", 12))
        status_label.pack(pady=40)

        # Function to stop the loop when the user closes the window
        def on_close():
            root.destroy()

        new_window.protocol("WM_DELETE_WINDOW", on_close)

        async def search_devices():
            nonlocal dwarf_devices, connection_state
            while not dwarf_devices:
                connection_state = await discover_dwarf_devices()
                dwarf_devices = connection_state.get("dwarf_devices")

                if not dwarf_devices:
                    restart = messagebox.askyesno("No Devices Found", "No devices found.\nDo you want to restart the scan?",parent=new_window)
                    if not restart:
                        log.info("Exiting...")
                        root.destroy()
                        return

            # Prompt for selection once the search is complete
            if dwarf_devices:
                # Change text
                status_label.config(text="Device(s) found...")
                new_window.update_idletasks()
                new_window.config(cursor="watch")
                connection_state = await select_dwarf_device(dwarf_devices)
                log.debug(connection_state)
                # None or one device found
                if connection_state and connection_state.get("step") == "2":
                    dwarf_device = connection_state["dwarf_device"]

                # More than one device found
                elif connection_state and connection_state.get("step") == "3":
                    selection = None
                    # Change text
                    status_label.config(text="select a Device...")
                    new_window.update_idletasks()
                    while selection is None:
                        selection = simpledialog.askinteger(
                            "Select a Device",
                            f"Multiple DWARF devices found:\n\n" +
                            "\n".join([f"{i+1}. {connection_state.get(f'dwarf_devices{i+1}')}" for i, d in enumerate(dwarf_devices)]) +
                            "\n\nEnter the number of the device to select (or 0 to exit):",
                            parent=new_window
                        )
                        if selection is None or selection < 0 or selection > len(dwarf_devices):
                            messagebox.showerror("Invalid Selection", "Please enter a valid number.", parent=new_window)
                            selection = None

                    if selection == 0:
                        log.info("Exiting...")
                        root.destroy()
                        return

                    # Set the selected device
                    new_window.config(cursor="watch")
                    connection_state = await choice_dwarf_device(dwarf_devices, selection)
                    dwarf_device = connection_state.get("dwarf_device")

                else:
                    # Close the window
                    root.destroy()
                    dwarf_device = None
                    messagebox.showerror("Error", "An error occurred while selecting DWARF devices.")

            if dwarf_device:
                status_label.config(text=f"Device {dwarf_device.name}, connecting...")
                new_window.update_idletasks()
                new_window.config(cursor="watch")
                connection_state = await connect_to_bluetooth_device(dwarf_device, Bluetooth_PWD, Wifi_SSID, Wifi_PWD)
                # Close the window
                root.destroy()
                if connection_state.get("is_connected"):
                    messagebox.showinfo("Success", f"{dwarf_device.name}\n\nSuccessfully connected\n\nwith ip: {connection_state.get('ip_address')}")
                else:
                    messagebox.showerror("Connection Failed", f"Error: {connection_state.get('error', 'Unknown error')}")
            else:
                # Close the window
                root.destroy()
                messagebox.showerror("Error", "No device selected.")

        def run_asyncio_loop():
             asyncio.run(search_devices())

        # Schedule the async function to start
        root.after(300, run_asyncio_loop)

        # Show the window
        new_window.deiconify()
        new_window.config(cursor="watch")

        # Run the Tkinter main loop
        root.mainloop()

    except Exception as error:
        log.error(f"An error occurred: {error}")

    finally:
        if connection_state.get("is_connected"):
            status_bluetooth = True
        try:
            dwarf_python_api.get_config_data.update_config_data('ip', connection_state.get('ip_address'))
            dwarf_python_api.get_config_data.update_config_data('dwarf_id', connection_state.get('device_dwarf_id'))
        except dwarf_python_api.get_config_data.ConfigFileNotFoundError as e:
            log.warning(f"Warning: {e}")

        log.notice (f"{connection_state}")
        log.notice("End of Function connect_ble_dwarf_win")
        return status_bluetooth;
