import websockets.client
import asyncio
import threading
import contextlib
import json
import gzip
import os
import time
from enum import Enum

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.my_logger import  SUCCESS_LEVEL_NUM

import dwarf_python_api.proto.protocol_pb2 as protocol
import dwarf_python_api.proto.notify_pb2 as notify
import dwarf_python_api.proto.astro_pb2 as astro
import dwarf_python_api.proto.system_pb2 as system
import dwarf_python_api.proto.camera_pb2 as camera
import dwarf_python_api.proto.rgb_pb2 as rgb
import dwarf_python_api.proto.motor_control_pb2 as motor
# in notify
import dwarf_python_api.proto.base_pb2 as base__pb2
# import data for config.py
import dwarf_python_api.get_config_data

class Dwarf_Result (Enum):
    DISCONNECTED = -2;
    WARNING = -1;
    ERROR = 0;
    OK = 1;

# Global variables to keep track of the client instance and event loop
global client_instance, event_loop, event_loop_thread
client_instance = None
event_loop = None
event_loop_thread = None
gb_timeout = 150 # 240
ERROR_TIMEOUT = -5
ERROR_INTERRUPTED = -10
ERROR_SLAVEMODE = -15

# Define the static table of valid command-result pairs
VALID_PAIRS = {
    (protocol.CMD_SYSTEM_SET_MASTERLOCK, protocol.CMD_NOTIFY_WS_HOST_SLAVE_MODE),
    (protocol.CMD_CAMERA_TELE_PHOTOGRAPH, protocol.CMD_NOTIFY_TELE_FUNCTION_STATE),
    (protocol.CMD_CAMERA_WIDE_PHOTOGRAPH, protocol.CMD_NOTIFY_WIDE_FUNCTION_STATE),
    (protocol.CMD_ASTRO_START_GOTO_DSO, protocol.CMD_NOTIFY_STATE_ASTRO_TRACKING),
    (protocol.CMD_ASTRO_START_GOTO_DSO, protocol.CMD_ASTRO_STOP_GOTO),
    (protocol.CMD_ASTRO_START_GOTO_SOLAR_SYSTEM, protocol.CMD_NOTIFY_STATE_ASTRO_TRACKING),
    (protocol.CMD_ASTRO_START_GOTO_SOLAR_SYSTEM, protocol.CMD_ASTRO_STOP_GOTO),
    (protocol.CMD_ASTRO_START_CALIBRATION,protocol.CMD_ASTRO_STOP_CALIBRATION),
    (protocol.CMD_ASTRO_START_CALIBRATION,protocol.CMD_NOTIFY_STATE_ASTRO_CALIBRATION),
    (protocol.CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING, protocol.CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING),
    (protocol.CMD_ASTRO_START_WIDE_CAPTURE_LIVE_STACKING, protocol.CMD_NOTIFY_STATE_WIDE_CAPTURE_RAW_LIVE_STACKING),
    (protocol.CMD_CAMERA_TELE_SET_EXP_MODE, protocol.CMD_NOTIFY_TELE_SET_PARAM),
    (protocol.CMD_CAMERA_TELE_SET_EXP, protocol.CMD_NOTIFY_TELE_SET_PARAM),
    (protocol.CMD_CAMERA_TELE_SET_GAIN, protocol.CMD_NOTIFY_TELE_SET_PARAM),
    (protocol.CMD_CAMERA_WIDE_SET_EXP_MODE, protocol.CMD_NOTIFY_WIDE_SET_PARAM),
    (protocol.CMD_CAMERA_WIDE_SET_EXP, protocol.CMD_NOTIFY_WIDE_SET_PARAM),
    (protocol.CMD_CAMERA_WIDE_SET_GAIN, protocol.CMD_NOTIFY_WIDE_SET_PARAM),
    (protocol.CMD_ASTRO_GO_LIVE, protocol.CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING),
    (protocol.CMD_ASTRO_GO_LIVE, protocol.CMD_NOTIFY_STATE_WIDE_CAPTURE_RAW_LIVE_STACKING),
    (protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING, protocol.CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING),
    (protocol.CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING, protocol.CMD_NOTIFY_STATE_WIDE_CAPTURE_RAW_LIVE_STACKING),
    (protocol.CMD_ASTRO_START_EQ_SOLVING, protocol.CMD_NOTIFY_EQ_SOLVING_STATE),
    (protocol.CMD_RGB_POWER_REBOOT, protocol.CMD_NOTIFY_POWER_OFF),
    (protocol.CMD_RGB_POWER_POWER_DOWN, protocol.CMD_NOTIFY_POWER_OFF),
    (protocol.CMD_RGB_POWER_POWERIND_ON, protocol.CMD_NOTIFY_POWER_IND_STATE),
    (protocol.CMD_RGB_POWER_POWERIND_OFF, protocol.CMD_NOTIFY_POWER_IND_STATE),
    (protocol.CMD_RGB_POWER_OPEN_RGB, protocol.CMD_NOTIFY_RGB_STATE),
    (protocol.CMD_RGB_POWER_CLOSE_RGB, protocol.CMD_NOTIFY_RGB_STATE),
}

# ID-to-name mapping
ID_TELE_PARAM_NAMES = {
    0: "Exposure",
    1: "Gain",
    2: "White Balance",
    3: "Brightness",
    4: "Contrast",
    5: "Hue",
    6: "Saturation",
    7: "Sharpness",
    8: "IR Cut"
}

ID_WIDE_PARAM_NAMES = {
    0: "Exposure",
    1: "Gain",
    2: "White Balance",
    3: "Brightness",
    4: "Contrast",
    5: "Hue",
    6: "Saturation",
    7: "Sharpness",
}

ID_FEATURE_PARAM_NAMES = {
    0: "Astro binning",
    1: "Astro img_to_take",
    2: "Astro format",
    3: "Burst count",
    4: "TimeLapse interval",
    5: "TimeLapse totalTime",
    6: "Panorama row",
    7: "Panorama col",
    8: "Astro display source",
    9: "Burst interval",
    10: "Telephoto video resolution",
    11: "Telephoto video fps",
    12: "Wide-angle video resolution",
    13: "Wide-angle video fps",
    14: "Astro ai enhance",
    15: "Astro mosaic sub img to take",
}

def fct_log_detail_tele_param(param):
    if not param:
        log.warning("No tele params found in response.")
        return
    # Get id and index
    id_value = param.get('id')
    index_value = param.get('index')
    auto_mode = param.get('auto_mode')
    value = param.get('continue_value')
    
    # Look up readable name
    id_name = ID_TELE_PARAM_NAMES.get(id_value, f"Unknown_ID_{id_value}")

    # Log it
    log.info(f"Logging TELE Param - Name: {id_name}, ID: {id_value}, Index: {index_value}, Auto: {auto_mode}, Value: {value}")

def fct_log_detail_wide_param(param):
    if not param:
        log.warning("No wide params found in response.")
        return
    # Get id and index
    id_value = param.get('id')
    index_value = param.get('index')
    auto_mode = param.get('auto_mode')
    value = param.get('continue_value')
    
    # Look up readable name
    id_name = ID_WIDE_PARAM_NAMES.get(id_value, f"Unknown_ID_{id_value}")

    # Log it
    log.info(f"Logging WIDE Param - Name: {id_name}, ID: {id_value}, Index: {index_value}, Auto: {auto_mode}, Value: {value} ")

def fct_log_feature_param(param):
    if not param:
        log.warning("No feature params found in response.")
        return
    # Get id and index
    id_value = param.get('id')
    index_value = param.get('index')
    auto_mode = param.get('auto_mode')
    value = param.get('continue_value')
    
    # Look up readable name
    id_name = ID_FEATURE_PARAM_NAMES.get(id_value, f"Unknown_ID_{id_value}")

    # Log it
    log.info(f"Logging ID_FEATURE_PARAM_NAMES Param - Name: {id_name}, ID: {id_value}, Index: {index_value}, Auto: {auto_mode}, Value: {value} ")

def process_command(command, result):
    # If the result matches the command, accept it by default
    if command == result:
        log.debug("Result matches command, accepting by default:", result)
        return result
    # Otherwise, check if the (command, result) pair is in the valid pairs
    elif (command, result) in VALID_PAIRS:
        log.debug("Valid result for command:", result)
        return result
    else:
        # Invalid pair, ignore and wait
        log.debug("Ignoring result, waiting for the correct response.")
        return None

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

def getPowerStateName(PowerStateCode):

    return "ON" if PowerStateCode else "OFF"

class StopClientException(Exception):
    pass

