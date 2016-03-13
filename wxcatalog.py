#!/usr/bin/env python


#######################################################################
#	import section
#######################################################################

import pdb # DEBUG

import datetime
import os
import logging
import optparse
import sys
import threading
import parsers
import wx

import customwidgets as cW
import catalog
import customart



LOGFILENAME = 'pyCatalog.log'



#######################################################################
#	code section
#######################################################################


class MainFrame(wx.Frame):


	def __init__(self, parent, id, title):
		
		# parse command line arguments
		self.parseArgs()
		
		# set up log
		self.logSetup() # set up application-wide log handler
		self.log = logging.getLogger('pyCatalog.main') # set up local log
		self.log.debug("DEBUG messages turned ON.") # notify if debug messages have been turned ON
		
		# parse option file
		self.configFileName = 'config.ini' 
		self.parseOptionFile()
		
		# if linux, force use of default icon set
		##		if 'wxGTK' in wx.PlatformInfo:
		##			self.options.iconDict = None
		
		# setUp ArtProvider
		self.setupArtProvider(self.options.iconDict)
		
		# setup GUI
		wx.Frame.__init__( self, parent, wx.ID_ANY, title, size = (600,400), style = wx.DEFAULT_FRAME_STYLE )
		self.setup_GUI()
		
		# Initialize catalog variable
		self.catalog = None
		
		# Try to load last used catalog
		if (self.options.lastUsedCatalog != None):
			
			# check existence
			if ( os.path.exists( self.options.lastUsedCatalog ) ):
				
				# try to open
				try:
					
					self.loadCatalog ( self.options.lastUsedCatalog )
					
				except catalog.Error, err:
					
					pass
				
			else:
				
				self.log.warning("Not able to open last used catalog.")
		
		# starts a timer of 10 second for refreshing log viewer content
		self.timer = threading.Timer(10.0, self.logViewer.refreshLog)
		self.timer.start()			
	


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
		
		#
		# other options #
		#
		self.options.groupByCat = False


	def parseOptionFile(self):
		
		self.config = parsers.ConfigurationFileParser(self.configFileName)
		
		try: # load configuration file
			
			self.config.load()
			
		except parsers.Error, err:
			
			# we can't log error to message box because we still don't
			# have a wx.frame !
			self.log.error (err.msg)
			# for the same reason we have to quit brutally
			sys.exit(0)
		
		try: # retrieve iconset
			
			try:
				
				iconSetName = self.config.getOption('GUI', 'iconset')
				
			except parsers.Error, err:
				
				self.log.error(err.msg)
				raise Exception("There was an error while trying to fetch 'iconset' opton in section 'GUI'.")
			
			try:
				
				# create an empty dictionary
				self.options.iconDict = {}
				
				sectionName = 'iconset:' + iconSetName
				
				# populate dictionary with iconName:path couples
				for item in self.config.getItems(sectionName):
					
					self.options.iconDict[item[0]] = item[1]
				
			except parsers.Error, err:
				
				self.log.error(err.msg)
				raise Exception("There was an error while trying to fetch items in 'iconset:%s' section." % (iconSetName,) )
			
		except Exception, err:
			
			self.log.error (err.args[0])
			self.options.iconDict = None
		
		
		try: # to retrieve hideWhenMinimized option
			
			if self.config.getOption('GUI', 'hidewhenMinimized').lower() == 'true':
				self.options.hideWhenMinimized = True
			else:
				self.options.hideWhenMinimized = False
			
		except parsers.Error, err:
			
			self.log.warning(err.msg)
			self.options.hideWhenMinimized = False # this is the default value
		
		try: # to retrieve last used catalog
			
			self.options.lastUsedCatalog = os.path.normpath( self.config.getOption('lastrun', 'lastUsedCatalog') )
			
		except parsers.Error, err:
			
			self.log.error(err.msg)
			self.options.lastUsedCatalog = None

	
	def updateOptionFile(self, section, option, value):
		
		try:
			
			self.config.setOption(section, option, value)
			
		except parsers.Error, err:
			
			msg = wx.MessageDialog (self, "Error while trying to update option file.", "", wx.OK | wx.ICON_EXCLAMATION)
			msg.ShowModal()
			return			
	

	def setupArtProvider(self, iconDictionary):
		
		# create Art Provider
		self.art = wx.ArtProvider()
		
		# push custom art provider with given icons
		wx.ArtProvider.Push( customart.CustomArtProvider(iconDictionary) )


	def setup_GUI(self):
		
		# set frame icon
		icon = wx.Icon("images/logo/yellow.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon( icon )
		
		# set taskbar icon
		trayIcon = cW.TrayIcon(self, icon)
		
		try:
			self.tbicon = trayIcon
		except:
			self.tbicon = None
		
		# main container (toolbar and splitter)
		self.mainBox = wx.BoxSizer(wx.VERTICAL)
		
		# add the toolbar
		##self.toolbar = cW.CustomToolBar(self)
		
		# add the button panel
		self.buttonPanel = cW.CustomButtonPanel(self, self.art)
		self.buttonPanel.setLabel("no catalog loaded") # default message
		
		self.mainSplitter = wx.SplitterWindow(self, 1)
		
		# left panel setUp
		self.leftPanel = wx.Panel(self.mainSplitter, -1)
		self.leftSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.deviceTree = cW.DeviceTree(self.leftPanel, -1, self.art, self)
		self.leftSizer.Add(self.deviceTree, 1, wx.EXPAND)
		self.leftPanel.SetSizer(self.leftSizer)
		
		# right panel setUp
		self.rightPanel = wx.Panel(self.mainSplitter, -1)
		self.rightSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.fileTree = cW.FileTree(self.rightPanel, -1, self.art)
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
		item = self.viewMenu.AppendCheckItem(wx.NewId(), "Group by category", " Group devices by category")
		wx.EVT_MENU(self, item.GetId(), self.OnGroupByCategory)
		
		# setup 'Tools' menu
		self.toolsMenu = wx.Menu()
		self.menuItemGroup = self.toolsMenu.Append(wx.NewId(), "Show category editor", " Show category editor")
		wx.EVT_MENU(self, self.menuItemGroup.GetId(), self.OnShowCategoryEditor)
		
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
		
		# create console window to read log messages
		self.logViewer = cW.LogViewer(self, -1)
		
		# show main frame 
		self.Centre() # show window in the center of the screen		
		self.Show(True)


	def newCatalog(self):
		
		if ( self.catalog != None and self.catalog.saved == False ):
			
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
		self.catalog = catalog.Catalog( self.notifyStatusChanged )
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
		
		# create new instance of Catalog class
		self.catalog = catalog.Catalog( self.notifyStatusChanged )
		
		try: # open catalog at given path
			
			self.catalog.openCatalog( path )
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			msg = wx.MessageDialog (self, "Error while trying to load catalog.\n Look at log file for more infos.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()	
			self.catalog = None	
			return
		
		self.buttonPanel.setLabel(self.catalog.name)
		self.updateOptionFile('lastrun', 'lastUsedCatalog', self.catalog.path)
		self.loadDeviceTree()



	def addDevice(self):
		
		# CHECK: catalog is currently loaded ?
		if self.catalog == None:
			
			msg = wx.MessageDialog (self, "No catalog loaded.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return
		
		
		dlg = cW.AddDeviceDialog(
									self, 
									-1, 
									sys.argv[0],
									self.catalog
									)
		
		# If all checks were ok, then fire up device dialog
		if ( dlg.ShowModal() == wx.ID_OK ):
			
			try:
				
				self.catalog.addDevice(dlg.devName, dlg.devTypeId, dlg.devPath, dlg.categoryId)
				
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
			
			# reload catalog
			self.loadDeviceTree()


	def editDevice(self):
		
		# CHECK: catalog is currently loaded ?
		if self.catalog == None:
			
			msg = wx.MessageDialog (self, "No catalog loaded.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			return
		
		
		dlg = cW.EditDeviceDialog(
									self, 
									-1, 
									sys.argv[0],
									self.catalog
									)
		
		# If all checks were ok, then fire up device dialog
		if ( dlg.ShowModal() == wx.ID_OK ):
			
			try:
				
				pass
				
			except catalog.Error, e:
				
				self.log.error ( str(e.msg) )
				return		
			
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
		
		self.buttonPanel.setLabel(self.catalog.name)
		self.updateOptionFile('lastrun', 'lastUsedCatalog', self.catalog.path)


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
		
		self.buttonPanel.setLabel(self.catalog.name)
		self.updateOptionFile('lastrun', 'lastUsedCatalog', self.catalog.path)


	def loadDeviceTree(self):
		
		# clear file tree too
		self.fileTree.clearTree()	
		
		# disconnect device tree events
		self.deviceTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		
		# clean device tree
		self.deviceTree.clearTree()	
		
		# load category view
		if self.options.groupByCat == True:
			
			try:
				
				cats = self.catalog.getCategories()
				
			except catalog.Error, err:
				
				self.log.error (err.msg)
				return
			
			# append categories
			for cat in cats:
				
				self.deviceTree.appendToNode(self.deviceTree.root, cat)
			
			try: # retrieve uncategorized devices
				
				devs = self.catalog.getDevices(0)
				
			except catalog.Error, e:
				
				self.log.error(e.msg)
				return
			
			# append device to
			for dev in devs:
				
				self.deviceTree.appendToNode(self.deviceTree.root, dev)
			
		# load simple view
		else:
			
			try: # retrieve ALL devices
				
				devs = self.catalog.getDevices()
				
			except catalog.Error, e:
				
				self.log.error(e.msg)
				return
			
			# append device to
			for dev in devs:
				
				self.deviceTree.appendToNode(self.deviceTree.root, dev)
		
		
		# reconnect events
		self.deviceTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnDeviceListSelChanged)


	def appendToDeviceTree(self, item, idCategory):
		
		# disconnect events
		self.deviceTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		
		try: # retrieve devices with given category
			
			devs = self.catalog.getDevices(idCategory)
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			return		
		
		# append device to
		for dev in devs:
			
			self.deviceTree.appendToNode ( item, dev )
		
		# reconnect events
		self.deviceTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnDeviceListSelChanged)




	def loadFileTree(self, idDevice):
		
		# disconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		self.fileTree.Bind(wx.EVT_TREE_ITEM_EXPANDED, None)
		self.fileTree.Bind(wx.EVT_TREE_ITEM_COLLAPSED, None)
		
		# clear tree from all items
		self.fileTree.clearTree()		
		
		# append level 0 entries for current device to root item
		self.appendToFileTree(self.fileTree.root, idDevice, 0)


	def appendToFileTree(self, curItem, idDevice, idParentDir):
		
		# disconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		self.fileTree.Bind(wx.EVT_TREE_ITEM_EXPANDED, None)
		self.fileTree.Bind(wx.EVT_TREE_ITEM_COLLAPSED, None)
		
		## ADD DIRS ##
		
		try: # retrieve dirs at given level
			
			entries = self.catalog.getChildrenDirs(idDevice, idParentDir)
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			return
		
		for e in entries:
			
			self.fileTree.appendToNode( curItem, e)
		
		
		## ADD FILES ##
		
		try: # retrieve files at levelo 0
			
			entries = self.catalog.getChildrenFiles(idDevice, idParentDir)
			
		except catalog.Error, e:
			
			self.log.error(e.msg)
			return
		
		for e in entries:
			
			self.fileTree.appendToNode( curItem, e )		
		
		# reconnect events
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnFileTreeSelChanged)
		self.fileTree.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.fileTree.OnDirExpanded)
		self.fileTree.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.fileTree.OnDirCollapsed)



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
		
		dlg = cW.CategoryEditor(self, self.catalog)
		dlg.ShowModal()
		
		# reload device tree after editing categories
		self.loadDeviceTree()


	def notifyStatusChanged(self, status):
		
		if status == False:
			
			self.buttonPanel.setLabel(self.catalog.name + "*")
			
		else:
			
			self.buttonPanel.setLabel(self.catalog.name)


	def quitApp(self):
		
		if ( self.catalog != None and self.catalog.saved == False ):
			
			# request user confirmation
			msg = wx.MessageDialog (self, "Current catalog has not been saved.\nDo you really want to quit application ?", "", wx.YES_NO | wx.ICON_QUESTION)
			response = msg.ShowModal()
			
			if response == wx.ID_NO:			
				
				return
		
		# delete timer used to refresh log viewer
		self.timer.cancel()
		
		## CLEAN UP ##
		
		# disconnect events
		self.deviceTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		self.fileTree.Bind(wx.EVT_TREE_SEL_CHANGED, None)
		
		# delete tree items
		##self.deviceTree.DeleteAllItems()
		##self.fileTree.DeleteAllItems()
		
		# destroy trees
		self.deviceTree.Destroy()
		self.fileTree.Destroy()
		
		# destroy taskBar icon
		self.tbicon.Destroy()
		
		# destroy main window
		self.Destroy()


	def OnIconize(self, event):
		
		pass

	def OnGroupByCategory (self, event):
		
		# update global variable
		if event.IsChecked():
			
			self.options.groupByCat = True
			
		else:
			
			self.options.groupByCat = False
		
		# refresh device tree view (if catalog is loaded)
		if ( self.catalog != None ):
			
			self.loadDeviceTree()


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
		
		# get currently selected tree item
		curItem = self.deviceTree.GetSelection()
		
		# get data from current item
		currentDevice = self.deviceTree.GetPyData( curItem )
		
		if currentDevice.type == 'category':
			
			# append entries only if node has not been already loaded
			if not ( self.deviceTree.ItemHasChildren(curItem) ):
				
				self.appendToDeviceTree(curItem, currentDevice.id)
			
		else:
			
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
		
		if ( self.catalog != None and self.catalog.saved == False ):
			
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

