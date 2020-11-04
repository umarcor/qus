#!/usr/bin/env python3

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
from os import listdir

from pyAttributes.ArgParseAttributes import (
    ArgParseMixin,
    ArgumentAttribute,
    Attribute,
    CommandAttribute,
    CommonSwitchArgumentAttribute,
    DefaultAttribute,
    SwitchArgumentAttribute,
)

from assets import get_json_from_api, extract_from_json, releases_report
from debian import (
    check_debian_latest,
    get_debs_list,
    get_debs,
    debian_report,
    extract_debs,
)
from fedora import check_fedora_latest
from build import builder


ROOT = Path(__file__).parent.parent


class Tool:
    HeadLine = "dbhi/qus CLI tool"

    def __init__(self):
        pass

    def PrintHeadline(self):
        print("{line}".format(line="=" * 80))
        print("{headline: ^80s}".format(headline=self.HeadLine))
        print("{line}".format(line="=" * 80))

    @staticmethod
    def assets(fname: Path = ROOT / "releases.json", report: Path = ROOT / "report.md"):
        (TARGETS, TABLES) = extract_from_json(get_json_from_api(fname))
        TARGETS.sort()
        releases_report(TARGETS, TABLES, report)

    @staticmethod
    def debian(report: Path = ROOT / "debian.md"):
        tmpdir = ROOT / "tmp_deb"
        debs = get_debs_list()
        get_debs(debs, tmpdir)
        targets = []
        extract_debs(targets, debs, tmpdir)
        targets.sort()
        debian_report(targets, debs, report)


class CLI(Tool, ArgParseMixin):
    def __init__(self):
        import argparse
        import textwrap

        # Call constructor of the main interitance tree
        super().__init__()
        # Call constructor of the ArgParseMixin
        ArgParseMixin.__init__(
            self,
            description=textwrap.dedent(
                "Tool for building (multiarch) images, and for easily browsing publicly available tags and assets."
            ),
            epilog=textwrap.fill("Happy hacking!"),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,
        )

    def Run(self):
        ArgParseMixin.Run(self)

    @DefaultAttribute()
    def HandleDefault(self, args):
        self.PrintHeadline()
        self.MainParser.print_help()

    @CommandAttribute("help", help="Display help page(s) for the given command name.")
    @ArgumentAttribute(
        metavar="<Command>",
        dest="Command",
        type=str,
        nargs="?",
        help="Print help page(s) for a command.",
    )
    def HandleHelp(self, args):
        if args.Command == "help":
            print("This is a recursion ...")
            return
        if args.Command is None:
            self.PrintHeadline()
            self.MainParser.print_help()
        else:
            try:
                self.PrintHeadline()
                self.SubParsers[args.Command].print_help()
            except KeyError:
                print("Command {0} is unknown.".format(args.Command))

    @CommandAttribute(
        "check", help="Check if new releases are available upstream (Debian/Fedora)."
    )
    def HandleCheck(self, _):
        check_debian_latest()
        check_fedora_latest()

    @CommandAttribute(
        "assets", help="Generate report of available releases and assets."
    )
    def HandleAssets(self, _):
        self.assets()

    @CommandAttribute(
        "debian", help="Generate report of available resources in DEB packages."
    )
    def HandleDebian(self, _):
        self.debian()

    @CommandAttribute("build", help="TODO.")
    @ArgumentAttribute(
        "-s",
        "--source",
        nargs=1,
        metavar="<Source>",
        dest="Source",
        type=str,
        help="Source to get packages from: debian or fedora",
    )
    # @ArgumentAttribute(metavar='<Builder>', dest="Builder", type=str, help="Builder architecture, typically amd64")
    @ArgumentAttribute(
        metavar="<Hosts>",
        dest="Hosts",
        type=str,
        nargs="*",
        help="Host architecture(s)",
    )
    def HandleDebian(self, args):
        builder(args.Source[0], "amd64", args.Hosts)


if __name__ == "__main__":
    CLI().Run()
