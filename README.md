# dwarf_python_api
Dwarf II, Dwarf 3, and Dwarf Mini - API functions to be used with python.

This is the V3 branch, supporting the new V3 protobuf/WebSocket protocol used by current DWARFLAB firmware across all three models (Dwarf II, Dwarf 3, Dwarf Mini). The old V2-only API lives on the `main` branch for reference, but V3 is now the actively maintained version and the one new projects should use.

The frames that can be used are :
- connect to the dwarf with bluetooth
- Sending config parameter : Time and Timezone
- Do a calibration
- Do a goto to different targets (Polaris, Vega, M42, M31, and solar system objects like Jupiter)
- Do manual target
- Change the parameters of your tele and wide lens (exposure, gain, IR filter, white balance...)
- Take Tele or Wide photo
- Run astro/DSO sessions (tele and wide): start/stop/wait, stacking status
- Download last image or previous one
- Start an imaging session
- Download images from last session
- Even do a Siril live integration with the current imaging session
- RGB/power indicator light control
- And many other functions

An interactive test CLI is included (`main_v3.py`) covering camera, astro, motor, Bluetooth, and light functions - useful for testing individual commands against real hardware without writing a script.

See `MIGRATION_V3.md` for detailed notes on the V2-to-V3 protocol migration, what's been hardware-confirmed vs. still unconfirmed, and cross-references against independent reverse-engineering (dwarfAlp).

To use this library, you need :

 1.  python installed on your computer

 2.  Install the require libraries with downloading the requirements.txt file and do
  
     python -m pip install -r requirements.txt

 3.  Install this package in the current root dir of your poject

     It's due to the bluetooth connection that's need a web page and so need to start a web server locally.

     So you have to install this package with :

     python -m pip install dwarf_python_api@git+https://github.com/stevejcl/dwarf_python_api --target .

 
     !!! Don't miss the dot at the end of the line

     This installs from the `V3` branch (the default branch). To pin a specific branch explicitly regardless of what the default branch is set to (e.g. to stay on the old V2-only API), append `@branch-name` to the URL, e.g. `git+https://github.com/stevejcl/dwarf_python_api@main`.


