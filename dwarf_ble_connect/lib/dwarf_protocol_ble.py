import dwarf_python_api.proto.protocol_pb2 as protocol
import dwarf_python_api.proto.ble_pb2 as ble
import dwarf_python_api.lib.my_logger as log

# Function to calculate CRC16
def calculate_crc16(buffer):
    crc = 0xffff
    for byte in buffer:
        crc ^= byte
        for _ in range(8):
            odd = crc & 0x0001
            crc >>= 1
            if odd:
                crc ^= 0xa001
    return crc

# Function to get an array from a hex string
def get_array_from_hex_string(data):
    result = []
    while data:
        x = data[:2]
        z = int(x, 16)  # hex string to int
        z = (z + 0xff + 1) & 0xff  # twos complement
        result.append(z)
        data = data[2:]
    return result

# Function to get decimal to hex string
def get_decimal_to_hex16b_string(number):
    # Constrain the number to 16 bits (twos complement)
    x = number & 0xffff  # Mask to 16 bits
    # Convert to hexadecimal and zero-fill to 4 digits
    result = hex(x)[2:].zfill(4)
    return result

# Function to create a Bluetooth packet
def create_packet_ble(cmd, message):
    frame_header = 0xaa
    frame_end = 0x0d
    protocol_id = 0x01
    package_id = 0x00
    total_id = 0x01
    reserved1_id = 0x00
    reserved2_id = 0x00
    message_buffer = message.SerializeToString()

    buffer = [frame_header, protocol_id, cmd, package_id, total_id, reserved1_id, reserved2_id]

    # Data length
    data_length = len(message_buffer)
    log.debug(f"message buffer = {buffer}")
    log.debug(f"data_length = {data_length}")
    data_length_hexa = get_decimal_to_hex16b_string(data_length)
    data_length_array = get_array_from_hex_string(data_length_hexa)
    buffer.extend(data_length_array)

    # Data
    buffer.extend(message_buffer)

    # CRC16
    crc16 = calculate_crc16(buffer)
    crc16_array = get_array_from_hex_string(get_decimal_to_hex16b_string(crc16))
    buffer.extend(crc16_array)
    buffer.append(frame_end)

    log.debug(f"buffer = {buffer}")
    return bytes(buffer)

# Function to analyze the Bluetooth packet
def analyze_packet_ble(message_buffer, input_data=False):
    if isinstance(message_buffer, (bytes, bytearray)):
        data_rcv = bytearray(message_buffer)
        log.debug(data_rcv)
    else:
        return {"text": ""}
    
    if len(data_rcv) < 12:
        log.error(f"analyzePacketBle error Decoding not enough data received! nb bytes: {len(data_rcv)}")
        return ""
    
    decoded_message = {}
    cmd = data_rcv[2]
    data_length = data_rcv[7] * 256 + data_rcv[8]
    data_buffer = data_rcv[9:9 + data_length] if data_length > 0 else bytearray()
    
    log.debug(f"receive input_data = {input_data}")
    log.debug(f"receive message cmd = {cmd}")
    log.debug(f"receive message data_length = {data_length}")

    # Analyze Data
    if input_data:
        response_message = decode_packet_ble_input(cmd, data_buffer)
        log.debug(f"Not all Data!>> {response_message}")
    else:
        response_message = decode_packet_ble(cmd, data_buffer)
        log.debug(f"Not all Data!>> {response_message}")
    
    # Fill in the default values
    decoded_message = fill_defaults_from_class(response_message)

    log.debug(f"End Analyze Packet >> {decoded_message}")
    return decoded_message

