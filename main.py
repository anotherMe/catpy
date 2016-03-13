#!/usr/bin/env python

#######################################################################
#	import section
#######################################################################


import sys

try:
	
	import wx

except ImportError, ie:
	
	print "\nCannot load wx module"
	sys.exit(1)
	
#~ else:
	#~ 
	#~ min = wx.MINOR_VERSION
	#~ maj = wx.MAJOR_VERSION
	#~ 
	#~ if ( maj < 1 or min < 8 ):
		#~ 
		#~ print "\nIncorrect version of wx module detected (found: %d.%d - needed >= 2.8)." % (maj, min)
		#~ sys.exit(1)	


import wxcatalog



#######################################################################
#	code section
#######################################################################


app = wx.PySimpleApp()
frame = wxcatalog.MainFrame(None, -1, "CATpy")
app.MainLoop()
