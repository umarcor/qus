from subprocess import check_call

from getter import Getter

class GetterDebian(Getter):

    def __init__(self, archs):
        super().__init__(archs)
        print("[GetterDebian] __init__", archs)