import ast
import re
import dwarf_python_api.proto.protocol_pb2 as protocol
import dwarf_python_api.proto.notify_pb2 as notify
import dwarf_python_api.proto.astro_pb2 as astro
import dwarf_python_api.proto.motor_control_pb2 as motor_control
import dwarf_python_api.proto.system_pb2 as system
import dwarf_python_api.proto.camera_pb2 as camera
# in notify
import dwarf_python_api.proto.base_pb2 as base__pb2

import dwarf_python_api.lib.my_logger as log

def getErrorCodeValueName(ErrorCode):

    try:
        ValueName = protocol.DwarfErrorCode.Name(ErrorCode)
    except ValueError:
        ValueName =""
        pass
    return ValueName

def getDwarfCMDName(DwarfCMDCode):

    try:
        ValueName = protocol.DwarfCMD.Name(DwarfCMDCode)
    except ValueError:
        ValueName =""
        pass
    return ValueName

def getAstroStateName(AstroStateCode):

    try:
        ValueName = notify.AstroState.Name(AstroStateCode)
    except ValueError:
        ValueName =""
        pass
    return ValueName

def fct_show_test(show_test = True, show_test1 = False, show_test2 = False):

    # TEST
    if (show_test):
      test_data = b'\x08\x01\x10\x01\x18\x01 \x03(\xfaU:\x1b\x09\xda\x01\xac\x95\xd6=\x04@\x11\xf7\x15R\x1b\xe8PV@\x1a\x07PolarisB$ff03aa11-5994-4857-a872-b41e8a3a5e51'
      WsPacket_message = base__pb2.WsPacket()
      WsPacket_message.ParseFromString(test_data)
      log.debug(">>")
      log.debug("decode START GOTO PACKET >>")
      log.debug("decode major_version >>", WsPacket_message.major_version) #1
      log.debug("decode minor_version >>", WsPacket_message.minor_version) #1
      log.debug("decode device_id >>", WsPacket_message.device_id) #1
      log.debug("decode module_id >>", WsPacket_message.module_id) #3
      log.debug("decode type >>", WsPacket_message.type) #0
      log.debug("decode cmd >>", WsPacket_message.cmd) #11002
      log.debug("decode type >>", WsPacket_message.type) #0
      log.debug("decode client_id >>", WsPacket_message.client_id) # ff03aa11-5994-4857-a872-b41e8a3a5e51

      ReqGotoDSO_message = astro.ReqGotoDSO()
      ReqGotoDSO_message.ParseFromString(WsPacket_message.data)
      log.debug("decode ra >>", ReqGotoDSO_message.ra)
      log.debug("decode dec >>", ReqGotoDSO_message.dec)
      log.debug("decode target_name >>", ReqGotoDSO_message.target_name)
      log.debug("<<")

