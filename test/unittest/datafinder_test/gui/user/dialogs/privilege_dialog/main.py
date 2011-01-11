# $Filename$$
# $Authors$
# Last Changed: $Date$ $Committer$ $Revision-Id$
#
# Copyright (c) 2003-2011, German Aerospace Center (DLR)
# All rights reserved.
#
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are
#met:
#
# * Redistributions of source code must retain the above copyright 
#   notice, this list of conditions and the following disclaimer. 
#
# * Redistributions in binary form must reproduce the above copyright 
#   notice, this list of conditions and the following disclaimer in the 
#   documentation and/or other materials provided with the 
#   distribution. 
#
# * Neither the name of the German Aerospace Center nor the names of
#   its contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
#LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR 
#A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT 
#OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
#SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
#LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
#DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
#THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  


""" 
Allows simplified start of the privilege dialog.
"""


import sys

from PyQt4.QtGui import QApplication

from datafinder.core.error import CoreError
from datafinder.core.item.privileges.acl import AccessControlList
from datafinder.core.item.privileges.principal import SPECIAL_PRINCIPALS
from datafinder.gui.user.dialogs.privilege_dialog.main import PrivilegeDialog


__version__ = "$Revision-Id:$" 


class RepositoryMock(object):
    """ Mocks the principal search functionality. """
    
    error = False
    searchMode = None
    
    def searchPrincipal(self, _, searchMode):
        """ Raises an error or returns all special principals. """

        self.searchMode = searchMode
        if self.error:
            raise CoreError("")
        return SPECIAL_PRINCIPALS


class ItemMock(object):
    """ Used to mock an item and its ACL. """
    
    def __init__(self, error=CoreError("")):
        """ Constructor. """
        
        self.name = "test.pdf"
        self.path = "/test/item/test.pdf"
        self.acl = AccessControlList()
        self.acl.addDefaultPrincipal(SPECIAL_PRINCIPALS[0])
        self.error = error
        
    def updateAcl(self, acl):
        """ Mocks update ACL method and 
        just set the given ACL to the current one. """
        
        if not self.error is None:
            raise self.error
        else:
            self.acl = acl


if __name__ == "__main__":
    application = QApplication(sys.argv)
    dialog = PrivilegeDialog(RepositoryMock())
    dialog.item = ItemMock(None)
    dialog.show()
    sys.exit(application.exec_())
