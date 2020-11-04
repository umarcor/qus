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
from subprocess import check_call

from getter import Getter


class GetterFedora(Getter):
    """
    Download qemu-user-static RPM packages from Fedora repositories.
    """

    def __init__(self, archs):
        super().__init__(archs)

    def get_package_binaries(self, host, bindir="bin-static"):
        """
        Get an RPM package and extract the binaries.
        """
        print(
            "[GetterFedora] get_package_binaries %s (%s)" % (host, str(bindir)),
            flush=True,
        )

        args = self.url_args("fedora", host)

        url = (
            "https://kojipkgs.fedoraproject.org/packages/qemu/%s/%s/%s/qemu-user-static-%s-%s.%s.rpm"
            % (args + args)
        )

        if type(bindir) is str:
            bindir = Path(bindir)
        bindir.mkdir(parents=True, exist_ok=True)

        # https://bugzilla.redhat.com/show_bug.cgi?id=837945
        check_call(
            'curl -fsSL "%s" | rpm2cpio - | zstdcat | cpio -dimv "*usr/bin*qemu-*-static"'
            % url,
            shell=True,
            cwd=bindir,
        )
        check_call("mv ./usr/bin/* ./; rm -rf ./usr", shell=True, cwd=bindir)