#    test_response = b'\x00\x1a\x11\x00\x00\x02\x00\x1a\x11\x00\x00\x01\x08\x00E\x00\x00a\x04\xf9@\x00\x10\x06\x99\xf2\xc0\xa8\x00\xfb\x0a\x08\x00\x01&\xac\x96\x02\xc9\x18U\x186\xe7\xbd(P\x18\xff\xff\x8a\xe5\x00\x00\x827\x08\x01\x10\x01\x18\x01 \x09(\xebv0\x02:\x02\x08\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51'
    test_response = []
    test_response1 = []

    start_test1 = 0
    end_test1 = 9
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x04(\xc8e:\x06\x08\xe5\xff\xf5\xac\x06B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x04(\xc9e:\x0e\x0a\x0cEurope/ParisB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\x90NB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x02(\xe0]B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x03(\x81VB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\xb7NB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\xb4NB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\xb6NB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xe1v0\x02:\x02\x08\x14B%ff03aa11-5994-4857-a872-b411e8a3a5e51')

    start_test2 = 9
    end_test2 = 40
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xebv0\x02:\x02\x08\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xedv0\x02:\x08\x0a\x06\x08\x01\x10\x01(xB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xedv0\x02:\x0a\x0a\x08\x08\x01\x10\x01\x18\x01(\x18B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xedv0\x02:\x08\x0a\x06\x10\x01\x18\x08(\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x03(\xfaU0\x03:\x0b\x08\x8f\xa6\xff\xff\xff\xff\xff\xff\xff\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xebv0\x02:\x02\x08\x03B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xebv0\x02B$ff03aa11-5994-4857-a872-b41e8a3a5e51')

    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\x91N0\x03B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\xe1]0\x03B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\xe0]0\x03B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xe1v0\x02:\x02\x08HB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xe3v0\x02:\x04\x08\x11\x10;B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xe1v0\x02:\x02\x08IB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x04(\xc8e0\x03B$0000DAF2-0000-1000-8000-00805F9B3500')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xeav0\x02:\x04\x08\x04\x10\x01B$0000DAF2-0000-1000-8000-00805F9B3500')

    # Calibration
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xe1v0\x02:\x02\x08dB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x03(\xf8U0\x03:\x0b\x08\x94\xa6\xff\xff\xff\xff\xff\xff\xff\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xeav0\x02:\x04\x08\x04\x10\x06B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x03(\xf8U0\x03:\x0b\x08\x94\xa6\xff\xff\xff\xff\xff\xff\xff\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xeav0\x02:\x04\x08\x04\x10\x07B$ff03aa11-5994-4857-a872-b41e8a3a5e51')

    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x03(\xf8U0\x03:\x0b\x08\xca\x8e\xff\xff\xff\xff\xff\xff\xff\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x03(\xf8U0\x03:\x0b\x08\x94\xa6\xff\xff\xff\xff\xff\xff\xff\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xeav0\x02:\x04\x08\x04\x10\x08B$ff03aa11-5994-4857-a872-b41e8a3a5e51')

    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x03(\xf8U0\x03:\x0b\x08\x90\xa6\xff\xff\xff\xff\xff\xff\xff\x01B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xeav0\x02:\x04\x08\x03\x10\x08B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x09(\xeav0\x02:\x02\x10\x08B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    # Reboot
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\x91NB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x02(\xe1]B$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x05(\xc1iB$ff03aa11-5994-4857-a872-b41e8a3a5e51')
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x01(\xe0]0\x03B$ff03aa11-5994-4857-a872-b41e8a3a5e51');
    test_response.append(b'\x08\x01\x10\x01\x18\x01 \x05(\xc1i0\x03B$ff03aa11-5994-4857-a872-b41e8a3a5e51')


    WsPacket_message = base__pb2.WsPacket()
    start = 0
    end = -1
    if (show_test1 and show_test2 ):
        start = start_test1
        end = end_test2
        print("--1--")
    if (show_test1 and (not show_test2 )):
        start = start_test1
        end = end_test1
        print("--2--")
    if ((not show_test1) and show_test2 ):
        start = start_test2
        end = end_test2
        print("--3--")
   
    if (show_test1 or show_test2):
        log.debug("")
        log.debug("<< START TEST : {start}-{end} >>")
        log.debug("<< ", start)
        log.debug("<< ", end)
        for i in range(start, end):
            WsPacket_message.ParseFromString(test_response[i])
            log.debug("") 
            log.debug("decode  >>", i) #1
            log.debug("decode major_version >>", WsPacket_message.major_version) #1
            log.debug("decode minor_version >>", WsPacket_message.minor_version) #1
            log.debug("decode device_id >>", WsPacket_message.device_id) #1
            log.debug("decode module_id >>", WsPacket_message.module_id) #9
            log.debug("decode type >>", WsPacket_message.type) #2
            log.debug("decode cmd >>", WsPacket_message.cmd) #15211
            log.debug(f">> {getDwarfCMDName(WsPacket_message.cmd)}")
            if (WsPacket_message.type == 3)or(WsPacket_message.type == 2):
                if ((WsPacket_message.cmd == protocol.CMD_ASTRO_STOP_CALIBRATION) or (WsPacket_message.cmd == protocol.CMD_NOTIFY_STATE_ASTRO_CALIBRATION)):
                    ResNotifyStateAstroCalibration_message = notify.ResNotifyStateAstroCalibration()
                    ResNotifyStateAstroCalibration_message.ParseFromString(WsPacket_message.data)
                    log.debug("receive notification data >>", ResNotifyStateAstroCalibration_message.state)
                    log.debug("receive notification times >>", ResNotifyStateAstroCalibration_message.plate_solving_times)
                elif (WsPacket_message.cmd == protocol.CMD_ASTRO_START_CALIBRATION):
                    ComResponse_message = base__pb2.ComResponse()
                    ComResponse_message.ParseFromString(WsPacket_message.data)
                    log.debug("receive data >>", ComResponse_message.code)
                else :
                    ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                    ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)
                    log.debug("receive notification data >>", ResNotifyStateAstroGoto_message.state)

            log.debug("decode client_id >>", WsPacket_message.client_id) # ff03aa11-5994-4857-a872-b41e8a3a5e51

            # Result Goto
            if (WsPacket_message.cmd==11002): #CMD_ASTRO_START_GOTO_DSO
                ComResponse_message = base__pb2.ComResponse()
                ComResponse_message.ParseFromString(WsPacket_message.data)

                log.debug("receive data >>", ComResponse_message.code)

            # Notification Goto State
            if (WsPacket_message.cmd==15211):
                ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                log.debug("receive data >>", ResNotifyStateAstroGoto_message.state)

        log.debug("<< END TEST >>")
        log.debug("")

def octal_and_special_to_hex(string):
    # Mapping of special escape characters to their hexadecimal equivalents
    special_char_map = {
        r'\a': r'\x07',   # Bell/alert
        r'\b': r'\x08',   # Backspace
        r'\t': r'\x09',   # Horizontal tab
        r'\n': r'\x0a',   # Newline
        r'\v': r'\x0b',   # Vertical tab
        r'\f': r'\x0c',   # Form feed
        r'\r': r'\x0d',   # Carriage return
        r'\\': r'\x5c',   # Backslash
        r'\"': r'\x22',   # Double quote
        r"\'": r'\x27',   # Single quote
    }
    
    # Replace special characters with their hex equivalents
    for special_char, hex_value in special_char_map.items():
        string = string.replace(special_char, hex_value)

    # Regular expression to find octal escape sequences like \001 or \020
    octal_pattern = r'\\([0-3]?[0-7]{1,2})'
    
    # Function to replace octal escape sequence with hex equivalent
    def replace_octal(match):
        octal_value = match.group(1)
        # Convert octal to decimal, then to hexadecimal, and format as \xXX
        hex_value = '\\x{:02x}'.format(int(octal_value, 8))
        return hex_value

    # Substitute all octal escape sequences with hexadecimal equivalents
    return re.sub(octal_pattern, replace_octal, string)

def fct_decode_wireshark(user_frame, masked = False, user_maskedcode = ""):
    # Use regular expression to find the desired substring
    start = 0
    start_pattern = "\\x08\\x01\\x10"
    start_pattern2 = "\\x18"

    # search for
    # start_pattern = "\\x08\\x01\\x10\\x02\\x18\\x01"
    # start_pattern = "\\x08\\x01\\x10\\x01\\x18\\x01"
    # start_pattern = "\\x08\\x01\\x10\\x07\\x18\\x02"

    end_pattern1 = "b41e8a3a5e51"
    end_pattern2 =  "54975d6e950e"
    end_pattern2 =  "bf19d82b5462"

    # Test if Octal format : new in Wireshark
    user_frame_convert = octal_and_special_to_hex(user_frame)
    # Avoid pb with character '
    user_frame_convert = user_frame_convert.replace("'", '\\\'')
    print(f"Converted frame: \"{user_frame_convert}\"")

    end_index , extracted_strings = extracted_frames(user_frame_convert, start_pattern, start_pattern2, end_pattern1)

    if end_index == -1:
      end_index , extracted_strings = extracted_frames(user_frame_convert, start_pattern, start_pattern2, end_pattern2)
      if end_index == -1:
        end_index , extracted_strings = extracted_frames(user_frame_convert, start_pattern, start_pattern2, end_pattern3)

    print("=====================")
    for idx, frame in enumerate(extracted_strings):
      print(f"Extracted frame {idx+1}: \"{frame}\"")
      python_expression = "\'"+ frame + "\'"
      decode_packet(python_expression, masked, user_maskedcode)
      print("=====================")

def extracted_frames(user_frame, start_pattern, start_pattern2, end_pattern):
    start_len = len(start_pattern) + 4
    start_len_total = start_len + len(start_pattern2) + 4
    end_len = len(end_pattern)
    start_index = 0
    extracted_frames = []

    start_index = 0

    while start_index < len(user_frame):

        start_index = user_frame.find(start_pattern, start_index)
        if start_index == -1:
            break
        start_index2 = user_frame.find(start_pattern2, start_index+start_len)
        if start_index2 == -1:
            break
        print(f"start_index: \"{start_index}\"")
        print(f"start_index2: \"{start_index2}\"")

        # Find the end pattern after the current start pattern
        end_index = user_frame.find(end_pattern, start_index + start_len_total)
        print(f"end_index: \"{end_index}\"")
        if end_index == -1:
            break

        # Include the end pattern in the extracted string
        end_index += end_len

        # Extract the desired substring
        desired_frame = user_frame[start_index:end_index]
        extracted_frames.append(desired_frame)

        # Move the start index to continue searching
        start_index = end_index

    return end_index, extracted_frames

def decode_packet(python_expression, masked = False, user_maskedcode = ""):

  if (python_expression):

    print("decoding:")
    data_frame = ast.literal_eval(f'b{python_expression}') #user_frame.encode('latin-1')
    print(data_frame)

    if (masked):
        # do something
        util_data_frame = data_frame
    else:
        util_data_frame = data_frame

    WsPacket_message = base__pb2.WsPacket()
    WsPacket_message.ParseFromString(util_data_frame)
    log.info("") 
    log.info("decode  >>", data_frame) #1
    log.info("decode major_version >>", WsPacket_message.major_version) #1
    log.info("decode minor_version >>", WsPacket_message.minor_version) #1
    log.info("decode device_id >>", WsPacket_message.device_id) #1
    log.info("decode module_id >>", WsPacket_message.module_id) #9
    log.info("decode type >>", WsPacket_message.type) #2
    log.info("decode cmd >>", WsPacket_message.cmd) #15211
    log.info(f">> {getDwarfCMDName(WsPacket_message.cmd)}")
    if (WsPacket_message.type == 0):
        if ((WsPacket_message.cmd == protocol.CMD_SYSTEM_SET_MASTERLOCK)):
            ReqSetHostSlaveMode_message = system.ReqSetHostSlaveMode()
            ReqSetHostSlaveMode_message.ParseFromString(WsPacket_message.data)
            log.info("receive notification data >>", ReqSetHostSlaveMode_message)
            log.info("receive notification mode >>", ReqSetHostSlaveMode_message.mode)
        if ((WsPacket_message.cmd == protocol.CMD_CAMERA_WIDE_SET_GAIN)):
            ReqSetGain_message = camera.ReqSetGain()
            ReqSetGain_message.ParseFromString(WsPacket_message.data)
            log.info("receive notification data >>", ReqSetGain_message)
            log.info("receive notification index >>", ReqSetGain_message.index)
        if (WsPacket_message.cmd == protocol.CMD_CAMERA_WIDE_GET_ALL_PARAMS):
            common_param_instance = base__pb2.CommonParam()
            ResGetAllParams_message = camera.ResGetAllParams()
            ResGetAllParams_message.ParseFromString(WsPacket_message.data)
            res_get_all_params_data = {
                "all_params": [],
                "code": ResGetAllParams_message.code
            }
            for common_param_instance in ResGetAllParams_message.all_params:
                common_param_data = {
                    "hasAuto": common_param_instance.hasAuto,
                    "auto_mode": common_param_instance.auto_mode,
                    "id": common_param_instance.id,
                    "mode_index": common_param_instance.mode_index,
                    "index": common_param_instance.index,
                    "continue_value": common_param_instance.continue_value
                }
                res_get_all_params_data["all_params"].append(common_param_data)
            print(res_get_all_params_data)

    if (WsPacket_message.type == 1):
        ComResponse_message = base__pb2.ComResponse()
        ComResponse_message.ParseFromString(WsPacket_message.data)
        log.info("receive data >>", ComResponse_message.code)
    if (WsPacket_message.type == 3)or(WsPacket_message.type == 2):
        if ((WsPacket_message.cmd == protocol.CMD_ASTRO_STOP_CALIBRATION) or (WsPacket_message.cmd == protocol.CMD_NOTIFY_STATE_ASTRO_CALIBRATION)):
            ResNotifyStateAstroCalibration_message = notify.ResNotifyStateAstroCalibration()
            ResNotifyStateAstroCalibration_message.ParseFromString(WsPacket_message.data)
            log.info("receive notification data >>", ResNotifyStateAstroCalibration_message.state)
            log.info("receive notification times >>", ResNotifyStateAstroCalibration_message.plate_solving_times)
        elif (WsPacket_message.cmd == protocol.CMD_STEP_MOTOR_SERVICE_JOYSTICK):
            ResMotorPosition_message = motor_control.ResMotorPosition()
            ResMotorPosition_message.ParseFromString(WsPacket_message.data)
            log.info("receive notification id >>", ResMotorPosition_message.id)
            log.info("receive notification code >>", ResMotorPosition_message.code)
            log.info("receive notification position >>", ResMotorPosition_message.position)
        elif (WsPacket_message.cmd == protocol.CMD_ASTRO_START_CALIBRATION):
            ComResponse_message = base__pb2.ComResponse()
            ComResponse_message.ParseFromString(WsPacket_message.data)
            log.info("receive data >>", ComResponse_message.code)
        elif ((WsPacket_message.cmd == protocol.CMD_CAMERA_WIDE_SET_GAIN)):
            ReqSetGain_message = camera.ReqSetGain()
            ReqSetGain_message.ParseFromString(WsPacket_message.data)
            log.info("receive notification data >>", ReqSetGain_message)
            log.info("receive notification index >>", ReqSetGain_message.index)
        elif ((WsPacket_message.cmd == 15234)):
            ComResWithInt_message = base__pb2.ComResWithInt()
            ComResWithInt_message.ParseFromString(WsPacket_message.data)
            log.info("receive data >>", ComResWithInt_message.code)
            log.info("receive data >>", ComResWithInt_message.value)
            ComResWithDouble_message_message = base__pb2.ComResWithDouble()
            ComResWithDouble_message_message.ParseFromString(WsPacket_message.data)
            log.info("receive data >>", ComResWithDouble_message_message.value)
            ComResTest_message = notify.ResNotifyTimeLapseOutTime()  
            log.info("receive data >>", ComResTest_message.interval)
            log.info("receive data >>", ComResTest_message.out_time)
            log.info("receive data >>", ComResTest_message.total_time)
        elif ((WsPacket_message.cmd == protocol.CMD_NOTIFY_WIDE_SET_PARAM)):
            common_param_instance = base__pb2.CommonParam()
            ResGetAllParams_message = camera.ResGetAllParams()
            ResGetAllParams_message.ParseFromString(WsPacket_message.data)
            res_get_all_params_data = {
                "all_params": [],
                "code": ResGetAllParams_message.code
            }
            for common_param_instance in ResGetAllParams_message.all_params:
                common_param_data = {
                    "hasAuto": common_param_instance.hasAuto,
                    "auto_mode": common_param_instance.auto_mode,
                    "id": common_param_instance.id,
                    "mode_index": common_param_instance.mode_index,
                    "index": common_param_instance.index,
                    "continue_value": common_param_instance.continue_value
                }
                res_get_all_params_data["all_params"].append(common_param_data)
            print(res_get_all_params_data)
        elif (WsPacket_message.type == 3):
            ComResWithInt_message = base__pb2.ComResWithInt()
            ComResWithInt_message.ParseFromString(WsPacket_message.data)
            log.info("receive data >>", ComResWithInt_message.code)
            log.info("receive data >>", ComResWithInt_message.value)
        else :
            ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
            ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)
            log.info("receive notification all data >>", ResNotifyStateAstroGoto_message)
            log.info("receive notification data >>", ResNotifyStateAstroGoto_message.state)

    log.info("decode client_id >>", WsPacket_message.client_id) # ff03aa11-5994-4857-a872-b41e8a3a5e51