# new version protobuf enabled
# use a Class
class WebSocketClient:
    # use init just once or after error connecting
    Init_Send_TeleGetSystemWorkingState = True;

    def __init__(self, loop, uri, client_id, ping_interval_task=5):
        self.loop = loop
        self.websocket = False
        self.result = False
        self.uri = uri
        self.start_client = False
        self.stop_client = False
        self.message = None
        self.command = None
        self.module_id = None
        self.type_id = None
        self.target_name = ""
        self.client_id = client_id
        self.ping_interval_task = ping_interval_task
        self.ping_task = None
        self.receive_task = None
        self.message_init_task = None
        self.abort_tasks = None
        self.abort_timeout = 900
        self.reset_timeout = True
        self.stop_task = asyncio.Event()
        self.result_queue = asyncio.Queue()
        self.result_queue_locked = asyncio.Lock()
        self.wait_pong = False
        self.stopcalibration = False
        self.takePhotoStarted = False
        self.takeWidePhotoStarted = False
        self.AstroCapture = False
        self.AstroWideCapture = False
        self.RestartAstroCapture = False
        self.RestartAstroWideCapture = False
        self.startEQSolving = False
        self.toDoSetExpMode = False
        self.toDoSetExp = False
        self.toDoSetGain = False
        self.toDoSetWideExpMode = False
        self.toDoSetWideExp = False
        self.toDoSetWideGain = False
        self.takePhotoCount = 0
        self.takePhotoStacked = 0
        self.takeWidePhotoCount = 0
        self.takeWidePhotoStacked = 0
        self.InitHostReceived = False
        self.ErrorConnection = False
        self.BatteryLevelDwarf = None
        self.availableSizeDwarf = None
        self.totalSizeDwarf = None
        self.TemperatureLevelDwarf = None
        self.StreamTypeDwarf = None
        self.FocusValueDwarf = None
        self.PowerIndStateDwarf = None
        self.RgbIndStateDwarf = None

        # TEST_CALIBRATION : Test Calibration Packet or Goto Packet
        # Test Mode : Calibration Packet => TEST_CALIBRATION = True
        # Production Mode GOTO Packet => TEST_CALIBRATION = False (default)
        self.modeCalibration = False

    def initialize_once(self):

        if WebSocketClient.Init_Send_TeleGetSystemWorkingState:
            # Perform the initialization logic here
            log.info("Initializing...")

            data_config = dwarf_python_api.get_config_data.get_config_data()
            if data_config['calibration']:
                self.modeCalibration = True
            if data_config['timeout_cmd']:
                self.abort_timeout = int(data_config.get('timeout_cmd', 900))
        else:
            log.info("Already initialized.")

    async def abort_tasks_timeout(self, timeout):

        try:
            count = 0
            self.abort_timeout = timeout
            log.info(f'TIMEOUT: init to {timeout}s')
            await asyncio.sleep(0.02)
            while not self.stop_task.is_set() and count <= self.abort_timeout:
                await asyncio.sleep(1)
                if self.abort_timeout > 0:
                    count += 1
                if self.reset_timeout:
                    log.info(f'TIMEOUT: Reset, CMD received')
                    self.reset_timeout = False
                    count = 0
            if not self.stop_task.is_set() and count > self.abort_timeout:
                log.warning(f'TIMEOUT: triggered after {self.abort_timeout}s')
        except asyncio.CancelledError as e:
            log.info(f'TIMEOUT: Cancelled {e}')
            pass
        except Exception as e:
            # Handle other exceptions
            log.error(f"TIMEOUT: Unhandled exception: {e}")
        finally:
            # Perform cleanup if needed
            if (not self.stop_task.is_set()):
                log.info("TIMEOUT function set stop_task.")
                self.stop_task.set()
            log.info("TERMINATING TIMEOUT function.")

    async def send_ping_periodically(self):
        if not self.websocket:
            log.error("Error No WebSocket in send_ping_periodically")
            self.stop_task.set()

        try:
            await asyncio.sleep(2)
            while not self.stop_task.is_set():
                if self.websocket.state != websockets.protocol.OPEN:
                    log.error("WebSocket connection is not open.")
                    self.stop_task.set()
                elif (not self.wait_pong):
                    # Adjust the interval based on your requirements
                    log.info("Sent a PING frame")

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
            log.error(f'Ping: ConnectionClosedOK', e)
            pass
        except websockets.ConnectionClosedError as e:
            log.error(f'Ping: ConnectionClosedError', e)
            pass
        except asyncio.CancelledError:
            log.info("Ping Cancelled.")
            pass
        except Exception as e:
            # Handle other exceptions
            log.error(f"Ping: Unhandled exception: {e}")
            if (not self.stop_task.is_set()):
                log.error("PING function set stop_task.")
                self.stop_task.set()
            await asyncio.sleep(1)
        finally:
            # Perform cleanup if needed
            log.info("TERMINATING PING function.")

    async def result_receive_messages(self, cmd_send, cmd_recv, result, message, code):
        try:
            log.info("result_receive_messages.")
            result_message = { 'cmd_send' : cmd_send, 'cmd_recv' : cmd_recv, 'result' : result, 'message' : message, 'code': code}
            log.info(result_message)
            async with self.result_queue_locked:
                await self.result_queue.put(result_message)
            log.info("end result_receive_messages.")
        except Exception as e:
            # Handle other exceptions
            log.error(f"result_receive_messages: Unhandled exception: {e}")
        finally:
            # Perform cleanup if neede
            log.info("End result_receive_messages.")

    async def result_notification_messages(self, cmd_send, cmd_recv, result, message, code):
        try:
            log.debug("result_notification_messages.")
            notification_message = { 'cmd_send' : cmd_send, 'cmd_recv' : cmd_recv, 'result' : result, 'message' : message, 'code': code, 'notification' : True}
            log.debug(notification_message)
            log.notice(notification_message['message'])
            async with self.result_queue_locked:
                await self.result_queue.put(notification_message)
            log.info("end result_notification_messages.")
        except Exception as e:
            # Handle other exceptions
            log.error(f"result_notification_messages: Unhandled exception: {e}")
        finally:
            # Perform cleanup if neede
            log.info("End result_notification_messages.")

    async def receive_messages(self):
        if not self.websocket:
            log.error("Error No WebSocket in receive_messages")
            self.stop_task.set()

        try:
            await asyncio.sleep(2)
            while not self.stop_task.is_set() or self.wait_pong:
                await asyncio.sleep(0.02)
                log.info("Wait for frames")

                if self.websocket.state != websockets.protocol.OPEN:
                    log.error("WebSocket connection is not open.")
                    self.wait_pong = False
                    self.stop_task.set()
                else:
                    message = await self.websocket.recv()
                    if (message):
                        if isinstance(message, str):
                            log.info("Receiving...")
                            log.info(message)
                            if (message =="pong"):
                                 self.wait_pong = False
                        elif isinstance(message, bytes):
                            log.info("------------------")
                            log.info("Receiving...  data")

                            WsPacket_message = base__pb2.WsPacket()
                            WsPacket_message.ParseFromString(message)
                            log.debug(f"receive cmd >> {WsPacket_message.cmd} type >> {WsPacket_message.type}")
                            log.debug(f">> {getDwarfCMDName(WsPacket_message.cmd)}")
                            log.debug(f"msg data len is >> {len(WsPacket_message.data)}")
                            log.info("------------------")

                            # CMD_NOTIFY_WS_HOST_SLAVE_MODE = 15223; // Leader/follower mode notification
                            if (WsPacket_message.cmd==protocol.CMD_NOTIFY_WS_HOST_SLAVE_MODE):
                                ResNotifyHostSlaveMode_message = notify.ResNotifyHostSlaveMode()
                                ResNotifyHostSlaveMode_message.ParseFromString(WsPacket_message.data)

                                log.info("Decoding CMD_NOTIFY_WS_HOST_SLAVE_MODE")
                                log.debug(f"receive Host/Slave data >> {ResNotifyHostSlaveMode_message.mode}")
                                log.debug(f"receive Host/Slave lock >> {ResNotifyHostSlaveMode_message.lock}")

                                # Host = 0 Slave = 1
                                if (ResNotifyHostSlaveMode_message.mode == 1):
                                    self.InitHostReceived = False
                                    log.debug("SLAVE_MODE >> EXIT")
                                    log.warning("SLAVE MODE detected")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.WARNING, "Error SLAVE MODE", ERROR_SLAVEMODE)
                                    await asyncio.sleep(1)
                                else:
                                    if (WsPacket_message.cmd==protocol.CMD_SYSTEM_SET_MASTERLOCK):
                                        log.info("Success SET HOST OK >> EXIT")
                                        log.success("Success SET HOST")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Success SET HOST MODE ", 0)
                                    else: 
                                        self.InitHostReceived = True
                                        log.info("Continue Decoding CMD_NOTIFY_WS_HOST_SLAVE_MODE")
                                        log.info("Result Sent for CMD_NOTIFY_WS_HOST_SLAVE_MODE")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK HOST MODE", ResNotifyHostSlaveMode_message.mode)

                            # CMD_SYSTEM_SET_MASTERLOCK = 13004; // Set HOST mode
                            if (WsPacket_message.cmd==protocol.CMD_SYSTEM_SET_MASTERLOCK):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.info("Decoding CMD_SYSTEM_SET_MASTERLOCK")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CMD_SYSTEM_SET_MASTERLOCK CODE {ComResponse_message.code} {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error SET HOST MODE", ComResponse_message.code)
                                else :
                                    log.info("Success SET HOST OK >> EXIT")
                                    log.success("Success SET HOST")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Success SET HOST MODE ", ComResponse_message.code)

                            # CMD_STEP_MOTOR_RUN = 14000; // Motor motion
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_RUN):
                                ResNotifyMotor_message = motor.ResMotor()
                                ResNotifyMotor_message.ParseFromString(WsPacket_message.data)

                                log.info("Decoding CMD_STEP_MOTOR_RUN")
                                log.debug(f"receive id data >> {ResNotifyMotor_message.id}")
                                log.debug(f"receive code data >> {ResNotifyMotor_message.code}")

                                # OK = 0; // No Error
                                if (ResNotifyMotor_message.code != protocol.OK):
                                    if (ResNotifyMotor_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        log.error(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    log.error(f"Error CMD_STEP_MOTOR_RUN CODE {getErrorCodeValueName(ResNotifyMotor_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.WARNING, "Error CMD_STEP_MOTOR_RUN", ResNotifyMotor_message.code)
                                    await asyncio.sleep(1)
                                else :
                                    log.info("Success CMD_STEP_MOTOR_RUN OK >> EXIT")
                                    log.success("Success CMD_STEP_MOTOR_RUN")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "CMD_STEP_MOTOR_RUN", ResNotifyMotor_message.code)

                            # CMD_STEP_MOTOR_RUN_TO = 14001; // Motor motion to
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_RUN_TO):
                                ResNotifyMotorPosition_message = motor.ResMotorPosition()
                                ResNotifyMotorPosition_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_STEP_MOTOR_RUN_TO")
                                log.debug(f"receive id data >> {ResNotifyMotorPosition_message.id}")
                                log.debug(f"receive code data >> {ResNotifyMotorPosition_message.code}")
                                log.debug(f"receive position data >> {ResNotifyMotorPosition_message.position}")

                                # OK = 0; // No Error
                                if (ResNotifyMotorPosition_message.code != protocol.OK):
                                    if (ResNotifyMotorPosition_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        log.error(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    log.error(f"Error CMD_STEP_MOTOR_RUN_TO CODE {getErrorCodeValueName(ResNotifyMotorPosition_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.WARNING, "Error CMD_STEP_MOTOR_RUN", ResNotifyMotorPosition_message.code)
                                    await asyncio.sleep(1)
                                else :
                                    log.info("CMD_STEP_MOTOR_RUN_TO OK >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "CMD_STEP_MOTOR_RUN", ResNotifyMotorPosition_message.code)

                            # CMD_STEP_MOTOR_RESET = 14003; // Motor CMD_STEP_MOTOR_RESET
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_RESET):
                                ResNotifyMotor_message = motor.ResMotor()
                                ResNotifyMotor_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_STEP_MOTOR_RESET")
                                log.debug(f"receive id data >> {ResNotifyMotor_message.id}")
                                log.debug(f"receive code data >> {ResNotifyMotor_message.code}")
                                # OK = 0; // No Error
                                if (ResNotifyMotor_message.code != protocol.OK):
                                    if (ResNotifyMotor_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        log.error(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    log.error(f"Error CMD_STEP_MOTOR_RESET CODE {getErrorCodeValueName(ResNotifyMotor_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_STEP_MOTOR_RESET", ResNotifyMotor_message.code)
                                    await asyncio.sleep(1)
                                else :
                                    log.info("CMD_STEP_MOTOR_RESET OK >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "CMD_STEP_MOTOR_RESET", ResNotifyMotor_message.code)

                            # CMD_STEP_MOTOR_SERVICE_JOYSTICK = 14006; // Motor motion to
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_SERVICE_JOYSTICK):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_STEP_MOTOR_SERVICE_JOYSTICK")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    if (ComResponse_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        log.error(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    log.error(f"Error CMD_STEP_MOTOR_SERVICE_JOYSTICK CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_STEP_MOTOR_SERVICE_JOYSTICK", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else :
                                    log.info("Success CMD_STEP_MOTOR_RUN OK >> EXIT")
                                    log.success("Success CMD_STEP_MOTOR_RUN")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CMD_STEP_MOTOR_SERVICE_JOYSTICK", ComResponse_message.code)

                            # CMD_STEP_MOTOR_GET_POSITION = 14011; // Motor Get Position
                            if (WsPacket_message.cmd==protocol.CMD_STEP_MOTOR_GET_POSITION):
                                ResMotorPosition_message = motor.ResMotorPosition()
                                ResMotorPosition_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_STEP_MOTOR_GET_POSITION")
                                log.info(f"receive id data >> {ResMotorPosition_message.id}")
                                log.info(f"receive code data >> {ResMotorPosition_message.code}")
                                log.info(f"receive position data >> {ResMotorPosition_message.position}")
                                log.info(f">> {getErrorCodeValueName(ResMotorPosition_message.code)}")

                                # OK = 0; // No Error
                                if (ResMotorPosition_message.code != protocol.OK):
                                    if (ResMotorPosition_message.code == protocol.CODE_STEP_MOTOR_POSITION_NEED_RESET):
                                        log.error(f"Error MOTOR need RESET >> EXIT")

                                    # Signal the ping and receive functions to stop
                                    log.error(f"Error CMD_STEP_MOTOR_GET_POSITION CODE {getErrorCodeValueName(ResMotorPosition_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_STEP_MOTOR_GET_POSITION", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else :
                                    log.info("Success CMD_STEP_MOTOR_GET_POSITION OK >> EXIT")
                                    log.success("Success CMD_STEP_MOTOR_GET_POSITION")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CMD_STEP_MOTOR_GET_POSITION", ComResponse_message.code)

                            # CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE = 10039; // // Get the working status of the whole machine
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA_TELE_GET_SYSTEM_WORKING_STATE CODE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    if not self.InitHostReceived:
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.WARNING, "Error SLAVE MODE", ERROR_SLAVEMODE)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("Continue OK CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE")
                                    if not self.InitHostReceived:
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.WARNING, "Error SLAVE MODE", ERROR_SLAVEMODE)

                            # CMD_CAMERA_TELE_OPEN_CAMERA = 10000; // // Open the TELE Camera
                            elif (self.command==protocol.CMD_CAMERA_TELE_OPEN_CAMERA and WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_OPEN_CAMERA):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_CAMERA_TELE_OPEN_CAMERA")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                await asyncio.sleep(1)
                                if (ComResponse_message.code != protocol.OK):
                                    log.error("Error CMD_CAMERA_TELE_OPEN_CAMERA")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_TELE_OPEN_CAMERA", ComResponse_message.code)
                                else:
                                    log.info("OK CMD_CAMERA_TELE_OPEN_CAMERA")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Succcess CMD_CAMERA_TELE_OPEN_CAMERA", ComResponse_message.code)

                            # CMD_CAMERA_TELE_OPEN_CAMERA = 10000; // // Open the TELE Camera
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_OPEN_CAMERA):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_CAMERA_TELE_OPEN_CAMERA")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error GET_CAMERA_TELE_OPEN_CAMERA {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_TELE_OPEN_CAMERA", ComResponse_message.code)
                                else:
                                    log.info("Continue OK CMD_CAMERA_TELE_OPEN_CAMERA")

                            # CMD_CAMERA_WIDE_OPEN_CAMERA = 12000; // // Open the Wide Camera
                            elif (self.command==protocol.CMD_CAMERA_WIDE_OPEN_CAMERA and WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_OPEN_CAMERA):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_CAMERA_WIDE_OPEN_CAMERA")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                await asyncio.sleep(1)
                                if (ComResponse_message.code != protocol.OK):
                                    log.error("Error CMD_CAMERA_WIDE_OPEN_CAMERA")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_WIDE_OPEN_CAMERA", ComResponse_message.code)
                                else:
                                    log.info("OK CMD_CAMERA_WIDE_OPEN_CAMERA")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Succcess CMD_CAMERA_WIDE_OPEN_CAMERA", ComResponse_message.code)

                            # CMD_CAMERA_WIDE_OPEN_CAMERA = 12000; // // Open the Wide Camera
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_OPEN_CAMERA):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_CAMERA_WIDE_OPEN_CAMERA")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error GET_CAMERA_WIDE_OPEN_CAMERA {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_WIDE_OPEN_CAMERA", ComResponse_message.code)
                                else:
                                    log.info("Continue OK CMD_CAMERA_WIDE_OPEN_CAMERA")

                            # CMD_FOCUS_START_ASTRO_AUTO_FOCUS = 15004; // Start astronomical autofocus
                            elif (WsPacket_message.cmd==protocol.CMD_FOCUS_START_ASTRO_AUTO_FOCUS):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_FOCUS_START_ASTRO_AUTO_FOCUS")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                await asyncio.sleep(1)
                                if (ComResponse_message.code != protocol.OK):
                                    log.error("Error CMD_FOCUS_START_ASTRO_AUTO_FOCUS")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_FOCUS_START_ASTRO_AUTO_FOCUS", ComResponse_message.code)
                                else:
                                    log.info("OK CMD_FOCUS_START_ASTRO_AUTO_FOCUS")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CMD_FOCUS_START_ASTRO_AUTO_FOCUS", ComResponse_message.code)
                            # CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS = 15005; // Stop Capture
                            elif (WsPacket_message.cmd==protocol.CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                await asyncio.sleep(1)
                                if (ComResponse_message.code != protocol.OK):
                                    log.error("Error CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS", ComResponse_message.code)
                                else:
                                    log.info("OK CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS", ComResponse_message.code)
                            # CMD_CAMERA_TELE_PHOTOGRAPH = 10002; // //  Take photos
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_PHOTOGRAPH):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_CAMERA_TELE_PHOTOGRAPH")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CMD_CAMERA_TELE_PHOTOGRAPH {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_TELE_PHOTOGRAPH", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("Continue OK CMD_CAMERA_TELE_PHOTOGRAPH")

                            # CMD_CAMERA_TELE_PHOTOGRAPH = 10002; // //  End Take photos
                            elif (self.command==protocol.CMD_CAMERA_TELE_PHOTOGRAPH and WsPacket_message.cmd==protocol.CMD_NOTIFY_TELE_FUNCTION_STATE):
    
                                ResNotifyCamFunctionState_message = notify.ResNotifyCamFunctionState()
                                ResNotifyCamFunctionState_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_TELE_FUNCTION_STATE")
                                log.debug(f"receive notification data >> {ResNotifyCamFunctionState_message.state}")
                                log.debug(f">> {getAstroStateName(ResNotifyCamFunctionState_message.state)}")

                                # ASTRO_STATE_IDLE = 0; // Idle => End
                                if (ResNotifyCamFunctionState_message.state == notify.ASTRO_STATE_IDLE):
                                    log.info("Success TAKE PHOTO OK >> EXIT")
                                    log.success("Success TAKE PHOTO")

                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK  TAKE PHOTO", ResNotifyCamFunctionState_message.state)
                                    await asyncio.sleep(1)
                                elif (ResNotifyCamFunctionState_message.state == notify.ASTRO_STATE_RUNNING):
                                    log.info("Starting CMD_CAMERA_TELE_PHOTOGRAPH")
                                else:
                                    log.error("Error CMD_CAMERA_TELE_PHOTOGRAPH PROCESS STOP}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_TELE_PHOTOGRAPH PROCESS STOP", ResNotifyCamFunctionState_message.state)
                                    await asyncio.sleep(1)

                            # CMD_CAMERA_WIDE_PHOTOGRAPH = 12022; // //  Take photos
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_PHOTOGRAPH):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_CAMERA_WIDE_PHOTOGRAPH")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # OK = 0; // No Error
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CMD_CAMERA_WIDE_PHOTOGRAPH {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_WIDE_PHOTOGRAPH", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("Continue OK CMD_CAMERA_WIDE_PHOTOGRAPH")

                            # CMD_CAMERA_WIDE_PHOTOGRAPH = 12022; // //  End Take photos
                            elif (self.command==protocol.CMD_CAMERA_WIDE_PHOTOGRAPH and WsPacket_message.cmd==protocol.CMD_NOTIFY_WIDE_FUNCTION_STATE):
    
                                ResNotifyCamFunctionState_message = notify.ResNotifyCamFunctionState()
                                ResNotifyCamFunctionState_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_WIDE_FUNCTION_STATE")
                                log.debug(f"receive notification data >> {ResNotifyCamFunctionState_message.state}")
                                log.debug(f">> {getAstroStateName(ResNotifyCamFunctionState_message.state)}")

                                # ASTRO_STATE_IDLE = 0; // Idle => End
                                if (ResNotifyCamFunctionState_message.state == notify.ASTRO_STATE_IDLE):
                                    log.info("Success TAKE WIDE PHOTO OK >> EXIT")
                                    log.success("Success TAKE WIDE PHOTO")

                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK  TAKE WIDE PHOTO", ResNotifyCamFunctionState_message.state)
                                    await asyncio.sleep(1)
                                elif (ResNotifyCamFunctionState_message.state == notify.ASTRO_STATE_RUNNING):
                                    log.info("Starting CMD_CAMERA_WIDE_PHOTOGRAPH")
                                else:
                                    log.error("Error CMD_CAMERA_WIDE_PHOTOGRAPH PROCESS STOP}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_CAMERA_WIDE_PHOTOGRAPH PROCESS STOP", ResNotifyCamFunctionState_message.state)
                                    await asyncio.sleep(1)

                            # CMD_NOTIFY_STATE_ASTRO_CALIBRATION = 15210; // Astronomical calibration status
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_ASTRO_CALIBRATION):
                                ResNotifyStateAstroCalibration_message = notify.ResNotifyStateAstroCalibration()
                                ResNotifyStateAstroCalibration_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_STATE_ASTRO_CALIBRATION")
                                log.debug(f"receive notification data >> {ResNotifyStateAstroCalibration_message.state}")
                                log.debug(f">> {getAstroStateName(ResNotifyStateAstroCalibration_message.state)}")
                                log.debug(f"receive notification times >> {ResNotifyStateAstroCalibration_message.plate_solving_times}")

                                # ASTRO_STATE_IDLE = 0; // Idle state Only when Success or Previous Error
                                if (ResNotifyStateAstroCalibration_message.state == notify.ASTRO_STATE_IDLE):
                                    if (self.stopcalibration):
                                        log.error("Error CALIBRATION CODE_ASTRO_CALIBRATION_FAILED")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CODE_ASTRO_CALIBRATION_FAILED", protocol.CODE_ASTRO_CALIBRATION_FAILED)
                                        await asyncio.sleep(1)
                                    else :
                                        log.info("Success ASTRO CALIBRATION OK >> EXIT")
                                        log.success("Success ASTRO CALIBRATION")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO CALIBRATION", 0)
                                else:
                                    log.info("Continue Decoding CMD_NOTIFY_STATE_ASTRO_CALIBRATION")
                                    log.info(f"CALIBRATION: Phase #{ResNotifyStateAstroCalibration_message.plate_solving_times} State:{getAstroStateName(ResNotifyStateAstroCalibration_message.state)}")
                                    # send a notification
                                    message = f"CALIBRATION: Phase #{ResNotifyStateAstroCalibration_message.plate_solving_times} State:{getAstroStateName(ResNotifyStateAstroCalibration_message.state)}"
                                    await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)

                            # CMD_NOTIFY_STATE_ASTRO_GOTO = 15211; // Astronomical GOTO status
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_ASTRO_GOTO):
                                ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                                ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_STATE_ASTRO_GOTO")
                                log.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                log.debug(f">> {getAstroStateName(ResNotifyStateAstroGoto_message.state)}")
                                # send a notification
                                message = f"GOTO: State:{getAstroStateName(ResNotifyStateAstroGoto_message.state)}"
                                await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)

                            # CMD_NOTIFY_STATE_ASTRO_TRACKING = 15212; // Astronomical tracking status
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_ASTRO_TRACKING):
                                ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroTracking()
                                ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_STATE_ASTRO_TRACKING")
                                log.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                log.debug(f">> {getAstroStateName(ResNotifyStateAstroGoto_message.state)}")
                                log.debug(f"receive notification target_name >> {ResNotifyStateAstroGoto_message.target_name}")

                                # ASTRO_STATE_RUNNING = 1; // Running 
                                # Can be sending during CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE
                                # DSO or STELLAR
                                if ((self.command == protocol.CMD_ASTRO_START_GOTO_DSO) and ResNotifyStateAstroGoto_message.state == notify.ASTRO_STATE_RUNNING and ResNotifyStateAstroGoto_message.target_name == self.target_name):
                                    log.debug("ASTRO GOTO : SAME CMD AND TARGET")
                                    log.debug("ASTRO GOTO OK TRACKING >> EXIT")
                                    log.info("Success ASTRO DSO GOTO TRACKING START")
                                    log.success("Success ASTRO DSO GOTO TRACKING START")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK  ASTRO DSO GOTO TRACKING START", 0)
                                    await asyncio.sleep(1)

                                if ((self.command == protocol.CMD_ASTRO_START_GOTO_SOLAR_SYSTEM) and ResNotifyStateAstroGoto_message.state == notify.ASTRO_STATE_RUNNING and ResNotifyStateAstroGoto_message.target_name == self.target_name):
                                    log.debug("ASTRO GOTO : SAME CMD AND TARGET")
                                    log.debug("ASTRO GOTO OK TRACKING >> EXIT")
                                    log.info("Success ASTRO SOLAR GOTO TRACKING START")
                                    log.success("Success ASTRO SOLAR GOTO TRACKING START")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK  ASTRO SOLAR GOTO TRACKING START", 0)
                                    await asyncio.sleep(1)

                            # CMD_ASTRO_START_CALIBRATION = 11000; // Start calibration
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_CALIBRATION):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_START_CALIBRATION")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # CODE_ASTRO_CALIBRATION_FAILED = -11504; // Calibration failed
                                if (ComResponse_message.code == -11504):
                                    log.error("Error CALIBRATION >> EXIT")
                                    self.stopcalibration = True

                                # CODE_ASTRO_FUNCTION_BUSY = -11501; // Calibration failed
                                if (ComResponse_message.code == -11501):
                                    log.error("Error CALIBRATION BUSY >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CODE_ASTRO_CALIBRATION_FAILED", protocol.CODE_ASTRO_CALIBRATION_FAILED)
                                    await asyncio.sleep(1)
                                    self.stopcalibration = True

                                # CODE_ASTRO_PLATE_SOLVING_FAILED = -11500; // Plate Solving failed
                                if (ComResponse_message.code == -11500):
                                    log.info("Continue Decoding CMD_ASTRO_START_CALIBRATION")
                                    message = "CALIBRATION: Error Plate solving"
                                    await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)

                            # CMD_ASTRO_STOP_CALIBRATION = 11001; // Stop Calibration
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_STOP_CALIBRATION):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_STOP_CALIBRATION")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                # CODE_ASTRO_CALIBRATION_FAILED = -11504; // Calibration failed
                                if (ComResponse_message.code == -11504):
                                    log.error("Error CALIBRATION >> EXIT")
                                    self.stopcalibration = True

                                else:
                                    log.info("OK CMD_ASTRO_STOP_CALIBRATION")
                                    log.success("Success CMD_ASTRO_STOP_CALIBRATION")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Succcess CMD_ASTRO_STOP_CALIBRATION", ComResponse_message.code)
                                    self.stopcalibration = True

                            # CMD_SYSTEM_SET_TIME = 13000; // Set the system time
                            elif (WsPacket_message.cmd==protocol.CMD_SYSTEM_SET_TIME):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_SYSTEM_SET_TIME")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code == protocol.CODE_SYSTEM_SET_TIME_FAILED):
                                    log.error("Error CMD_SYSTEM_SET_TIME")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_SYSTEM_SET_TIME", ComResponse_message.code)
                                else:
                                    log.info("OK CMD_SYSTEM_SET_TIME")
                                    log.success("Success CMD_SYSTEM_SET_TIME")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Succcess CMD_SYSTEM_SET_TIME", ComResponse_message.code)

                            # CMD_SYSTEM_SET_TIME_ZONE = 13001; // Set the time zone
                            elif (WsPacket_message.cmd==protocol.CMD_SYSTEM_SET_TIME_ZONE):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_SYSTEM_SET_TIME_ZONE")
                                log.debug(f"receive code data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code == protocol.CODE_SYSTEM_SET_TIMEZONE_FAILED):
                                    log.error("Error CMD_SYSTEM_SET_TIME_ZONE")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_SYSTEM_SET_TIME_ZONE", ComResponse_message.code)
                                else:
                                    log.info("OK CMD_SYSTEM_SET_TIME_ZONE")
                                    log.success("Success CMD_SYSTEM_SET_TIME_ZONE")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Succcess CMD_SYSTEM_SET_TIME_ZONE", ComResponse_message.code)

                            # CMD_ASTRO_START_GOTO_DSO = 11002; // Start GOTO Deep Space Object
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_GOTO_DSO):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_START_GOTO_DSO")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error GOTO {ComResponse_message.code} >> EXIT")
                                    if (ComResponse_message.code == protocol.CODE_ASTRO_GOTO_FAILED):
                                        log.error("Error GOTO CODE_ASTRO_GOTO_FAILED")
                                    elif (ComResponse_message.code == protocol.CODE_STEP_MOTOR_LIMIT_POSITION_WARNING):
                                        log.error("Error GOTO CODE_STEP_MOTOR_LIMIT_POSITION_WARNING")
                                    elif (ComResponse_message.code == protocol.CODE_STEP_MOTOR_LIMIT_POSITION_HITTED):
                                        log.error("Error GOTO CODE_STEP_MOTOR_LIMIT_POSITION_HITTED")
                                    else:
                                        log.error(f"Error GOTO CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CODE_ASTRO_GOTO_FAILED", ComResponse_message.code)
                                    await asyncio.sleep(1)
                            # CMD_ASTRO_START_GOTO_SOLAR_SYSTEM = 11003; // Start GOTO SOLAR SYSTEM Object
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_GOTO_SOLAR_SYSTEM):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_START_GOTO_SOLAR_SYSTEM")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error GOTO {ComResponse_message.code} >> EXIT")
                                    if (ComResponse_message.code == protocol.CODE_ASTRO_GOTO_FAILED):
                                        log.error("Error GOTO CODE_ASTRO_GOTO_FAILED")
                                    elif (ComResponse_message.code == protocol.CODE_STEP_MOTOR_LIMIT_POSITION_WARNING):
                                        log.error("Error GOTO CODE_STEP_MOTOR_LIMIT_POSITION_WARNING")
                                    elif (ComResponse_message.code == protocol.CODE_STEP_MOTOR_LIMIT_POSITION_HITTED):
                                        log.error("Error GOTO CODE_STEP_MOTOR_LIMIT_POSITION_HITTED")
                                    else:
                                        log.error(f"Error GOTO CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CODE_ASTRO_GOTO_FAILED", ComResponse_message.code)
                                    await asyncio.sleep(1)
                            # CMD_ASTRO_STOP_GOTO = 11004; // Stop GOTO
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_STOP_GOTO):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_STOP_GOTO")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error STOP GOTO CODE {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error CMD_ASTRO_STOP_GOTO", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("OK CMD_ASTRO_STOP_GOTO")
                                    log.success("Success CMD_ASTRO_STOP_GOTO")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "Succcess CMD_ASTRO_STOP_GOTO", ComResponse_message.code)
                            # CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING = 11005; // Start Capture
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code == protocol.CODE_ASTRO_NEED_GOTO):
                                    log.warning("START_CAPTURE : ASTRO_NEED_GOTO message receive")
                                elif (ComResponse_message.code == protocol.CODE_ASTRO_FUNCTION_BUSY):
                                    log.warning("START_CAPTURE : CODE_ASTRO_FUNCTION_BUSY message receive")
                                    if (self.takePhotoStarted):
                                        log.notice(f"CAPTURE IN PROGRESS Continue ...")
                                    else:
                                        log.error(f"Error START_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error START_CAPTURE", ComResponse_message.code)
                                        await asyncio.sleep(1)
                                elif (ComResponse_message.code == protocol.CODE_ASTRO_NEED_ADJUST_SHOOT_PARAM):
                                    log.warning("START_CAPTURE : CODE_ASTRO_NEED_ADJUST_SHOOT_PARAM message receive")
                                    if (self.takePhotoStarted):
                                        log.notice(f"CAPTURE IN PROGRESS Continue ...")
                                    else:
                                        log.error(f"Error START_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error START_CAPTURE", ComResponse_message.code)
                                        await asyncio.sleep(1)
                                elif (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error START_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error START_CAPTURE", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    self.takePhotoStarted = True
                            # CMD_ASTRO_START_WIDE_CAPTURE_LIVE_STACKING = 11016; // Start WIDE Capture
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_WIDE_CAPTURE_LIVE_STACKING):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_START_WIDE_CAPTURE_LIVE_STACKING")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code == protocol.CODE_ASTRO_NEED_GOTO):
                                    log.warning("START_CAPTURE : ASTRO_NEED_GOTO message receive")
                                elif (ComResponse_message.code == protocol.CODE_ASTRO_FUNCTION_BUSY):
                                    log.warning("START_CAPTURE : CODE_ASTRO_FUNCTION_BUSY message receive")
                                    if (self.takeWidePhotoStarted):
                                        log.notice(f"CAPTURE IN PROGRESS Continue ...")
                                    else:
                                        log.error(f"Error START_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error START_CAPTURE", ComResponse_message.code)
                                        await asyncio.sleep(1)
                                elif (ComResponse_message.code == protocol.CODE_ASTRO_NEED_ADJUST_SHOOT_PARAM):
                                    log.warning("START_CAPTURE : CODE_ASTRO_NEED_ADJUST_SHOOT_PARAM message receive")
                                    if (self.takeWidePhotoStarted):
                                        log.notice(f"CAPTURE IN PROGRESS Continue ...")
                                    else:
                                        log.error(f"Error START_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                        await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error START_CAPTURE", ComResponse_message.code)
                                        await asyncio.sleep(1)
                                elif (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error START_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error START_CAPTURE", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    self.takeWidePhotoStarted = True
                            # CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING = 11006; // Stop Capture
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error STOP_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error STOP_CAPTURE", ComResponse_message.code)
                                    await asyncio.sleep(1)
                            # CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING = 11017; // Stop Capture ??
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING")
                                log.debug(f"receive data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error STOP_CAPTURE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "Error STOP_CAPTURE", ComResponse_message.code)
                                    await asyncio.sleep(1)
                            # CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING = 15208 // Test Capture Ending
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING):
                                ResNotifyOperationState_message = notify.ResNotifyOperationState()
                                ResNotifyOperationState_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING")
                                log.debug(f"receive notification data >> {ResNotifyOperationState_message.state}")
                                log.debug(f">> {getOperationStateName(ResNotifyOperationState_message.state)}")

                                if ( self.command==protocol.CMD_ASTRO_GO_LIVE and ResNotifyOperationState_message.state == notify.OPERATION_STATE_IDLE):
                                    log.info("ASTRO CAPTURE IDLE >> EXIT")
                                    log.info("Success ASTRO GO LIVE ENDING")
                                    log.success("Success ASTRO GO LIVE ENDING")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO GO LIVE ENDING", 0)
                                    await asyncio.sleep(1)

                                if ( self.command==protocol.CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING and ResNotifyOperationState_message.state == notify.OPERATION_STATE_RUNNING):
                                    log.info("ASTRO CAPTURE RUNNING")
                                    log.success("ASTRO CAPTURE RUNNING")
                                    self.takePhotoStarted = True
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO CAPTURE RUNNING", 0)
                                    await asyncio.sleep(1)

                                if ( ResNotifyOperationState_message.state == notify.OPERATION_STATE_RUNNING and self.RestartAstroCapture):
                                    self.AstroCapture = True

                                # OPERATION_STATE_STOPPED = 3; // Stopped
                                if ( self.AstroCapture and self.takePhotoStarted and ResNotifyOperationState_message.state == notify.OPERATION_STATE_STOPPED):
                                    log.debug("ASTRO CAPTURE OK STOPPING >> EXIT")
                                    log.info("Success ASTRO CAPTURE ENDING")
                                    log.success("Success ASTRO CAPTURE ENDING")
                                    self.AstroCapture = False
                                    self.RestartAstroCapture = False
                                    self.takePhotoStarted = False
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO CAPTURE ENDING", 0)
                                    await asyncio.sleep(1)
                                # OPERATION_STATE_STOPPED = 3; // Stopped
                                if ( self.RestartAstroCapture and ResNotifyOperationState_message.state == notify.OPERATION_STATE_STOPPED):
                                    log.debug("ASTRO CAPTURE OK STOPPING >> EXIT")
                                    log.info("Success ASTRO CAPTURE ENDING")
                                    log.success("Success ASTRO CAPTURE ENDING")
                                    self.AstroCapture = False
                                    self.RestartAstroCapture = False
                                    self.takePhotoStarted = False
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO CAPTURE ENDING", 0)
                                    await asyncio.sleep(1)
                            # CMD_NOTIFY_STATE_CAPTURE_RAW_WIDE_LIVE_STACKING = 15236 // Test Capture Ending
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STATE_WIDE_CAPTURE_RAW_LIVE_STACKING):
                                ResNotifyOperationState_message = notify.ResNotifyOperationState()
                                ResNotifyOperationState_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_STATE_CAPTURE_RAW_WIDE_LIVE_STACKING")
                                log.debug(f"receive notification data >> {ResNotifyOperationState_message.state}")
                                log.debug(f">> {getOperationStateName(ResNotifyOperationState_message.state)}")

                                if ( self.command==protocol.CMD_ASTRO_GO_LIVE and ResNotifyOperationState_message.state == notify.OPERATION_STATE_IDLE):
                                    log.info("ASTRO WIDE CAPTURE IDLE >> EXIT")
                                    log.info("Success ASTRO GO LIVE ENDING")
                                    log.success("Success ASTRO GO LIVE ENDING")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO GO LIVE ENDING", 0)
                                    await asyncio.sleep(1)

                                if ( self.command==protocol.CMD_ASTRO_START_WIDE_CAPTURE_LIVE_STACKING and ResNotifyOperationState_message.state == notify.OPERATION_STATE_RUNNING):
                                    log.info("ASTRO WIDE CAPTURE RUNNING")
                                    log.success("ASTRO WIDE CAPTURE RUNNING")
                                    self.takeWidePhotoStarted = True
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO WIDE CAPTURE RUNNING", 0)
                                    await asyncio.sleep(1)

                                if ( ResNotifyOperationState_message.state == notify.OPERATION_STATE_RUNNING and self.RestartAstroWideCapture):
                                    self.AstroWideCapture = True

                                # OPERATION_STATE_STOPPED = 3; // Stopped
                                if ( self.AstroWideCapture and ResNotifyOperationState_message.state == notify.OPERATION_STATE_STOPPED):
                                    log.debug("ASTRO CAPTURE OK STOPPING >> EXIT")
                                    log.info("Success ASTRO WIDE CAPTURE ENDING")
                                    log.success("Success ASTRO WIDE CAPTURE ENDING")
                                    self.AstroWideCapture = False
                                    self.RestartAstroWideCapture = False
                                    self.takeWidePhotoStarted = False
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO WIDE CAPTURE ENDING", 0)
                                    await asyncio.sleep(1)
                                # OPERATION_STATE_STOPPED = 3; // Stopped
                                if ( self.RestartAstroWideCapture and ResNotifyOperationState_message.state == notify.OPERATION_STATE_STOPPED):
                                    log.debug("ASTRO CAPTURE OK STOPPING >> EXIT")
                                    log.info("Success ASTRO WIDE CAPTURE ENDING")
                                    log.success("Success ASTRO WIDE CAPTURE ENDING")
                                    self.AstroWideCapture = False
                                    self.RestartAstroWideCapture = False
                                    self.takeWidePhotoStarted = False
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO WIDE CAPTURE ENDING", 0)
                                    await asyncio.sleep(1)
                            # CMD_NOTIFY_PROGRASS_CAPTURE_RAW_LIVE_STACKING = 15209 // Test Capture Ending
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_PROGRASS_CAPTURE_RAW_LIVE_STACKING):
                                ResNotifyProgressCaptureRawLiveStacking_message = notify.ResNotifyProgressCaptureRawLiveStacking()
                                ResNotifyProgressCaptureRawLiveStacking_message.ParseFromString(WsPacket_message.data)
                                self.takePhotoStarted = True
                                if self.RestartAstroCapture:
                                    self.AstroCapture = True
                                log.debug("Decoding CMD_NOTIFY_PROGRASS_CAPTURE_RAW_LIVE_STACKING")
                                log.debug(f"receive notification target_name >> {ResNotifyProgressCaptureRawLiveStacking_message.target_name}")
                                log.debug(f"receive notification total_count >> {ResNotifyProgressCaptureRawLiveStacking_message.total_count}")
                                update_count_type = ResNotifyProgressCaptureRawLiveStacking_message.update_count_type
                                if (update_count_type == 0 or update_count_type == 2):
                                   self.takePhotoCount = ResNotifyProgressCaptureRawLiveStacking_message.current_count
                                if (update_count_type == 1 or update_count_type == 2):
                                   self.takePhotoStacked = ResNotifyProgressCaptureRawLiveStacking_message.stacked_count
                                log.info(f"receive notification current_count >> {self.takePhotoCount}")
                                log.info(f"receive notification stacked_count >> {self.takePhotoStacked}")
                                message = f"current_count >> {self.takePhotoCount} - stacked_count >> {self.takePhotoStacked}"
                                # send a notification
                                await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)
                            # CMD_NOTIFY_PROGRASS_WIDE_CAPTURE_RAW_LIVE_STACKING = 15237 // Test Capture Ending
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_PROGRASS_WIDE_CAPTURE_RAW_LIVE_STACKING):
                                ResNotifyProgressCaptureRawLiveStacking_message = notify.ResNotifyProgressCaptureRawLiveStacking()
                                ResNotifyProgressCaptureRawLiveStacking_message.ParseFromString(WsPacket_message.data)
                                self.takeWidePhotoStarted = True
                                if self.RestartAstroWideCapture:
                                    self.AstroWideCapture = True
                                log.debug("Decoding CMD_NOTIFY_PROGRASS_WIDE_CAPTURE_RAW_LIVE_STACKING")
                                log.debug(f"receive notification target_name >> {ResNotifyProgressCaptureRawLiveStacking_message.target_name}")
                                log.debug(f"receive notification total_count >> {ResNotifyProgressCaptureRawLiveStacking_message.total_count}")
                                update_count_type = ResNotifyProgressCaptureRawLiveStacking_message.update_count_type
                                if (update_count_type == 0 or update_count_type == 2):
                                   self.takeWidePhotoCount = ResNotifyProgressCaptureRawLiveStacking_message.current_count
                                if (update_count_type == 1 or update_count_type == 2):
                                   self.takeWidePhotoStacked = ResNotifyProgressCaptureRawLiveStacking_message.stacked_count
                                log.info(f"receive notification current_count >> {self.takeWidePhotoCount}")
                                log.info(f"receive notification stacked_count >> {self.takeWidePhotoStacked}")
                                message = f"current_count >> {self.takeWidePhotoCount} - stacked_count >> {self.takeWidePhotoStacked}"
                                # send a notification
                                await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)
                            # CMD_CAMERA_TELE_SET_ALL_PARAMS
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_ALL_PARAMS):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_SET_ALL_PARAMS")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET ALL PARAMS {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET ALL PARAMS", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    # Signal the ping and receive functions to stop
                                    log.info("Success CAMERA SET ALL PARAM OK >> EXIT")
                                    log.success("Success CAMERA SET ALL PARAM")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET ALL PARAMS", ComResponse_message.code)
                                    await asyncio.sleep(1)
                            # CMD_CAMERA_TELE_GET_ALL_PARAMS
                            elif (self.command == protocol.CMD_CAMERA_TELE_GET_ALL_PARAMS and WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_ALL_PARAMS):
                                common_param_instance = base__pb2.CommonParam()
                                # Populate fields of common_param_instance
                                ResGetAllParams_message = camera.ResGetAllParams()
                                # Add common_param_instance to the repeated field all_params
                                ResGetAllParams_message.all_params.append(common_param_instance)

                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_ALL_PARAMS")
                                log.debug(f"receive request response data >> {ResGetAllParams_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")
                                if (ResGetAllParams_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET ALL_PARAMS {getErrorCodeValueName(ResGetAllParams_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET ALL PARAMS", ResGetAllParams_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    # Signal the ping and receive functions to stop
                                    log.info("Success CAMERA GET ALL_PARAMS OK >> EXIT")
                                    log.success("Success CAMERA GET ALL_PARAMS")
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
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET ALL_PARAMS", res_get_all_params_data)
                                    await asyncio.sleep(1)
                            # CMD_CAMERA_WIDE_SET_ALL_PARAMS
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_SET_ALL_PARAMS):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_SET_ALL_PARAMS")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA WIDE SET ALL PARAMS {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA WIDE SET ALL PARAMS", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    # Signal the ping and receive functions to stop
                                    log.info("Success CAMERA WIDE SET ALL PARAM OK >> EXIT")
                                    log.success("Success CAMERA WIDE SET ALL PARAM")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA WIDE SET ALL PARAMS", ComResponse_message.code)
                                    await asyncio.sleep(1)
                            # CMD_CAMERA_WIDE_GET_ALL_PARAMS
                            elif (self.command == protocol.CMD_CAMERA_WIDE_GET_ALL_PARAMS and WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_GET_ALL_PARAMS):
                                common_param_instance = base__pb2.CommonParam()
                                # Populate fields of common_param_instance
                                ResGetAllParams_message = camera.ResGetAllParams()
                                # Add common_param_instance to the repeated field all_params
                                ResGetAllParams_message.all_params.append(common_param_instance)

                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_GET_ALL_PARAMS")
                                log.debug(f"receive request response data >> {ResGetAllParams_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")
                                if (ResGetAllParams_message.code != protocol.OK):
                                    log.error(f"Error CAMERA _WIDE_GET ALL_PARAMS {getErrorCodeValueName(ResGetAllParams_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA_WIDE_GET ALL PARAMS", ResGetAllParams_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    # Signal the ping and receive functions to stop
                                    log.info("Success CAMERA_WIDE_GET ALL_PARAMS OK >> EXIT")
                                    log.success("Success CAMERA_WIDE_GET ALL_PARAMS")
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
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA _WIDE_GET ALL_PARAMS", res_get_all_params_data)
                                    await asyncio.sleep(1)
                            # CMD_CAMERA_TELE_SET_FEATURE_PARAM
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_FEATURE_PARAM):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_SET_FEATURE_PARAM")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA FEATURE PARAM {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET FEATURE PARAM", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    # Signal the ping and receive functions to stop
                                    log.info("Success CAMERA SET FEATURE PARAM OK >> EXIT")
                                    log.success("Success CAMERA SET FEATURE PARAM")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET FEATURE PARAM", ComResponse_message.code)
                            # CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS
                            elif (self.command == protocol.CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS and WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS):
                                common_param_instance = base__pb2.CommonParam()
                                # Populate fields of common_param_instance
                                ResGetAllFeatureParams_message = camera.ResGetAllFeatureParams()
                                # Add common_param_instance to the repeated field all_feature_params
                                ResGetAllFeatureParams_message.all_feature_params.append(common_param_instance)

                                ResGetAllFeatureParams_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS")
                                log.debug(f"receive request response data >> {ResGetAllFeatureParams_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllFeatureParams_message.code)}")
                                if (ResGetAllFeatureParams_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET ALL FEATURE PARAMS {getErrorCodeValueName(ResGetAllFeatureParams_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET ALL FEATURE PARAMS", ResGetAllFeatureParams_message.code)
                                    await asyncio.sleep(1)
                                else:
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
                                    log.info(f"Success CAMERA GET ALL FEATURE PARAMS")
                                    log.success(f"Success CAMERA GET ALL FEATURE PARAMS")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET ALL FEATURE PARAMS", res_get_all_params_data)
                            # CMD_CAMERA_TELE_SET_EXP_MODE
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_EXP_MODE and self.toDoSetExpMode == True):
                                self.toDoSetExpMode = False
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_SET_EXP_MODE")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET EXP MODE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET EXP MODE", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET EXP MODE OK >> EXIT")
                                    log.success(f"Success CAMERA SET EXP MODE:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET EXP MODE", ComResponse_message.code)
                            elif (self.command == protocol.CMD_CAMERA_TELE_SET_EXP_MODE and WsPacket_message.cmd==protocol.CMD_NOTIFY_TELE_SET_PARAM and self.toDoSetExpMode == True):
                                ResGetAllParams_message = camera.ResGetAllParams()
                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)

                                # Access the first common_param_instance directly
                                common_param_instance = ResGetAllParams_message.all_params[0]
                                log.debug("Decoding EXP_MODE CMD_NOTIFY_TELE_SET_PARAM")
                                log.debug(f"receive request response data >> {common_param_instance}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")

                                # Check the specific condition and take actions accordingly
                                if (common_param_instance.id == 0):
                                    self.toDoSetWideExpMode = False
                                    log.info("CAMERA SET TELE EXP MODE OK >> EXIT")
                                    log.success(f"Success CAMERA SET TELE EXP MODE:  {common_param_instance.auto_mode}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET TELE EXP MODE", protocol.OK)
                            # CMD_CAMERA_TELE_SET_EXP
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_EXP and self.toDoSetExp == True):
                                self.toDoSetExp == False
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_SET_EXP")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET EXP {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET EXP", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET EXP OK >> EXIT")
                                    log.success(f"Success CAMERA SET EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET EXP", ComResponse_message.code)
                            elif (self.command == protocol.CMD_CAMERA_TELE_SET_EXP and WsPacket_message.cmd==protocol.CMD_NOTIFY_TELE_SET_PARAM and self.toDoSetExp == True):
                                ResGetAllParams_message = camera.ResGetAllParams()
                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)

                                # Access the first common_param_instance directly
                                common_param_instance = ResGetAllParams_message.all_params[0]
                                log.debug("Decoding EXP CMD_NOTIFY_TELE_SET_PARAM")
                                log.debug(f"receive request response data >> {common_param_instance}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")

                                # Check the specific condition and take actions accordingly
                                if (common_param_instance.id == 0):
                                    self.toDoSetExp = False
                                    log.info("CAMERA SET TELE EXP OK >> EXIT")
                                    log.success(f"Success CAMERA SET TELE EXP:  {common_param_instance.index}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET TELE EXP", protocol.OK)
                            # CMD_CAMERA_TELE_GET_EXP
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_EXP and WsPacket_message.type == 3):
                                ComResponseWithDouble_message = base__pb2.ComResWithDouble()
                                ComResponseWithDouble_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_EXP")
                                log.debug(f"receive request response data >> {ComResponseWithDouble_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponseWithDouble_message.code)}")
                                if (ComResponseWithDouble_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET EXP {getErrorCodeValueName(ComResponseWithDouble_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET EXP", ComResponseWithDouble_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET EXP OK >> EXIT")
                                    log.success(f"Success CAMERA GET EXP:  {ComResponseWithDouble_message.value}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET EXP", ComResponseWithDouble_message)
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_EXP):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_EXP")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET EXP {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET EXP", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET EXP OK >> EXIT")
                                    log.success(f"Success CAMERA GET EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET EXP", ComResponse_message.code)
                            # CMD_CAMERA_TELE_SET_GAIN
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_GAIN and WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_GAIN and self.toDoSetGain == True):
                                self.toDoSetGain == False
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_SET_GAIN")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET GAIN {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET GAIN", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET GAIN OK >> EXIT")
                                    log.success(f"Success CAMERA SET GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET GAIN", ComResponse_message.code)
                            elif (self.command == protocol.CMD_CAMERA_TELE_SET_GAIN and WsPacket_message.cmd==protocol.CMD_NOTIFY_TELE_SET_PARAM and self.toDoSetGain == True):
                                ResGetAllParams_message = camera.ResGetAllParams()
                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)

                                # Access the first common_param_instance directly
                                common_param_instance = ResGetAllParams_message.all_params[0]
                                log.debug("Decoding GAIN CMD_NOTIFY_TELE_SET_PARAM")
                                log.debug(f"receive request response data >> {common_param_instance}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")

                                # Check the specific condition and take actions accordingly
                                if common_param_instance.id == 1:
                                    self.toDoSetGain = False
                                    log.info("CAMERA SET TELE GAIN >> EXIT")
                                    log.success(f"Success CAMERA SET TELE GAIN: index {common_param_instance.index}")
                                    await self.result_receive_messages(
                                        self.command,
                                        WsPacket_message.cmd,
                                        Dwarf_Result.OK,
                                        "OK CAMERA SET TELE GAIN",
                                        protocol.OK
                                    )
                            # CMD_CAMERA_TELE_GET_GAIN
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_GAIN")
                                log.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET GAIN {getErrorCodeValueName(ComResWithInt_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET GAIN", ComResWithInt_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET GAIN OK >> EXIT")
                                    log.success(f"Success CAMERA GET GAIN:  {ComResWithInt_message.value}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET GAIN", ComResWithInt_message)
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_GAIN")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET GAIN {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET GAIN", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET GAIN OK >> CONTINUE TO GET VALUE")
                                    #log.success(f"Success CAMERA GET GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    #await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET GAIN", ComResponse_message.code)
                            # CMD_CAMERA_TELE_GET_GAIN MODE
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN_MODE and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_GAIN_MODE")
                                log.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET GAIN MODE {getErrorCodeValueName(ComResWithInt_message.code)} >> EXIT")
                                    # Signal the ping and receive functions to stop
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET GAIN MODE", ComResWithInt_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    # Signal the ping and receive functions to stop
                                    log.info("CAMERA GET GAIN MODE OK >> EXIT")
                                    log.success(f"Success CAMERA GET GAIN MODE:  {ComResWithInt_message.value}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET GAIN", ComResWithInt_message)
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_GAIN_MODE):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_GAIN_MODE")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET GAIN MODE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET GAIN MODE", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET GAIN MODE OK >> EXIT")
                                    log.success(f"Success CAMERA GET GAIN MODE:  {ComResWithInt_message.value}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET GAIN", ComResWithInt_message.code)
                            # CMD_CAMERA_TELE_GET_BRIGHTNESS
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_BRIGHTNESS and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_BRIGHTNESS")
                                log.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET BRIGHTNESS {getErrorCodeValueName(ComResWithInt_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET BRIGHTNESS", ComResWithInt_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET BRIGHTNESS MODE OK >> EXIT")
                                    log.success(f"Success CAMERA GET BRIGHTNESS:  {ComResWithInt_message.value}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET BRIGHTNESS", ComResWithInt_message)
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_SET_IRCUT):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_SET_IRCUT")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET IRCUT {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET IRCUT", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET IRCUT OK >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET IRCUT", ComResponse_message.code)
                                    log.success(f"Success CAMERA SET IRCUT:  {getErrorCodeValueName(ComResponse_message.code)}")
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_IRCUT and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_IRCUT")
                                log.debug(f"receive request response data >> {ComResWithInt_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET IRCUT {getErrorCodeValueName(ComResWithInt_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET IRCUT", ComResWithInt_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET IRCUT OK >> EXIT")
                                    log.success(f"Success CAMERA GET IRCUT:  {ComResWithInt_message.value}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET IRCUT", ComResWithInt_message.code)
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_TELE_GET_IRCUT):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_TELE_GET_IRCUT")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET IRCUT {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET IRCUT", ComResponse_message)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET GRCUT OK >> EXIT")
                                    log.success(f"Success CAMERA GET IRCUT:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET IRCUT", ComResponse_message.code)
                            # CMD_CAMERA_WIDE_SET_EXP_MODE
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_SET_EXP_MODE and self.toDoSetWideExpMode == True):
                                self.toDoSetWideExpMode = False
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_SET_EXP_MODE")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET WIDE EXP MODE {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET WIDE EXP MODE", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET WIDE EXP MODE OK >> EXIT")
                                    log.success(f"Success CAMERA SET WIDE EXP MODE:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET WIDE EXP MODE", ComResponse_message.code)
                            elif (self.command == protocol.CMD_CAMERA_WIDE_SET_EXP_MODE and WsPacket_message.cmd==protocol.CMD_NOTIFY_WIDE_SET_PARAM and self.toDoSetWideExpMode == True):
                                ResGetAllParams_message = camera.ResGetAllParams()
                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)

                                # Access the first common_param_instance directly
                                common_param_instance = ResGetAllParams_message.all_params[0]
                                log.debug("Decoding EXP_MODE CMD_NOTIFY_WIDE_SET_PARAM")
                                log.debug(f"receive request response data >> {common_param_instance}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")

                                # Check the specific condition and take actions accordingly
                                if (common_param_instance.id == 0):
                                    self.toDoSetWideExpMode = False
                                    log.info("CAMERA SET WIDE EXP MODE OK >> EXIT")
                                    log.success(f"Success CAMERA SET WIDE EXP MODE:  {common_param_instance.auto_mode}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET WIDE EXP MODE", protocol.OK)
                            # CMD_CAMERA_WIDE_SET_EXP
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_SET_EXP and self.toDoSetWideExp == True):
                                self.toDoSetWideExp == False
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_SET_EXP")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET WIDE EXP {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET WIDE EXP", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET WIDE EXP OK >> EXIT")
                                    log.success(f"Success CAMERA SET WIDE EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET WIDE EXP", ComResponse_message.code)
                            elif (self.command == protocol.CMD_CAMERA_WIDE_SET_EXP and WsPacket_message.cmd==protocol.CMD_NOTIFY_WIDE_SET_PARAM and self.toDoSetWideExp == True):
                                ResGetAllParams_message = camera.ResGetAllParams()
                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)

                                # Access the first common_param_instance directly
                                common_param_instance = ResGetAllParams_message.all_params[0]
                                log.debug("Decoding EXP CMD_NOTIFY_WIDE_SET_PARAM")
                                log.debug(f"receive request response data >> {common_param_instance}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")

                                # Check the specific condition and take actions accordingly
                                if (common_param_instance.id == 0):
                                    self.toDoSetWideExp = False
                                    log.info("CAMERA SET WIDE EXP OK >> EXIT")
                                    log.success(f"Success CAMERA SET WIDE EXP:  {common_param_instance.index}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET WIDE EXP", protocol.OK)
                            # CMD_CAMERA_WIDE_GET_EXP
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_GET_EXP and WsPacket_message.type == 3):
                                ComResponseWithDouble_message = base__pb2.ComResWithDouble()
                                ComResponseWithDouble_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_GET_EXP")
                                log.debug(f"receive request response data >> {ComResponseWithDouble_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponseWithDouble_message.code)}")
                                if (ComResponseWithDouble_message.code != protocol.OK):
                                    log.error(f"Error CAMERA WIDE GET EXP {getErrorCodeValueName(ComResponseWithDouble_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA WIDE GET EXP", ComResponseWithDouble_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET WIDE EXP OK >> EXIT")
                                    log.success(f"Success CAMERA WIDE GET EXP:  {ComResponseWithDouble_message.value}")
                                    data = { "code" : ComResponseWithDouble_message.code , "value" : ComResponseWithDouble_message.value}
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA WIDE GET EXP", data)
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_GET_EXP):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_GET_EXP")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA WIDE GET EXP {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET EXP", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET EXP OK >> CONTINUE TO GET VALUE")
                                    #log.success(f"Success CAMERA WIDE GET EXP:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    #await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET EXP", ComResponse_message.code)
                            # CMD_CAMERA_WIDE_SET_GAIN
                            elif (self.command == protocol.CMD_CAMERA_WIDE_SET_GAIN and WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_SET_GAIN and self.toDoSetWideGain == True):
                                self.toDoSetWideGain == False

                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_SET_GAIN")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA SET WIDE  GAIN {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA SET WIDE  GAIN", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA SET WIDE GAIN OK >> EXIT")
                                    log.success(f"Success CAMERA SET WIDE  GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA SET WIDE  GAIN", ComResponse_message.code)
                            elif (self.command == protocol.CMD_CAMERA_WIDE_SET_GAIN and WsPacket_message.cmd==protocol.CMD_NOTIFY_WIDE_SET_PARAM and self.toDoSetWideGain == True):
                                ResGetAllParams_message = camera.ResGetAllParams()
                                ResGetAllParams_message.ParseFromString(WsPacket_message.data)

                                # Access the first common_param_instance directly
                                common_param_instance = ResGetAllParams_message.all_params[0]
                                log.debug("Decoding GAIN CMD_NOTIFY_WIDE_SET_PARAM")
                                log.debug(f"receive request response data >> {common_param_instance}")
                                log.debug(f">> {getErrorCodeValueName(ResGetAllParams_message.code)}")

                                # Check the specific condition and take actions accordingly
                                if common_param_instance.id == 1:
                                    self.toDoSetWideGain = False
                                    log.info("CAMERA SET WIDE GAIN >> EXIT")
                                    log.success(f"Success CAMERA SET WIDE GAIN: index {common_param_instance.index}")
                                    await self.result_receive_messages(
                                        self.command,
                                        WsPacket_message.cmd,
                                        Dwarf_Result.OK,
                                        "OK CAMERA SET WIDE GAIN",
                                        protocol.OK
                                    )
                            # CMD_CAMERA_WIDE_GET_GAIN
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_GET_GAIN and WsPacket_message.type == 3):
                                ComResWithInt_message = base__pb2.ComResWithInt()
                                ComResWithInt_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_GET_GAIN")
                                log.debug(f"receive request response data >> {ComResWithInt_message}")
                                log.debug(f">> {getErrorCodeValueName(ComResWithInt_message.code)}")
                                if (ComResWithInt_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET WIDE GAIN {getErrorCodeValueName(ComResWithInt_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET WIDE GAIN", ComResWithInt_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET WIDE GAIN OK >> EXIT ")
                                    log.success(f"Success CAMERA GET WIDE GAIN:  {ComResWithInt_message.value}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET WIDE GAIN", ComResWithInt_message.value)
                            elif (WsPacket_message.cmd==protocol.CMD_CAMERA_WIDE_GET_GAIN):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_CAMERA_WIDE_GET_GAIN")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error CAMERA GET WIDE GAIN {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR CAMERA GET WIDE GAIN", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CAMERA GET WIDE GAIN OK >> CONTINUE TO GET VALUE")
                                    #log.success(f"Success CAMERA GET WIDE GAIN:  {getErrorCodeValueName(ComResponse_message.code)}")
                                    #await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA GET WIDE GAIN", ComResponse_message.code)
                            # CMD_NOTIFY_TELE_SET_PARAM ignore multiple message
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_TELE_SET_PARAM):
                                # send a notification
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
                                log.debug(f"received CMD_NOTIFY_TELE_SET_PARAM : {res_get_all_params_data}")
                                # Log the data received
                                all_params = res_get_all_params_data.get("all_params", [])
                                if len(all_params) > 0:                            
                                    fct_log_detail_tele_param(param = all_params[0])
                                else:
                                    log.info(f"Logging TELE Param: No DATA!")
                                # send a notification
                                message = f"CMD_NOTIFY_TELE_SET_PARAM received (notify)"
                                await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)
                            # CMD_NOTIFY_WIDE_SET_PARAM ignore multiple message
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_WIDE_SET_PARAM):
                                # send a notification
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
                                log.debug(f"received CMD_NOTIFY_WIDE_SET_PARAM : {res_get_all_params_data}")
                                # Log the data received
                                all_params = res_get_all_params_data.get("all_params", [])
                                if len(all_params) > 0:                            
                                    fct_log_detail_wide_param(param = all_params[0])
                                else:
                                    log.info(f"Logging WIDE Param: No DATA!")
                                # send a notification
                                message = f"CMD_NOTIFY_WIDE_SET_PARAM received (notify)"
                                await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)
                            # CMD_NOTIFY_SET_FEATURE_PARAM ignore multiple message
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_SET_FEATURE_PARAM):
                                # send a notification
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
                                log.debug(f"received CMD_NOTIFY_SET_FEATURE_PARAM : {res_get_all_params_data}")
                                # Log the data received
                                all_params = res_get_all_params_data.get("all_params", [])
                                if len(all_params) > 0:                            
                                    fct_log_feature_param(param = all_params[0])
                                else:
                                    log.info(f"Logging Features Param: No DATA!")
                                # send a notification
                                message = f"CMD_NOTIFY_SET_FEATURE_PARAM received (notify)"
                                await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)
                            # CMD_ASTRO_START_EQ_SOLVING
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_START_EQ_SOLVING):
                                ResStartEqSolving_message = astro.ResStartEqSolving()
                                ResStartEqSolving_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_ASTRO_START_EQ_SOLVING")
                                log.debug(f"receive request response data >> {ResStartEqSolving_message}")
                                log.debug(f" ASTRO START EQ SOLVING azi_err:  {ResStartEqSolving_message.azi_err}")
                                log.debug(f" ASTRO START EQ SOLVING alt_err:  {ResStartEqSolving_message.alt_err}")
                                log.debug(f">> {getErrorCodeValueName(ResStartEqSolving_message.code)}")
                                if (ResStartEqSolving_message.code != protocol.OK):
                                    log.error(f"Error ASTRO START EQ SOLVING {getErrorCodeValueName(ResStartEqSolving_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR ASTRO START EQ SOLVING", ResStartEqSolving_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CMD_ASTRO_START_EQ_SOLVING >> EXIT ")
                                    log.success(f"Success ASTRO START EQ SOLVING azi_err:  {ResStartEqSolving_message.azi_err}")
                                    log.success(f"Success ASTRO START EQ SOLVING alt_err:  {ResStartEqSolving_message.alt_err}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK CAMERA ASTRO START EQ SOLVING", ResStartEqSolving_message.code)
                            # CMD_ASTRO_STOP_EQ_SOLVING
                            elif (WsPacket_message.cmd==protocol.CMD_ASTRO_STOP_EQ_SOLVING and WsPacket_message.type == 3):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_ASTRO_STOP_EQ_SOLVING")
                                log.debug(f"receive request response data >> {ComResponse_message}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if (ComResponse_message.code != protocol.OK):
                                    log.error(f"Error ASTRO STOP EQ SOLVING {getErrorCodeValueName(ComResponse_message.code)} >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.ERROR, "ERROR ASTRO STOP EQ SOLVING", ComResponse_message.code)
                                    await asyncio.sleep(1)
                                else:
                                    log.info("CMD_ASTRO_STOP_EQ_SOLVING STOPPING >> EXIT ")
                                    log.success(f"Success ASTRO STOP EQ SOLVING:  {ComResponse_message.code}")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK ASTRO STOP EQ SOLVING ", ComResponse_message.code)
                            # CMD_NOTIFY_EQ_SOLVING_STATE = 15239; //EQ check status
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_EQ_SOLVING_STATE):
                                ResNotifyEqSolvingState_message = notify.ResNotifyEqSolvingState()
                                ResNotifyEqSolvingState_message.ParseFromString(WsPacket_message.data)

                                log.debug("Decoding CMD_NOTIFY_EQ_SOLVING_STATE")
                                log.debug(f"receive notification step >> {ResNotifyEqSolvingState_message.step}")
                                log.debug(f">> {notify.ResNotifyEqSolvingState.Action.Name(ResNotifyEqSolvingState_message.step)}")
                                log.debug(f"receive notification state >> {ResNotifyEqSolvingState_message.state}")
                                log.debug(f">> {getAstroStateName(ResNotifyEqSolvingState_message.state)}")

                                if (self.startEQSolving == False):
                                    self.startEQSolving = True
                                    log.info("Starting EQ SOLVING")
                                    message = f"EQ SOLVING: Starting.."
                                    await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)

                                log.info("Continue Decoding CMD_ASTRO_START_EQ_SOLVING")
                                message = f"EQ SOLVING: Step #{notify.ResNotifyEqSolvingState.Action.Name(ResNotifyEqSolvingState_message.step)} State:{getAstroStateName(ResNotifyEqSolvingState_message.state)}"
                                await self.result_notification_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, message, 0)

                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_POWER_OFF):
                                ComResponse_message = base__pb2.ComResponse()
                                ComResponse_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_NOTIFY_POWER_OFF")
                                log.debug(f"receive request response data >> {ComResponse_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")
                                log.success("CMD_NOTIFY_POWER_OFF received >> EXIT")
                                await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "POWER OFF", protocol.OK)
                                # disconnect  
                                await asyncio.sleep(1)
                                await self.disconnect()
                            # notify Battery level
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_ELE):
                                ComResWithInt_message_message = base__pb2.ComResWithInt()
                                ComResWithInt_message_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_NOTIFY_ELE")
                                log.debug(f"receive request response value >> {ComResWithInt_message_message.value}")
                                log.debug(f">> {getErrorCodeValueName(ComResWithInt_message_message.code)}")
                                value = ComResWithInt_message_message.value
                                # notify ?
                                if (self.BatteryLevelDwarf is None or abs(self.BatteryLevelDwarf - value) >= 10 or ((value == 100) and abs(self.BatteryLevelDwarf - value) >= 1) or ((value < 10) and (self.BatteryLevelDwarf - value) >= 1)):
                                   if value < 10:
                                       log.warning(f"Battery Level is {value}%")
                                   else:
                                       log.notice(f"Battery Level is {value}%")
                                   self.BatteryLevelDwarf = value
                            # CMD_NOTIFY_TEMPERATURE 15243
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_TEMPERATURE):
                                ResNotifyTemperature_message = notify.ResNotifyTemperature()
                                ResNotifyTemperature_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding TEMPERATURE ")
                                log.debug(f"receive request temperature value >> {ResNotifyTemperature_message.temperature}")
                                log.debug(f">> {getErrorCodeValueName(ResNotifyTemperature_message.code)}")
                                value = ResNotifyTemperature_message.temperature
                                # notify ?
                                if (self.TemperatureLevelDwarf is None or abs(self.TemperatureLevelDwarf - value) >= 5):
                                   log.notice(f"Temperature is {value}°C - {(value/5)+32}°F")
                                   self.TemperatureLevelDwarf = value
                            # CMD_NOTIFY_STREAM_TYPE 15234
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_STREAM_TYPE):
                                ResNotifyStreamType_message = notify.ResNotifyStreamType()
                                ResNotifyStreamType_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_NOTIFY_STREAM_TYPE ")
                                log.debug(f"receive request Stream type (RTSP , JPEG) >> {ResNotifyStreamType_message.stream_type}")
                                log.debug(f"receive request Camera value >> {ResNotifyStreamType_message.cam_id}")
                                cameraId = ResNotifyStreamType_message.cam_id
                                value = ResNotifyStreamType_message.stream_type
                                # notify ?
                                if (self.StreamTypeDwarf is None or (self.StreamTypeDwarf != value)):
                                  if (value == 1):
                                    log.notice(f"Dwarf Stream Video Type is RTSP for {'Wide_Angle' if cameraId == 1 else 'Tele Photo'}.")
                                  elif (value == 2):
                                    log.notice(f"Dwarf Stream Video Type is JPEG for {'Wide_Angle' if cameraId == 1 else 'Tele Photo'}.")
                                  else :
                                    log.notice("Dwarf Stream Video Type is unknown!")
                                  self.StreamTypeDwarf = value
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_SDCARD_INFO):
                                ResNotifySDcardInfo_message = notify.ResNotifySDcardInfo()
                                ResNotifySDcardInfo_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding CMD_NOTIFY_SDCARD_INFO")
                                log.debug(f"receive request response code >> {ResNotifySDcardInfo_message.code}")
                                log.debug(f">> {getErrorCodeValueName(ResNotifySDcardInfo_message.code)}")
                                availableSizeDwarf = ResNotifySDcardInfo_message.available_size
                                totalSizeDwarf = ResNotifySDcardInfo_message.total_size
                                # notify ?
                                if (self.totalSizeDwarf is None or (self.availableSizeDwarf - availableSizeDwarf) >= 10 or ((availableSizeDwarf < 10) and (self.availableSizeDwarf - availableSizeDwarf) >= 1)):
                                   if availableSizeDwarf < 10:
                                       log.warning(f"Available Space: {availableSizeDwarf}/{totalSizeDwarf} GB")
                                   else:
                                       log.notice(f"Available Space: {availableSizeDwarf}/{totalSizeDwarf} GB")
                                   self.availableSizeDwarf = availableSizeDwarf
                                   self.totalSizeDwarf = totalSizeDwarf
                            # CMD_NOTIFY_FOCUS 15257
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_FOCUS):
                                ResNotifyFocus_message = notify.ResNotifyFocus()
                                ResNotifyFocus_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding FOCUS ")
                                log.debug(f"receive request focus value >> {ResNotifyFocus_message.focus}")
                                value = ResNotifyFocus_message.focus
                                # notify ?
                                if (self.FocusValueDwarf is None or self.FocusValueDwarf != value):
                                   log.notice(f"Focus Position is {value}")
                                   self.FocusValueDwarf = value
                            # CMD_NOTIFY_RGB_STATE 15221
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_RGB_STATE):
                                ResNotifyRgbState_message = notify.ResNotifyRgbState()
                                ResNotifyRgbState_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding RGB STATE ")
                                value = ResNotifyRgbState_message.state
                                display_value = getPowerStateName(value)
                                log.debug(f"receive request state >> {display_value}")
                                # notify ?
                                if (self.command == protocol.CMD_RGB_POWER_OPEN_RGB or self.command == protocol.CMD_RGB_POWER_CLOSE_RGB):
                                    log.success("CMD_NOTIFY_RGB_STATE received >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK TOOGLE RGB INDICATOR", value)
                                if (self.RgbIndStateDwarf is None or self.RgbIndStateDwarf != value):
                                   log.notice(f"RGB Indicator is {display_value}")
                                   self.RgbIndStateDwarf = value
                            # CMD_NOTIFY_POWER_IND_STATE 15222
                            elif (WsPacket_message.cmd==protocol.CMD_NOTIFY_POWER_IND_STATE):
                                ResNotifyPowerIndState_message = notify.ResNotifyPowerIndState()
                                ResNotifyPowerIndState_message.ParseFromString(WsPacket_message.data)
                                log.debug("Decoding POWER IND ")
                                log.debug(f"receive request state >> {getPowerStateName(ResNotifyPowerIndState_message.state)} ")
                                value = ResNotifyPowerIndState_message.state
                                # notify ?
                                if (self.command == protocol.CMD_RGB_POWER_POWERIND_ON or self.command == protocol.CMD_RGB_POWER_POWERIND_OFF):
                                    log.success("CMD_NOTIFY_POWER_IND_STATE received >> EXIT")
                                    await self.result_receive_messages(self.command, WsPacket_message.cmd, Dwarf_Result.OK, "OK TOOGLE POWER INDICATOR", value)
                                if (self.PowerIndStateDwarf is None or self.PowerIndStateDwarf != value):
                                   log.notice(f"Power Indicator is {getPowerStateName(value)}")
                                   self.PowerIndStateDwarf = value
                            # Unknown
                            elif (WsPacket_message.cmd != self.command):
                                log.info(f"Receiving command {WsPacket_message.cmd}")
                                if( WsPacket_message.type == 0):
                                    log.debug("Get Request Frame")
                                if( WsPacket_message.type == 1):
                                    log.debug("Decoding Response Request Frame")
                                    ComResponse_message = base__pb2.ComResponse()
                                    ComResponse_message.ParseFromString(WsPacket_message.data)

                                    log.debug(f"receive request response data >> {ComResponse_message.code}")
                                    log.debug(f">> {getErrorCodeValueName(ComResponse_message.code)}")

                                if( WsPacket_message.type == 2):
                                    log.debug("Decoding Notification Frame")
                                    ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                                    ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                    log.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                    log.debug(f">> {getAstroStateName(ResNotifyStateAstroGoto_message.state)}")

                                if( WsPacket_message.type == 3):
                                    log.debug("Decoding Response Notification Frame")
                                    ResNotifyStateAstroGoto_message = notify.ResNotifyStateAstroGoto()
                                    ResNotifyStateAstroGoto_message.ParseFromString(WsPacket_message.data)

                                    log.debug(f"receive notification data >> {ResNotifyStateAstroGoto_message.state}")
                                    log.debug(f">> {getErrorCodeValueName(ResNotifyStateAstroGoto_message.state)}")
                        else:
                            log.debug("Ignoring Unkown Type Frames")
                    else:
                        log.debug("No Messages Rcv : close ??")
                        log.debug("Continue .....")

        except websockets.ConnectionClosedOK  as e:
            log.debug(f'Rcv: ConnectionClosedOK', e)
            pass
        except websockets.ConnectionClosedError as e:
            log.error(f'Rcv: ConnectionClosedError', e)
            pass
        except asyncio.CancelledError as e:
            log.debug(f'Rcv: Cancelled', e)
            pass
        except Exception as e:
            # Handle other exceptions
            log.error(f"Rcv: Unhandled exception: {e}")
            if (not self.stop_task.is_set()):
                log.debug("RCV function set stop_task.")
                self.stop_task.set()
            await asyncio.sleep(1)
        finally:
            if self.stop_task.is_set():
                 log.debug("stop Task : OK")
            else:
                 log.debug("stop Task: KO")
            if self.wait_pong:
                 log.debug("stop Pong : OK")
            else:
                 log.debug("stop Pong: KO")
            # Perform cleanup if needed
            log.info("TERMINATING Receive function.")

    async def send_message_init(self):
        # Create a protobuf message
        # Start Sending
        major_version = 1
        minor_version = 1
        device_id = 1  # DWARF II
        #self.takePhotoStarted = False
        #self.takeWidePhotoStarted = False

        if not self.websocket:
            log.error("Error No WebSocket in send_message_init")
            WebSocketClient.Init_Send_TeleGetSystemWorkingState = True
            return

        self.InitHostReceived = False
        self.BatteryLevelDwarf = None
        self.availableSizeDwarf = None
        self.totalSizeDwarf = None
        self.TemperatureLevelDwarf = None
        self.StreamTypeDwarf = None
        self.FocusValueDwarf = None
        self.PowerIndStateDwarf = None
        self.RgbIndStateDwarf = None
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
       
        #CMD_CAMERA_WIDE_OPEN_CAMERA
        WsPacket_messageCameraWideOpen = base__pb2.WsPacket()
        ReqOpenCamera_message = camera.ReqOpenCamera()
        WsPacket_messageCameraWideOpen.data = ReqOpenCamera_message.SerializeToString()

        WsPacket_messageCameraWideOpen.major_version = major_version
        WsPacket_messageCameraWideOpen.minor_version = minor_version
        WsPacket_messageCameraWideOpen.device_id = device_id
        WsPacket_messageCameraWideOpen.module_id = 2  # MODULE_WIDEHOTO
        WsPacket_messageCameraWideOpen.cmd = 12000 #CMD_CAMERA_WIDE_OPEN_CAMERA
        WsPacket_messageCameraWideOpen.type = 0; #REQUEST
        WsPacket_messageCameraWideOpen.client_id = self.client_id # "0000DAF2-0000-1000-8000-00805F9B34FB"  # ff03aa11-5994-4857-a872-b411e8a3a5e51

        try:
            # Serialize the message to bytes and send
            # Send Command
            await asyncio.sleep(0.02)

            if (WebSocketClient.Init_Send_TeleGetSystemWorkingState):
                await self.websocket.send(WsPacket_messageTeleGetSystemWorkingState.SerializeToString())
                log.debug("#----------------#")
                log.debug(f"Send cmd >> {WsPacket_messageTeleGetSystemWorkingState.cmd}")
                log.debug(f">> {getDwarfCMDName(WsPacket_messageTeleGetSystemWorkingState.cmd)}")

                log.debug(f"Send type >> {WsPacket_messageTeleGetSystemWorkingState.type}")
                log.debug(f"msg data len is >> {len(WsPacket_messageTeleGetSystemWorkingState.data)}")
                log.debug("Sendind End ....");  

                await asyncio.sleep(1)

                await self.websocket.send(WsPacket_messageCameraTeleOpen.SerializeToString())
                log.debug("#----------------#")
                log.debug(f"Send cmd >> {WsPacket_messageCameraTeleOpen.cmd}")
                log.debug(f">> {getDwarfCMDName(WsPacket_messageCameraTeleOpen.cmd)}")

                log.debug(f"Send type >> {WsPacket_messageCameraTeleOpen.type}")
                log.debug(f"msg data len is >> {len(WsPacket_messageCameraTeleOpen.data)}")
                log.debug("Sendind End ....");

                await asyncio.sleep(1)

                await self.websocket.send(WsPacket_messageCameraWideOpen.SerializeToString())
                log.debug("#----------------#")
                log.debug(f"Send cmd >> {WsPacket_messageCameraWideOpen.cmd}")
                log.debug(f">> {getDwarfCMDName(WsPacket_messageCameraWideOpen.cmd)}")

                log.debug(f"Send type >> {WsPacket_messageCameraWideOpen.type}")
                log.debug(f"msg data len is >> {len(WsPacket_messageCameraWideOpen.data)}")
                log.debug("Sendind End ....");
                WebSocketClient.Init_Send_TeleGetSystemWorkingState = False

            # await asyncio.sleep(1)

            log.info("Sendind Init End ....");  

        except asyncio.CancelledError:
            log.debug("End Of Init Message Task.")
            pass
        except Exception as e:
            # Handle other exceptions
            log.error(f"Unhandled exception 1a: {e}")
            WebSocketClient.Init_Send_TeleGetSystemWorkingState = True
        finally:
            # Perform cleanup if needed
            log.info("TERMINATING Sending init function.")

    async def send_message(self, message, command, type_id, module_id):
        # Create a protobuf message
        # Start Sending
        major_version = 1
        minor_version = 1
        device_id = 1  # DWARF II
        self.target_name = ""
        self.message = message
        self.command = command
        self.module_id = type_id
        self.type_id = module_id
        self.toDoSetExpMode = False
        self.toDoSetExp = False
        self.toDoSetGain = False
        self.toDoSetWideExpMode = False
        self.toDoSetWideExp = False
        self.toDoSetWideGain = False

        if not self.websocket:
            log.error("Error No WebSocket in send_message")
            WebSocketClient.Init_Send_TeleGetSystemWorkingState = True
            return

        # reset time out
        self.reset_timeout = True

        # Special Command ASTRO CAPTURE ENDING
        # Special Command ASTRO CAPTURE ENDING RESTART
        # Special Command ASTRO WIDE CAPTURE ENDING
        # Special Command ASTRO WIDE CAPTURE ENDING RESTART
        if isinstance(message, str):
            if message == "ASTRO CAPTURE ENDING RESTART":
                self.RestartAstroCapture = True
                self.command = protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING
                return
            if message == "ASTRO WIDE CAPTURE ENDING RESTART":
                self.RestartAstroWideCapture = True
                self.command = protocol.CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING
                return
            if message == "ASTRO CAPTURE ENDING" and self.AstroCapture:
                log.info("TERMINATING Sending empty function.")
                self.command = protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING
                return
            if message == "ASTRO WIDE CAPTURE ENDING" and self.AstroWideCapture:
                log.info("TERMINATING Sending empty function.")
                self.command = protocol.CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING
                return
            elif ( message == "ASTRO CAPTURE ENDING"):
                await self.result_receive_messages(protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING, protocol.CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING, Dwarf_Result.WARNING, "ASTRO CAPTURE NOT STARTED", -1)
                return
            elif ( message == "ASTRO WIDE CAPTURE ENDING"):
                await self.result_receive_messages(protocol.CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING, protocol.CMD_NOTIFY_STATE_WIDE_CAPTURE_RAW_LIVE_STACKING, Dwarf_Result.WARNING, "ASTRO WIDE CAPTURE NOT STARTED",-1)
                return
            else:
                raise RuntimeError(f"Unknown Message String")

        # SEND COMMAND
        WsPacket_message = base__pb2.WsPacket()
        WsPacket_message.data = self.message.SerializeToString()

        WsPacket_message.major_version = major_version
        WsPacket_message.minor_version = minor_version
        WsPacket_message.device_id = device_id
        WsPacket_message.module_id = module_id
        WsPacket_message.cmd = command 
        WsPacket_message.type = type_id;
        WsPacket_message.client_id = self.client_id # "0000DAF2-0000-1000-8000-00805F9B34FB"  # ff03aa11-5994-4857-a872-b411e8a3a5e51
       
        try:
            # Serialize the message to bytes and send
            # Send Command
            await asyncio.sleep(1)

            await self.websocket.send(WsPacket_message.SerializeToString())
            log.info("#----------------#")
            log.info(f"Send cmd >> {WsPacket_message.cmd}")
            log.info(f">> {getDwarfCMDName(WsPacket_message.cmd)}")
            log.info("#----------------#")

            # Special GOTO  DSO or SOLAR save Target Name to verifiy is GOTO is success
            if ((self.command == protocol.CMD_ASTRO_START_GOTO_DSO) or (self.command == protocol.CMD_ASTRO_START_GOTO_SOLAR_SYSTEM)):
                self.target_name = self.message.target_name

            # Special CALIBRATION
            if (self.command == protocol.CMD_ASTRO_START_CALIBRATION):
                self.stopcalibration = False

            # Special EQ Solving
            if (self.command == protocol.CMD_ASTRO_START_EQ_SOLVING):
                self.startEQSolving = False

            # Special ASTRO START or STOP CAPTURE
            if ( self.command == protocol.CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING or self.command == protocol.CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING):
                self.AstroCapture = True

            # Special ASTRO START or STOP CAPTURE
            if ( self.command == protocol.CMD_ASTRO_START_WIDE_CAPTURE_LIVE_STACKING or self.command == protocol.CMD_ASTRO_STOP_WIDE_CAPTURE_LIVE_STACKING):
                self.AstroWideCapture = True

            # Special CMD_CAMERA_TELE_SET_EXP_MODE
            if (self.command == protocol.CMD_CAMERA_TELE_SET_EXP_MODE):
                self.toDoSetExpMode = True

            # Special CMD_CAMERA_TELE_SET_EXP
            if (self.command == protocol.CMD_CAMERA_TELE_SET_EXP):
                self.toDoSetExp = True

            # Special CMD_CAMERA_TELE_SET_GAIN
            if (self.command == protocol.CMD_CAMERA_TELE_SET_GAIN):
                self.toDoSetGain = True

            # Special CMD_CAMERA_WIDE_SET_EXP_MODE
            if (self.command == protocol.CMD_CAMERA_WIDE_SET_EXP_MODE):
                self.toDoSetWideExpMode = True

            # Special CMD_CAMERA_WIDE_SET_EXP
            if (self.command == protocol.CMD_CAMERA_WIDE_SET_EXP):
                self.toDoSetWideExp = True

            # Special CMD_CAMERA_WIDE_SET_GAIN
            if (self.command == protocol.CMD_CAMERA_WIDE_SET_GAIN):
                self.toDoSetWideGain = True

            log.debug(f"Send type >> {WsPacket_message.type}")
            log.debug(f"Send message >> {self.message}")
            log.debug(f"msg data len is >> {len(WsPacket_message.data)}")
            log.debug("Sendind End ....");  

        except Exception as e:
            # Handle other exceptions
            log.error(f"Unhandled exception 1b: {e}")
            WebSocketClient.Init_Send_TeleGetSystemWorkingState = True
        finally:
            # Perform cleanup if needed
            log.info("TERMINATING Sending function.")


    async def message_init(self):
        try:
            log.debug("message_init start Class.")
            result = False
            count = 0
            max = 30
            await asyncio.sleep(0.02)
            while not (self.start_client and self.websocket) and count < max:
                await asyncio.sleep(1)
                count += 1

            if self.start_client and self.websocket:
                result = True
                log.debug("message_init init Class.")
                #self.message_init_task()
                self.message_init_task = asyncio.create_task(self.send_message_init())
                await self.message_init_task
                log.debug("message_init end Class.")
        except asyncio.CancelledError:
            log.debug("End Of Init Message Task 2.")
            pass
        except Exception as e:
            # Handle other exceptions
            log.error(f"Unhandled exception 1c: {e}")
        finally:
            # Perform cleanup if needed
            log.info("TERMINATING message_init function.")

    async def start(self):
        try:
            result = False  
            self.ErrorConnection = False
            #asyncio.set_event_loop(asyncio.new_event_loop())
            #ping_timeout=self.ping_interval_task+2
            log.debug(f"ping_interval : {self.ping_interval_task}")
            self.start_client = False
            self.stop_client = False
            self.stop_task.clear();
            async with websockets.client.connect(self.uri, ping_interval=None, extra_headers=[("Accept-Encoding", "gzip"), ("Sec-WebSocket-Extensions", "permessage-deflate")]) as websocket:
                try:
                    self.websocket = websocket
                    if self.websocket:
                        log.info(f"Connected to {self.uri}")
                        log.info("------------------")

                    # Start the task to receive messages
                    #self.receive_task = asyncio.ensure_future(self.receive_messages())
                    self.receive_task = asyncio.create_task(self.receive_messages())

                    # Start the periodic task to send pings
                    #self.ping_task = asyncio.ensure_future(self.send_ping_periodically())
                    self.ping_task = asyncio.create_task(self.send_ping_periodically())

                    # Start the periodic task to abort all task after timeout
                    self.abort_tasks = asyncio.create_task(self.abort_tasks_timeout(self.abort_timeout))

                    self.start_client = True
                    await self.result_receive_messages("Connection", "Connection", Dwarf_Result.OK, "Dwarf Connection OK", 0)

                    # Send a unique message to the server
                    try:
                        log.debug("Wait End of Current Tasks.")
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
                        log.debug(results)
                        log.debug("End of Current Tasks.")

                        # get the exception #raised by a task

                        try:
                            self.receive_task.result()
                            self.ping_task.result()
                            self.abort_tasks.result()

                        except Exception as e:
                            log.error(f"Exception occurred in the Gather try block: {e}")

                        log.debug("End of Current Tasks Results.")

                    except Exception as e:
                        self.stop_client = True
                        log.error(f"Exception occurred in the try block: {e}")

                except Exception as e:
                    self.stop_client = True
                    log.error(f"Exception occurred in the 2nd try block: {e}")
        except Exception as e:
            self.stop_client = True
            log.error(f"unknown exception with error: {e}")
            self.ErrorConnection = True
            await self.result_receive_messages("Connection", "Connection", Dwarf_Result.ERROR, "Error Connection", -1)

        finally:
            if self.start_client:
                await self.disconnect()
            else:
                self.stop_client = True
                self.websocket = False
            if not self.ErrorConnection:
                await self.result_notification_messages("Connection", "Connection", Dwarf_Result.DISCONNECTED, "Disconnected", -1)

    async def disconnect(self):
        # Signal the ping and receive functions to stop
        log.info("DISCONNECT function set stop_task.")
        self.stop_task.set()
        self.task.cancel()

        # Cancel the ping task when the client is done
        if self.ping_task:
            log.debug("Closing Ping Task ....")
            self.ping_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                try:
                    await self.ping_task
                except Exception as e:
                    log.error(f"unknown exception with error: {e}")

        # Cancel the receive task when the client is done
        if self.receive_task:
            log.debug("Closing Receive Task ....")
            self.receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                try:
                    await self.receive_task
                except Exception as e:
                    log.error(f"unknown exception with error: {e}")

        # Cancel the abort task when the client is done
        if self.abort_tasks:
            log.debug("Closing Abort Task ....")
            self.abort_tasks.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                try:
                    await self.abort_tasks
                except Exception as e:
                    log.error(f"unknown exception with error: {e}")

        # Close the WebSocket connection explicitly
        if self.start_client:
            if self.websocket: #and self.websocket.open:
                log.debug("Closing Socket ....")
                try:
                    if self.websocket.open:
                        await self.websocket.close()
                        log.debug("WebSocket connection closed.")
                    else:
                        log.debug("WebSocket was already closed.")
                except websockets.ConnectionClosedOK  as e:
                    log.error(f'Close: ConnectionClosedOK', e)
                    pass
                except websockets.ConnectionClosedError as e:
                    log.error(f'Close: ConnectionClosedError', e)
                    pass
                except Exception as e:
                    log.error(f"unknown exception with error: {e}")

            self.start_client = False
            self.stop_client = True
            self.websocket = False
            log.info("WebSocket Terminated.")

        log.notice("WebSocketClient Terminated.")
        WebSocketClient.Init_Send_TeleGetSystemWorkingState = True

    def run(self):
        self.task = asyncio.create_task(self.start())

