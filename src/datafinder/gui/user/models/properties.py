#
# Created: 18.02.2008 lege_ma <malte.legenhausen@dlr.de>
# Changed: $Id: properties.py 4552 2010-03-16 12:28:19Z schlauch $
#
# Copyright (C) 2003-2008 DLR/SISTEC, Germany
#
# All rights reserved
#
# http://www.dlr.de/datafinder/
#


"""
This module contains the properties model.
"""


from PyQt4 import QtCore, QtGui

from datafinder.gui.user.common.util import extractPyObject, determineDisplayRepresentation, determinePropertyDefinitionToolTip
from datafinder.core.configuration.properties import constants
from datafinder.core.configuration.properties.property_type import determinePropertyTypeConstant
from datafinder.core.error import PropertyError

__version__ = "$LastChangedRevision: 4552 $"


class PropertiesModel(QtCore.QAbstractTableModel):
    """
    This model represents a set of properties.
    """

    PROPERTY_STATE_CHANGED_SIGNAL = "propertyStateChanged"
    IS_CONSISTENT_SIGNAL = "isConsistentSignal"

    _SYSTEM = 1
    _DATA = 2
    _PROP = 4
    _NEW = 8

    _DELETED = 16
    _EDITED = 32
    _REQUIRED_NOT_SET = 64
    
    def __init__(self, repositoryModel, trackRepositoryUpdates=True):
        """
        Constructor.

        @param repositoryModel: The parent model which handles access to item of the data repository.
        @type repositoryModel: L{RepositoryModel<datafinder.gui.user.models.repository.RepositoryModel>}
        @param trackRepositoryUpdates: Optional flag determining whether the property model
                                       reacts on changes of the repository. Default: C{true}
        @type trackRepositoryUpdates: C{bool}
        """

        QtCore.QAbstractTableModel.__init__(self)

        self._sortedColumn = 0
        self._sortedOrder = QtCore.Qt.AscendingOrder
        self._headers = [self.tr("Name"), self.tr("Type"), self.tr("Value")]

        self._itemIndex = None
        self.isReadOnly = False
        self._isConsistent = False
        self.itemName = ""
        self._repositoryModel = repositoryModel
        self._properties = list(list())
        if trackRepositoryUpdates:
            self.connect(self._repositoryModel, QtCore.SIGNAL("itemDataChanged"), self._handleUpdateSlot)
            self.connect(self._repositoryModel, QtCore.SIGNAL("modelReset()"), self.clear)
    
    def _handleUpdateSlot(self, index):
        """ Handles update. """
        
        if index.row() == self._itemIndex.row():
            self.itemIndex = index
            self.reset()
            self._emitPropertyDataChanged()
    
    def _emitPropertyDataChanged(self):
        """ Emits the signal C{self.PROPERTY_STATE_CHANGED_SIGNAL}. """
        
        self.emit(QtCore.SIGNAL(self.PROPERTY_STATE_CHANGED_SIGNAL))
    
    def load(self, properties):
        """
        Initializes the model with the given properties.
        
        @param properties: Properties represented by this model.
        @type properties: C{list} of L{Property<datafinder.core.item.property.Property>}
        """

        self._properties = list(list())
        propertyIds = list()
        for prop in properties:
            try:
                propDef = prop.propertyDefinition
            except AttributeError:
                propDef = prop
            state = self._determinePropertyState(propDef.category)
            if not propDef.identifier in propertyIds and not state is None:
                propertyIds.append(propDef.identifier)
                try:
                    value = prop.value
                except AttributeError:
                    value = propDef.defaultValue
                displayPropertyTypeName = self._determinePropertyTypeName(propDef.type, value)
                self._properties.append([propDef.displayName, displayPropertyTypeName, value,
                                         propDef, propDef.restrictions, propDef.type, value, state])
        self._checkConsistency()

    def _checkConsistency(self):
        """ Checks whether all properties are set correctly. """
        
        self._isConsistent = True
        for prop in self._properties:
            try:
                if prop[-1] & self._NEW:
                    self._repositoryModel.repository.createProperty(prop[0], prop[2])
                else:
                    try:
                        namespace = prop[3].namespace
                    except AttributeError:
                        namespace = prop[3].propertyDefinition.namespace
                    self._repositoryModel.repository.createProperty(prop[3].identifier, prop[2], namespace)
                if prop[-1] & self._REQUIRED_NOT_SET:
                    prop[-1] ^= self._REQUIRED_NOT_SET
            except PropertyError:
                prop[-1] |= self._REQUIRED_NOT_SET
                self._isConsistent = False
        self.emit(QtCore.SIGNAL(self.IS_CONSISTENT_SIGNAL), self._isConsistent)

    @staticmethod
    def _determinePropertyState(category):
        """ Determines the internal state of the property. E.g. data model specific. """
        
        if category in (constants.UNMANAGED_SYSTEM_PROPERTY_CATEGORY, 
                        constants.MANAGED_SYSTEM_PROPERTY_CATEGORY):
            state = PropertiesModel._SYSTEM
        elif category == constants.DATAMODEL_PROPERTY_CATEGORY:
            state = PropertiesModel._DATA
        elif category == constants.USER_PROPERTY_CATEGORY:
            state = PropertiesModel._PROP
        else:
            state = None
        return state
        
    @staticmethod
    def _determinePropertyTypeName(propertyType, propertyValue):
        """ Determines the display name of the property type. """
        
        displayPropertyTypeName = propertyType
        if displayPropertyTypeName == constants.ANY_TYPE:
            try:
                displayPropertyTypeName = determinePropertyTypeConstant(propertyValue)
            except ValueError:
                displayPropertyTypeName = constants.STRING_TYPE    
        return displayPropertyTypeName    
        
    def rowCount(self, _=QtCore.QModelIndex()):
        """
        @see: L{rowCount<PyQt4.QtCore.QAbstractTableModel.rowCount>}
        """
        
        return len(self._properties)

    def columnCount(self, _):
        """
        @see: L{columnCount<PyQt4.QtCore.QAbstractTableModel.columnCount>}
        """

        return len(self._headers)

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        """
        @see: L{headerData<PyQt4.QtCore.QAbstractTableModel.headerData>}
        """

        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return QtCore.QVariant(self._headers[section])
            if role == QtCore.Qt.TextAlignmentRole:
                return QtCore.QVariant(int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter))
        return QtCore.QVariant()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ @see: L{data<PyQt4.QtCore.QAbstractTableModel.data>} """

        row = index.row()
        variant = QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:
            value = self._properties[row][index.column()]
            if index.column() == 2:
                propDef = self._properties[row][3]
                propId = None
                if not propDef is None:
                    propId = propDef.identifier
                variant = QtCore.QVariant(determineDisplayRepresentation(value, propId))
            else:
                variant = QtCore.QVariant(value)
        elif role == QtCore.Qt.BackgroundColorRole:
            state = self._properties[row][-1]
            attribute = QtGui.QColor(QtCore.Qt.white)
            if state & self._DELETED:
                attribute = QtGui.QColor(255, 100, 100)
            elif state & self._NEW:
                attribute = QtGui.QColor(100, 255, 100)
            elif state & self._REQUIRED_NOT_SET:
                attribute = QtGui.QColor(255, 255, 0)
            elif state & self._EDITED:
                attribute = QtGui.QColor(240, 240, 240)
            variant = QtCore.QVariant(attribute)
        elif role == QtCore.Qt.ToolTipRole and index.column() == 0:
            propertyEntry = self._properties[index.row()]
            if not propertyEntry[3] is None:
                variant = determinePropertyDefinitionToolTip(propertyEntry[3])
        return variant

    def setData(self, index, value, _=None):
        """
        @see: L{setData<PyQt4.QtCore.QAbstractTableModel.setData>}
        """

        row = index.row()
        column = index.column()

        value = extractPyObject(value)
        try:
            changed = cmp(self._properties[row][column], value)
        except TypeError:
            changed = True
        
        if changed:
            self._properties[row][column] = value
            if not self._properties[row][-1] & self._NEW:
                self._properties[row][-1] |= self._EDITED
                self._checkConsistency()
            if column == 1:
                self._properties[row][2] = None
                self._checkConsistency()

        if self._properties[row][0] is None:
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            del self._properties[row]
            self.endRemoveRows()
            self._emitPropertyDataChanged()
            return False

        self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        self._emitPropertyDataChanged()
        return True

    def flags(self, index):
        """
        @see: L{flags<PyQt4.QtCore.QAbstractTableModel.flags>}
        """

        state = self._properties[index.row()][-1]
        flags = QtCore.Qt.ItemIsSelectable
        if not self.isReadOnly:
            if state & self._NEW \
               or (state & (self._DATA|self._PROP) and index.column() == 2) \
               or (self._properties[index.row()][5] == constants.ANY_TYPE and state & (self._DATA|self._PROP) and index.column() == 1):
                flags |= QtCore.Qt.ItemIsEnabled
                if not state & self._DELETED:
                    flags |= QtCore.Qt.ItemIsEditable
        return flags

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        """
        @see: L{sort<PyQt4.QtCore.QAbstractTableModel.sort>}
        """

        self._sortedColumn = column
        self._sortedOrder = order
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self._properties.sort(reverse = (order == QtCore.Qt.DescendingOrder),
                              cmp=lambda x, y: cmp(determineDisplayRepresentation(x[column]).lower(), 
                                                   determineDisplayRepresentation(y[column]).lower()))
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def save(self):
        """
        Save all modified attributes of the given item.
        """

        dirty = False
        for row in self._properties:
            state = row[-1]
            if state &  (self._EDITED|self._NEW| self._DELETED):
                dirty = True
        if dirty:
            self._updateProperties(self._properties)
        
    def _updateProperties(self, properties):
        """
        Converts the data saved in the model back to its internally used 
        representation and stores it.
        """
        
        addedEditedProperties = list()
        deletableProperties = list()
        for prop in properties:
            state = prop[-1]
            if state & self._DELETED:
                deletableProperties.append(prop[0])
            elif state & self._NEW:
                newProperty = self._repositoryModel.repository.createProperty(prop[0], prop[2])
                addedEditedProperties.append(newProperty)
            elif state & self._EDITED:
                newProperty = self._repositoryModel.repository.createPropertyFromDefinition(prop[3], prop[2])
                addedEditedProperties.append(newProperty)
        if len(addedEditedProperties) > 0 or len(deletableProperties) > 0:
            if not self._itemIndex is None:
                self._repositoryModel.updateProperties(self._itemIndex, addedEditedProperties, deletableProperties)
                    
    def clear(self):
        """
        Clears the model internal data and resets the model.
        """

        self._itemIndex = None
        self._properties = list()
        self.reset()

    def refresh(self):
        """ Reloads all data from the server and resets the data model. """

        if not self._itemIndex is None:
            self._repositoryModel.refresh(self._itemIndex, True)
            self.itemIndex = self._itemIndex
            self.sort(self._sortedColumn, self._sortedOrder)
            self.reset()
            self._emitPropertyDataChanged()

    def add(self):
        """
        Appends a new property to the end of the existing properties.

        @return: The index the new property.
        @rtype: L{QModelIndex<PyQt4.QtCore.QModelIndex>}
        """

        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self._properties.append([None, None, None, None, None, constants.ANY_TYPE, None, self._NEW])
        self.endInsertRows()

        index = self.createIndex(row, 0, self._properties[row][0])
        self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        self._emitPropertyDataChanged()
        return index

    def clearValue(self, index):
        """ 
        Clears the value of the property, i.e. set it to C{None}.
        
        @param index: The index that has to be cleared.
        @type index: L{QModelIndex<PyQt4.QtCore.QModelIndex>}
        """
        
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self._properties[index.row()][2] = None
        self._properties[index.row()][-1] |= self._EDITED
        self._checkConsistency()
        self.emit(QtCore.SIGNAL("layoutChanged()"))
        self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        self._emitPropertyDataChanged()
        
    def remove(self, index):
        """
        Removes the property by the given index.
        When the item was a new item the item will delete instantly otherwise the property
        will first deleted after a save operation.

        @param index: The index that has to be removed.
        @type index: L{QModelIndex<PyQt4.QtCore.QModelIndex>}
        """

        row = index.row()
        props = self._properties[row][-1]

        if not props & self._NEW | self._PROP:
            raise ValueError("Given index at %d, %d can not be deleted." % (row, index.column()))

        if props & self._NEW:
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            del self._properties[row]
            self.endRemoveRows()
        else:
            self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
            self._properties[row][-1] |= self._DELETED
            self.emit(QtCore.SIGNAL("layoutChanged()"))
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        self._emitPropertyDataChanged()
        
    def revert(self, index=None):
        """
        If the given index has the status deleted, this method removes the deleted status.

        @param index: The index that has to be reverted.
        @type index: L{QModelIndex<PyQt4.QtCore.QModelIndex>}
        """

        if not index is None:
            row = index.row()
            self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
            if self._properties[row][-1] & self._DELETED:
                self._properties[row][-1] ^= self._DELETED
            elif self._properties[row][-1] & self._EDITED:
                originalType = constants.STRING_TYPE
                originalValue = None
                if not self._properties[row][6] is None:
                    originalValue = self._properties[row][6]
                    originalType = self._determinePropertyTypeName(self._properties[row][5], originalValue)
                        
                self._properties[row][1] = originalType
                self._properties[row][2] = originalValue
                self._properties[row][-1] ^= self._EDITED
                self._checkConsistency()
            self.emit(QtCore.SIGNAL("layoutChanged()"))
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
            self._emitPropertyDataChanged()
            
    def _isPropertyNameUnique(self, propertyName):
        """ Checks whether the given property name is a unique identifier. """
        
        for item in self._properties:
            existingIdentifer = item[0]
            if not item[3] is None:
                existingIdentifer = item[3].identifier
            if existingIdentifer == propertyName:
                return False
        return True 
    
    def isDeleteable(self, index):
        """
        Return whether the given index can be deleted or not.

        @param index: Index that has to be checked.
        @type index: L{QModelIndex<PyQt4.QtCore.QModelIndex>}

        @return: C{True} if the index can be deleted else C{False}.
        @rtype: C{bool}
        """

        flags = self._properties[index.row()][-1]
        return flags & (self._NEW | self._PROP) and not flags & self._DELETED

    def isRevertable(self, index):
        """
        Return whether the given index can be reverted or not.

        @param index: Index that has to be checked.
        @type index: L{QModelIndex<PyQt4.QtCore.QModelIndex>}

        @return: C{True} if the index can be reverted else False.
        @rtype: C{bool}
        """

        return self._properties[index.row()][-1] & (self._DELETED | self._EDITED)

    def canBeCleared(self, index):
        """
        Checks whether the given index can be cleared or not.

        @param index: Index that has to be checked.
        @type index: L{QModelIndex<PyQt4.QtCore.QModelIndex>}

        @return: C{True} if the index can be cleared else C{False}.
        @rtype: C{bool}
        """

        return not self._properties[index.row()][-1] & self._SYSTEM \
               and not self._properties[index.row()][2] is None

    def getModelData(self, row, column):
        """
        This function allows direct access the model data structure.
        """
        
        return self._properties[row][column]
    
    @property
    def hasCustomMetadataSupport(self):
        """ Getter for the has custom meta data flag. """
        
        return self._repositoryModel.hasCustomMetadataSupport

    @property
    def propertyNameValidationFunction(self):
        """ Getter for the property identifier validation function. """
        
        def wrapper(inputString):
            return self._repositoryModel.repository.configuration.propertyNameValidationFunction(inputString) \
                   and self._isPropertyNameUnique(inputString)
        return wrapper

    @property
    def dirty(self):
        """
        Returns whether the data has changed.

        @return: C{True} if the data has changed else C{False}.
        @rtype: C{bool}
        """

        for item in self._properties:
            if item[-1] & (self._EDITED | self._DELETED | self._NEW):
                return True
        return False

    @property
    def sortProperties(self):
        """
        Returns how the model is sorted.

        @return: The properties for the sorting, i.e. sorted column number and sort order.
        @rtype: C{tuple}
        """

        return self._sortedColumn, self._sortedOrder

    @property
    def properties(self):
        """
        Returns the properties represented by this model.
        
        @return: List of property instances contained in this model.
        @rtype: C{list} of L{Property<datafinder.core.item.property.Property>}
        """
        
        properties = list()
        for prop in self._properties:
            if prop[-1] & self._NEW:
                newProperty = self._repositoryModel.repository.createProperty(prop[0], prop[2])
            else:
                newProperty = self._repositoryModel.repository.createPropertyFromDefinition(prop[3], prop[2])
            properties.append(newProperty)
        return properties
             
    @property
    def isConsistent(self):
        """ Checks whether all properties are set correctly. """
        
        return self._isConsistent
             
    def _setItemIndex(self, index):
        """
        Set the index from which the properties have to be loaded.
        In the most cases this is the current selected index in the view.

        @param itemIndex: The itemIndex from which the properties has to be loaded.
        @type itemIndex: L{QModelIndex<PyQt4.QtCore.QModelIndex>}
        """

        self._properties = list(list())
        self.isReadOnly = True
        if index.isValid():
            item = self._repositoryModel.nodeFromIndex(index)
            if item.isLink:
                item = item.linkTarget
            if not item is None:
                if not item.path is None:
                    self._itemIndex = self._repositoryModel.indexFromPath(item.path)
                    self.itemName = item.name
                    self.isReadOnly = not item.capabilities.canStoreProperties
                    properties = item.properties.values() + item.requiredPropertyDefinitions
                    self.load(properties)
                    self.sort(self._sortedColumn, self._sortedOrder)
    itemIndex = property(fset=_setItemIndex)