import asyncio
from bleak import BleakClient, BleakScanner, BleakError

import dwarf_python_api.proto.ble_pb2 as ble
from dwarf_ble_connect.lib.dwarf_protocol_ble import analyze_packet_ble, get_wifi_config_message, set_wifi_STA_message
import dwarf_python_api.lib.my_logger as log

# UUIDs for the DWARF services and characteristics
DWARF_CHARACTERISTIC_UUID = "00009999-0000-1000-8000-00805f9b34fb"
DWARFII_SERVICE_UUID = "0000daf2-0000-1000-8000-00805f9b34fb"
DWARF3_SERVICE_UUID = "0000daf3-0000-1000-8000-00805f9b34fb"

async def discover_dwarf_devices():
    # Discover nearby devices (with a timeout of 15 seconds)
    log.info("Scanning for DWARF devices...")
    connection_state = {
        "step" : "1",
        "dwarf_devices":None,
        "error": None,
    }

    try:
        devices = await BleakScanner.discover(timeout=15)
    
        # Filter devices that start with "DWARF"
        dwarf_devices = [d for d in devices if d.name and d.name.startswith("DWARF")]

        connection_state["dwarf_devices"] = dwarf_devices 

    except Exception as error:
        connection_state["error"] = str(error)
        log.error(f"An error occurred: {error}")

    return connection_state

async def select_dwarf_device(dwarf_devices):

    connection_state = {
        "step" : "2",
        "dwarf_device" :None,
        "error": None,
    }

    selected_device = None
    if not dwarf_devices:
        log.notice("No DWARF devices found.")

    elif len(dwarf_devices) == 1:
        # If only one device is found, automatically select it
        selected_device = dwarf_devices[0]
        log.notice(f"Automatically selected device: {selected_device.name} ({selected_device.address})")
        connection_state["dwarf_device"] = selected_device
    else:
        connection_state["step"] = "3"
        connection_state["dwarf_devices"] = dwarf_devices
        for i, d in enumerate(dwarf_devices):
            dwarf_device_i = "dwarf_devices"+ str(i+1)
            connection_state[dwarf_device_i] = d.name

    return connection_state

async def choice_dwarf_device(dwarf_devices, choice):

    connection_state = {
        "step" : "2",
        "dwarf_device" :None,
        "error": None,
    }

    if not dwarf_devices:
        log.notice("No DWARF devices found.")

    elif choice > 0 or choice <= len(dwarf_devices):

        selected_device = dwarf_devices[choice - 1]
        connection_state["dwarf_device"] = selected_device
        log.notice(f"Selected device: {selected_device.name} ({selected_device.address})")

    return connection_state

