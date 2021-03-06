# $Filename$ 
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
Defines SVN-specific connection parameters. 
"""


import hashlib
import os
import tempfile

from datafinder.persistence.error import PersistenceError
from datafinder.persistence.adapters.svn.util.util import pepareSvnPath


__version__ = "$Revision-Id$" 


class Configuration(object):
    """ Defines a set of configuration parameters of the SVN protocol. """
    
    def __init__(self, baseConfiguration):
        """ 
        @param baseConfiguration: General basic configuration.
        @type baseConfiguration: L{BaseConfiguration<datafinder.persistence.common.configuration.BaseConfiguration>}
        """
        
        path = pepareSvnPath(baseConfiguration.uriPath)
        self.baseUrl = baseConfiguration.uriScheme + "://" + baseConfiguration.uriNetloc + path 
        self.protocol = baseConfiguration.uriScheme

        self.username = baseConfiguration.username
        self.password = baseConfiguration.password
        
        baseWorkingCopyPath = baseConfiguration.baseWorkingDirectory or tempfile.gettempdir()
        if not baseWorkingCopyPath is None:
            hash_ = hashlib.sha1(self.baseUrl).hexdigest()
            self.workingCopyPath = os.path.join(baseWorkingCopyPath, hash_, "working_copy")
            self.workingCopyPath = self.workingCopyPath.replace("\\", "/")
        else:
            raise PersistenceError("Cannot determine temporary working copy directory.")
