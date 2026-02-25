from importlib.metadata import version

try:
    __version__ = version("d_pygen")
except:
    __version__ = "0.0.0-dev"