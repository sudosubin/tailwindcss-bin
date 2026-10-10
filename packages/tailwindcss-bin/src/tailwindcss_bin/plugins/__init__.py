"""Optional plugin wheels extend this namespace."""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
