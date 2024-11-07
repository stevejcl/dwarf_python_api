# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: base.proto

from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='base.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\nbase.proto\"\x9a\x01\n\x08WsPacket\x12\x15\n\rmajor_version\x18\x01 \x01(\r\x12\x15\n\rminor_version\x18\x02 \x01(\r\x12\x11\n\tdevice_id\x18\x03 \x01(\r\x12\x11\n\tmodule_id\x18\x04 \x01(\r\x12\x0b\n\x03\x63md\x18\x05 \x01(\r\x12\x0c\n\x04type\x18\x06 \x01(\r\x12\x0c\n\x04\x64\x61ta\x18\x07 \x01(\x0c\x12\x11\n\tclient_id\x18\x08 \x01(\t\"\x1b\n\x0b\x43omResponse\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\",\n\rComResWithInt\x12\r\n\x05value\x18\x01 \x01(\x05\x12\x0c\n\x04\x63ode\x18\x02 \x01(\x05\"/\n\x10\x43omResWithDouble\x12\r\n\x05value\x18\x01 \x01(\x01\x12\x0c\n\x04\x63ode\x18\x02 \x01(\x05\"-\n\x10\x43omResWithString\x12\x0b\n\x03str\x18\x01 \x01(\t\x12\x0c\n\x04\x63ode\x18\x02 \x01(\x05\"x\n\x0b\x43ommonParam\x12\x0f\n\x07hasAuto\x18\x01 \x01(\x08\x12\x11\n\tauto_mode\x18\x02 \x01(\x05\x12\n\n\x02id\x18\x03 \x01(\x05\x12\x12\n\nmode_index\x18\x04 \x01(\x05\x12\r\n\x05index\x18\x05 \x01(\x05\x12\x16\n\x0e\x63ontinue_value\x18\x06 \x01(\x01*K\n\x0eWsMajorVersion\x12\x1c\n\x18WS_MAJOR_VERSION_UNKNOWN\x10\x00\x12\x1b\n\x17WS_MAJOR_VERSION_NUMBER\x10\x01*K\n\x0eWsMinorVersion\x12\x1c\n\x18WS_MINOR_VERSION_UNKNOWN\x10\x00\x12\x1b\n\x17WS_MINOR_VERSION_NUMBER\x10\tb\x06proto3'
)

_WSMAJORVERSION = _descriptor.EnumDescriptor(
  name='WsMajorVersion',
  full_name='WsMajorVersion',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='WS_MAJOR_VERSION_UNKNOWN', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='WS_MAJOR_VERSION_NUMBER', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=464,
  serialized_end=539,
)
_sym_db.RegisterEnumDescriptor(_WSMAJORVERSION)

WsMajorVersion = enum_type_wrapper.EnumTypeWrapper(_WSMAJORVERSION)
_WSMINORVERSION = _descriptor.EnumDescriptor(
  name='WsMinorVersion',
  full_name='WsMinorVersion',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='WS_MINOR_VERSION_UNKNOWN', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='WS_MINOR_VERSION_NUMBER', index=1, number=9,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=541,
  serialized_end=616,
)
_sym_db.RegisterEnumDescriptor(_WSMINORVERSION)

WsMinorVersion = enum_type_wrapper.EnumTypeWrapper(_WSMINORVERSION)
WS_MAJOR_VERSION_UNKNOWN = 0
WS_MAJOR_VERSION_NUMBER = 1
WS_MINOR_VERSION_UNKNOWN = 0
WS_MINOR_VERSION_NUMBER = 9



_WSPACKET = _descriptor.Descriptor(
  name='WsPacket',
  full_name='WsPacket',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='major_version', full_name='WsPacket.major_version', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='minor_version', full_name='WsPacket.minor_version', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='device_id', full_name='WsPacket.device_id', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='module_id', full_name='WsPacket.module_id', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='cmd', full_name='WsPacket.cmd', index=4,
      number=5, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='type', full_name='WsPacket.type', index=5,
      number=6, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='data', full_name='WsPacket.data', index=6,
      number=7, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='client_id', full_name='WsPacket.client_id', index=7,
      number=8, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=15,
  serialized_end=169,
)


