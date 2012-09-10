import collections
import io
from gettext import gettext as _


class NameAwareOrderedDict(collections.OrderedDict):
    _("""
    A custom namespace that not only orders its items, but can
    also make those items aware of their names immediately.
    It also helps maintain the list of fields in the stack.
    """)

    def __setitem__(self, name, obj):
        super(NameAwareOrderedDict, self).__setitem__(name, obj)
        if hasattr(obj, 'set_name'):
            obj.set_name(name)


class StructureMetaclass(type):
    @classmethod
    def __prepare__(cls, name, bases, **options):
        return NameAwareOrderedDict()

    def __new__(cls, name, bases, attrs, **options):
        # Nothing to do here, but we need to make sure options
        # don't get passed in to type.__new__() itself.
        return type.__new__(cls, name, bases, attrs)

    def __init__(cls, name, bases, attrs, **options):
        cls._fields = collections.OrderedDict()

        for name, attr in attrs.items():
            if hasattr(attr, 'attach_to_class'):
                attr.attach_to_class(cls)


class Structure(metaclass=StructureMetaclass):
    size = 0

    def __init__(self, **kwargs):

        # Initialize raw value storage
        self._raw_values = {}

        # Values can be added explicitly
        for name, value in kwargs.items():
            setattr(self, name, value)

    # Marshal/Pickle API

    @classmethod
    def load(cls, fp, eager=True):
        obj = cls()
        obj._file = fp
        obj._mode = 'rb'

        if eager:
            # Force each attribute onto the class immediately
            for name in cls._fields:
                getattr(obj, name)

        return obj

    @classmethod
    def loads(cls, string, eager=True):
        return cls.load(io.BytesIO(string), eager=eager)

    def dump(self, fp):
        for name in self._fields:
            fp.write(self._raw_values[name])

    def dumps(self):
        output = io.BytesIO()
        self.dump(output)
        return output.getvalue()

    def __str__(self):
        return _('<Binary Data>')

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self)
