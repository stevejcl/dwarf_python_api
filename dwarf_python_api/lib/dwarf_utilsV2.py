"""
dwarf_utilsV2.py
----------------
Legacy V2-era functions, moved out of dwarf_utils.py (Aug 2026) once
confirmed to have zero active callers left in dwarf_python_api,
astro_dwarf_session, or main_v3.py.

Every function here uses an old V2 command that is either:
  - CONFIRMED NON-RESPONSIVE on real V3 hardware (the three
    perform_get_all_*_setting() GET commands, and perform_getstatus() -
    same CAMERA_TELE/CAMERA_WIDE module family, never got a response
    when tested directly), or
  - superseded by a confirmed-working V3 function for every case that
    was actually exercised (perform_update_camera_setting()'s "exposure"/
    "gain"/"IR"/"count" branches - see perform_set_astro_exposure_by_name_v3(),
    perform_set_astro_gain_v3(), perform_set_ir_filter_v3(),
    perform_set_astro_stack_count_v3(), perform_set_astro_stack_binning_v3(),
    perform_set_astro_stack_format_v3() in dwarf_utils.py), with the
    "binning"/"fileFormat"/"wide_exposure"/"wide_gain" branches never
    independently confirmed to still work in V3 either way.

Kept here for reference / in case a V2-only consumer still needs them -
NOT recommended for new V3 code. See MIGRATION_V3.md for the full
history of what was checked and when.
"""

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.websockets_utils import connect_socket
from dwarf_python_api.lib.dwarf_utils import get_result_value

import dwarf_python_api.proto.camera_pb2 as camera

from dwarf_python_api.lib.data_utils import get_exposure_index_by_name
from dwarf_python_api.lib.data_utils import get_gain_index_by_name
from dwarf_python_api.lib.data_wide_utils import get_wide_exposure_index_by_name
from dwarf_python_api.lib.data_wide_utils import get_wide_gain_index_by_name


