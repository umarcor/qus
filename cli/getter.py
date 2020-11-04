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


class Getter:
    """
    Getter provides common features for downloading packages from distribution repositories.
    """

    def __init__(self, archs):
        """
        Initialise the Getter, providing a config object containing archs, aliases and versions.
        """
        self._archs = archs
        print("[Getter] __init__", archs)
        pass

    def _normalise_arch(self, arch):
        """
        Return the normalised name of one of archs.
        """
        for key, val in self._archs.items():
            if key == arch:
                return key
            if "alias" in val:
                alias = val["alias"]
                if alias is not None:
                    if arch in alias:
                        return key

    def normalise_arch(self, source, arch):
        """
        Return the name of one of the archs, normalised for a given source/usage.
        """
        key = self._normalise_arch(arch)
        return self._archs[key][source] if source in self._archs[key] else key

    def _version(self, source, host):
        """
        Return the version of one of the archs, normalised for a given source/usage.
        """
        key = self._normalise_arch(host)
        ver = self._archs[key]["version"][source]
        return (ver["base"], ver["rev"])

    def url_args(self, source, host):
        """
        Return the URL arguments for one of the archs, normalised for a given source/usage.
        """
        return self._version(source, host) + tuple([self.normalise_arch(source, host)])

    def get_package_binaries(self, host, bindir="bin-static"):
        """
        Get a package and extract the binaries. To be implemented in children classes.
        """
        print("[Getter] get_package_binaries not implemented!", flush=True)

    def generate_tarballs(self, host, bindir="bin-static"):
        """
        Generate a tarball with the binary for an arch, normalised for a given source/usage.
        """
        print(
            "[Getter] generate_tarballs %s (%s)" % (host, str(bindir)),
            flush=True,
        )

        if type(bindir) is str:
            bindir = Path(bindir)

        for item in bindir.iterdir():
            check_call(
                "tar -czf '../releases/%s_%s.tgz' '%s'"
                % (item.name, self._normalise_arch(host), item.name),
                shell=True,
                cwd=bindir,
            )
