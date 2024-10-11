from setuptools import setup, find_packages

setup(
    name='dwarf_python_api',
    version='1.3.7',
    author='stevejcl',
    packages= find_packages(include=['dwarf_python_api','dwarf_ble_connect']),  # Include the main package directory
    package_dir={'dwarf_python_api': 'dwarf_python_api','dwarf_ble_connect': 'dwarf_ble_connect'},  # Specify the root of the package
    package_data={ 'dwarf_ble_connect' : [ '*','dist_js/**'],'dwarf_python_api': ['lib/*', 'proto/*'],},  # Specify package data relative to the main package directory
    include_package_data=True,
    install_requires=[]
)
