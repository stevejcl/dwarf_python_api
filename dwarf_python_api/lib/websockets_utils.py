import logging
import websockets.client
import asyncio
import json
import gzip
import dwarf_python_api.lib.my_logger as my_logger

import dwarf_python_api.proto.protocol_pb2 as protocol
import dwarf_python_api.proto.notify_pb2 as notify
import dwarf_python_api.proto.astro_pb2 as astro
import dwarf_python_api.proto.system_pb2 as system
import dwarf_python_api.proto.camera_pb2 as camera
import dwarf_python_api.proto.motor_control_pb2 as motor
# in notify
import dwarf_python_api.proto.base_pb2 as base__pb2

CONFIG_FILE = 'config.py'

def ws_uri(dwarf_ip):
    return f"ws://{dwarf_ip}:9900"

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

def getOperationStateName(OperationStateCode):

    try:
        ValueName = notify.OperationState.Name(OperationStateCode)
    except ValueError:
        ValueName =""
        pass
    return ValueName

def read_config_values(config_file):
    config_values = {}
    with open(config_file, 'r') as file:
        for line in file:
            # Ignore lines starting with '#' (comments) and empty lines
            if line.strip() and not line.strip().startswith('#'):
                key, value = line.strip().split('=')
                config_values[key.strip()] = value.strip().strip('"')  # Remove extra spaces and quotes
    return config_values

# Function to dynamically import and reload the config module
def get_current_data():
    config_values = read_config_values(CONFIG_FILE)
    return { 'ip' : config_values.get('DWARF_IP', ''), 'client_id' : config_values.get('CLIENT_ID', ''), 'calibration' : config_values.get('TEST_CALIBRATION', '')}


class StopClientException(Exception):
    pass

