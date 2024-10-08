/*** ---------------------------------------------------- ***/
/*** ---------------- MODULE CAMERA WIDE ---------------- ***/
/*** ---------------------------------------------------- ***/
/**
 * 3.9.3 Turn on the camera
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_OPEN_CAMERA
 * @returns {Uint8Array}
 */
export function messageCameraWideOpenCamera(): Uint8Array;
/**
 * 3.9.4 Turn off the camera
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_CLOSE_CAMERA
 * @returns {Uint8Array}
 */
export function messageCameraWideCloseCamera(): Uint8Array;
/**
 * 3.9.5 Take photos
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_PHOTOGRAPH
 * @returns {Uint8Array}
 */
export function messageCameraWidePhotograph(): Uint8Array;
/**
 * 3.9.6 Start continuous shooting
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_BURST
 * @returns {Uint8Array}
 */
export function messageCameraWideStartBurst(): Uint8Array;
/**
 * 3.9.7 Stop continuous shooting
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_STOP_BURST
 * @returns {Uint8Array}
 */
export function messageCameraWideStopBurst(): Uint8Array;
/**
 * 3.9.8 Get all parameters
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_GET_ALL_PARAMS
 * @returns {Uint8Array}
 */
export function messageCameraWideGetAllParams(): Uint8Array;
/**
 * 3.9.9 Set exposure mode
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_SET_EXP_MODE
 * @param {number} mode ; //0: Auto 1: Manual  ;
 * @returns {Uint8Array}
 */
export function messageCameraWideSetExpMode(mode: number): Uint8Array;
/**
 * 3.9.10 Acquire exposure mode
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_GET_EXP_MODE
 * @returns {Uint8Array}
 */
export function messageCameraWideGetExpMode(): Uint8Array;
/**
 * 3.9.11 Set exposure value
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_SET_EXP
 * @param {number} index  ;
 * @returns {Uint8Array}
 */
export function messageCameraWideSetExp(index: number): Uint8Array;
/**
 * 3.9.12 Get exposure value
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_GET_EXP
 * @returns {Uint8Array}
 */
export function messageCameraWideGetExp(): Uint8Array;
/**
 * 3.9.13 Set gain mode
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_SET_GAIN_MODE
 * @param {number} mode ; //0: Auto 1: Manual  ;
 * @returns {Uint8Array}
 */
export function messageCameraWideSetGainMode(mode: number): Uint8Array;
/**
 * 3.9.14 Acquisition gain mode
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_GET_GAIN_MODE
 * @returns {Uint8Array}
 */
export function messageCameraWideGetGainMode(): Uint8Array;
/**
 * 3.9.15 Set gain value
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_SET_GAIN
 * @param {number} index  ;
 * @returns {Uint8Array}
 */
export function messageCameraWideSetGain(index: number): Uint8Array;
/**
 * 3.9.16 Get gain value
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_GET_GAIN
 * @returns {Uint8Array}
 */
export function messageCameraWideGetGain(): Uint8Array;
/**
 * 3.9.23 Start time-lapse photography
 * Not documented
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_START_TIMELAPSE_PHOTO
 * @returns {Uint8Array}
 */
export function messageCameraWideStartTimeLapsePhoto(): Uint8Array;
/**
 * 3.9.24 Stop time-lapse photography
 * Not documented
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_STOP_TIMELAPSE_PHOTO
 * @returns {Uint8Array}
 */
export function messageCameraWideStopTimeLapsePhoto(): Uint8Array;
/**
 * 3.9.25 Set all camera parameters
 * Not documented
 * Create Encoded Packet for the command CMD_CAMERA_WIDE_SET_ALL_PARAMS
 * @param {number} exp_mode ; // 0: Auto 1: Manual
 * @param {number} exp_index ;
 * @param {number} gain_mode ;
 * @param {number} gain_index ;
 * @param {number} ircut_value ; //IRCUT value 0: CUT 1: PASS
 * @param {number} wb_mode ; //white balance mode 0: automatic 1: manual
 * @param {number} wb_index_type ; //White Balance Manual Mode Index Type: 0: Color Temperature Mode 1: Scene Mode
 * @param {number} wb_index ;
 * @param {number} brightness ;
 * @param {number} contrast ;
 * @param {number} hue ;
 * @param {number} saturation ;
 * @param {number} sharpness ;
 * @param {number} jpg_quality ;
 * @returns {Uint8Array}
 */
export function messageCameraWideSetAllParams(exp_mode: number, exp_index: number, gain_mode: number, gain_index: number, ircut_value: number, wb_mode: number, wb_index_type: number, wb_index: number, brightness: number, contrast: number, hue: number, saturation: number, sharpness: number, jpg_quality: number): Uint8Array;
//# sourceMappingURL=camera_wide.d.ts.map