#--------------------------------------
# Run the client
#--------------------------------------
async def start_socket(uri=None, client_id=None, ping_interval_task=10):
    global client_instance
    result = True

    if uri is None or client_id is None:
        data_config = dwarf_python_api.get_config_data.get_config_data()
        if uri is None:
            uri = data_config['ip']
        if client_id is None:
            client_id = data_config['client_id']

    if uri and client_id:
        websocket_uri = ws_uri(uri)

        log.info(f"Try Connect to {websocket_uri} for {client_id}")

        try:
            # Create an instance of WebSocketClient
            client_instance = WebSocketClient(asyncio.get_event_loop(), websocket_uri, client_id, ping_interval_task)
            client_instance.initialize_once()
            log.debug("WebSocket Client init Once.")

            # Call the start method to initiate the WebSocket connection and tasks
            client_instance.run() # Ensure the run method is called
            log.debug("WebSocket Client run.")

            return result;

        except asyncio.CancelledError:
            log.debug("start_socket cancelled Error.")
            # Perform any cleanup here if necessary

        except Exception as e:
            # Handle any errors that may occur during the close operation
            log.error(f"Unknown Error closing : {e}")
            pass  # Ignore this exception, it's expected during clean-up

    return False;

async def send_message_init():
    global client_instance

    result = False
    try:
        if client_instance:
            log.debug("WebSocket Client Message Init Start.")
            task_init = client_instance.message_init()
            await task_init  # Ensure the task is awaited
            log.debug("WebSocket Client init Message Start.")

            if not client_instance:
                log.debug("WebSocket Client Terminated.")
            log.debug("WebSocket Client End.")
            return result;

    except asyncio.CancelledError:
        log.debug("start_socket cancelled Error.")
        # Perform any cleanup here if necessary

    except Exception as e:
        # Handle any errors that may occur during the close operation
        log.error(f"Unknown Error closing : {e}")
        pass  # Ignore this exception, it's expected during clean-up

    return False;

