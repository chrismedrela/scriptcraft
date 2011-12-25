# Copyright (C) 2004-2011 by Barry A. Warsaw
#
# This file is part of flufl.enum
#
# flufl.enum is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# flufl.enum is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with flufl.enum.  If not, see <http://www.gnu.org/licenses/>.

"""Python enumerations."""

from __future__ import absolute_import, unicode_literals

__metaclass__ = type
__all__ = [
    b'Enum',
    b'make_enum',
    ]


COMMASPACE = ', '
SPACE = ' '

import re
import warnings



# pylint: disable-msg=C0203
class EnumMetaclass(type):
    """Meta class for Enums."""

    def __init__(cls, name, bases, attributes):
        """Create an Enum class.

        :param cls: The class being defined.
        :param name: The name of the class.
        :param bases: The class's base classes.
        :param attributes: The class attributes.
        """
        super(EnumMetaclass, cls).__init__(name, bases, attributes)
        # Store EnumValues here for easy access.
        cls._enums = {}
        # Figure out the set of enum values on the base classes, to ensure
        # that we don't get any duplicate values (which would screw up
        # conversion from integer).
        for basecls in cls.__mro__:
            if hasattr(basecls, '_enums'):
                # pylint: disable-msg=W0212
                cls._enums.update(basecls._enums)
        # For each class attribute, create an EnumValue and store that back on
        # the class instead of the int.  Skip Python reserved names.  Also add
        # a mapping from the integer to the instance so we can return the same
        # object on conversion.
        for attr in attributes:
            if not (attr.startswith('__') and attr.endswith('__')):
                intval  = attributes[attr]
                enumval = EnumValue(cls, intval, attr)
                if intval in cls._enums:
                    raise TypeError('Multiple enum values: %s' % intval)
                # Store as an attribute on the class, and save the attr name
                setattr(cls, attr, enumval)
                cls._enums[intval] = attr

    def __getattr__(cls, name):
        if name == '__members__':
            return cls._enums.values()
        raise AttributeError(name)

    def __repr__(cls):
        enums = ['%s: %d' % (cls._enums[k], k) for k in sorted(cls._enums)]
        return '<%s {%s}>' % (cls.__name__, COMMASPACE.join(enums))

    def __iter__(cls):
        for i in sorted(cls._enums):
            yield getattr(cls, cls._enums[i])

    def __getitem__(cls, i):
        # i can be an integer or a string
        attr = cls._enums.get(i)
        if attr is None:
            # It wasn't an integer -- try attribute name
            try:
                return getattr(cls, i)
            except (AttributeError, TypeError):
                raise ValueError(i)
        return getattr(cls, attr)

    # Support both MyEnum[i] and MyEnum(i)
    __call__ = __getitem__



class EnumValue:
    """Class to represent an enumeration value.

    EnumValue('Color', 'red', 12) prints as 'Color.red' and can be converted
    to the integer 12.
    """
    def __init__(self, cls, value, name):
        self._enum = cls
        self._value = value
        self._name = name

    def __repr__(self):
        return '<EnumValue: %s.%s [int=%d]>' % (
            self._enum.__name__, self._name, self._value)

    def __str__(self):
        return '%s.%s' % (self._enum.__name__, self._name)

    def __int__(self):
        return self._value

    def __reduce__(self):
        return getattr, (self._enum, self._name)

    @property
    def enum(self):
        """Return the class associated with the enum value."""
        return self._enum

    @property
    def name(self):
        """Return the name of the enum value."""
        return self._name

    @property
    def enumclass(self):
        """Return the class associated with the enum value."""
        warnings.warn('.enumclass is deprecated; use .enum instead',
                      DeprecationWarning)
        return self._enum

    @property
    def enumname(self):
        """Return the name of the enum value."""
        warnings.warn('.enumname is deprecated; use .name instead',
                      DeprecationWarning)
        return self._name

    # Support only comparison by identity and equality.  Ordered comparisions
    # are not supported.
    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __lt__(self, other):
        raise NotImplementedError

    __gt__ = __lt__
    __le__ = __lt__
    __ge__ = __lt__
    __hash__ = object.__hash__



class Enum:
    """The public API Enum class."""

    # pylint: disable-msg=W0232
    __metaclass__ = EnumMetaclass



def make_enum(name, value_string, iterable=None):
    """Return an Enum class from a name and a value string.

    This is a convenience function for defining a new enumeration when you
    don't care about the values of the items.  The values are automatically
    created by splitting the value string on spaces.

    Normally, values are assigned to sequentially increasing integers starting
    at one.  With optional `iterable`, integer values are extracted one at a
    time and assigned to the values.

    :param name: The resulting enum's class name.
    :type name: byte string (or ASCII-only unicode string)
    :param value_string: A string of enumeration item names, separated by
        spaces, e.g. 'one two three'.
    :type value_string: byte string (or ASCII-only unicode string)
    :param iterable: A sequence of integers.
    :type iterable: iterator over int
    :return: The new enumeration class.
    :rtype: instance of `EnumMetaClass`
    """
    value_names = value_string.split()
    illegals = [value for value in value_names
                if re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', value) is None]
    if len(illegals) > 0:
        raise ValueError('non-identifiers: {0}'.format(SPACE.join(illegals)))
    if iterable is None:
        namespace = dict((str(value), i)
                         for i, value in enumerate(value_names, 1))
    else:
        namespace = dict((str(value), i)
                         for i, value in zip(iterable, value_names))
    return EnumMetaclass(str(name), (Enum,), namespace)
