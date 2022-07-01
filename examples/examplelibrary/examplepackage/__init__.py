print("examplepackage being imported")
from .version import __version__
print("examplepackage version:", __version__)
print("examplelibrary version:", end=' ')
import pkg_resources
print(pkg_resources.get_distribution("examplelibrary"))
