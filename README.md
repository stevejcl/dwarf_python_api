# dwarf_python_api
Dwarf II, some api functions to be used with python

It uses the new api V2.0.

The frames that can be used are : 
- connect to the dwarf with bluetooth
- Sendind config parameter : Time and Timezone
- Do a calibration
- Do a goto to differents target (Polaris, Vega, M42 and M31)
- Do a goto to a solar system target : Jupiter
- Do manual target
- Change the parameters of you tele lens
- Take Tele photo
- Download last image or previous one
- Start a imaging session
- Download images from last session
- Even do a Siril live integration with the current imaging session
- And many others functions


To use this library, you need :

 1.  python installed on your computer

 2.  Install the require libraries with downloading the requirements.txt file and do
  
     python -m pip install -r requirements.txt

 3.  Install this package in the current root dir of your poject

     It's due to the bluetooth connection that's need a web page and so need to start a web server locally.

     So you have to install this package with :

     python -m pip install dwarf_python_api@git+https://github.com/stevejcl/dwarf_python_api --target .

 
     !!! Don't miss the dot at the end of the line

