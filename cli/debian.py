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


from sys import platform
from pathlib import Path
from tabulate import tabulate
import subprocess
import requests
import re
import sys


TMP_DEB = Path(__file__).parent.parent / "tmp_deb"


def check_call(args):
    print("check_call: %s" % " ".join(args))
    if platform == "linux":
        return subprocess.check_call(args)
    runfile = TMP_DEB / "run.sh"
    runfile.open("w").write(" ".join(args))
    return subprocess.check_call(["bash", str(runfile)], shell=True)


def check_output(args):
    print("check_output: %s" % " ".join(args))
    if platform == "linux":
        return subprocess.check_output(args).splitlines()
    runfile = TMP_DEB / "run.sh"
    runfile.open("w").write(" ".join(args))
    return subprocess.check_output(["bash", str(runfile)], shell=True).splitlines()


def check_debian_latest():
    print("Check Debian")
    versions = []
    for line in requests.get(
        "http://ftp.debian.org/debian/pool/main/q/qemu/", stream=True
    ).iter_lines():
        reg = re.search(">qemu-user-static_(.*)_.*.deb", str(line))
        if reg is not None:
            version = reg.group(1)
            if version not in versions:
                versions.append(version)

    versions.reverse()

    latest = versions[0]

    with (Path(__file__).parent.parent / "run.sh").open("r") as fptr:
        for l in fptr.readlines():
            if 'DEBIAN_VERSION="' in l:
                reg = re.search('DEF_DEBIAN_VERSION="(.*)".*', str(l))
                if reg is None:
                    reg = re.search('DEBIAN_VERSION="(.*)".*', str(l))
                    if reg is not None:
                        debv = reg.group(1)
                defdebv = reg.group(1)

    if defdebv + debv != latest:
        print("Current version:", defdebv + debv)
        print("Latest upstream:", latest)
        sys.exit(1)

    print(latest)


def get_debs_list():
    """
    Extract list of targets, for each host, in each version.

    TABLES = {
        "version" : {
            "host": []
        }
    }
    """
    debs = {}
    for line in requests.get(
        "http://ftp.debian.org/debian/pool/main/q/qemu/", stream=True
    ).iter_lines():
        reg = re.search(".*>qemu-user-static_(.*)_(.*).deb", str(line))
        if reg is not None:
            version = reg.group(1)
            host = reg.group(2)

            print("%s @ %s" % (version, host))

            if version not in debs:
                debs[version] = {}

            if host not in debs[version]:
                debs[version][host] = []

    for i in debs:
        print(i)

    return debs


def _get_debs(tmpdir, version, hosts):
    for host in hosts:
        fname = "qemu-user-static_%s_%s.deb" % (version, host)
        if not (tmpdir / fname).exists():
            g = requests.get("http://ftp.debian.org/debian/pool/main/q/qemu/%s" % fname)
            (tmpdir / fname).open("wb").write(g.content)


def get_debs(debs, tmpdir, version=None):
    tmpdir.mkdir(parents=True, exist_ok=True)
    if version is None:
        for version, hosts in debs.items():
            _get_debs(tmpdir, version, hosts)
    else:
        _get_debs(tmpdir, version, debs[version])


def _extract_debs(targets, debs, version, tmpdir):
    TMP_DEB = tmpdir
    for host in debs[version]:
        fname = "qemu-user-static_%s_%s.deb" % (version, host)
        debdir = tmpdir / fname[0:-4]
        if not debdir.exists():
            check_call(
                ["7z", "x", "-o./" + str(debdir), "-y", "./" + str(tmpdir / fname)]
            )

        for line in check_output(["7z", "l", "./" + str(debdir / "data.tar")]):
            reg = re.search("bin/qemu-(.*)-static.*", str(line))
            if reg is not None:
                target = reg.group(1)

                debs[version][host] += [target]

                if target not in targets:
                    targets += [target]


def extract_debs(targets, debs, tmpdir, version=None):
    if version is None:
        for version, hosts in debs.items():
            _extract_debs(targets, debs, version, tmpdir)
    else:
        _extract_debs(targets, debs, version, tmpdir)


# http://ftp.debian.org/debian/pool/main/q/qemu/qemu-user-static_${VERSION}${DEBIAN_VERSION}_$(pkg_arch ${HOST_ARCH}).deb


def debian_report(targets, tables, report: Path):
    """
    Print data about releases/assets as a markdown report.
    """
    print("> Print report")

    with report.open("w") as fptr:
        fptr.write("# dbhi/qus report: DEB\n")

    with report.open("a") as fptr:
        for version, assets in tables.items():
            print("  - %s: generate table" % version)
            hosts = list(assets.keys())
            hosts.sort()
            ROWS = [
                ([tgt] + ["ok" if tgt in assets[h] else "!" for h in hosts])
                for tgt in targets
            ]

            print("  - %s: write table" % version)
            fptr.write(
                tabulate(
                    ROWS,
                    headers=[version] + hosts,
                    stralign="center",
                    tablefmt="github",
                )
            )
            fptr.write("\n\n---\n\n")
