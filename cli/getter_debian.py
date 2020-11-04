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

from subprocess import check_call

from getter import Getter


class GetterDebian(Getter):
    """
    Download qemu-user-static DEB packages from Debian repositories.
    """

    def __init__(self, archs):
        super().__init__(archs)

    def get_package_binaries(self, host, bindir="bin-static"):
        """
        Get a DEB package and extract the binaries.
        """
        print(
            "[GetterDebian] get_package_binaries %s (%s)" % (host, str(bindir)),
            flush=True,
        )

        url = (
            "http://ftp.debian.org/debian/pool/main/q/qemu/qemu-user-static_%s%s_%s.deb"
            % self.url_args("debian", host)
        )

        if type(bindir) is str:
            bindir = Path(bindir)
        bindir.mkdir(parents=True, exist_ok=True)

        check_call(
            "curl -fsSL '%s' | dpkg --fsys-tarfile - | tar xvf - --wildcards ./usr/bin/qemu-*-static --strip-components=3"
            % url,
            shell=True,
            cwd=bindir,
        )