def perform_getstatus():
    """CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE (10039) - old V2 command.
    CONFIRMED NON-RESPONSIVE on V3 hardware (Aug 2026), never wired into
    any menu since (no V3 replacement identified - see MIGRATION_V3.md).
    """
    # GET STATUS
    module_id = 1  # MODULE_TELEPHOTO
    type_id = 0; #REQUEST

    ReqGetSystemWorkingState_message = camera.ReqGetSystemWorkingState()

    command = 10039 #CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE
    response = connect_socket(ReqGetSystemWorkingState_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Get Status success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_get_all_camera_setting():
    """CMD_CAMERA_TELE_GET_ALL_PARAMS (10036) - old V2 command.
    CONFIRMED NON-RESPONSIVE on V3 hardware (Aug 2026, timeout at 150s in
    every scenario tested). Use perform_read_camera_params_http_v3()
    instead (dwarf_utils.py) - see MIGRATION_V3.md.
    """
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetAllParams_message = camera.ReqGetAllParams ()

    command = 10036; #CMD_CAMERA_TELE_GET_ALL_PARAMS

    response = connect_socket(ReqGetAllParams_message, command, type_id, module_id)

    return response


def perform_get_all_feature_camera_setting():
    """CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS (10038) - old V2 command.
    CONFIRMED NON-RESPONSIVE on V3 hardware (Aug 2026), same as
    perform_get_all_camera_setting()/perform_get_all_camera_wide_setting().
    Use perform_read_camera_params_http_v3() instead (dwarf_utils.py) -
    stackCount/mosaicCount are available there via tech_settings[0]/[1],
    which is what this function was mainly used for (binning/format via
    this path are not replaceable that way currently, see
    MIGRATION_V3.md).
    """
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetAllFeatureParams_message = camera.ReqGetAllFeatureParams ()

    command = 10038; #CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS

    response = connect_socket(ReqGetAllFeatureParams_message, command, type_id, module_id)

    return response


def perform_get_all_camera_wide_setting():
    """CMD_CAMERA_WIDE_GET_ALL_PARAMS (12027) - old V2 command.
    CONFIRMED NON-RESPONSIVE on V3 hardware (Aug 2026), same family as
    perform_get_all_camera_setting(). Use perform_read_camera_params_http_v3()
    instead (dwarf_utils.py) - see MIGRATION_V3.md.
    """
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqGetAllParams_message = camera.ReqGetAllParams ()

    command = 12027; #CMD_CAMERA_WIDE_GET_ALL_PARAMS

    response = connect_socket(ReqGetAllParams_message, command, type_id, module_id)

    return response


def perform_update_all_camera_setting( type, allValue, dwarf_id = "2"):
    """CMD_CAMERA_TELE_SET_ALL_PARAMS (10035) / CMD_CAMERA_WIDE_SET_ALL_PARAMS
    (12028) - old V2 batch-set command. Never independently confirmed to
    still be accepted on V3 hardware, no active caller since the V3
    migration (exposure/gain/IR are set individually now via their own
    confirmed V3 functions in dwarf_utils.py)."""
    type_id = 0; #REQUEST
    if (type == "wide"):
        module_id = 2  # MODULE_WIDE_CAMERA
    else:
        module_id = 1  # MODULE_TELE_CAMERA

    ReqSetAllParam_message = camera.ReqSetAllParams ()
    if (type == "wide"):
        if (allValue['camera_exposure']):
            ReqSetAllParam_message.exp_mode = 1
            ReqSetAllParam_message.exp_index = get_wide_exposure_index_by_name(str(allValue['camera_exposure']), str(dwarf_id))
        else:
            ReqSetAllParam_message.exp_mode = 0
            ReqSetAllParam_message.exp_index = 0
        if (allValue['camera_gain']):
            ReqSetAllParam_message.gain_mode = 1
            ReqSetAllParam_message.gain_index = get_wide_gain_index_by_name(str(allValue['camera_gain']),str(dwarf_id))
        else:
            ReqSetAllParam_message.gain_mode = 1
            ReqSetAllParam_message.gain_index = 0
    else:
        if (allValue['camera_exposure']):
            ReqSetAllParam_message.exp_mode = 1
            ReqSetAllParam_message.exp_index = get_exposure_index_by_name(str(allValue['camera_exposure']), str(dwarf_id))
        else:
            ReqSetAllParam_message.exp_mode = 0
            ReqSetAllParam_message.exp_index = 0
        if (allValue['camera_gain']):
            ReqSetAllParam_message.gain_mode = 1
            ReqSetAllParam_message.gain_index = get_gain_index_by_name(str(allValue['camera_gain']),str(dwarf_id))
        else:
            ReqSetAllParam_message.gain_mode = 1
            ReqSetAllParam_message.gain_index = 0

    ReqSetAllParam_message.ircut_value = 0;
    ReqSetAllParam_message.wb_mode = 0;
    ReqSetAllParam_message.wb_index_type = 2;
    ReqSetAllParam_message.wb_index = 0;
    ReqSetAllParam_message.brightness = 0;
    ReqSetAllParam_message.contrast = 0;
    ReqSetAllParam_message.hue = 0;
    ReqSetAllParam_message.saturation = 0;
    ReqSetAllParam_message.sharpness = 50;
    ReqSetAllParam_message.jpg_quality = 80;

    if (type == "wide"):
        command = 12028; #CMD_CAMERA_WIDE_SET_ALL_PARAMS
    else:
        command = 10035; #CMD_CAMERA_TELE_SET_ALL_PARAMS

    response = connect_socket(ReqSetAllParam_message, command, type_id, module_id)

    if response is not False: 

        if response == 0:
            log.success("Update camera setting")
            return True
        else:
            log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_get_camera_setting( type):
    """Old V2 individual-parameter GET commands (CMD_CAMERA_TELE_GET_EXP
    10010, CMD_CAMERA_TELE_GET_GAIN 10014, CMD_CAMERA_TELE_GET_IRCUT
    10032, CMD_CAMERA_WIDE_GET_EXP 12005, CMD_CAMERA_WIDE_GET_GAIN 12007) -
    same CAMERA_TELE/CAMERA_WIDE module family confirmed non-responsive
    in V3 for the "ALL_PARAMS" variants; never independently re-tested
    per-parameter, no active caller since the V3 migration. Use
    perform_read_camera_params_http_v3() instead (dwarf_utils.py)."""

    Test = False
    if Test:
        # brightness
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqGetBrightness_message = camera.ReqGetBrightness ()

        command = 10016; #CMD_CAMERA_TELE_GET_BRIGHTNESS

        response = connect_socket(ReqGetBrightness_message, command, type_id, module_id)

        if get_result_value(type, response) is not False:
            ReqGetContrast_message = camera.ReqGetContrast ()

            command = 10018; #CMD_CAMERA_TELE_GET_CONTRAST

            response = connect_socket(ReqGetContrast_message, command, type_id, module_id)

            return get_result_value(type, response)

    if (type == "exposure"):
        # exposure
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqGetExp_message = camera.ReqGetExp ()

        command = 10010; #CMD_CAMERA_TELE_GET_EXP

        response = connect_socket(ReqGetExp_message, command, type_id, module_id)

        return get_result_value(type, response, true)

    elif (type == "gain"):
        # gain
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqGetGain_message = camera.ReqGetGain ()

        command = 10014; #CMD_CAMERA_TELE_GET_GAIN

        response = connect_socket(ReqGetGain_message, command, type_id, module_id)

        return get_result_value(type, response, type)

    elif (type == "IR"):
        # IR
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqGetIrCut_message = camera.ReqGetIrCut ()

        command = 10032; #CMD_CAMERA_TELE_GET_IRCUT

        response = connect_socket(ReqGetIrCut_message, command, type_id, module_id)

        return get_result_value(type, response)

    elif (type == "wide_exposure"):
        # exposure
        module_id = 2  # MODULE_WIDE_CAMERA
        type_id = 0; #REQUEST

        ReqGetExp_message = camera.ReqGetExp ()

        command = 12005; #CMD_CAMERA_WIDE_GET_EXP

        response = connect_socket(ReqGetExp_message, command, type_id, module_id)

        return get_result_value(type, response, True)

    elif (type == "wide_gain"):
        # gain
        module_id = 2  # MODULE_WIDE_CAMERA
        type_id = 0; #REQUEST

        ReqGetGain_message = camera.ReqGetGain ()

        command = 12007; #CMD_CAMERA_WIDE_GET_GAIN

        response = connect_socket(ReqGetGain_message, command, type_id, module_id)

        return get_result_value(type, response)

    return False


def perform_update_camera_setting( type, value, dwarf_id = "2"):
    """Old V2 catch-all camera setting function. Superseded branch by
    branch (Aug 2026) once every value actually exercised by
    astro_dwarf_session/main_v3.py had a confirmed V3 replacement:
      - "exposure"/"gain" -> perform_set_astro_exposure_by_name_v3() /
        perform_set_astro_gain_v3() (dwarf_utils.py)
      - "IR" -> perform_set_ir_filter_v3() (dwarf_utils.py) - this one
        actually reuses the same CMD_CAMERA_TELE_SET_IRCUT (10031)
        command as here, confirmed still working in V3
      - "count" -> perform_set_astro_stack_count_v3() (dwarf_utils.py)
      - "binning" -> perform_set_astro_stack_binning_v3() (dwarf_utils.py)
      - "fileFormat" -> perform_set_astro_stack_format_v3() (dwarf_utils.py)
    "wide_exposure"/"wide_gain" here were never migrated to a confirmed
    V3 path (the astro wide functions use PARAM_ID_ASTRO_WIDE_EXPOSURE/
    GAIN instead, a different mechanism than what's below) - never
    independently confirmed working in V3 either way, no active caller.
    """

    if (type == "exposure"):
        # exposure_mode
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqSetExpMode_message = camera.ReqSetExpMode ()
        ReqSetExpMode_message.mode = 1

        command = 10007; #CMD_CAMERA_TELE_SET_EXP_MODE

        response = connect_socket(ReqSetExpMode_message, command, type_id, module_id)

        if response == 0:
            # exposure
            ReqSetExp_message = camera.ReqSetExp ()
            ReqSetExp_message.index = get_exposure_index_by_name(str(value), str(dwarf_id))
            log.notice(f"Set Exp Index to:  {get_exposure_index_by_name(str(value), str(dwarf_id))}")

            command = 10009; #CMD_CAMERA_TELE_SET_EXP

            response = connect_socket(ReqSetExp_message, command, type_id, module_id)

    elif (type == "gain"):
        # gain 
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqSetGain_message = camera.ReqSetGain ()
        ReqSetGain_message.index = get_gain_index_by_name(str(value),str(dwarf_id))
        log.notice(f"Set Gain Index to:  {get_gain_index_by_name(str(value), str(dwarf_id))}")

        command = 10013; #CMD_CAMERA_TELE_SET_GAIN

        response = connect_socket(ReqSetGain_message, command, type_id, module_id)

    elif (type == "IR"):
        # gain
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqSetIrCut_message = camera.ReqSetIrCut ()
        ReqSetIrCut_message.value = int(value)

        command = 10031; #CMD_CAMERA_TELE_SET_IRCUT

        response = connect_socket(ReqSetIrCut_message, command, type_id, module_id)

    elif (type == "binning"):
        # binning
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
        ReqSetFeatureParams_message.param.hasAuto = False;
        ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
        ReqSetFeatureParams_message.param.id = 0; # "Astro binning"
        ReqSetFeatureParams_message.param.mode_index = 0;
        ReqSetFeatureParams_message.param.index = int(value);
        ReqSetFeatureParams_message.param.continue_value = 0;

        command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

        response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

    elif (type == "fileFormat"):
        # fileFormat
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
        ReqSetFeatureParams_message.param.hasAuto = False;
        ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
        ReqSetFeatureParams_message.param.id = 2; # "Astro format"
        ReqSetFeatureParams_message.param.mode_index = 0;
        ReqSetFeatureParams_message.param.index = int(value);
        ReqSetFeatureParams_message.param.continue_value = 0;

        command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

        response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

    elif (type == "count"):
        module_id = 1  # MODULE_TELE_CAMERA
        type_id = 0; #REQUEST

        ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
        ReqSetFeatureParams_message.param.hasAuto = False;
        ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
        ReqSetFeatureParams_message.param.id = 1; # "Astro img_to_take"
        ReqSetFeatureParams_message.param.mode_index = 1;
        ReqSetFeatureParams_message.param.index = 0;
        ReqSetFeatureParams_message.param.continue_value = int(value);

        command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

        response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

    elif (type == "wide_exposure"):
        # exposure_mode
        module_id = 2  # MODULE_WIDE_CAMERA
        type_id = 0; #REQUEST

        ReqSetExpMode_message = camera.ReqSetExpMode ()
        ReqSetExpMode_message.mode = 1

        command = 12002; #CMD_CAMERA_WIDE_SET_EXP_MODE

        response = connect_socket(ReqSetExpMode_message, command, type_id, module_id)

        if response == 0:
            # exposure
            ReqSetExp_message = camera.ReqSetExp ()
            ReqSetExp_message.index = get_wide_exposure_index_by_name(str(value), str(dwarf_id))
            log.notice(f"Set Wide Exp Index to:  {get_wide_exposure_index_by_name(str(value), str(dwarf_id))}")

            command = 12004; #CMD_CAMERA_WIDE_SET_EXP

            response = connect_socket(ReqSetExp_message, command, type_id, module_id)

    elif (type == "wide_gain"):
        # gain 
        module_id = 2  # MODULE_WIDE_CAMERA
        type_id = 0; #REQUEST

        ReqSetGain_message = camera.ReqSetGain ()
        ReqSetGain_message.index = get_wide_gain_index_by_name(str(value),str(dwarf_id))
        log.notice(f"Set Wide Gain Index to:  {get_wide_gain_index_by_name(str(value), str(dwarf_id))}")

        command = 12006; #CMD_CAMERA_WIDE_SET_GAIN

        response = connect_socket(ReqSetGain_message, command, type_id, module_id)

    if response is not False: 

        if response == 0:
            log.success("Update camera setting")
            return True
        else:
            log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False
