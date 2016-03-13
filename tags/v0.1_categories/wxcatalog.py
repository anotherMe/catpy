#!/usr/bin/env python


import datetime
import os
import logging
import optparse
import sys
import threading

try:
	
	import wx

except ImportError, ie:
	
	print "\nCannot load wx module"
	sys.exit(1)
	
else:
	
	min = wx.MINOR_VERSION
	maj = wx.MAJOR_VERSION
	
	if ( maj < 1 or min < 8 ):
		
		print "\nIncorrect version of wx module detected (found: %d.%d - needed >= 2.8)." % (maj, min)
		sys.exit(1)	

import customwidgets as cW
import catalog


LOGFILENAME = 'pyCatalog.log'


class MainFrame(wx.Frame):


	def __init__(self, parent, id, title):
		
		
		# parse command line arguments
		self.parseArgs()
		
		# set up log
		self.logSetup() # set up log globally
		
		# set up local log
		self.log = logging.getLogger('pyCatalog.main') 
		
		# notify DEBUG turned ON
		self.log.debug("DEBUG messages turned ON.") 		
		
		# we call the init method of the inherited class
		wx.Frame.__init__( self, parent, wx.ID_ANY, title, size = (600,400) )
		
		# GUI stuff
		self.setup_GUI()
		
		## TODO: delete while subsituting with logging
		# create console window to log messages
		self.logViewer = cW.LogViewer(self, -1)
		
		# Initialize catalog variable
		self.catalog = None
		
		# even if we haven't yet loaded a catalog
		self.catalogSaved = True
		
		# starts a timer of 10 second for refreshing log viewer content
		self.timer = threading.Timer(10.0, self.logViewer.refreshLog)
		self.timer.start()			
		
		self.buttonPanel.setLabel("no catalog loaded")
	


	def logSetup(self):
		
		#~	Level  		Numeric value
		#~	--------------------	-----------------------
		#~	CRITICAL 	50
		#~	ERROR 		40
		#~	WARNING 	30
		#~	INFO 		20
		#~	DEBUG 		10
		#~	NOTSET 		0		
		
		# set up logging to file 
		logging.basicConfig(
		    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
		    datefmt='%m-%d %H:%M',
		    filename=LOGFILENAME,
		    filemode='w')
		
		# set logging level
		if self.options.debug == True:
		    
		    logging.getLogger('pyCatalog').setLevel (logging.DEBUG)
		    
		else:
		    
		    logging.getLogger('pyCatalog').setLevel (logging.WARNING)
		
		## CHECK logging level
		## print logging.getLogger('pyCatalog').getEffectiveLevel()
		
		# define a Handler which writes INFO messages or higher to the sys.stderr
		console = logging.StreamHandler()
		console.setLevel(logging.WARNING)
		
		# set a format which is simpler for console use
		formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
		
		# tell the handler to use this format
		console.setFormatter(formatter)
		
		# add the handler to the root logger
		logging.getLogger('pyCatalog').addHandler(console)



	def parseArgs(self):
		
		# create new parser object
		parser = optparse.OptionParser()
		
		# set help message
		parser.usage = "usage: %prog [options] [catalog to open]"
		
		parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Set debug messages ON.", default=False)
		##parser.add_option("-c", "--create", dest="catalog", help="Create new catalog.", default="")
		
		(self.options, args) = parser.parse_args()
		
		# initialize variable
		self.options.catalog = ''
		
		# recuperiamo l'eventuale nome del catalogo da aprire
		if ( len(args) > 0 ):
			
			self.options.catalog = args[0]



	def setup_GUI(self):
		
		# main container (toolbar and splitter)
		self.mainBox = wx.BoxSizer(wx.VERTICAL)
		
		# add the toolbar
		##self.toolbar = cW.CustomToolBar(self)
		
		# add the button panel
		self.buttonPanel = cW.CustomButtonPanel(self)
		
		self.mainSplitter = wx.SplitterWindow(self, 1)
		
		# left panel setUp
		self.leftPanel = wx.Panel(self.mainSplitter, -1)
		self.leftSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.deviceTree = cW.DeviceTree(self.leftPanel, -1)
		self.leftSizer.Add(self.deviceTree, 1, wx.EXPAND)
		self.leftPanel.SetSizer(self.leftSizer)
		
		# right panel setUp
		self.rightPanel = wx.Panel(self.mainSplitter, -1)
		self.rightSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.fileTree = cW.FileTree(self.rightPanel, -1)
		self.rightSizer.Add(self.fileTree, 1, wx.EXPAND)
		self.rightPanel.SetSizer(self.rightSizer)
		
		# set up main splitter
		self.mainSplitter.SplitVertically(self.leftPanel, self.rightPanel)
		self.mainSplitter.SetMinimumPaneSize(20) # to prevent unsplitting
		self.mainSplitter.SetSashPosition(self.GetSize().x / 3) # set initial sash position
		
		# setUp a StatusBar at the bottom of the window with 2 text field
		self.statusBar = self.CreateStatusBar()
		
		# setup 'Catalog' menu
		self.catalogMenu = wx.Menu()
		self.catalogMenu.Append(wx.ID_NEW, help=" Create new catalog")
		wx.EVT_MENU(self, wx.ID_NEW, self.OnNewCatalog)
		self.catalogMenu.Append(wx.ID_OPEN,help=" Open existing catalog")
		wx.EVT_MENU(self, wx.ID_OPEN, self.OnOpen)
		self.catalogMenu.Append(wx.ID_SAVE, help=" Save current catalog")
		wx.EVT_MENU(self, wx.ID_SAVE, self.OnSaveCatalog)
		self.catalogMenu.Append(wx.ID_SAVEAS, help=" Save current catalog as ...")
		wx.EVT_MENU(self, wx.ID_SAVEAS, self.OnSaveCatalogAs)
		self.catalogMenu.AppendSeparator()
		self.catalogMenu.Append(wx.ID_EXIT, help=" Terminate the program")
		wx.EVT_MENU(self, wx.ID_EXIT, self.OnQuit)
		
		# setup 'View' menu
		self.viewMenu = wx.Menu()
		self.viewMenu.Append(wx.ID_PROPERTIES, "Show log viewer", " Show content of log file")
		wx.EVT_MENU(self, wx.ID_PROPERTIES, self.showLogViewer)
		
		# setup 'Tools' menu
		self.toolsMenu = wx.Menu()
		item = self.toolsMenu.Append(wx.NewId(), "Show category editor", " Show category editor")
		wx.EVT_MENU(self, item.GetId(), self.OnShowCategoryEditor)
		
		# setup 'Help' menu
		self.helpMenu = wx.Menu()
		self.helpMenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
		
		# setUp menubar
		self.menuBar = wx.MenuBar()
		self.menuBar.Append(self.catalogMenu,"&Catalog") 
		self.menuBar.Append(self.viewMenu, "&View")
		self.menuBar.Append(self.toolsMenu, "&Tools")
		self.menuBar.Append(self.helpMenu, "?")
		self.SetMenuBar(self.menuBar)
		
		# lay out widgets in main sizer
		
		##self.mainBox.Add(self.toolbar, 0, wx.EXPAND)
		self.mainBox.Add(self.buttonPanel, 0, wx.EXPAND)
		self.mainBox.Add(self.mainSplitter, 1, wx.EXPAND)
		self.SetSizer(self.mainBox)
		
		
		
		# main frame events
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_CLOSE, self.OnQuit)
		
		# show main frame 
		self.Centre() # show window in the center of the screen		
		self.Show(True)


	def newCatalog(self):
		
		if ( self.catalog != None and self.catalogSaved == False ):
			
			# request user confirmation
			msg = wx.MessageDialog (self, "Current catalog has not been saved.\nDo you want to continue anyway ?", "", wx.YES_NO | wx.ICON_EXCLAMATION)
			response = msg.ShowModal()
			
			if response == wx.ID_NO:			
				
				return
		
		dlg = wx.FileDialog(self, style=wx.FD_OVERWRITE_PROMPT|wx.FD_SAVE, wildcard="Catalog files (*.db)|*.db")
		retValue = dlg.ShowModal()
		
		# exit if no file is choosen
		if retValue == wx.ID_CANCEL:
			
			return
		
		path = os.path.join( dlg.GetDirectory(), dlg.GetFilename() )
		
		# CHECK if selected file already exists and try to delete it
		if os.path.exists(path):
			
			try: # to remove selected file
				
				os.remove(path)
				
			except Exception, e:
				
				self.log.error("Error while trying to remove pre-existent file")
				msg = wx.MessageDialog (self, "Cannot overwrite selected file. Please choose another one.", "", wx.OK | wx.ICON_ERROR)
				msg.ShowModal()
				return
		
		# create a new catalog at the specified path
		self.catalog = catalog.Catalog()
		try: 
			
			self.catalog.createNew(path)
			
		except catalog.Error, e:
			
			msg = wx.MessageDialog (self, "Cannot create catalog at given path. Please check log file for more details.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
			self.catalog = None
			return
		
		# now load newly created catalog
		self.loadCatalog(path)



	def loadCatalog(self, path):
		
		self.catalog = catalog.Catalog()
		
		try: # open catalog at given path
			
			self.catalog.openCatalog( path )
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			msg = wx.MessageDialog (self, "Error while trying to load catalog.\n Look at log file for more infos.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()			
			return
		
		# The catalog has not been modified yet
		self.catalogSaved = True
		
		self.buttonPanel.setLabel(self.catalog.name)
		self.loadDeviceTree()



	def addDevice(self):
		
		# CHECK: catalog is currently loaded ?
		if self.catalog == None:
			
			msg = wx.MessageDialog (self, "No catalog loaded.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return
		
		try: # retrieve list of device types from catalog
			
			types = self.catalog.getDeviceTypes()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to retrieve device types.")
			return		
		
		# we need only type name 
		typesList = ()
		for t in types:
			
			typesList = typesList + (t[1],)
		
		
		dlg = cW.AddDeviceDialog(
									self, 
									-1, 
									sys.argv[0],
									typesList
									)
		
		# If all checks were ok, then fire up device dialog
		if ( dlg.ShowModal() == wx.ID_OK ):
			
			try:
				
				self.catalog.addDevice(dlg.devName, dlg.devTypeId, dlg.devPath)
				
			except catalog.Error, e:
				
				self.log.error ( str(e.msg) )
				return		
		
		# CHECK number of Unicode errors
		if self.catalog.unicodeErrors > 0:
			
			msg = wx.MessageDialog (self, "There were many unicode " \
				"errors while parsing given device (look at log for " \
				"more infos).\n Maybe you are trying to parse a CD / "\
				"DVD mastered under another OS.\n Try to parse device " \
				"under the original OS to reduce number of errors." \
				, "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()			
		
		# catalog has been modified
		self.buttonPanel.setLabel(self.catalog.name + "*")
		self.catalogSaved = False
		
		# reload catalog
		self.loadDeviceTree()


	def delDevice(self):
		
		curItem = self.deviceTree.GetSelection()
		curDevice = self.deviceTree.GetPyData( curItem )
		
		# CHECK: a catalog is currently loaded ?
		if self.catalog == None:
			
			msg = wx.MessageDialog (self, "No catalog loaded.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return		
		
		# CHECK if a device is currently selected
		if curDevice == None:
			
			msg = wx.MessageDialog (self, "No device selected.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return
		
		# REQUEST user confirmation
		msg = wx.MessageDialog (self, "Do you really want to delete " + curDevice.name + " ?", "", wx.YES_NO | wx.ICON_QUESTION)
		response = msg.ShowModal()
		
		if response == wx.ID_NO:
			
			return
		
		
		try: # to remove given device
			
			self.catalog.removeDevice(curDevice.id)
			
		except catalog.Error, e:
			
			msg = wx.MessageDialog (self, "Error while trying to delete selected device.\nLook at log file for more informations.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
			return
		
		# catalog has been modified
		self.catalogSaved = False
		self.buttonPanel.setLabel(self.catalog.name + "*")
		
		# reload device tree
		self.loadDeviceTree()
	


	def saveCatalog(self):
		
		# CHECK if a catalog is currently loaded
		if self.catalog == None:
			
			# request user confirmation
			msg = wx.MessageDialog (self, "There is no catalog to save at the moment.", "", wx.OK | wx.ICON_INFORMATION)
			response = msg.ShowModal()
			return
		
		try: 
			
			self.catalog.saveCatalog()
			
		except catalog.Error, e:
			
			self.log.error("Error while trying to save catalog.")
			msg = wx.MessageDialog (self, "There was an error while trying to save catalog.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
			return
		
		# catalog has been correctly saved
		self.catalogSaved = True
		
		self.buttonPanel.setLabel(self.catalog.name)


	def saveCatalogAs(self):
		
		# CHECK if a catalog is currently loaded
		if self.catalog == None:
			
			# request user confirmation
			msg = wx.MessageDialog (self, "There is no catalog to save at the moment.", "", wx.OK | wx.ICON_INFORMATION)
			response = msg.ShowModal()
			return
		
		# pop up file dialog 
		dlg = wx.FileDialog(self, style=wx.FD_OVERWRITE_PROMPT|wx.FD_SAVE, wildcard="Catalog files (*.db)|*.db")
		##dlg = wx.FileDialog(self, "Choose a file", "", "", "Catalog files (*.db)|*.db") # wxFileDialog(wxWindow* parent, const wxString& message = "Choose a file", const wxString& defaultDir = "", const wxString& defaultFile = "", const wxString& wildcard = "*.*", long style = wxFD_DEFAULT_STYLE, const wxPoint& pos = wxDefaultPosition, const wxSize& sz = wxDefaultSize, const wxString& name = "filedlg")
		result = dlg.ShowModal()
		
		# exit if no file is choosen
		if result == wx.ID_CANCEL:
			
			return
		
		# load the selected file
		path = os.path.join( dlg.GetDirectory(), dlg.GetFilename() )
		
		try: 
			
			self.catalog.saveCatalogAs(path)
			
		except catalog.Error, e:
			
			self.log.error("Error while trying to save catalog.")
			msg = wx.MessageDialog (self, "There was an error while trying to save catalog.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
			return
		
		# catalog has been correctly saved
		self.catalogSaved = True
		
		self.buttonPanel.setLabel(self.catalog.name)


	def loadDeviceTree(self):
		
		try: # retrieve stored devices
			
			devs = self.catalog.listDevices()
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			return
		
		# reconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)		
		
		# clean file tree
		self.fileTree.clearTree()
		
		# disconnect events
		self.deviceTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		
		# clean device tree
		self.deviceTree.clearTree()		
		
		for dev in devs:
			
			# DeviceItem( id, name, type )
			d = cW.DeviceItem( dev[0], dev[1], dev[2] )
			self.deviceTree.appendDevice(d)
		
		# reconnect events
		self.deviceTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnDeviceListSelChanged)



	def loadFileTree(self, idDevice):
		
		# disconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		
		# clear tree from all items
		self.fileTree.clearTree()		
		
		# append level 0 entries for current device to root item
		self.appendToFileTree(self.fileTree.root, idDevice, 0)
		
		# reconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnFileTreeSelChanged)


	def appendToFileTree(self, curItem, idDevice, idParentDir):
		
		# disconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		
		## ADD DIRS ##
		
		try: # retrieve dirs at given level
			
			entries = self.catalog.getChildrenDirs(idDevice, idParentDir)
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			return
		
		for e in entries:
			
			e = cW.EntryItem( e[0], e[1], 'dir' )
			self.fileTree.appendToNode( curItem, e)
		
		
		## ADD FILES ##
		
		try: # retrieve files at levelo 0
			
			entries = self.catalog.getChildrenFiles(idDevice, idParentDir)
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			return
		
		for e in entries:
			
			e = cW.EntryItem( e[0], e[1], 'file' )
			self.fileTree.appendToNode( curItem, e)		
		
		# reconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnFileTreeSelChanged)


	def showLogViewer(self, id):
		
		self.logViewer.Show()
		self.logViewer.refreshLog()


	def searchCatalog(self):
		
		# CHECK: catalog is currently loaded ?
		if self.catalog == None:
			
			msg = wx.MessageDialog (self, "No catalog loaded.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return
		
		dlg = cW.SearchDialog(
									self, 
									-1,
									self.catalog
									)
		
		dlg.Show()


	def showCategoryEditor(self):
		
		# CHECK: catalog is currently loaded ?
		if self.catalog == None:
			
			msg = wx.MessageDialog (self, "No catalog loaded.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return		
		
		dlg = cW.CategoryEditor(self, -1, self.catalog)
		dlg.ShowModal()


	def quitApp(self):
		
		if ( self.catalog != None and self.catalogSaved == False ):
			
			# request user confirmation
			msg = wx.MessageDialog (self, "Current catalog has not been saved.\nDo you really want to quit application ?", "", wx.YES_NO | wx.ICON_QUESTION)
			response = msg.ShowModal()
			
			if response == wx.ID_NO:			
				
				return
		
		# delete timer used to refresh log viewer
		self.timer.cancel()
		
		# destroy window
		self.Destroy()


	def OnSaveCatalog(self, event):
		
		self.saveCatalog()

	def OnSaveCatalogAs(self, event):
		
		self.saveCatalogAs()

	def OnNewCatalog(self, event):
		
		self.newCatalog()


	def OnAddDevice(self, event):
		
		# CHECK: a catalog is currently loaded ?
		if self.catalog == None:
			
			msg = wx.MessageDialog (self, "No catalog loaded.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return
		
		self.addDevice()



	def OnDelDevice(self, event):
		
		self.delDevice()



	def OnDeviceListSelChanged(self, event):
		
		curItem = self.deviceTree.GetSelection()
		currentDevice = self.deviceTree.GetPyData( curItem )
		
		self.loadFileTree(currentDevice.id)
	



	def OnFileTreeSelChanged(self, event):
		
		curItem = self.fileTree.GetSelection()
		curEntry = self.fileTree.GetPyData( curItem )
		
		# only if current entry is a directory
		if curEntry.type == 'dir':
			
			curDeviceItem = self.deviceTree.GetSelection()
			curDevice = self.deviceTree.GetPyData( curDeviceItem )
			
			# append entries only if node has not been already loaded
			if not ( self.fileTree.ItemHasChildren(curItem) ):
				
				# appendToFileTree(curItem, idDevice, idParentDir)
				self.appendToFileTree(curItem, curDevice.id, curEntry.id)
			
			# expand current node
			self.fileTree.Expand(curItem)



	def OnAbout(self,e):
		
		# Create a message dialog box
		d = wx.MessageDialog( self, " pyCatalog ","About", wx.OK)
		d.ShowModal() # Shows it
	
	
	def OnOpen(self, event):
		
		if ( self.catalog != None and self.catalogSaved == False ):
			
			# request user confirmation
			msg = wx.MessageDialog (self, "Current catalog has not been saved.\nDo you want to continue anyway ?", "", wx.YES_NO | wx.ICON_EXCLAMATION)
			response = msg.ShowModal()
			
			if response == wx.ID_NO:			
				
				return
		
		# pop up file dialog 
		dlg = wx.FileDialog(self, "Choose a file", "", "", "Catalog files (*.db)|*.db") # wxFileDialog(wxWindow* parent, const wxString& message = "Choose a file", const wxString& defaultDir = "", const wxString& defaultFile = "", const wxString& wildcard = "*.*", long style = wxFD_DEFAULT_STYLE, const wxPoint& pos = wxDefaultPosition, const wxSize& sz = wxDefaultSize, const wxString& name = "filedlg")
		result = dlg.ShowModal()
		
		# exit if no file is choosen
		if result == wx.ID_CANCEL:
			
			return
		
		# load the selected file
		path = os.path.join( dlg.GetDirectory(), dlg.GetFilename() )
		self.loadCatalog(path)


	def OnSearch(self, event):
		
		self.searchCatalog()


	def OnQuit(self, event):
		
		self.quitApp()


	def OnSize(self, event):
		
		event.Skip(True) # cause the event processing system to continue searching for a handler function for this event


	def OnDoubleClick(self, event):
		
		size =  self.GetSize()
		self.mainSplitter.SetSashPosition(size.x / 2)
	

	def OnGeneric(self, event):
		
		print 'OnGeneric handler - event = ', event.GetId()


	def OnShowCategoryEditor(self, event):
		
		self.showCategoryEditor()





if __name__ == '__main__':

	app = wx.PySimpleApp()
	frame = MainFrame(None, -1, "pyCatalog")
	app.MainLoop()