# new version protobuf enabled
# use a Class
class WebSocketClient:
    # use init just once or after error connecting
    Init_Send_TeleGetSystemWorkingState = True;

    def __init__(self, uri, client_id, message, command, type_id, module_id, ping_interval_task=5):
        self.websocket = False
        self.result = False
        self.uri = uri
        self.message = message
        self.command = command
        self.target_name = ""
        self.type_id = type_id
        self.module_id = module_id
        self.client_id = client_id
        self.ping_interval_task = ping_interval_task
        self.ping_task = None
        self.receive_task = None
        self.abort_tasks = None
        self.abort_timeout = 240
        self.stop_task = asyncio.Event()
        self.wait_pong = False
        self.stopcalibration = False
        self.takePhotoStarted = False
        self.AstroCapture = False
        self.takePhotoCount = 0
        self.takePhotoStacked = 0

        # TEST_CALIBRATION : Test Calibration Packet or Goto Packet
        # Test Mode : Calibration Packet => TEST_CALIBRATION = True
        # Production Mode GOTO Packet => TEST_CALIBRATION = False (default)
        self.modeCalibration = False

        data_config = get_current_data()
        if data_config['calibration'] != "":
            self.modeCalibration = True

    def initialize_once(self):
        if WebSocketClient.Init_Send_TeleGetSystemWorkingState:
            # Perform the initialization logic here
            print("Initializing...")
            
            # Set the class variable to True to indicate it has been initialized
            WebSocketClient.Init_Send_TeleGetSystemWorkingState = True
        else:
            print("Already initialized.")

    async def abort_tasks_timeout(self, timeout):

        try:
            count = 0
            self.abort_timeout = timeout
            await asyncio.sleep(0.02)
            while not self.stop_task.is_set() and count < self.abort_timeout:
                await asyncio.sleep(1)
                count += 1
        except Exception as e:
            # Handle other exceptions
            print(f"Timeout: Unhandled exception: {e}")
        finally:
            # Perform cleanup if needed
            if (not self.stop_task.is_set()):
                self.stop_task.set()
            await asyncio.sleep(0.02)
            print("TERMINATING TIMEOUT function.")

    async def send_ping_periodically(self):
        if not self.websocket:
            print("Error No WebSocket in send_ping_periodically")
            self.stop_task.set()

        try:
            await asyncio.sleep(2)
            while not self.stop_task.is_set():
                if self.websocket.state != websockets.protocol.OPEN:
                    print("WebSocket connection is not open.")
                    self.stop_task.set()
                elif (not self.wait_pong):
                    # Adjust the interval based on your requirements
                    print("Sent a PING frame")

                    # Python by defaut sends a frame OP_CODE Ping with 4 bytes
                    # The dwarf II respond by a frame OP_CODE Pong with no data
                    await self.websocket.ping("")
                    await self.websocket.send("ping")
                    # Signal to Receive to Wait the Pong Frame
                    self.wait_pong = True
                    await asyncio.sleep(self.ping_interval_task)
                else:
                    await asyncio.sleep(1)
            await asyncio.sleep(0.02)

        except websockets.ConnectionClosedOK as e:
            print(f'Ping: ConnectionClosedOK', e)
        except websockets.ConnectionClosedError as e:
            print(f'Ping: ConnectionClosedError', e)
        except asyncio.CancelledError:
            print("Ping Cancelled.")
        except Exception as e:
            # Handle other exceptions
            print(f"Ping: Unhandled exception: {e}")
            if (not self.stop_task.is_set()):
                self.stop_task.set()
            await asyncio.sleep(1)
        finally:
            # Perform cleanup if needed
            print("TERMINATING PING function.")

    async def receive_messages(self):
        if not self.websocket:
            print("Error No WebSocket in receive_messages")
            self.stop_task.set()

        try:
            await asyncio.sleep(2)
            while not self.stop_task.is_set() or self.wait_pong:
                await asyncio.sleep(0.02)
                print("Wait for frames")

                if self.websocket.state != websockets.protocol.OPEN:
                    print("WebSocket connection is not open.")
                    self.wait_pong = False
                    self.stop_task.set()
                else:
                    message = await self.websocket.recv()
                    if (message):
                        if isinstance(message, str):
                            print("Receiving...")
                            print(message)
                            if (message =="pong"):
                                 self.wait_pong = False
                        elif isinstance(message, bytes):
                            print("------------------")
                            print("Receiving...  data")

                            WsPacket_message = base__pb2.WsPacket()
                            WsPacket_message.ParseFromString(message)
                            my_logger.debug(f"receive cmd >> {WsPacket_message.cmd} type >> {WsPacket_message.type}")
                            my_logger.debug(f">> {getDwarfCMDName(WsPacket_message.cmd)}")
                            my_logger.debug(f"msg data len is >> {len(WsPacket_message.data)}")
                            print("------------------")

                            # CMD_NOTIFY_WS_HOST_SLAVE_MODE = 15223; // Leader/follower mode notification
                            if (WsPacket_message.cmd==protocol.CMD_NOTIFY_WS_HOST_SLAVE_MODE):
                                ResNotifyHostSlaveMode_message = notify.ResNotifyHostSlaveMode()
                                ResNotifyHostSlaveMode_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_NOTIFY_WS_HOST_SLAVE_MODE")
                                my_logger.debug(f"receive Host/Slave data >> {ResNotifyHostSlaveMode_message.mode}")

                                # Host = 0 Slave = 1
                                if (ResNotifyHostSlaveMode_message.mode == 1):
                                    my_logger.debug("SLAVE_MODE >> EXIT")
                                    # Signal the abort_tasks_timeout functions to stop in 15 s
                                    if (self.abort_timeout > 15 ):
                                        self.abort_timeout = 15
                                    self.result = "Error SLAVE MODE"
                                    await asyncio.sleep(1)
                                    print("Error SLAVE MODE detected")
                                else:
                                    print("Continue Decoding CMD_NOTIFY_WS_HOST_SLAVE_MODE")

                            # CMD_SYSTEM_SET_HOSTSLAVE_MODE = 13004; // Set HOST mode
                            if (WsPacket_message.cmd==protocol.CMD_SYSTEM_SET_HOSTSLAVE_MODE):
                                ResNotifyHostSlaveMode_message = notify.ResNotifyHostSlaveMode()
                                ResNotifyHostSlaveMode_message.ParseFromString(WsPacket_message.data)

                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_SYSTEM_SET_HOSTSLAVE_MODE")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CMD_SYSTEM_SET_HOSTSLAVE_MODE {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                    print(f"Error CMD_SYSTEM_SET_HOSTSLAVE_MODE CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                else :
                                    self.result = "ok"
                                    my_logger.debug("SET HOST OK >> EXIT")
                                    print("Success SET HOST OK OK")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    await asyncio.sleep(5)

                            # CMD_STEP_MOTOR_RUN = 14000; // Motor motion
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_RUN):
                                ResNotifyMotor_message = motor.ResMotor()
                                ResNotifyMotor_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_STEP_MOTOR_RUN")
                                my_logger.debug(f"receive id data >> {ResNotifyMotor_message.id}")
                                my_logger.debug(f"receive code data >> {ResNotifyMotor_message.code}")
                                print("Decoding CMD_STEP_MOTOR_RUN")

                                # OK = 0; // No Error
                                if (ResNotifyMotor_message.code != protocol.OK):
                                    if (ResNotifyMotor_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        my_logger.debug(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ResNotifyMotor_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CMD_STEP_MOTOR_RUN CODE {getErrorCodeValueName(ResNotifyMotor_message.code)}")
                                else :
                                    self.result = "ok"
                                    my_logger.debug("CMD_STEP_MOTOR_RUN OK >> EXIT")
                                    print("Success CMD_STEP_MOTOR_RUN")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    await asyncio.sleep(5)

                            # CMD_STEP_MOTOR_RUN_TO = 14001; // Motor motion to
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_RUN_TO):
                                ResNotifyMotorPosition_message = motor.ResMotorPosition()
                                ResNotifyMotorPosition_message.ParseFromString(WsPacket_message.data)

                                my_logger.debug(f"receive id data >> {ResNotifyMotorPosition_message.id}")
                                my_logger.debug(f"receive code data >> {ResNotifyMotorPosition_message.code}")
                                my_logger.debug(f"receive position data >> {ResNotifyMotorPosition_message.position}")
                                print("Decoding CMD_STEP_MOTOR_RUN_TO")

                                # OK = 0; // No Error
                                if (ResNotifyMotorPosition_message.code != protocol.OK):
                                    if (ResNotifyMotorPosition_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        my_logger.debug(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ResNotifyMotorPosition_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CMD_STEP_MOTOR_RUN_TO CODE {getErrorCodeValueName(ResNotifyMotorPosition_message.code)}")
                                else :
                                    self.result = "ok"
                                    my_logger.debug("CMD_STEP_MOTOR_RUN_TO OK >> EXIT")
                                    print("Success CMD_STEP_MOTOR_RUN_TO")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    await asyncio.sleep(5)

                            # CMD_STEP_MOTOR_RESET = 14003; // Motor CMD_STEP_MOTOR_RESET
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_RESET):
                                ResNotifyMotor_message = motor.ResMotor()
                                ResNotifyMotor_message.ParseFromString(WsPacket_message.data)

                                my_logger.debug(f"receive id data >> {ResNotifyMotor_message.id}")
                                my_logger.debug(f"receive code data >> {ResNotifyMotor_message.code}")
                                print("Decoding CMD_STEP_MOTOR_RESET")
                                # OK = 0; // No Error
                                if (ResNotifyMotor_message.code != protocol.OK):
                                    if (ResNotifyMotor_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        my_logger.debug(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ResNotifyMotor_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CMD_STEP_MOTOR_RESET CODE {getErrorCodeValueName(ResNotifyMotor_message.code)}")
                                else :
                                    self.result = "ok"
                                    my_logger.debug("CMD_STEP_MOTOR_RESET OK >> EXIT")
                                    print("Success CMD_STEP_MOTOR_RESET")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    await asyncio.sleep(5)

                            # CMD_STEP_MOTOR_SERVICE_JOYSTICK = 14006; // Motor motion to
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_SERVICE_JOYSTICK):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_STEP_MOTOR_SERVICE_JOYSTICK")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    if (ComResponse_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        my_logger.debug(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CMD_STEP_MOTOR_SERVICE_JOYSTICK CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                else :
                                    self.result = "ok"
                                    my_logger.debug("CMD_STEP_MOTOR_SERVICE_JOYSTICK OK >> EXIT")
                                    print("Success CMD_STEP_MOTOR_SERVICE_JOYSTICK")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    await asyncio.sleep(5)

                            # CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE = 10039; // // Get the working status of the whole machine
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error GET_SYSTEM_WORKING_STATE {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA_TELE_GET_SYSTEM_WORKING_STATE CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    print("Continue OK CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE")

                            # CMD_CAMERA_TELE_OPEN_CAMERA = 10000; // // Open the TELE Camera
                            elif (self.command==protocol.CMD_CAMERA_TELE_OPEN_CAMERA and WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_OPEN_CAMERA):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_CAMERA_TELE_OPEN_CAMERA")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # Signal the ping and receive functions to stop
                                self.stop_task.set()
                                self.result = ComResponse_message.code
                                await asyncio.sleep(5)
                                if (ComResponse_message.code != protocol.OK):
                                    print("Error CMD_CAMERA_TELE_OPEN_CAMERA")
                                else:
                                    print("OK CMD_CAMERA_TELE_OPEN_CAMERA")

                            # CMD_CAMERA_TELE_OPEN_CAMERA = 10000; // // Open the TELE Camera
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_OPEN_CAMERA):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_CAMERA_TELE_OPEN_CAMERA")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error GET_CAMERA_TELE_OPEN_CAMERA {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                    print(f"Error CMD_CAMERA_TELE_OPEN_CAMERA CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    print("Continue OK CMD_CAMERA_TELE_OPEN_CAMERA")

                            # CMD_FOCUS_START_ASTRO_AUTO_FOCUS = 15004; // Start astronomical autofocus
                            elif (WsPacket_message.cmd==protocol.CMD_FOCUS_START_ASTRO_AUTO_FOCUS):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_FOCUS_START_ASTRO_AUTO_FOCUS")
                                my_logger.debug(f"receive data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # Signal the ping and receive functions to stop
                                self.stop_task.set()
                                self.result = ComResponse_message.code
                                await asyncio.sleep(5)
                                if (ComResponse_message.code != protocol.OK):
                                    print("Error CMD_FOCUS_START_ASTRO_AUTO_FOCUS")
                                else:
                                    print("OK CMD_FOCUS_START_ASTRO_AUTO_FOCUS")
                            # CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS = 15005; // Stop Capture
                            elif (WsPacket_message.cmd==protocol.CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS")
                                my_logger.debug(f"receive data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # Signal the ping and receive functions to stop
                                self.stop_task.set()
                                self.result = ComResponse_message.code
                                await asyncio.sleep(5)
                                if (ComResponse_message.code != protocol.OK):
                                    print("Error CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS")
                                else:
                                    print("OK CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS")
                            # CMD_CAMERA_TELE_PHOTOGRAPH = 10002; // //  Take photos
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_PHOTOGRAPH):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_CAMERA_TELE_PHOTOGRAPH")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CMD_CAMERA_TELE_PHOTOGRAPH {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CMD_CAMERA_TELE_PHOTOGRAPH CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    print("Continue OK CMD_CAMERA_TELE_PHOTOGRAPH")

                            # CMD_CAMERA_TELE_PHOTOGRAPH = 10002; // //  End Take photos
                            elif (self.command==protocol.CMD_CAMERA_TELE_PHOTOGRAPH and WsPacket_message.cmd==protocol.CMD_NOTIFY_TELE_FUNCTION_STATE):
    
                                ResNotifyCamFunctionState_message = notify.ResNotifyCamFunctionState()
                                ResNotifyCamFunctionState_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_NOTIFY_TELE_FUNCTION_STATE")
                                my_logger.debug(f"receive notification data >> {ResNotifyCamFunctionState_message.state}")
                                my_logger.debug(f">> {getAstroStateName(ResNotifyCamFunctionState_message.state)}")

                                # ASTRO_STATE_IDLE = 0; // Idle => End
                                if (ResNotifyCamFunctionState_message.state == notify.ASTRO_STATE_IDLE):
                                    self.result = "ok"
                                    my_logger.debug("TAKE PHOTO OK >> EXIT")
                                    print("Success TAKE PHOTO OK")

                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                elif (ResNotifyCamFunctionState_message.state == notify.ASTRO_STATE_RUNNING):
                                    print("Starting CMD_CAMERA_TELE_PHOTOGRAPH")
                                else:
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ResNotifyCamFunctionState_message.state
                                    await asyncio.sleep(5)
                                    print("Error CMD_CAMERA_TELE_PHOTOGRAPH PROCESS STOP}")

                            # CMD_NOTIFY_STATE_ASTRO_CALIBRATION = 15210; // Astronomical calibration status
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_ASTRO_CALIBRATION):
                                ResNotifyStateAstroCalibration_message = notify.ResNotifyStateAstroCalibration()
                                ResNotifyStateAstroCalibration_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_NOTIFY_STATE_ASTRO_CALIBRATION")
                                my_logger.debug(f"receive notification data >> {ResNotifyStateAstroCalibration_message.state}")
                                my_logger.debug(f">> {getAstroStateName(ResNotifyStateAstroCalibration_message.state)}")
                                my_logger.debug(f"receive notification times >> {ResNotifyStateAstroCalibration_message.plate_solving_times}")

                                # ASTRO_STATE_IDLE = 0; // Idle state Only when Success or Previous Error
                                if (ResNotifyStateAstroCalibration_message.state == notify.ASTRO_STATE_IDLE):
                                    if (self.stopcalibration):
                                        self.result = protocol.CODE_ASTRO_CALIBRATION_FAILED
                                        await asyncio.sleep(5)
                                        print("Error CALIBRATION CODE_ASTRO_CALIBRATION_FAILED")
                                    else :
                                        self.result = "ok"
                                        my_logger.debug("ASTRO CALIBRATION OK >> EXIT")
                                        print("Success ASTRO CALIBRATION OK")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                else:
                                    print("Continue Decoding CMD_NOTIFY_STATE_ASTRO_CALIBRATION")

                            # CMD_NOTIFY_STATE_ASTRO_GOTO = 15211; // Astronomical GOTO status
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_ASTRO_GOTO):
                                ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                                ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_NOTIFY_STATE_ASTRO_GOTO")
                                my_logger.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                my_logger.debug(f">> {getAstroStateName(ResNotifyStateAstroGoto_message.state)}")

                            # CMD_NOTIFY_STATE_ASTRO_TRACKING = 15212; // Astronomical tracking status
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_ASTRO_TRACKING):
                                ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroTracking()
                                ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_NOTIFY_STATE_ASTRO_TRACKING")
                                my_logger.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                my_logger.debug(f">> {getAstroStateName(ResNotifyStateAstroGoto_message.state)}")
                                my_logger.debug(f"receive notification target_name >> {ResNotifyStateAstroGoto_message.target_name}")

                                # ASTRO_STATE_RUNNING = 1; // Running 
                                # Can be sending during CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE
                                # DSO or STELLAR
                                if ((self.command == protocol.CMD_ASTRO_START_GOTO_DSO) and ResNotifyStateAstroGoto_message.state == notify.ASTRO_STATE_RUNNING and ResNotifyStateAstroGoto_message.target_name == self.target_name):
                                    my_logger.debug("ASTRO GOTO : SAME CMD AND TARGET")
                                    my_logger.debug("ASTRO GOTO OK TRACKING >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                    print("Success ASTRO DSO GOTO TRACKING START")

                                if ((self.command == protocol.CMD_ASTRO_START_GOTO_SOLAR_SYSTEM) and ResNotifyStateAstroGoto_message.state == notify.ASTRO_STATE_RUNNING and ResNotifyStateAstroGoto_message.target_name == self.target_name):
                                    my_logger.debug("ASTRO GOTO : SAME CMD AND TARGET")
                                    my_logger.debug("ASTRO GOTO OK TRACKING >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                    print("Success ASTRO SOLAR GOTO TRACKING START")

                            # CMD_ASTRO_START_CALIBRATION = 11000; // Start calibration
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_CALIBRATION):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_ASTRO_START_CALIBRATION")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # CODE_ASTRO_CALIBRATION_FAILED = -11504; // Calibration failed
                                if (ComResponse_message.code == -11504):
                                    my_logger.debug("Error CALIBRATION >> EXIT")
                                    self.stopcalibration = True

                            # CMD_SYSTEM_SET_TIME = 13000; // Set the system time
                            elif (WsPacket_message.cmd==protocol.CMD_SYSTEM_SET_TIME):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_SYSTEM_SET_TIME")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # Signal the ping and receive functions to stop
                                self.stop_task.set()
                                self.result = ComResponse_message.code
                                await asyncio.sleep(5)
                                if (ComResponse_message.code == protocol.CODE_SYSTEM_SET_TIME_FAILED):
                                    print("Error CMD_SYSTEM_SET_TIME")
                                else:
                                    print("OK CMD_SYSTEM_SET_TIME")

                            # CMD_SYSTEM_SET_TIME_ZONE = 13001; // Set the time zone
                            elif (WsPacket_message.cmd==protocol.CMD_SYSTEM_SET_TIME_ZONE):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_SYSTEM_SET_TIME_ZONE")
                                my_logger.debug(f"receive code data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # Signal the ping and receive functions to stop
                                self.stop_task.set()
                                self.result = ComResponse_message.code
                                await asyncio.sleep(5)
                                if (ComResponse_message.code == protocol.CODE_SYSTEM_SET_TIMEZONE_FAILED):
                                    print("Error CMD_SYSTEM_SET_TIME_ZONE")
                                else:
                                    print("OK CMD_SYSTEM_SET_TIME_ZONE")

                            # CMD_ASTRO_START_GOTO_DSO = 11002; // Start GOTO Deep Space Object
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_GOTO_DSO):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_ASTRO_START_GOTO_DSO")
                                my_logger.debug(f"receive data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error GOTO {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    if (ComResponse_message.code == protocol.CODE_ASTRO_GOTO_FAILED):
                                        print("Error GOTO CODE_ASTRO_GOTO_FAILED")
                                    elif (ComResponse_message.code == protocol.CODE_STEP_MOTOR_LIMIT_POSITION_WARNING):
                                        print("Error GOTO CODE_STEP_MOTOR_LIMIT_POSITION_WARNING")
                                    elif (ComResponse_message.code == protocol.CODE_STEP_MOTOR_LIMIT_POSITION_HITTED):
                                        print("Error GOTO CODE_STEP_MOTOR_LIMIT_POSITION_HITTED")
                                    else:
                                        print(f"Error GOTO CODE {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING = 11005; // Start Capture
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING")
                                my_logger.debug(f"receive data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code == protocol.CODE_ASTRO_NEED_GOTO):
                                    print("START_CAPTURE : ASTRO_NEED_GOTO message receive")
                                elif (ComResponse_message.code == protocol.CODE_ASTRO_FUNCTION_BUSY):
                                    print("START_CAPTURE : CODE_ASTRO_FUNCTION_BUSY message receive")
                                    if (self.takePhotoStarted):
                                        my_logger.debug(f"CAPTURE IN PROGRESS Continue ...")
                                    else:
                                        my_logger.debug(f"Error START_CAPTURE {ComResponse_message.code} >> EXIT")
                                        # Signal the ping and receive functions to stop
                                        self.stop_task.set()
                                        self.result = ComResponse_message.code
                                        await asyncio.sleep(5)
                                        print(f"Error START_CAPTURE:  {getErrorCodeValueName(ComResponse_message.code)}")
                                elif (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error START_CAPTURE {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error START_CAPTURE:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    self.takePhotoStarted = True
                            # CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING = 11006; // Stop Capture
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING")
                                my_logger.debug(f"receive data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error STOP_CAPTURE {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error STOP_CAPTURE:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING = 15208 // Test Capture Ending
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING):
                                ResNotifyOperationState_message = notify.ResNotifyOperationState()
                                ResNotifyOperationState_message.ParseFromString(WsPacket_message.data)

                                print("Decoding CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING")
                                my_logger.debug(f"receive notification data >> {ResNotifyOperationState_message.state}")
                                my_logger.debug(f">> {getOperationStateName(ResNotifyOperationState_message.state)}")

                                if ( self.command==protocol.CMD_ASTRO_GO_LIVE and ResNotifyOperationState_message.state == notify.OPERATION_STATE_IDLE):
                                    my_logger.debug("ASTRO CAPTURE IDLE >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                    print("Success ASTRO GO LIVE ENDING")

                                if ( ResNotifyOperationState_message.state == notify.OPERATION_STATE_RUNNING):
                                    my_logger.debug("ASTRO CAPTURE RUNNING")
                                    self.takePhotoStarted = True

                                # OPERATION_STATE_STOPPED = 3; // Stopped
                                if ( self.AstroCapture and ResNotifyOperationState_message.state == notify.OPERATION_STATE_STOPPED):
                                    my_logger.debug("ASTRO CAPTURE OK STOPPING >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = "ok"
                                    await asyncio.sleep(5)
                                    print("Success ASTRO CAPTURE ENDING")
                            # CMD_NOTIFY_PROGRASS_CAPTURE_RAW_LIVE_STACKING = 15209 // Test Capture Ending
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_PROGRASS_CAPTURE_RAW_LIVE_STACKING):
                                ResNotifyProgressCaptureRawLiveStacking_message = notify.ResNotifyProgressCaptureRawLiveStacking()
                                ResNotifyProgressCaptureRawLiveStacking_message.ParseFromString(WsPacket_message.data)
                                self.takePhotoStarted = True
                                print("Decoding CMD_NOTIFY_PROGRASS_CAPTURE_RAW_LIVE_STACKING")
                                my_logger.debug(f"receive notification target_name >> {ResNotifyProgressCaptureRawLiveStacking_message.target_name}")
                                my_logger.debug(f"receive notification total_count >> {ResNotifyProgressCaptureRawLiveStacking_message.total_count}")
                                update_count_type = ResNotifyProgressCaptureRawLiveStacking_message.update_count_type
                                if (update_count_type == 0 or update_count_type == 2):
                                   self.takePhotoCount = ResNotifyProgressCaptureRawLiveStacking_message.current_count
                                if (update_count_type == 1 or update_count_type == 2):
                                   self.takePhotoStacked = ResNotifyProgressCaptureRawLiveStacking_message.stacked_count
                                my_logger.debug(f"receive notification current_count >> {self.takePhotoCount}")
                                my_logger.debug(f"receive notification stacked_count >> {self.takePhotoStacked}")
                            # CMD_CAMERA_TELE_SET_ALL_PARAMS
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_ALL_PARAMS):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA SET ALL PARAMS {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error SET ALL PARAMS:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET FEATURE PARAM OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA SET ALL PARAMS:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_GET_ALL_PARAMS
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_ALL_PARAMS):
                                common_param_instance = base__pb2.CommonParam()
                                # Populate fields of common_param_instance
                                ResGetAllParams_message = camera.ResGetAllParams()
                                # Add common_param_instance to the repeated field all_params
                                ResGetAllParams_message.all_params.append(common_param_instance)

                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ResGetAllParams_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")
                                if (ResGetAllParams_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET ALL_PARAMS {ResGetAllParams_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ResGetAllParams_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET ALL_PARAMS:  {getErrorCodeValueName(ResGetAllParams_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA GET ALL_PARAMS OK >> EXIT")
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                    # Create a dictionary to store the content
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

                                    self.result = res_get_all_params_data
                                    print(f"Success CAMERA GET ALL_PARAMS")
                            # CMD_CAMERA_TELE_SET_FEATURE_PARAM
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_FEATURE_PARAM):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA FEATURE PARAM {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error SET FEATURE PARAM:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET FEATURE PARAM OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA SET FEATURE PARAM:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS):
                                common_param_instance = base__pb2.CommonParam()
                                # Populate fields of common_param_instance
                                ResGetAllFeatureParams_message = camera.ResGetAllFeatureParams()
                                # Add common_param_instance to the repeated field all_feature_params
                                ResGetAllFeatureParams_message.all_feature_params.append(common_param_instance)

                                ResGetAllFeatureParams_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ResGetAllFeatureParams_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ResGetAllFeatureParams_message.code)}")
                                if (ResGetAllFeatureParams_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET ALL FEATURE PARAMS {ResGetAllFeatureParams_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ResGetAllFeatureParams_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET ALL FEATURE PARAMS:  {getErrorCodeValueName(ResGetAllFeatureParams_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA GET ALL FEATURE PARAMS OK >> EXIT")
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                    # Create a dictionary to store the content
                                    res_get_all_params_data = {
                                        "all_feature_params": [],
                                        "code": ResGetAllFeatureParams_message.code
                                    }
                                    for common_param_instance in ResGetAllFeatureParams_message.all_feature_params:
                                        common_param_data = {
                                            "hasAuto": common_param_instance.hasAuto,
                                            "auto_mode": common_param_instance.auto_mode,
                                            "id": common_param_instance.id,
                                            "mode_index": common_param_instance.mode_index,
                                            "index": common_param_instance.index,
                                            "continue_value": common_param_instance.continue_value
                                        }
                                        res_get_all_params_data["all_feature_params"].append(common_param_data)

                                    self.result = res_get_all_params_data
                                    print(f"Success CAMERA GET ALL FEATURE PARAMS")
                            # CMD_CAMERA_TELE_SET_EXP_MODE
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_EXP_MODE):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA SET EXP MODE {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA SET EXP MODE:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET EXP MODE OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA SET EXP MODE:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_SET_EXP
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_EXP):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA SET EXP {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA SET EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET EXP OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA SET EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_GET_EXP
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_EXP and WsPacket_message.type == 3):
                                ComResponseWithDouble_message = base__pb2.ComResWithDouble()
                                ComResponseWithDouble_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponseWithDouble_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponseWithDouble_message.code)}")
                                if (ComResponseWithDouble_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET EXP {ComResponseWithDouble_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponseWithDouble_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET EXP:  {getErrorCodeValueName(ComResponseWithDouble_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA GET EXP OK >> EXIT")
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                    self.result = str(ComResponseWithDouble_message.value)
                                    print(f"Success CAMERA GET EXP:  {ComResponseWithDouble_message.value}")
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_EXP):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET EXP {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET EXP OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA GET EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_SET_GAIN
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_GAIN):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA SET GAIN {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA SET GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET GAIN OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA SET GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_GET_GAIN
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET GAIN {ComResWithInt_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResWithInt_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET GAIN:  {getErrorCodeValueName(ComResWithInt_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA GET GAIN OK >> EXIT")
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                    self.result = str(ComResWithInt_message.value)
                                    print(f"Success CAMERA GET GAIN:  {ComResWithInt_message.value}")
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET GAIN {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET GAIN OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA GET GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_GET_GAIN MODE
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN_MODE and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET GAIN MODE {ComResWithInt_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResWithInt_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET GAIN MODE:  {getErrorCodeValueName(ComResWithInt_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA GET GAIN MODE OK >> EXIT")
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                    self.result = str(ComResWithInt_message.value)
                                    print(f"Success CAMERA GET GAIN MODE:  {ComResWithInt_message.value}")
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN_MODE):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET GAIN MODE {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET GAIN MODE:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET GAIN MODE OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA GET GAIN MODE:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # CMD_CAMERA_TELE_GET_BRIGHTNESS
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_BRIGHTNESS and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET BRIGHTNESS {ComResWithInt_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResWithInt_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET BRIGHTNESS:  {getErrorCodeValueName(ComResWithInt_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA GET BRIGHTNESS MODE OK >> EXIT")
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                    self.result = str(ComResWithInt_message.value)
                                    print(f"Success CAMERA GET BRIGHTNESS:  {ComResWithInt_message.value}")
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_IRCUT):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA SET IRCUT {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA SET IRCUT:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET IRCUT OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA SET IRCUT:  {getErrorCodeValueName(ComResponse_message.code)}")
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_IRCUT and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET IRCUT {ComResWithInt_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResWithInt_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET IRCUT:  {getErrorCodeValueName(ComResWithInt_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA GET IRCUT OK >> EXIT")
                                    self.stop_task.set()
                                    await asyncio.sleep(5)
                                    self.result = str(ComResWithInt_message.value)
                                    print(f"Success CAMERA GET IRCUT:  {ComResWithInt_message.value}")
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_IRCUT):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    my_logger.debug(f"Error CAMERA GET IRCUT {ComResponse_message.code} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Error CAMERA GET IRCUT:  {getErrorCodeValueName(ComResponse_message.code)}")
                                else:
                                    # Signal the ping and receive functions to stop
                                    my_logger.debug("CAMERA SET GRCUT OK >> EXIT")
                                    self.stop_task.set()
                                    self.result = ComResponse_message.code
                                    await asyncio.sleep(5)
                                    print(f"Success CAMERA GET IRCUT:  {getErrorCodeValueName(ComResponse_message.code)}")
                            # Unknown
                            elif (WsPacket_message.cmd != self.command):
                                if( WsPacket_message.type == 0):
                                    print("Get Request Frame")
                                if( WsPacket_message.type == 1):
                                    print("Decoding Response Request Frame")
                                    ComResponse_message = base__pb2.ComResponse()
                                    ComResponse_message.ParseFromString(WsPacket_message.data)

                                    my_logger.debug(f"receive request response data >> {ComResponse_message.code}")
                                    my_logger.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if( WsPacket_message.type == 2):
                                    print("Decoding Notification Frame")
                                    ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                                    ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                    my_logger.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                    my_logger.debug(f">> {getAstroStateName(ResNotifyStateAstroGoto_message.state)}")

                                if( WsPacket_message.type == 3):
                                    print("Decoding Response Notification Frame")
                                    ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                                    ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                    my_logger.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                    my_logger.debug(f">> {getErrorCodeValueName(ResNotifyStateAstroGoto_message.state)}")
                        else:
                            print("Ignoring Unkown Type Frames")
                    else:
                        print("No Messages Rcv : close ??")
                        self.wait_pong = False
                        self.stop_task.set()
                print("Continue .....")

        except websockets.ConnectionClosedOK  as e:
            print(f'Rcv: ConnectionClosedOK', e)
        except websockets.ConnectionClosedError as e:
            print(f'Rcv: ConnectionClosedError', e)
        except asyncio.CancelledError:
            print("Rcv Cancelled.")
        except Exception as e:
            # Handle other exceptions
            print(f"Rcv: Unhandled exception: {e}")
            if (not self.stop_task.is_set()):
                self.stop_task.set()
            await asyncio.sleep(1)
        finally:
            # Perform cleanup if needed
            print("TERMINATING Receive function.")

    async def send_message(self):
        # Create a protobuf message
        # Start Sending
        major_version = 1
        minor_version = 1
        device_id = 1  # DWARF II
        self.target_name = ""
        #self.takePhotoStarted = False

        if not self.websocket:
            print("Error No WebSocket in send_message")
            WebSocketClient.Init_Send_TeleGetSystemWorkingState = False
            return

        #CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE
        WsPacket_messageTeleGetSystemWorkingState = base__pb2.WsPacket()
        ReqGetSystemWorkingState_message = camera.ReqGetSystemWorkingState()
        WsPacket_messageTeleGetSystemWorkingState.data = ReqGetSystemWorkingState_message.SerializeToString()

        WsPacket_messageTeleGetSystemWorkingState.major_version = major_version
        WsPacket_messageTeleGetSystemWorkingState.minor_version = minor_version
        WsPacket_messageTeleGetSystemWorkingState.device_id = device_id
        WsPacket_messageTeleGetSystemWorkingState.module_id = 1  # MODULE_TELEPHOTO
        WsPacket_messageTeleGetSystemWorkingState.cmd = 10039 #CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE
        WsPacket_messageTeleGetSystemWorkingState.type = 0; #REQUEST
        WsPacket_messageTeleGetSystemWorkingState.client_id = self.client_id # "0000DAF2-0000-1000-8000-00805F9B34FB"  # ff03aa11-5994-4857-a872-b411e8a3a5e51

        #CMD_CAMERA_TELE_OPEN_CAMERA
        WsPacket_messageCameraTeleOpen = base__pb2.WsPacket()
        ReqOpenCamera_message = camera.ReqOpenCamera()
        WsPacket_messageCameraTeleOpen.data = ReqOpenCamera_message.SerializeToString()

        WsPacket_messageCameraTeleOpen.major_version = major_version
        WsPacket_messageCameraTeleOpen.minor_version = minor_version
        WsPacket_messageCameraTeleOpen.device_id = device_id
        WsPacket_messageCameraTeleOpen.module_id = 1  # MODULE_TELEPHOTO
        WsPacket_messageCameraTeleOpen.cmd = 10000 #CMD_CAMERA_TELE_OPEN_CAMERA
        WsPacket_messageCameraTeleOpen.type = 0; #REQUEST
        WsPacket_messageCameraTeleOpen.client_id = self.client_id # "0000DAF2-0000-1000-8000-00805F9B34FB"  # ff03aa11-5994-4857-a872-b411e8a3a5e51

        # SEND COMMAND
        WsPacket_message = base__pb2.WsPacket()
        WsPacket_message.data = self.message.SerializeToString()

        WsPacket_message.major_version = major_version
        WsPacket_message.minor_version = minor_version
        WsPacket_message.device_id = device_id
        WsPacket_message.module_id = self.module_id
        WsPacket_message.cmd = self.command 
        WsPacket_message.type = self.type_id;
        WsPacket_message.client_id = self.client_id # "0000DAF2-0000-1000-8000-00805F9B34FB"  # ff03aa11-5994-4857-a872-b411e8a3a5e51
       
        try:
            # Serialize the message to bytes and send
            # Send Command
            await asyncio.sleep(0.02)

            if (WebSocketClient.Init_Send_TeleGetSystemWorkingState):
                await self.websocket.send(WsPacket_messageTeleGetSystemWorkingState.SerializeToString())
                print("#----------------#")
                my_logger.debug(f"Send cmd >> {WsPacket_messageTeleGetSystemWorkingState.cmd}")
                my_logger.debug(f">> {getDwarfCMDName(WsPacket_messageTeleGetSystemWorkingState.cmd)}")

                my_logger.debug(f"Send type >> {WsPacket_messageTeleGetSystemWorkingState.type}")
                my_logger.debug(f"msg data len is >> {len(WsPacket_messageTeleGetSystemWorkingState.data)}")
                print("Sendind End ....");  

                await asyncio.sleep(1)

                await self.websocket.send(WsPacket_messageCameraTeleOpen.SerializeToString())
                print("#----------------#")
                my_logger.debug(f"Send cmd >> {WsPacket_messageCameraTeleOpen.cmd}")
                my_logger.debug(f">> {getDwarfCMDName(WsPacket_messageCameraTeleOpen.cmd)}")

                my_logger.debug(f"Send type >> {WsPacket_messageCameraTeleOpen.type}")
                my_logger.debug(f"msg data len is >> {len(WsPacket_messageCameraTeleOpen.data)}")
                print("Sendind End ....");
                WebSocketClient.Init_Send_TeleGetSystemWorkingState = False

            await asyncio.sleep(1)

            await self.websocket.send(WsPacket_message.SerializeToString())
            print("#----------------#")
            my_logger.debug(f"Send cmd >> {WsPacket_message.cmd}")
            my_logger.debug(f">> {getDwarfCMDName(WsPacket_message.cmd)}")

            # Special GOTO  DSO or SOLAR save Target Name to verifiy is GOTO is success
            if ((self.command == protocol.CMD_ASTRO_START_GOTO_DSO) or (self.command == protocol.CMD_ASTRO_START_GOTO_SOLAR_SYSTEM)):
                self.target_name = self.message.target_name

            # Special CALIBRATION
            if (self.command == protocol.CMD_ASTRO_START_CALIBRATION):
                self.stopcalibration = False

            # Special ASTRO START or STOP CAPTURE
            if ( self.command == protocol.CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING or self.command == protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING):
                self.AstroCapture = True

            my_logger.debug(f"Send type >> {WsPacket_message.type}")
            my_logger.debug(f"Send message >> {self.message}")
            my_logger.debug(f"msg data len is >> {len(WsPacket_message.data)}")
            print("Sendind End ....");  

        except Exception as e:
            # Handle other exceptions
            print(f"Unhandled exception1: {e}")
            WebSocketClient.Init_Send_TeleGetSystemWorkingState = False
        finally:
            # Perform cleanup if needed
            print("TERMINATING Sending function.")

    async def start(self):
        try:
            result = False  
            #asyncio.set_event_loop(asyncio.new_event_loop())
            #ping_timeout=self.ping_interval_task+2
            print(f"ping_interval : {self.ping_interval_task}")
            start_client = False
            self.stop_task.clear();
            async with websockets.client.connect(self.uri, ping_interval=None, extra_headers=[("Accept-Encoding", "gzip"), ("Sec-WebSocket-Extensions", "permessage-deflate")]) as websocket:
                try:
                    start_client = True
                    self.websocket = websocket
                    if self.websocket:
                        print(f"Connected to {self.uri} with {self.message}command:{self.command}")
                        print("------------------")

                    # Start the task to receive messages
                    #self.receive_task = asyncio.ensure_future(self.receive_messages())
                    self.receive_task = asyncio.create_task(self.receive_messages())

                    # Start the periodic task to send pings
                    #self.ping_task = asyncio.ensure_future(self.send_ping_periodically())
                    self.ping_task = asyncio.create_task(self.send_ping_periodically())

                    # Start the periodic task to abort all task after timeout
                    self.abort_tasks = asyncio.create_task(self.abort_tasks_timeout(180))

                    await asyncio.sleep(2)

                    # Send a unique message to the server
                    try:
                        await self.send_message()

                        # For python 11
                        #async with asyncio.TaskGroup() as tg:
                        #    self.receive_task = tg.create_task(self.receive_messages())
                        #    self.ping_task = tg.create_task(self.send_ping_periodically())

                        #print(f"Both tasks have completed now: {self.receive_task.result()}, {self.ping_task.result()}")
                        #await self.abort_tasks_timeout(30)

                        results = await asyncio.gather( 
                            self.receive_task,
                            self.ping_task,
                            self.abort_tasks,
                            return_exceptions=True
                        ) 
                        print(results)
                        print("End of Current Tasks.")

                        # get the exception #raised by a task

                        try:
                            self.receive_task.result()
                            self.ping_task.result()
                            self.abort_tasks.result()

                        except Exception as e:
                            print(f"Exception occurred in the Gather try block: {e}")

                        print("End of Current Tasks Results.")

                    except Exception as e:
                        print(f"Exception occurred in the try block: {e}")

                except Exception as e:
                    print(f"Exception occurred in the 2nd try block: {e}")
        except Exception as e:
            print(f"unknown exception with error: {e}")
        finally:
            # Signal the ping and receive functions to stop
            self.stop_task.set()

            # Cancel the ping task when the client is done
            if self.ping_task:
                print("Closing Ping Task ....")
                self.ping_task.cancel()
                try:
                    await self.ping_task
                except Exception as e:
                    print(f"unknown exception with error: {e}")

            # Cancel the receive task when the client is done
            if self.receive_task:
                print("Closing Receive Task ....")
                self.receive_task.cancel()
                try:
                    await self.receive_task
                except Exception as e:
                    print(f"unknown exception with error: {e}")

            # Close the WebSocket connection explicitly
            if start_client:
                if self.websocket: #and self.websocket.open:
                    print("Closing Socket ....")
                    try:
                        await self.websocket.close()
                        print("WebSocket connection closed.")
                    except websockets.ConnectionClosedOK  as e:
                        print(f'Close: ConnectionClosedOK', e)
                    except websockets.ConnectionClosedError as e:
                        print(f'Close: ConnectionClosedError', e)
                    except Exception as e:
                        print(f"unknown exception with error: {e}")

                print("WebSocket Terminated.")

# Run the client
def start_socket(message, command, type_id, module_id, uri=None, client_id=None, ping_interval_task=10):
    if uri is None or client_id is None:
        data_config = get_current_data()
        if uri is None:
            uri = data_config['ip']
        if client_id is None:
            client_id = data_config['client_id']

    websocket_uri = ws_uri(uri)

    print(f"Try Connect to {websocket_uri} for {client_id} with data:")
    print(f"{message}")
    print(f"command:{command}")
    my_logger.debug(f">> {getDwarfCMDName(command)}")
    print("------------------")

    try:
        # Create an instance of WebSocketClient
        client_instance = WebSocketClient(websocket_uri, client_id, message, command, type_id, module_id, ping_interval_task)
        client_instance.initialize_once()

        # Call the start method to initiate the WebSocket connection and tasks
        asyncio.run(client_instance.start())
        print("WebSocket Client End.")
        return client_instance.result;

    except Exception as e:
        # Handle any errors that may occur during the close operation
        print(f"Unknown Error closing : {e}")
        pass  # Ignore this exception, it's expected during clean-up

    return False;

def connect_socket(message, command, type_id, module_id):

    result = False

    try:
        # Call the start function
        result = start_socket(message, command, type_id, module_id)
        print(f"Result : {result}")

    except KeyboardInterrupt:
        # Handle KeyboardInterrupt separately
        print("KeyboardInterrupt received. Stopping gracefully.")
        pass  # Ignore this exception, it's expected during clean-up
    return result

