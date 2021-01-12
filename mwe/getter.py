from subprocess import check_call

class Getter:
    def __init__(self, archs):
        self._archs = archs
        print("[Getter] __init__", archs)
        pass

    def _normalise_arch(self, arch):
        for key, val in self._archs.items():
            if key == arch:
                return key
            if "alias" in val:
                alias = val["alias"]
                if alias is not None:
                    if arch in alias:
                        return key
