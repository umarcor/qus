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


from pathlib import Path
from json import dump, load, loads
from tabulate import tabulate
import subprocess
from shutil import which
import requests
import re


def get_json_from_api(fname: Path, force=False):
    """
    Get metadata of releases and assets from GitHub's API and save it in a JSON file.

    :param fname: name of the JSON file to save data in.
    :param force: retrieve data, even if the file exists (overwrite it).
    """
    if force or not fname.exists():
        print("> Get api.github.com/repos/dbhi/qus/releases")
        data = loads(
            requests.get("https://api.github.com/repos/dbhi/qus/releases").text
        )
        with fname.open("w") as fptr:
            dump(data, fptr, indent=2)

    print("> Load %s" % str(fname))
    with fname.open("r") as fptr:
        return load(fptr)


def extract_from_json(jsondata):
    """
    Extract list of targets, for each host, in each release.

    TARGETS = []
    TABLES = {
        "release_name" : {
            "tag": []
            "assets": {
                "host": []
            }
        }
    }
    """
    print("> Extract from JSON")
    tables = {}
    targets = []

    for r in jsondata:
        name = r["name"]

        if name in tables:
            raise (Exception("Duplicated host name %s!" % name))
        tables[name] = {"tag": r["tag_name"], "assets": {}}
        print("> Processing %s @ %s" % (name, tables[name]["tag"]))

        for reg in [
            re.search("qemu-(.*)-static_(.*).tgz", i["name"]) for i in r["assets"]
        ]:
            if reg is not None:
                host = reg.group(2)
                target = reg.group(1)

                if host not in tables[name]["assets"]:
                    tables[name]["assets"][host] = []

                if target not in tables[name]["assets"][host]:
                    tables[name]["assets"][host] += [target]
                else:
                    raise (Exception("Duplicated target %s for %s!" % (target, host)))

                if target not in targets:
                    targets += [target]
        for i, l in tables[name]["assets"].items():
            print("  - %s: %s" % (i, " ".join(l)))
    return (targets, tables)


def releases_report(targets, tables, report: Path):
    """
    Print data about releases/assets as a markdown report.
    """
    print("> Print report")

    with report.open("w") as fptr:
        fptr.write("# dbhi/qus report\n")

    with report.open("a") as fptr:
        for rname, release in tables.items():
            print("  - %s: generate table" % rname)
            assets = release["assets"]
            hosts = list(assets.keys())
            hosts.sort()
            ROWS = [
                (
                    [tgt]
                    + [
                        "[ok](https://github.com/dbhi/qus/releases/download/%s/qemu-%s-static_%s.tgz)"
                        % (release["tag"], tgt, h)
                        if tgt in assets[h]
                        else "!"
                        for h in hosts
                    ]
                )
                for tgt in targets
            ]

            print("  - %s: write table" % rname)
            fptr.write(
                tabulate(
                    ROWS, headers=[rname] + hosts, stralign="center", tablefmt="github"
                )
            )
            fptr.write("\n\n---\n\n")