async def send_socket(message, command, type_id, module_id):
    global client_instance

    result = False
    try:
        if client_instance:
            log.debug("WebSocket Client Send Start.")
            await client_instance.send_message(message, command, type_id, module_id)
            result = True
        log.debug("WebSocket Client Send End.")
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt received. Stopping gracefully 1.")
    return result


#--------------------------------------
# Calling Functions
#--------------------------------------
# Run the asyncio event loop in a background thread
def run_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def flush_queue_for_command_id(queue, queue_lock, cmd_send):
    temp_items = []
    flushed = 0

    async with queue_lock:
        try:
            while True:
                msg = queue.get_nowait()
                if msg.get("cmd_send") == cmd_send:
                    flushed += 1  # discard
                else:
                    temp_items.append(msg)  # keep
        except asyncio.QueueEmpty:
            pass

        # Restore only unrelated messages in original order
        for msg in temp_items:
            await queue.put(msg)

    log.debug(f"Flushed {flushed} message(s) with ID={cmd_send}")

async def get_result_with_timeout(queue, timeout = 30):

    elapsed_time = 0
    step_timeout = 1
    while elapsed_time < timeout:
        try:
            # Attempt to get a result from the queue in small intervals
            result = await asyncio.wait_for(queue.get(), step_timeout)
            return result
        except asyncio.TimeoutError:
            elapsed_time += step_timeout
            log.debug(f"Waiting for result... {elapsed_time}/{timeout} seconds elapsed.")
        except KeyboardInterrupt:
            # Handle KeyboardInterrupt separately
            log.debug("KeyboardInterrupt received. Stopping gracefully 5.")
            pass  # Ignore this exception, it's expected during clean-up
        except Exception as e:
            # Handle other exceptions
            log.error(f"TIMEOUT: Unhandled exception: {e}")

    result_timeout = { 'result' : Dwarf_Result.WARNING, 'message' : {f"No result after {timeout} seconds."}, 'code': ERROR_TIMEOUT}
    log.warning(f"No result after {timeout} seconds.")
    return result_timeout
 