async def connect_to_bluetooth_device(dwarf_device = None, Bluetooth_PWD = None, Wifi_SSID = None, Wifi_PWD = None):
    """Scan for DWARF Bluetooth devices and connect."""
    IsFirstStepOK = False

    # Object to hold shared data
    connection_state = {
        "step" : "4",
        "is_connected": False,
        "connecting": True,
        "error": None,
        "device_dwarf_id": None,
        "device_dwarf_name": None,
        "device_dwarf_uid": None,
        "ip_address": None,
    }
    data_state = {
       "IsFirstStepOK" : False,
       "deviceDwarf" : None,
       "characteristicDwarf" : None,
    }

    async def handle_value_changed(sender, data):
        """Callback for when a characteristic value changes."""
        log.debug(f"Notification from {sender}: {data}")

        configValue = "";

        try:
            if data:
                configValue = analyze_packet_ble(data)

            if not data_state["IsFirstStepOK"] and configValue:
                result_data = configValue

                if 'cmd' not in result_data or result_data['cmd'] != 1:
                    log.debug("Ignore Frame Received: cmd=", result_data.get('cmd'))
                elif 'code' in result_data and result_data['code'] != 0:
                    log.error(
                        f"Error get Config: {result_data['code']}"
                    )
                    connection_state["error"] = f"Error get Config: {result_data['code']} "
                    await action_disconnect(data_state["deviceDwarf"], data_state["characteristicDwarf"])
                elif result_data.get('state') == 0 and Wifi_SSID and Wifi_PWD:
                    data_state["IsFirstStepOK"] = True
                    connection_state["error"] = "Pending.. "
                    if (result_data.get('ip') == "192.168.88.1" or
                      result_data.get('ssid', '').startswith("DWARF3_")) and Wifi_SSID and Wifi_PWD:
                        log.info("Load WiFi configuration (1)...")
                        data_state["IsFirstStepOK"] = True
                        connection_state["error"] = "Pending.. "
                        bufferSetWifiSta = set_wifi_STA_message(0, Bluetooth_PWD, Wifi_SSID, Wifi_PWD)
                    else:
                        log.info("Load WiFi configuration...")
                        bufferSetWifiSta = set_wifi_STA_message(1, Bluetooth_PWD, Wifi_SSID, Wifi_PWD)
                    await data_state["deviceDwarf"].write_gatt_char(DWARF_CHARACTERISTIC_UUID, bufferSetWifiSta)
                elif result_data.get('state') != 2:
                    log.error(
                        "Error WiFi configuration not Completed! Restart it and Use the mobile App."
                    )
                    connection_state["error"] = "Error WiFi configuration not Completed! Restart it and Use the mobile App."
                    await action_disconnect(data_state["deviceDwarf"], data_state["characteristicDwarf"])
                elif result_data.get('wifi_mode') != 2:
                    log.error(
                        "Error STA MODE not Configured! Restart it and Use the mobile App."
                    )
                    connection_state["error"] = "Error STA MODE not Configured! Restart it and Use the mobile App."
                    await action_disconnect(data_state["deviceDwarf"], data_state["characteristicDwarf"])
                elif (result_data.get('ip') == "192.168.88.1" or
                  result_data.get('ssid', '').startswith("DWARF3_")) and Wifi_SSID and Wifi_PWD:
                    log.info("Load WiFi configuration (2)...")
                    data_state["IsFirstStepOK"] = True
                    connection_state["error"] = "Pending.. "
                    bufferSetWifiSta = set_wifi_STA_message(0, Bluetooth_PWD, Wifi_SSID, Wifi_PWD)
                    await data_state["deviceDwarf"].write_gatt_char(DWARF_CHARACTERISTIC_UUID, bufferSetWifiSta)
                elif (result_data.get('ssid') and result_data.get('psd') and
                  Wifi_SSID and Wifi_PWD):
                    log.info("Load WiFi configuration (3)...")
                    data_state["IsFirstStepOK"] = True
                    connection_state["error"] = "Pending.. "
                    bufferSetWifiSta = set_wifi_STA_message(
                        0, Bluetooth_PWD, Wifi_SSID, Wifi_PWD
                    )
                    await data_state["deviceDwarf"].write_gatt_char(DWARF_CHARACTERISTIC_UUID, bufferSetWifiSta)
                else:
                    data_state["IsFirstStepOK"] = True
                    connection_state["error"] = "Pending.. "
                    bufferSetWifiSta = set_wifi_STA_message(
                        0, Bluetooth_PWD, result_data.get('ssid'), result_data.get('psd')
                    )
                    await data_state["deviceDwarf"].write_gatt_char(DWARF_CHARACTERISTIC_UUID, bufferSetWifiSta)

            elif data_state["IsFirstStepOK"] and configValue:
                data_state["IsFirstStepOK"] = False
                result_data = configValue

                if 'cmd' not in result_data or result_data['cmd'] != 3:
                    log.debug("Ignore Frame Received: cmd=", result_data.get('cmd'))
                elif 'code' in result_data and result_data['code'] != 0:
                    log.error(
                        f"Error set WifiSTA: {result_data['code']}"
                    )
                    connection_state["error"] = f"Error set WifiSTA: {result_data['code']}"
                    await action_disconnect(data_state["deviceDwarf"], data_state["characteristicDwarf"])
                elif 'code' in result_data and result_data['code'] == 0:
                    log.success("Connected with IP:", result_data.get('ip'))
                    connection_state["error"] = None
                    connection_state["is_connected"] = True
                    connection_state["ip_address"] = result_data.get('ip')
                else:
                    log.error(
                        f"Error set WifiSTA: unknown Error"
                    )
                    connection_state["error"] = f"Error set WifiSTA: unknown Error"
                    await action_disconnect(data_state["deviceDwarf"], data_state["characteristicDwarf"])
    
        except Exception as error:
            connection_state["connecting"] = False
            connection_state["is_connected"] = False
            connection_state["error"] = str(error)
            log.error(f"An error occurred: {error}")

    def onDisconnected(client):
        log.info("> Bluetooth Device disconnected");
        log.info(f"Device {client.address} has disconnected.")
        connection_state["connecting"] = False
        connection_state["is_connected"] = False
        connection_state["error"] = "Device disconnected unexpectedly."

    async def action_disconnect(deviceDwarf=None, characteristicDwarf=None):
        try:
            # Disconnect Bluetooth
            if characteristicDwarf:
                # Stop notifications
                await deviceDwarf.stop_notify(characteristicDwarf)

            if deviceDwarf:
                # Remove event listener for disconnection
                deviceDwarf.set_disconnected_callback(None)
                # Disconnect from GATT server if available
                if hasattr(deviceDwarf, 'gatt') and deviceDwarf.gatt:
                    await deviceDwarf.gatt.disconnect()

            log.info("Disconnected from DWARF device.")
            connection_state["connecting"] = False
            connection_state["is_connected"] = False

        except Exception as error:
            log.error(f"An error occurred during disconnection: {error}")
            connection_state["error"] = str(error)
            connection_state["connecting"] = False
            connection_state["is_connected"] = False

    try:
        data_state["IsFirstStepOK"] = False
        data_state["deviceDwarf"] = None
        data_state["characteristicDwarf"] = None

        if dwarf_device == None:
            connection_state["connecting"] = False
            return connection_state

        # Connect to the DWARF device
        connection_state["device_dwarf_uid"] = dwarf_device.name.replace("DWARF3_","").replace("DWARF_","")
        log.info(f"Connecting to DWARF device: {dwarf_device.name} {dwarf_device.address}...")

        async with BleakClient(dwarf_device.address) as client:
            log.info(f"Connected to {dwarf_device.name} ({dwarf_device.address})")
            data_state["deviceDwarf"] = client

            # Check for services
            service_uuid = None
            service_dwarf = None

            # Use the `services` property instead of `get_services()`
            services = client.services  # Fetch the services
            if services is None:  # This ensures services are fetched if not already populated
                await client.get_services()
                services = client.services

            for service in client.services:

              if DWARFII_SERVICE_UUID == service.uuid:
                service_uuid = DWARFII_SERVICE_UUID
                connection_state["device_dwarf_id"] = 1
                connection_state["device_dwarf_name"] = "Dwarf II"
                service_dwarf = service
              elif DWARF3_SERVICE_UUID == service.uuid:
                service_uuid = DWARF3_SERVICE_UUID
                connection_state["device_dwarf_id"] = 2
                connection_state["device_dwarf_name"] = "Dwarf3"
                service_dwarf = service

            if not service_uuid:
                raise ValueError("Could not find DWARF services on device.")

            log.debug(f"Connected to {connection_state['device_dwarf_name']}. Service UUID: {service_uuid}")

            # Find the specific characteristic
            for char in service_dwarf.characteristics:
                log.debug(f"[char] {char.uuid} (Handle: {char.handle})")

                # Check if this is the characteristic we are looking for
                if char.uuid == DWARF_CHARACTERISTIC_UUID:
                    data_state["characteristicDwarf"] = char
                    break

            # If the characteristic is not found, raise an error
            if not data_state["characteristicDwarf"]:
                raise ValueError("Bluetooth characteristic not found.")

            # Proceed with interacting with the characteristic
            # For example, reading or writing to the characteristic
            log.debug(f"Found characteristic: {data_state['characteristicDwarf'].uuid}")

            # Start notifications
            await client.start_notify(DWARF_CHARACTERISTIC_UUID, handle_value_changed)

            # Write WiFi configuration
            wifi_config = get_wifi_config_message(Bluetooth_PWD)
            
            await client.write_gatt_char(DWARF_CHARACTERISTIC_UUID, wifi_config)
            log.info("Sent WiFi configuration...")

            await asyncio.sleep(2) 

    except Exception as error:
        connection_state["connecting"] = False
        connection_state["is_connected"] = False
        connection_state["error"] = str(error)
        log.error(f"Error: {error}")

    return connection_state

