from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    print('package is not installed')
    __version__ = '0.0.0'


class InstallError(Exception):
    def __init__(self, path, error):
        super(InstallError, self).__init__("{} could not be installed - [{}]".format(path, error))


class ClearError(Exception):
    def __init__(self, package, error):
        super(ClearError, self).__init__("Package {} could not be cleared - [{}]".format(package, error))
