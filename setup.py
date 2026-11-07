from setuptools import setup, find_packages

# No install_requires on purpose: every project installs this package with
# `pip install ... --target .` (see README), and --target ignores what is
# already installed - declared dependencies would be copied again into the
# project root (19 packages, ~43 MB). Dependencies come from
# requirements.txt, installed first (step 2 of the README), which pins
# protobuf>=7.35.1: every proto/*_pb2.py is generated for it and refuses to
# import on an older runtime.

setup(
    name='dwarf_python_api',
    version='3.1.7',
    author='stevejcl',
    packages= find_packages(include=['dwarf_python_api','dwarf_ble_connect']),  # Include the main package directory
    package_dir={'dwarf_python_api': 'dwarf_python_api','dwarf_ble_connect': 'dwarf_ble_connect'},  # Specify the root of the package
    package_data={ 'dwarf_ble_connect' : [ '*','dist_js/**', 'lib/*'],'dwarf_python_api': ['lib/*', 'proto/*'],},  # Specify package data relative to the main package directory
    include_package_data=True,
    install_requires=[],
)
