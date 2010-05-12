# pylint: disable-msg=W0142
# W0142: In this case i think it improves the readability.
#        Used in struct_time for datetime conversion.
#
# Created: 19.02.2009 schlauch <Tobias.Schlauch@dlr.de>
# Changed: $Id: value_mapping.py 4552 2010-03-16 12:28:19Z schlauch $ 
# 
# Copyright (c) 2008, German Aerospace Center (DLR)
# All rights reserved.
# 
# http://www.dlr.de/datafinder/
#


""" 
Implements conversion of meta data values from 
Python types to the persistence format and vice versa.
"""


import time
from datetime import datetime, timedelta, tzinfo
import rfc822
import decimal


__version__ = "$LastChangedRevision: 4552 $"


_LIST_SEPARATOR = ";"
_ISO8601_DATETIME_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"
_NONE_PERSISTENCE_REPRESENTATION = ""
_EMPTY_LIST_REPRESENTATION = "____EMPTY____LIST____"


class MetadataValue(object):
    """ Wrapper around a meta data value in persistence format. """

    def __init__(self, persistedValue, expectedType=None):
        """ 
        Constructor. 
        
        @param persistedValue: The persistence representation of a property value.
        @type persistedValue: C{unicode}
        """
        
        self._expectedType = expectedType
        self.__persistedValue = persistedValue
        self.__conversionFunctions = list()
        self.__conversionFunctions.append(self._convertToBool)
        self.__conversionFunctions.append(self._convertToDecimal)
        self.__conversionFunctions.append(self._convertToDatetime)
        self.__conversionFunctions.append(self._convertToList)
        self.__conversionFunctions.append(self._convertToUnicode)
        
    def __getPersistedValue(self):
        """ Simple getter. """
        
        return self.__persistedValue
    persistedValue = property(__getPersistedValue)
    
    def __getValue(self):
        """ Getter for the most probable value. """
        
        representations = self.guessRepresentation()
        if not self._expectedType is None:
            for representation in representations:
                if type(representation) == self._expectedType:
                    return representation
        return representations[0]
    value = property(__getValue)
        
    def guessRepresentation(self):
        """ 
        Tries to convert the retrieved value to the expected type.
        If the conversion fails an empty list is returned.
        
        @return: List of possible value representations.
        @rtype: C{list} of C{object}
        """
        
        result = list()
        if _NONE_PERSISTENCE_REPRESENTATION == self.__persistedValue:
            result.append(None)
        else:
            convertedValue = None
            for conversionFunction in self.__conversionFunctions:
                convertedValue = conversionFunction(self.__persistedValue)
                if not convertedValue is None:
                    result.append(convertedValue)
        return result
        
    def _convertToList(self, value):
        """ Converts value to a list. """
        
        if _LIST_SEPARATOR in value:
            stringList = value.split(_LIST_SEPARATOR)[:-1]
            typedList = list()
            for item in stringList:
                if item == _NONE_PERSISTENCE_REPRESENTATION:
                    convertedValue = None
                else:
                    for conversionFunction in self.__conversionFunctions:
                        convertedValue = conversionFunction(item)
                        if not convertedValue is None:
                            break
                typedList.append(convertedValue)
            return typedList
        elif value == _EMPTY_LIST_REPRESENTATION:
            return  list()

    @staticmethod
    def _convertToUnicode(value):
        """ Converts to a unicode value. """
        
        return value
    
    @staticmethod
    def _convertToBool(value):
        """ Converts the given unicode value to boolean. """
        
        try:
            intValue = int(value)
        except ValueError:
            return None
        else:
            if intValue in [0, 1]:
                return bool(intValue)
    
    @staticmethod
    def _convertToDecimal(value):
        """ Converts value to decimal. """
        
        try:
            return decimal.Decimal(value)
        except decimal.InvalidOperation:
            return None
        
    def _convertToDatetime(self, value):
        """ Converts value to date time. """
        
        datetimeInstance = None
        datetimeConversionFunctions = [self._convertToDatetimeFromIso8601,
                                       self._convertToDatetimeFromRfc822,
                                       self._convertToDatetimeFromFloat]
        for datetimeConversionFunction in datetimeConversionFunctions:
            datetimeInstance = datetimeConversionFunction(value)
            if not datetimeInstance is None:
                return datetimeInstance.replace(tzinfo=None)
    
    @staticmethod
    def _convertToDatetimeFromFloat(value):
        """ 
        Converts to datetime instance from float 
        value representing time ticks since 1970.
        """
        
        try:
            floatValue = float(value)
            dt = datetime.fromtimestamp(floatValue)
            dt = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, _LocalTimezone())
        except ValueError:
            return None
        return dt
    
    @staticmethod
    def _convertToDatetimeFromRfc822(value):
        """
        Converts to datetime instance from string
        representing date and time in format defined by RFC 822.
        """
        
        try:
            structTime = rfc822.parsedate(value)
        except IndexError:
            return None
        if not structTime is None:
            dt = datetime(*(structTime[0:6]))
            dt = dt.replace(tzinfo=_Utc())
            return dt.astimezone(_LocalTimezone())
        else:
            return None
    
    @staticmethod
    def _convertToDatetimeFromIso8601(value):
        """ 
        Converts to datetime from string 
        representing date and time in format defined by ISO 8601.
        """
        
        try:
            dt = datetime(*(time.strptime(value, _ISO8601_DATETIME_FORMAT)[0:6]))
            dt = dt.replace(tzinfo=_Utc())
            return dt.astimezone(_LocalTimezone())
        except ValueError:
            return None
    
    def __cmp__(self, instance):
        """ Compares to instances. """
        
        if self.persistedValue == instance.persistedValue:
            return 0
        else:
            return 1

    
