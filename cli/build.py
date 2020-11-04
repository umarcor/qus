# Copyright 2020-2021 Unai Martinez-Corral <unai.martinezcorral@ehu.eus>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import environ
from pathlib import Path
from shutil import rmtree

from getter_debian import GetterDebian
from getter_fedora import GetterFedora
from builder import Builder

from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


with (Path(__file__).parent / "config.yml").open("r") as fptr:
    CONFIG = load(fptr, Loader=Loader)


def rmkdir(dpath):
    """
    Remove dir if exists, and create it.
    """
    if dpath.exists():
        rmtree(str(dpath))
    dpath.mkdir()


def builder(source="debian", builder="amd64", hosts=None):
    """
    Wrapper around Getter(s) and Builder for generating sets of qus images for multiple hosts.
    """
    print("Builder %s %s %s" % (source, builder, hosts), flush=True)

    dreleases = Path("releases")
    rmkdir(dreleases)

    dbin = Path("bin-static")
    rmkdir(dbin)

    if source == "debian":
        print("[build] GetterDebian", flush=True)
        get_hnd = GetterDebian(CONFIG["archs"])
    elif source == "fedora":
        print("[build] GetterFedora", flush=True)
        get_hnd = GetterFedora(CONFIG["archs"])
    else:
        raise (BaseException("Unknown source '%s'" % source))

    build_hnd = Builder(get_hnd)

    for host in hosts:
        get_hnd.get_package_binaries(host, dbin)
        get_hnd.generate_tarballs(host, dbin)

        build_hnd.generate_pkg_image(source, host, environ.get("REPO", "aptman/qus"))

        arch = build_hnd._normalise_arch(host)
        if arch in [
            "amd64",
            "arm64v8",
            "arm32v7",
            "arm32v6",
            "i386",
            "ppc64le",
            "s390x",
            "mips64le",
        ]:
            barch = build_hnd._normalise_arch(builder)
            if arch != barch:
                build_hnd.register_interpreter(barch, arch)

            build_hnd.generate_register_images(
                source, host, environ.get("REPO", "aptman/qus")
            )