def fill_defaults_from_class(proto_instance):
    """
    Ensure all fields in the protobuf message instance are populated with their default values.

    :param proto_instance: The protobuf message instance.
    :return: A dictionary with all fields populated with defaults if not explicitly set.
    """
    from google.protobuf.json_format import MessageToDict

    # Convert to dictionary including unset fields with default values
    filled_message = MessageToDict(
        proto_instance,
        including_default_value_fields=True,  # Ensure default values are included
        preserving_proto_field_name=True      # Use field names as they appear in the proto definition
    )

    return filled_message

  ## BLE Class Command
  # cmd: 1: "ReqGetconfig", // Get WiFi configuration
  # cmd: 2: "ReqAp", // Configure WiFi AP mode
  # cmd: 3: "ReqSta", // Configure WiFi STA mode
  # cmd: 4: "ReqSetblewifi", // Configure BLE wifi
  # cmd: 5: "ReqReset", // Reset Bluetooth WiFi
  # cmd: 6: "ReqWifilist", // Get WiFi list
  # cmd: 7: "ReqGetsysteminfo", // Obtain device information
  # cmd: 8: "ReqCheckFile", // Check File

def get_wifi_config_message(bluetooth_pwd):
    # cmd: 1: "ReqGetconfig", // Get WiFi configuration
    ReqGetconfig_message = ble.ReqGetconfig ()
    ReqGetconfig_message.cmd = 1
    ReqGetconfig_message.ble_psd = bluetooth_pwd

    message_buffer = create_packet_ble(ReqGetconfig_message.cmd, ReqGetconfig_message)
    log.debug(f"message_buffer = {message_buffer}")

    # test deoding
    analyze_packet_ble(message_buffer, True)
    
    return message_buffer

def set_wifi_STA_message(auto_start, ble_psd, wifi_ssid, wifi_pwd):
    # cmd: 3: "ReqSta", // Configure WiFi STA mode
    ReqSta_message = ble.ReqSta ()
    ReqSta_message.cmd = 3
    ReqSta_message.auto_start = auto_start
    ReqSta_message.ble_psd = ble_psd 
    ReqSta_message.ssid = wifi_ssid
    ReqSta_message.psd = wifi_pwd

    return create_packet_ble(ReqSta_message.cmd, ReqSta_message)

# Function to decode the packet
def decode_packet_ble(cmd, buffer):
  # BLE Class Response
  # cmd: 4: "ResSetblewifi", // Configure BLE wifi
  # cmd: 5: "ResReset", // Reset Bluetooth WiFi
  # cmd: 6: "ResWifilist", // Get WiFi list
  # cmd: 7: "ResGetsysteminfo", // Obtain device information
  # cmd: 8: "ResCheckFile", // Check File

  # cmd: 0: "ResReceiveDataError", // Get Error
  if (cmd==0):
    ResReceiveDataError_message = ble.ResReceiveDataError()
    ResReceiveDataError_message.ParseFromString(buffer)
    log.debug("Decoding ReceiveDataError")
    log.debug(f"receive error code >> {ResReceiveDataError_message.code}")

    return ResReceiveDataError_message

  # cmd: 1: "ResGetconfig", // Get WiFi configuration
  if (cmd==1):
    ResGetconfig_message = ble.ResGetconfig()
    ResGetconfig_message.ParseFromString(buffer)
    log.debug("Decoding ResGetconfig")
    log.debug(f"receive error code >> {ResGetconfig_message.code}")

    return ResGetconfig_message

  # cmd: 2: "ResAp", // Configure WiFi AP mode
  if (cmd==2):
    ResAp_message = ble.ResAp()
    ResAp_message.ParseFromString(buffer)
    log.debug("Decoding ResAp")
    log.debug(f"receive error code >> {ResAp_message.code}")

    return ResAp_message

  # cmd: 3: "", // Configure WiFi STA mode
  if (cmd==3):
    ResSta_message = ble.ResSta()
    ResSta_message.ParseFromString(buffer)
    log.debug("Decoding ResSta")
    log.debug(f"receive error code >> {ResSta_message.code}")

    return ResSta_message
  return
  
# Function to decode the packet
def decode_packet_ble_input(cmd, buffer):

  # cmd: 1: "ReqGetconfig", // Get WiFi configuration
  if (cmd==1):
    ReqGetconfig_message = ble.ReqGetconfig()
    ReqGetconfig_message.ParseFromString(buffer)
    log.debug("Decoding ReqGetconfig")
    log.debug(f"receive cmd >> {ReqGetconfig_message.cmd}")
    log.debug(f"receive ble_psd >> {ReqGetconfig_message.ble_psd}")

    return ReqGetconfig_message

  return