async def init_socket():
    global client_instance, event_loop, event_loop_thread

    result = False

    try:

        if not client_instance :
            event_loop = asyncio.new_event_loop()
            event_loop_thread = threading.Thread(target=run_event_loop, args=(event_loop,))
            event_loop_thread.start()

        if not client_instance or not client_instance.start_client:

            future = asyncio.run_coroutine_threadsafe(start_socket(), event_loop)

            # Wait for the start_socket coroutine to finish
            future.result()  # This blocks until start_socket completes

            log.debug(f"client_instance {client_instance}")
            if client_instance:
                log.debug("WebSocket Client init Queue.")
                result_cnx = asyncio.run_coroutine_threadsafe(get_result_with_timeout(client_instance.result_queue), event_loop).result()

                log.debug("WebSocket Client result Queue.")
                log.debug(f"Result : init_socket")
                log.debug(f"Result : {result_cnx}")
                if isinstance(result_cnx, dict) and 'code' in result_cnx:
                    if result_cnx['result'] == Dwarf_Result.DISCONNECTED:
                        log.error("Error WebSocket Disconnected.")
                        stop_event_loop()
                        result = False
                    elif result_cnx['result'] == Dwarf_Result.ERROR:
                        log.error("Error WebSocket Connection.")
                        stop_event_loop()
                        result = False
                    else:
                        result = result_cnx['code']
                elif isinstance(result_cnx, int):
                    result = result_cnx

            if client_instance and (result is not False):
                future = asyncio.run_coroutine_threadsafe(send_message_init(), event_loop)

                # Wait for the send_message_init coroutine to finish
                future.result()  # This blocks until send_message_init completes

                log.debug(f"client_instance {client_instance}")

                log.debug("WebSocket Client init Queue.")
                result_cnx = asyncio.run_coroutine_threadsafe(get_result_with_timeout(client_instance.result_queue), event_loop).result()

                log.debug("WebSocket Client result Queue.")
                log.debug(f"Result : init_socket")
                log.debug(f"Result : {result_cnx}")
                if isinstance(result_cnx, dict) and 'code' in result_cnx:
                    if result_cnx['result'] == Dwarf_Result.DISCONNECTED:
                        log.error("Error WebSocket Disconnected.")
                        stop_event_loop()
                        result = False
                    elif result_cnx['result'] == Dwarf_Result.ERROR:
                        log.error("Error WebSocket Connection.")
                        stop_event_loop()
                        result = False
                    elif result_cnx['result'] == Dwarf_Result.WARNING and result_cnx['code'] == ERROR_SLAVEMODE:
                        log.error("Can't send command , SLAVE MODE detected.")
                        result = False
                    elif result_cnx['result'] == Dwarf_Result.WARNING and result_cnx['code'] == ERROR_TIMEOUT:
                        log.error("command TIMEOUT.")
                        result = False
                    elif result_cnx['result'] == Dwarf_Result.WARNING:
                        log.error("command error: {result_cnx['message']}")
                        result = False
                    else:
                        result = result_cnx['code']
                elif isinstance(result_cnx, int):
                    result = result_cnx

            log.info(f"Result : {result}")

    except KeyboardInterrupt:
        # Handle KeyboardInterrupt separately
        log.debug("KeyboardInterrupt received. Stopping gracefully 2.")
        pass  # Ignore this exception, it's expected during clean-up
    return result

