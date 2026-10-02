from pathlib import Path

from setuptools import setup, find_packages

# Same dependencies as requirements.txt, so `pip install` of the package
# pulls them too. protobuf must be >= 7.35.1: every proto/*_pb2.py is
# generated for it and refuses to import on an older runtime.
_requirements = [
    line.strip()
    for line in (Path(__file__).parent / "requirements.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
]

setup(
    name='dwarf_python_api',
    version='3.1.2',
    author='stevejcl',
    packages= find_packages(include=['dwarf_python_api','dwarf_ble_connect']),  # Include the main package directory
    package_dir={'dwarf_python_api': 'dwarf_python_api','dwarf_ble_connect': 'dwarf_ble_connect'},  # Specify the root of the package
    package_data={ 'dwarf_ble_connect' : [ '*','dist_js/**', 'lib/*'],'dwarf_python_api': ['lib/*', 'proto/*'],},  # Specify package data relative to the main package directory
    include_package_data=True,
    install_requires=_requirements,
)
