from os import environ
from pathlib import Path
from shutil import rmtree

from getter_debian import GetterDebian
from builder import Builder

from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


with (Path(__file__).parent / "config.yml").open("r") as fptr:
    CONFIG = load(fptr, Loader=Loader)

print("[build] GetterDebian", flush=True)
get_hnd = GetterDebian(CONFIG["archs"])

build_hnd = Builder(get_hnd)

print(get_hnd._normalise_arch('amd64'))