async def send_socket_message(message, command, type_id, module_id):
    global client_instance, event_loop

    result = False

    try:
        if client_instance:

            # flush the queue for this message
            await flush_queue_for_command_id(client_instance.result_queue, client_instance.result_queue_locked, command)

            # Call the send function
            future = asyncio.run_coroutine_threadsafe(send_socket(message, command, type_id, module_id), client_instance.task.get_loop())
            
            # Wait for the send_socket coroutine to finish
            future.result()  # This blocks until send_socket completes

            log.debug(f"client_instance {client_instance}")
            if client_instance:
                notification_result = True
                while notification_result:
                    notification_result = False
                    log.debug("WebSocket Client wait Queue.")
                    future_cnx = asyncio.run_coroutine_threadsafe(get_result_with_timeout(client_instance.result_queue, gb_timeout), event_loop)

                    while not future_cnx.done():
                        # Check every short interval for task completion or interruption
                        time.sleep(0.1)  # Small sleep to allow for other tasks
                        #  client_instance.result_queue.put(result_interrupt)

                    result_cnx = future_cnx.result()

                    log.debug("WebSocket Client connect Queue.")
                    log.debug(f"Result : send_socket")
                    log.debug(f"Result : {result_cnx}")
                       
                    if isinstance(result_cnx, dict) and 'code' in result_cnx:
                        if result_cnx['result'] == Dwarf_Result.DISCONNECTED:
                            log.error("Error WebSocket Disconnected.")
                            stop_event_loop()
                            result = False
                        elif result_cnx['result'] == Dwarf_Result.WARNING and result_cnx['code'] == ERROR_SLAVEMODE:
                            log.error("Can't send command , SLAVE MODE detected.")
                            result = False
                        elif result_cnx['result'] == Dwarf_Result.WARNING and result_cnx['code'] == ERROR_TIMEOUT:
                            log.error("command TIMEOUT.")
                            result = False
                        elif result_cnx['result'] == Dwarf_Result.WARNING:
                            log.error("command error: {result_cnx['message']}")
                            result = False
                        else:
                            result = result_cnx['code']
                            # test if it is a notification so we will continue (Astro photo)
                            if result == 0 and isinstance(result_cnx, dict) and 'notification' in result_cnx:
                                log.debug("Notification Received : continue loop.")
                                notification_result = result_cnx['notification']
                            # test if command received corresponds to possible command sent
                            elif result == 0 and process_command(result_cnx['cmd_send'], result_cnx['cmd_recv']) is None:
                                log.info("Ignore Frame Received : continue loop.")
                                notification_result = True

                    elif isinstance(result_cnx, int):
                        result = result_cnx

            log.info(f"Result : {result}")

            #reset Command to avoid new message for it
            if client_instance:
                client_instance.command = None

    except KeyboardInterrupt:
        # Handle KeyboardInterrupt separately
        log.debug("KeyboardInterrupt received. Stopping gracefully 3.")
        log.warning("Operation interrupted by the user (CTRL+C).")
        result = ERROR_INTERRUPTED
        pass  # Ignore this exception, it's expected during clean-up
    return result