def getPersistenceRepresentation(value):
    """ 
    Tries to convert the given value to the persistence string format.
    
    @param value: Value to persist.
    @type value: C{object}

    @return: String representation.
    @rtype: C{string}
    """
    
    if value is None:
        return _NONE_PERSISTENCE_REPRESENTATION
    else:
        typeConversionFunctionMap = {str: _convertFromUnicode,
                                     unicode: _convertFromUnicode,
                                     int: _convertFromDecimal,
                                     float: _convertFromDecimal,
                                     bool: _convertFromBool,
                                     decimal.Decimal: _convertFromDecimal,
                                     list: _convertFromList,
                                     datetime: _convertFromDatetime} 
        valueType = type(value)
        if valueType in typeConversionFunctionMap:
            return typeConversionFunctionMap[valueType](value)
        else:
            raise ValueError("Persistence support for values of type '%s' is not available." % str(valueType))


def _convertFromDatetime(value):
    """ Converts an datetime instance to a string. """

    value = value.replace(tzinfo=_LocalTimezone())
    value = value.astimezone(_Utc())
    return value.strftime(_ISO8601_DATETIME_FORMAT)
    

def _convertFromDecimal(value):
    """ Converts a Decimal instance to a string. """
    
    return unicode(value)
    
    
def _convertFromBool(value):
    """ Converts a boolean value to a string. """
    
    return unicode(int(value))


def _convertFromList(value):
    """ Converts a list to a string. """
    
    listAsString = ""
    for item in value:
        convertedItem = getPersistenceRepresentation(item)
        listAsString += convertedItem + _LIST_SEPARATOR
    if len(listAsString) == 0:
        listAsString = _EMPTY_LIST_REPRESENTATION
    return listAsString


def _convertFromUnicode(value):
    """ Converts an unicode. """
    
    if not isinstance(value, unicode):
        value = unicode(value)
    return value
    
    
class _Utc(tzinfo):
    """ Representation of UTC time. """

    def utcoffset(self, _):
        """ @see: L{datetime.tzinfo.utcoffset} """
        
        return timedelta(0)

    def tzname(self, _):
        """ @see: L{datetime.tzinfo.tzname} """
        
        return "UTC"

    def dst(self, _):
        """ @see: L{datetime.tzinfo.dst} """
        
        return timedelta(0)
    

class _LocalTimezone(tzinfo):
    """ Representation of the local time. """

    def __init__(self):
        """ Constructor. """
        
        tzinfo.__init__(self)
        self.__standardOffset = timedelta(seconds=-time.timezone)
        self.__dstOffset = self.__standardOffset
        if time.daylight:
            self.__dstOffset = timedelta(seconds=-time.altzone)
        self.__destDifference = self.__dstOffset - self.__standardOffset

    def utcoffset(self, dt):
        """ @see: L{datetime.tzinfo.utcoffset} """
        
        if self.__isdst(dt):
            return self.__dstOffset
        else:
            return self.__standardOffset

    def dst(self, dt):
        """ @see: L{datetime.tzinfo.dst} """
        
        if self.__isdst(dt):
            return self.__destDifference
        else:
            return timedelta(0)

    def tzname(self, dt):
        """ @see: L{datetime.tzinfo.tzname} """
        
        return time.tzname[self.__isdst(dt)]

    @staticmethod
    def __isdst(dt):
        """ 
        Helper method determining datetime
        instance in daylight saving time or not.
        """
        
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        try:
            stamp = time.mktime(tt)
            tt = time.localtime(stamp)
            return tt.tm_isdst > 0
        except (ValueError, OverflowError):
            return False