_COMRESPONSE = _descriptor.Descriptor(
  name='ComResponse',
  full_name='ComResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='code', full_name='ComResponse.code', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=171,
  serialized_end=198,
)


_COMRESWITHINT = _descriptor.Descriptor(
  name='ComResWithInt',
  full_name='ComResWithInt',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='ComResWithInt.value', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='code', full_name='ComResWithInt.code', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=200,
  serialized_end=244,
)


_COMRESWITHDOUBLE = _descriptor.Descriptor(
  name='ComResWithDouble',
  full_name='ComResWithDouble',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='ComResWithDouble.value', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='code', full_name='ComResWithDouble.code', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=246,
  serialized_end=293,
)


_COMRESWITHSTRING = _descriptor.Descriptor(
  name='ComResWithString',
  full_name='ComResWithString',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='str', full_name='ComResWithString.str', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='code', full_name='ComResWithString.code', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=295,
  serialized_end=340,
)


_COMMONPARAM = _descriptor.Descriptor(
  name='CommonParam',
  full_name='CommonParam',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='hasAuto', full_name='CommonParam.hasAuto', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='auto_mode', full_name='CommonParam.auto_mode', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='id', full_name='CommonParam.id', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='mode_index', full_name='CommonParam.mode_index', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='index', full_name='CommonParam.index', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='continue_value', full_name='CommonParam.continue_value', index=5,
      number=6, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=342,
  serialized_end=462,
)

DESCRIPTOR.message_types_by_name['WsPacket'] = _WSPACKET
DESCRIPTOR.message_types_by_name['ComResponse'] = _COMRESPONSE
DESCRIPTOR.message_types_by_name['ComResWithInt'] = _COMRESWITHINT
DESCRIPTOR.message_types_by_name['ComResWithDouble'] = _COMRESWITHDOUBLE
DESCRIPTOR.message_types_by_name['ComResWithString'] = _COMRESWITHSTRING
DESCRIPTOR.message_types_by_name['CommonParam'] = _COMMONPARAM
DESCRIPTOR.enum_types_by_name['WsMajorVersion'] = _WSMAJORVERSION
DESCRIPTOR.enum_types_by_name['WsMinorVersion'] = _WSMINORVERSION
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

WsPacket = _reflection.GeneratedProtocolMessageType('WsPacket', (_message.Message,), {
  'DESCRIPTOR' : _WSPACKET,
  '__module__' : 'base_pb2'
  # @@protoc_insertion_point(class_scope:WsPacket)
  })
_sym_db.RegisterMessage(WsPacket)

ComResponse = _reflection.GeneratedProtocolMessageType('ComResponse', (_message.Message,), {
  'DESCRIPTOR' : _COMRESPONSE,
  '__module__' : 'base_pb2'
  # @@protoc_insertion_point(class_scope:ComResponse)
  })
_sym_db.RegisterMessage(ComResponse)

ComResWithInt = _reflection.GeneratedProtocolMessageType('ComResWithInt', (_message.Message,), {
  'DESCRIPTOR' : _COMRESWITHINT,
  '__module__' : 'base_pb2'
  # @@protoc_insertion_point(class_scope:ComResWithInt)
  })
_sym_db.RegisterMessage(ComResWithInt)

ComResWithDouble = _reflection.GeneratedProtocolMessageType('ComResWithDouble', (_message.Message,), {
  'DESCRIPTOR' : _COMRESWITHDOUBLE,
  '__module__' : 'base_pb2'
  # @@protoc_insertion_point(class_scope:ComResWithDouble)
  })
_sym_db.RegisterMessage(ComResWithDouble)

ComResWithString = _reflection.GeneratedProtocolMessageType('ComResWithString', (_message.Message,), {
  'DESCRIPTOR' : _COMRESWITHSTRING,
  '__module__' : 'base_pb2'
  # @@protoc_insertion_point(class_scope:ComResWithString)
  })
_sym_db.RegisterMessage(ComResWithString)

CommonParam = _reflection.GeneratedProtocolMessageType('CommonParam', (_message.Message,), {
  'DESCRIPTOR' : _COMMONPARAM,
  '__module__' : 'base_pb2'
  # @@protoc_insertion_point(class_scope:CommonParam)
  })
_sym_db.RegisterMessage(CommonParam)


# @@protoc_insertion_point(module_scope)