def stop_event_loop():
    global client_instance, event_loop, event_loop_thread

    if event_loop:
        # Stop the event loop
        event_loop.call_soon_threadsafe(event_loop.stop)
        event_loop_thread.join()  # Ensure the event loop thread is properly joined
        log.debug("Event loop and thread stopped.")
        client_instance = None

#--------------------------------------
# External Functions
#--------------------------------------
# Store previous values
previous_values = {}

def get_client_status():
    global previous_values
 
    if client_instance is None:
        return json.dumps({"error": "Dwarf is not connected"})

    status = {
        "HostMode": client_instance.InitHostReceived,
        "takePhotoStarted": client_instance.takePhotoStarted,
        "takeWidePhotoStarted": client_instance.takeWidePhotoStarted,
        "AstroCapture": client_instance.AstroCapture,
        "AstroWideCapture": client_instance.AstroWideCapture,
        "startEQSolving": client_instance.startEQSolving,
        "takePhotoCount": client_instance.takePhotoCount,
        "takePhotoStacked": client_instance.takePhotoStacked,
        "takeWidePhotoCount": client_instance.takeWidePhotoCount,
        "takeWidePhotoStacked": client_instance.takeWidePhotoStacked,
        "ErrorConnection": client_instance.ErrorConnection,
        "BatteryLevelDwarf": client_instance.BatteryLevelDwarf,
        "availableSizeDwarf": client_instance.availableSizeDwarf,
        "totalSizeDwarf": client_instance.totalSizeDwarf,
        "TemperatureLevelDwarf": client_instance.TemperatureLevelDwarf,
        "StreamTypeDwarf": client_instance.StreamTypeDwarf,
        "FocusValueDwarf": client_instance.FocusValueDwarf,
        "PowerIndicatorDwarf": client_instance.PowerIndStateDwarf,
        "RgbIndicatorDwarf": client_instance.RgbIndStateDwarf
    }

    # Detect changes
    new_values = {}
    has_new_values = False

    for key, value in status.items():
        if key not in previous_values or previous_values[key] != value:
            new_values[key] = value
            has_new_values = True

    # Update previous values
    previous_values = status.copy()

    # Include change indicators in response
    response = {
        "hasNewValues": has_new_values,
        "fullStatus": status,
        "newValues": new_values
    }

    return response

def connect_socket(message, command, type_id, module_id):
    global client_instance

    result = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)  # Set this loop as the current loop

    try:
        if not client_instance or not client_instance.start_client:
            result = loop.run_until_complete(init_socket()) #asyncio.run(init_socket())

        if client_instance and (result is not False):
            result = loop.run_until_complete(send_socket_message(message, command, type_id, module_id)) #asyncio.run(send_socket_message(message, command, type_id, module_id))
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt separately
        result = False
        log.debug("KeyboardInterrupt received. Stopping gracefully 4.")
        pass  # Ignore this exception, it's expected during clean-up

    finally:
        # Close the event loop gracefully
        loop.close()

    return result

def disconnect_socket():
    global client_instance, event_loop, event_loop_thread

    # To disconnect the client explicitly
    if client_instance and hasattr(client_instance, 'task'):
        future = asyncio.run_coroutine_threadsafe(client_instance.disconnect(), client_instance.task.get_loop())
        log.notice("Disconnect signal sent to the client instance.")
        future.result()  # This blocks until disconnect completes
        stop_event_loop()
    else:
        log.warning("Client not started")


