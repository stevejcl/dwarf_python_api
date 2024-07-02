# dwarf_python_api
Dwarf II, some api functions to be used with python

It uses the new api V2.0.

The frames that can be tested are : 
- Connect with Bluetooth
- Sendind config parameter : Time and Timezone
- Do a calibration
- Do a goto to differents target (Polaris, Vega, M42 and M31)
- Do a goto to a solar system target : Jupiter
- Take Photo
- Download the files

Install this package in the current dir of your poject with the option: --target .


When using this package, you nned to install :

websockets==11.0.3

protobuf==3.20.*

bleak