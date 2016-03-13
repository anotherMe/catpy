
import wx
import wx.lib.buttonpanel as bp

import sys
import datetime
import os
import logging
import pdb

import catalog


ID_TOOLBARNEW=201
ID_TOOLBAROPEN=202
ID_TOOLBARSAVE=203
ID_TOOLBARADD=204
ID_TOOLBARDEL=205
ID_TOOLBARSEARCH=206
ID_TOOLBAREXIT=207



class TrayIcon(wx.TaskBarIcon):
	
	TBMENU_RESTORE = wx.NewId()
	TBMENU_CLOSE   = wx.NewId()
	TBMENU_CHANGE  = wx.NewId()
	TBMENU_REMOVE  = wx.NewId()

	def __init__(self, frame, icon):
		
		wx.TaskBarIcon.__init__(self)
		self.parent = frame
		
		# Set the image
		self.SetIcon(icon, "CatPy")
		self.imgidx = 1
		
		# bind some events
		self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarActivate)
		self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=self.TBMENU_RESTORE)
		self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)


	def CreatePopupMenu(self):
		"""
		This method is called by the base class when it needs to popup
		the menu for the default EVT_RIGHT_DOWN event.  Just create
		the menu how you want it and return it from this function,
		the base class takes care of the rest.
		"""
		menu = wx.Menu()
		menu.Append(self.TBMENU_RESTORE, "Restore")
		menu.Append(self.TBMENU_CLOSE,   "Quit")
		return menu


	def MakeIcon(self, img):
		"""
		The various platforms have different requirements for the
		icon size...
		"""
		
		if "wxMSW" in wx.PlatformInfo:
			img = img.Scale(16, 16)
		elif "wxGTK" in wx.PlatformInfo:
			img = img.Scale(22, 22)
		# wxMac can be any size upto 128x128, so leave the source img alone....
		icon = wx.IconFromBitmap(img.ConvertToBitmap() )
		return icon


	def OnTaskBarActivate(self, evt):
		
		if self.parent.IsIconized():
			self.parent.Iconize(False)
		if not self.parent.IsShown():
			self.parent.Show(True)
		self.parent.Raise()


	def OnTaskBarClose(self, evt):
		
		#self.parent.Close()
		self.parent.quitApp()

	def OnTaskBarChange(self, evt):
		
		names = [ "WXPdemo", "Mondrian", "Pencil", "Carrot" ]                  
		name = names[self.imgidx]

		getFunc = getattr(images, "get%sImage" % name)
		self.imgidx += 1
		if self.imgidx >= len(names):
			self.imgidx = 0
			
		icon = self.MakeIcon(getFunc())
		self.SetIcon(icon, "This is a new icon: " + name)


	def OnTaskBarRemove(self, evt):
		
		self.RemoveIcon()



class ImageBrowser (wx.Dialog):
	
	def __init__(	self, 
					parent, 
					path,
					size=(-1, -1), 
					pos=(-1,-1), 
					style=wx.CAPTION | wx.CLOSE_BOX | wx.RESIZE_BORDER
				):
		
		wx.Dialog.__init__	(	self, 
								parent, 
								wx.NewId(), 
								"Browse images", 
								size, 
								pos, 
								style
							)
		
		self.path = path
		self.setupGUI()

	
	def setupGUI(self):
		
		# main sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		# LINE : list
		
		self.list = wx.ListCtrl( self, wx.NewId(), style=wx.LC_REPORT|wx.LC_VRULES)
		
		# add columns
		self.list.InsertColumn(0, "icon")
		self.list.InsertColumn(1, "name", wx.LIST_FORMAT_RIGHT)
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
		self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
		
		self.loadImages()
		
		# add list to sizer
		sizer.Add(self.list, 1, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		# LINE 3 : buttons
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
		
		self.SetSizer(sizer)	


	def loadImages(self):
		
		art = wx.ArtProvider() # create the art provider
		self.imageList = wx.ImageList(16, 16) # create the image list
		#
		# add images to list ( index starts counting from 0 )
		self.imageList.Add(art.GetBitmap('normal_file', wx.ART_MENU))
		self.imageList.Add(art.GetBitmap('folder', wx.ART_MENU))
		#
		self.list.AssignImageList(self.imageList, wx.IMAGE_LIST_SMALL) # bind image list to control
		
		items = os.listdir(self.path)
		
		# load results on list
		for entry in items:
			
			idx = self.list.InsertImageItem(sys.maxint, 0)
			self.list.SetStringItem(idx, 1, entry)
		
		# resize colum
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)



class FileTree(wx.TreeCtrl):
	
	def __init__(self, parent, id, artProvider):
		
		# set up local log
		self.log = logging.getLogger('pyCatalog.FileTree')
		
		self.art = artProvider
		
		wx.TreeCtrl.__init__(self, parent, id, wx.DefaultPosition, (-1,-1), wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS)		
		
		# load icons
		self.loadImageList()
		
		# add root node
		self.root = self.AddRoot('root_node')

	
	def loadImageList(self):
		
		# create the art provider
		art = wx.ArtProvider()
		
		# create the image list
		self.imageList = wx.ImageList(16, 16) ## This seems to be ignored
		
		# add images to list
		self.imageList.Add(self.art.GetBitmap('folder')) # index = 0
		self.imageList.Add(self.art.GetBitmap('folder_open')) # index = 1
		self.imageList.Add(self.art.GetBitmap('normal_file')) # index = 2
		self.imageList.Add(self.art.GetBitmap('normal_file')) # index = 3
		
		# bind image list to control
		self.AssignImageList(self.imageList)


	def clearTree(self):	
		
		# clear tree
		self.DeleteAllItems()
		
		# re-add root node
		self.root = self.AddRoot('root_node')


	def appendToNode(self, node, entry):
		""" Retrieve node children and append them to given node.
			The 'entries' argument is a list of 2tuples of type (name, type).
			For a list of possible types (and associated icons), look at loadImageList() method.		
		"""
		
		
		if entry.type == 'dir':
			
			image = 0
			selImage = 0
			
		else:
			
			image = 2
			selImage = 2
		
		try:
			
			# AppendItem(const wxTreeItemId& parent, const wxString& text, int image = -1, int selImage = -1, wxTreeItemData* data = NULL)
			item = self.AppendItem ( node, entry.name, image, selImage, wx.TreeItemData(entry) )
			
		except Exception, err:
			
			self.log.error ( "Error while trying to add item %s to FileTree." % (entry.name, ) )
			self.log.error ( err )
			return


	def OnSelChanged(self, event):
		
		print event

	def OnDirExpanded(self, event):
		
		curItem = self.GetSelection()
		self.SetItemImage(curItem, 1)
	
	def OnDirCollapsed(self, event):
		
		curItem = self.GetSelection()
		self.SetItemImage(curItem, 0)



class DeviceTree(wx.TreeCtrl):
	
	
	def __init__(self, parent, id, artProvider, mainWindow):
		
		wx.TreeCtrl.__init__(self, parent, id, wx.DefaultPosition, (-1,-1), wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS)
		
		# 
		self.main = mainWindow
		
		#
		self.art = artProvider
		
		#
		self.loadImageList()
		
		# add root node
		self.root = self.AddRoot('root_node')
		
		# bind right click event
		self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)



	def clearTree(self):	
		
		# clear tree
		self.DeleteAllItems()
		
		# re-add root node
		self.root = self.AddRoot('root_node')
	


	def appendToNode(self, node, device):
		
		if device.type == "Folder":
			
			image = 1
			
		elif device.type == "Floppy":
			
			image = 2
			
		elif device.type == "CD-Rom":
			
			image = 3
			
		elif device.type == "DVD":
			
			image = 4
			
		elif device.type == "HardDisk":
			
			image = 5
			
		elif device.type == "Removable Device":
			
			image = 6
			
		elif device.type == "category":
			
			image = 7
			
		else:
			
			image = 0
		
		
		##AppendItem(const wxTreeItemId& parent, const wxString& text, int image = -1, int selImage = -1, wxTreeItemData* data = NULL)
		itemId = self.AppendItem ( node, device.name, image, image, wx.TreeItemData(device) )


	def loadImageList(self):
		
		# create the image list
		self.imageList = wx.ImageList(16, 16) ## This seems to be ignored
		
		# add images to list ( index starts counting from 0 )
		self.imageList.Add(self.art.GetBitmap('jolly', wx.ART_MENU)) #0
		self.imageList.Add(self.art.GetBitmap('folder', wx.ART_MENU)) #1
		self.imageList.Add(self.art.GetBitmap('floppy', wx.ART_MENU)) #2
		self.imageList.Add(self.art.GetBitmap('cdrom', wx.ART_MENU)) #3
		self.imageList.Add(self.art.GetBitmap('dvd', wx.ART_MENU)) #4
		self.imageList.Add(self.art.GetBitmap('harddisk', wx.ART_MENU)) #5
		self.imageList.Add(self.art.GetBitmap('removable', wx.ART_MENU)) #6
		self.imageList.Add(self.art.GetBitmap('category', wx.ART_MENU)) #7
		
		
		# bind image list to control
		self.AssignImageList(self.imageList)
	
	
	def popupMenu(self):
		
		if not hasattr(self, "popupIdEdit"):
			
			# generate new IDs
			self.popupIdEdit = wx.NewId()
			self.popupIdRemove = wx.NewId()
			
			# bind IDs to event handler
			self.Bind(wx.EVT_MENU, self.OnPopupEdit, id=self.popupIdEdit)
			self.Bind(wx.EVT_MENU, self.OnPopupRemove, id=self.popupIdRemove)
		
		# make a menu
		menu = wx.Menu()
		
		# Show how to put an icon in the menu
		item = wx.MenuItem(menu, self.popupIdEdit,"Edit")
		##bmp = images.getSmilesBitmap()
		##item.SetBitmap(bmp)
		menu.AppendItem(item)
		menu.Append(self.popupIdRemove, "Remove")
		
		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		self.PopupMenu(menu)
		menu.Destroy()

	def OnRightDown(self, event):
		
		pt = event.GetPosition();
		item, flags = self.HitTest(pt)
		
		if item:
			
			##print("OnRightClick: %s, %s, %s\n" % (self.GetItemText(item), type(item), item.__class__))
			self.SelectItem(item)
			device = self.GetPyData(item)
			
			# we don't want to remove categories
			if device.type != 'category':
				
				self.popupMenu()

	def OnPopupEdit(self, event):
		
		print("Popup edit\n")

	def OnPopupRemove(self, event):
		
		self.main.delDevice()




class CustomButtonPanel(bp.ButtonPanel):
	
	
	def __init__(self, parent, artProvider):
		
		# override default constructor
		bp.ButtonPanel.__init__(self, parent, id=wx.NewId(), style=bp.BP_USE_GRADIENT)
		
		self.art = artProvider
		
		# mess up with colors
		self.setCustomColors()
		
		# add buttons
		self.addTools(parent)
		
		# layout
		self.DoLayout()


	def addTools(self, parent):
		
		# firstly we add a spacer to push all buttons to the right
		##self.AddSpacer(proportion=1)
		
		btn = bp.ButtonInfo(self, wx.NewId(), self.art.GetBitmap('new', 
			wx.ART_TOOLBAR), shortHelp='New catalog', longHelp='Create new catalog')
		self.Bind(wx.EVT_BUTTON, parent.OnNewCatalog, id=btn.GetId())
		self.AddButton(btn)
		
		btn = bp.ButtonInfo(self, wx.NewId(), self.art.GetBitmap('open', 
			wx.ART_TOOLBAR), shortHelp='Open catalog', longHelp='Open catalog')
		self.Bind(wx.EVT_BUTTON, parent.OnOpen, id=btn.GetId())
		self.AddButton(btn)		
		
		btn = bp.ButtonInfo(self, wx.NewId(), self.art.GetBitmap('save', 
			wx.ART_TOOLBAR), shortHelp='Save catalog', longHelp='Save current catalog')
		self.Bind(wx.EVT_BUTTON, parent.OnSaveCatalog, id=btn.GetId())
		self.AddButton(btn)		
		
		btn = bp.ButtonInfo(self, wx.NewId(), self.art.GetBitmap('add', 
			wx.ART_TOOLBAR), shortHelp='Add device', longHelp='Add a new device')
		self.Bind(wx.EVT_BUTTON, parent.OnAddDevice, id=btn.GetId())
		self.AddButton(btn)
		
		btn = bp.ButtonInfo(self, wx.NewId(), self.art.GetBitmap('remove', 
			wx.ART_TOOLBAR), shortHelp='Delete device', longHelp='Delete selected device')
		self.Bind(wx.EVT_BUTTON, parent.OnDelDevice, id=btn.GetId())
		self.AddButton(btn)
		
		btn = bp.ButtonInfo(self, wx.NewId(), self.art.GetBitmap('find', 
			wx.ART_TOOLBAR), shortHelp='Find', longHelp='Find in current catalog')
		self.Bind(wx.EVT_BUTTON, parent.OnSearch, id=btn.GetId())
		self.AddButton(btn)
		
		self.AddSeparator()
		
		btn = bp.ButtonInfo(self, wx.NewId(), self.art.GetBitmap('quit', 
			wx.ART_TOOLBAR), shortHelp='Quit', longHelp='Quit application')
		self.Bind(wx.EVT_BUTTON, parent.OnQuit, id=btn.GetId())
		self.AddButton(btn)		



	def setCustomColors(self):
		
		# Sets the colours for the two demos: called only if the user didn't
		# modify the colours and sizes using the Settings Panel
		bpArt = self.GetBPArt()
		
		# set the color the text is drawn with
		bpArt.SetColor(bp.BP_TEXT_COLOR, wx.WHITE)
		
		# These default to white and whatever is set in the system
		# settings for the wx.SYS_COLOUR_ACTIVECAPTION.  We'll use
		# some specific settings to ensure a consistent look for the
		# demo.
		bpArt.SetColor(bp.BP_BORDER_COLOR, wx.Colour(120,23,224))
		bpArt.SetColor(bp.BP_GRADIENT_COLOR_FROM, wx.Colour(60,11,112))
		bpArt.SetColor(bp.BP_GRADIENT_COLOR_TO, wx.Colour(120,23,224))
		bpArt.SetColor(bp.BP_BUTTONTEXT_COLOR, wx.Colour(70,143,255))
		bpArt.SetColor(bp.BP_SEPARATOR_COLOR,
					   bp.BrightenColour(wx.Colour(60, 11, 112), 0.85))
		bpArt.SetColor(bp.BP_SELECTION_BRUSH_COLOR, wx.Color(225, 225, 255))
		bpArt.SetColor(bp.BP_SELECTION_PEN_COLOR, wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION))



	def setLabel(self, label):
		"""
			Change the title of the button bar with the given label.
		"""
		
		self.SetBarText(label)
		self.DoLayout()




## This class has been substituted by the CustomButtonPanel
class CustomToolBar(wx.ToolBar):


	def __init__(self, parent):
		
		wx.ToolBar.__init__(self, parent, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
		
		# new instance of wx.ArtProvider
		self.art = wx.ArtProvider()
		
		# add buttons
		self.refreshButtons()
		
		# bind buttons to event handlers
		self.connect(parent)



	def	refreshButtons(self):
		
		self.AddSimpleTool(ID_TOOLBARNEW, self.art.GetBitmap('new', wx.ART_TOOLBAR), 'New catalog', 'Create new catalog')
		self.AddSimpleTool(ID_TOOLBAROPEN, self.art.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR), 'Open catalog', 'Open catalog')
		self.AddSimpleTool(ID_TOOLBARSAVE, self.art.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR), 'Save catalog', 'Save current catalog')
		self.AddSimpleTool(ID_TOOLBARADD, self.art.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR), 'Add device', 'Add a new device')
		self.AddSimpleTool(ID_TOOLBARDEL, self.art.GetBitmap(wx.ART_DEL_BOOKMARK, wx.ART_TOOLBAR), 'Delete device', 'Delete selected device')
		self.AddSimpleTool(ID_TOOLBARSEARCH, self.art.GetBitmap(wx.ART_FIND, wx.ART_TOOLBAR), 'Search', 'Search in current catalog')
		self.AddSeparator()
		self.AddSimpleTool(ID_TOOLBAREXIT, self.art.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR), 'Exit', 'Quit application')
		self.Realize()


	def connect(self, parent):
		
		self.Bind(wx.EVT_TOOL, parent.OnNewCatalog, id=ID_TOOLBARNEW)
		self.Bind(wx.EVT_TOOL, parent.OnOpen, id=ID_TOOLBAROPEN)
		self.Bind(wx.EVT_TOOL, parent.OnSaveCatalog, id=ID_TOOLBARSAVE)
		self.Bind(wx.EVT_TOOL, parent.OnAddDevice, id=ID_TOOLBARADD)
		self.Bind(wx.EVT_TOOL, parent.OnDelDevice, id=ID_TOOLBARDEL)
		self.Bind(wx.EVT_TOOL, parent.OnQuit, id=ID_TOOLBAREXIT)		


class AddDeviceDialog(wx.Dialog):
	"""	User dialog to add new devices. """
	
	def __init__(	self, 
					parent, 
					ID, 
					title, 
					catalog,
					size=(-1, -1), 
					pos=(-1,-1), 
					style=wx.DEFAULT_DIALOG_STYLE
				):
		
		wx.Dialog.__init__	(	self, 
								parent, 
								ID, 
								title, 
								size, 
								pos, 
								style
							)
		
		# set up log
		self.log = logging.getLogger('pyCatalog.AddDeviceDialog') 
		
		# set up variables & get needed data
		self.catalog = catalog
		
		# set up Graphical User Interface
		self.setupGUI()
		
		self.setDeviceTypes()
		self.setCategories()
	
	def setupGUI(self):
		
		# main sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		# LINE
		label = wx.StaticText(self, -1, "Add new device")
		sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		# LINE
		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Name:")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)		
		self.txtDeviceName = wx.TextCtrl( self, -1, "", size=(180,-1))
		self.txtDeviceName.SetToolTip( wx.ToolTip("Choose a name for the device.") )
		box.Add( self.txtDeviceName, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		# LINE 
		box = wx.BoxSizer(wx.HORIZONTAL)
		
		label = wx.StaticText(self, -1, "Category:")
		label.SetHelpText("Choose category for this device (if any).")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.cmbCategory = wx.ComboBox( self, -1, "", style=wx.CB_READONLY )
		self.cmbCategory.SetToolTip( wx.ToolTip("Choose category for this device (if any).") )
		box.Add(self.cmbCategory, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		btn = wx.Button(self, wx.NewId(), "...", wx.Point(-1, -1), wx.Size(30, -1))
		btn.SetToolTip( wx.ToolTip("Edit categories") )
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)		
		self.Bind ( wx.EVT_BUTTON, self.OnEditCatBtn, id=btn.GetId() )		
		
		# LINE
		box = wx.BoxSizer(wx.HORIZONTAL)
		
		label = wx.StaticText(self, -1, "Path:")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.txtPath = wx.TextCtrl(self, -1, "", size=(180,-1))
		label.SetToolTip( wx.ToolTip("Insert here path to add") )
		box.Add(self.txtPath, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		btn = wx.Button(self, wx.NewId(), "...", wx.Point(-1, -1), wx.Size(30, -1))
		btn.SetToolTip( wx.ToolTip("Browse filesystem") )
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)		
		self.Bind ( wx.EVT_BUTTON, self.OnBrowseBtn, id=btn.GetId() )
		
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		# LINE
		box = wx.BoxSizer(wx.HORIZONTAL)
		
		label = wx.StaticText(self, -1, "Type:")
		label.SetHelpText("This is the help text for the label")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.cmbDeviceType = wx.ComboBox( self, -1, "", style = wx.CB_READONLY )
		self.cmbDeviceType.SetToolTip( wx.ToolTip("Choose type of device to add.") )
		box.Add(self.cmbDeviceType, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
		
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("The OK button completes the dialog")
		btn.SetDefault()
		btnsizer.AddButton(btn)
		self.Bind(wx.EVT_BUTTON, self.OnOkBtn, id=wx.ID_OK)
		
		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		
		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		self.SetSizer(sizer)
		sizer.Fit(self)
		
		# set focus to
		self.txtDeviceName.SetFocus()


	def setDeviceTypes (self):
		
		try: # retrieve list of device types from catalog
			
			types = self.catalog.getDeviceTypes()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to retrieve device types.")
			return		
		
		# clear combo box
		self.cmbDeviceType.Clear()
		
		# create dictionary with device index:name couples
		self.devicetypeDict = {}
		for t in types:
			
			# device name : device index
			self.devicetypeDict[t[1]] = t[0]
			
			self.cmbDeviceType.Append( t[1] )


	def setCategories (self):
		
		try: # retrieve list of categories from catalog
			
			categories = self.catalog.getCategories()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to retrieve categories.")
			return		
		
		# create dictionary with category index:name couples
		self.categoryDict = {}
		
		# clear combo box
		self.cmbCategory.Clear()
		
		# add empty element
		self.cmbCategory.Append('')
		
		for c in categories:
			
			self.cmbCategory.Append(c.name)
			
			# category name : category index
			self.categoryDict[c.name] = c.id
	


	def check(self):
		
		# CHECK selected device name
		if self.txtDeviceName.GetValue() == "":
			
			msg = wx.MessageDialog (self, "Please insert a name for the device.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()			
			self.txtDeviceName.SetFocus()
			return False
		
		# CHECK selected path
		if self.txtPath.GetValue() == "":
			
			msg = wx.MessageDialog (self, "Please review inserted path.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()			
			self.txtPath.SetFocus()
			return False
		
		# CHECK selected path
		if not(os.path.isdir(self.txtPath.GetValue()) == True and os.path.islink(self.txtPath.GetValue()) == False ):
			
			msg = wx.MessageDialog (self, "Please review inserted path.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			self.txtPath.SetFocus()
			return False
		
		# CHECK selected device type
		if self.cmbDeviceType.GetSelection() == -1:
			
			msg = wx.MessageDialog (self, "Please select a device type.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			self.cmbDeviceType.SetFocus()
			return False	
		
		return True


	def OnOkBtn(self, event):
		
		if ( self.check() ):
			
			self.devName = self.txtDeviceName.GetValue()
			self.devTypeId = int ( self.devicetypeDict[ self.cmbDeviceType.GetValue() ] )
			if self.cmbCategory.GetValue() == '':
				
				self.categoryId = None
				
			else:
				
				self.categoryId = int ( self.categoryDict[ self.cmbCategory.GetValue() ] )
			
			self.devPath = self.txtPath.GetValue()
			
			self.EndModal(wx.ID_OK)


	def OnBrowseBtn(self, event):
		
		# pop up directory dialog 
		dlg = wx.DirDialog(self, "Choose a directory", "", wx.DD_DEFAULT_STYLE | wx.DD_CHANGE_DIR ) 
		if dlg.ShowModal() == wx.ID_OK:
			
			self.txtPath.SetValue( dlg.GetPath() )
		
		dlg.Destroy()


	def OnEditCatBtn(self, event):
		
		self.Hide()
		
		# show category editor dialog
		editorDlg = CategoryEditor(self, self.catalog)
		editorDlg.ShowModal()
		
		# refresh category combobox
		self.setCategories()
		
		self.Show()




class EditDeviceDialog(wx.Dialog):
	"""	User dialog to edit existing devices. """
	
	def __init__(	self, 
					parent, 
					ID, 
					title, 
					catalog,
					size=(-1, -1), 
					pos=(-1,-1), 
					style=wx.DEFAULT_DIALOG_STYLE
				):
		
		wx.Dialog.__init__	(	self, 
								parent, 
								ID, 
								title, 
								size, 
								pos, 
								style
							)
		
		# set up log
		self.log = logging.getLogger('pyCatalog.EditDeviceDialog') 
		
		# set up variables & get needed data
		self.catalog = catalog
		
		# set up Graphical User Interface
		self.setupGUI()
		
		self.setDeviceTypes()
		self.setCategories()


	def setupGUI(self):
		
		# main sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		# LINE
		label = wx.StaticText(self, -1, "Add new device")
		sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		# LINE
		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Name:")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)		
		self.txtDeviceName = wx.TextCtrl( self, -1, "", size=(180,-1))
		self.txtDeviceName.SetToolTip( wx.ToolTip("Choose a name for the device.") )
		box.Add( self.txtDeviceName, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		# LINE 
		box = wx.BoxSizer(wx.HORIZONTAL)
		
		label = wx.StaticText(self, -1, "Category:")
		label.SetHelpText("Choose category for this device (if any).")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.cmbCategory = wx.ComboBox( self, -1, "", style=wx.CB_READONLY )
		self.cmbCategory.SetToolTip( wx.ToolTip("Choose category for this device (if any).") )
		box.Add(self.cmbCategory, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		btn = wx.Button(self, wx.NewId(), "...", wx.Point(-1, -1), wx.Size(30, -1))
		btn.SetToolTip( wx.ToolTip("Edit categories") )
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)		
		self.Bind ( wx.EVT_BUTTON, self.OnEditCatBtn, id=btn.GetId() )		
		
		# LINE
		box = wx.BoxSizer(wx.HORIZONTAL)
		
		label = wx.StaticText(self, -1, "Path:")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.txtPath = wx.TextCtrl(self, -1, "", size=(180,-1))
		label.SetToolTip( wx.ToolTip("Insert here path to add") )
		box.Add(self.txtPath, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		btn = wx.Button(self, wx.NewId(), "...", wx.Point(-1, -1), wx.Size(30, -1))
		btn.SetToolTip( wx.ToolTip("Browse filesystem") )
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)		
		self.Bind ( wx.EVT_BUTTON, self.OnBrowseBtn, id=btn.GetId() )
		
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		# LINE
		box = wx.BoxSizer(wx.HORIZONTAL)
		
		label = wx.StaticText(self, -1, "Type:")
		label.SetHelpText("This is the help text for the label")
		box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.cmbDeviceType = wx.ComboBox( self, -1, "", style = wx.CB_READONLY )
		self.cmbDeviceType.SetToolTip( wx.ToolTip("Choose type of device to add.") )
		box.Add(self.cmbDeviceType, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
		
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("The OK button completes the dialog")
		btn.SetDefault()
		btnsizer.AddButton(btn)
		self.Bind(wx.EVT_BUTTON, self.OnOkBtn, id=wx.ID_OK)
		
		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		
		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		self.SetSizer(sizer)
		sizer.Fit(self)
		
		# set focus to
		self.txtDeviceName.SetFocus()


	def setDeviceTypes (self):
		
		try: # retrieve list of device types from catalog
			
			types = self.catalog.getDeviceTypes()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to retrieve device types.")
			return		
		
		# clear combo box
		self.cmbDeviceType.Clear()
		
		# create dictionary with device index:name couples
		self.devicetypeDict = {}
		for t in types:
			
			# device name : device index
			self.devicetypeDict[t[1]] = t[0]
			
			self.cmbDeviceType.Append( t[1] )


	def setCategories (self):
		
		try: # retrieve list of categories from catalog
			
			categories = self.catalog.getCategories()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to retrieve categories.")
			return		
		
		# create dictionary with category index:name couples
		self.categoryDict = {}
		
		# clear combo box
		self.cmbCategory.Clear()
		
		# add empty element
		self.cmbCategory.Append('')
		
		for c in categories:
			
			self.cmbCategory.Append(c.name)
			
			# category name : category index
			self.categoryDict[c.name] = c.id
	


	def check(self):
		
		# CHECK selected device name
		if self.txtDeviceName.GetValue() == "":
			
			msg = wx.MessageDialog (self, "Please insert a name for the device.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()			
			self.txtDeviceName.SetFocus()
			return False
		
		# CHECK selected path
		if self.txtPath.GetValue() == "":
			
			msg = wx.MessageDialog (self, "Please review inserted path.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()			
			self.txtPath.SetFocus()
			return False
		
		# CHECK selected path
		if not(os.path.isdir(self.txtPath.GetValue()) == True and os.path.islink(self.txtPath.GetValue()) == False ):
			
			msg = wx.MessageDialog (self, "Please review inserted path.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			self.txtPath.SetFocus()
			return False
		
		# CHECK selected device type
		if self.cmbDeviceType.GetSelection() == -1:
			
			msg = wx.MessageDialog (self, "Please select a device type.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			self.cmbDeviceType.SetFocus()
			return False	
		
		return True


	def OnOkBtn(self, event):
		
		if ( self.check() ):
			
			self.devName = self.txtDeviceName.GetValue()
			self.devTypeId = int ( self.devicetypeDict[ self.cmbDeviceType.GetValue() ] )
			if self.cmbCategory.GetValue() == '':
				
				self.categoryId = None
				
			else:
				
				self.categoryId = int ( self.categoryDict[ self.cmbCategory.GetValue() ] )
			
			self.devPath = self.txtPath.GetValue()
			
			self.EndModal(wx.ID_OK)


	def OnBrowseBtn(self, event):
		
		# pop up directory dialog 
		dlg = wx.DirDialog(self, "Choose a directory", "", wx.DD_DEFAULT_STYLE | wx.DD_CHANGE_DIR ) 
		if dlg.ShowModal() == wx.ID_OK:
			
			self.txtPath.SetValue( dlg.GetPath() )
		
		dlg.Destroy()


	def OnEditCatBtn(self, event):
		
		self.Hide()
		
		# show category editor dialog
		editorDlg = CategoryEditor(self, self.catalog)
		editorDlg.ShowModal()
		
		# refresh category combobox
		self.setCategories()
		
		self.Show()




class CategoryEditor(wx.Dialog):
	"""	User dialog to insert/modify categories. """
	
	def __init__(	self, 
					parent, 
					catalog,
					size=(-1, -1), 
					pos=(-1,-1), 
					style=wx.CAPTION | wx.CLOSE_BOX | wx.RESIZE_BORDER
				):
		
		wx.Dialog.__init__	(	self, 
								parent, 
								wx.NewId(), 
								"Edit categories", 
								size, 
								pos, 
								style
							)
		
		self.catalog = catalog
		
		self.curItemIdx = None
		
		# main sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.list = wx.ListCtrl( self, wx.NewId(), style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
		#
		# add columns
		self.list.InsertColumn(0, "id")
		self.list.InsertColumn(1, "category")
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)		
		self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		# add list to sizer
		sizer.Add(self.list, 1, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		# LINE 3 : buttons
		btnsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		btn = wx.Button(self, wx.ID_ADD)
		btn.SetToolTip( wx.ToolTip("Add new category.") )
		btnsizer.Add(btn, 0, wx.ALIGN_LEFT)
		btn.Bind(wx.EVT_BUTTON, self.OnBtnAdd, id=btn.GetId())
		
		btn = wx.Button(self, wx.ID_REMOVE)
		btn.SetToolTip( wx.ToolTip("Remove selected category.") )
		btnsizer.Add(btn, 0, wx.ALIGN_LEFT)
		btn.Bind(wx.EVT_BUTTON, self.OnBtnRemove, id=btn.GetId())
		
		#btn = wx.Button(self, wx.NewId(), "Edit")
		#btn.SetToolTip( wx.ToolTip("Edit selected category.") )
		#btnsizer.Add(btn, 0, wx.ALIGN_LEFT)
		#btn.Bind(wx.EVT_BUTTON, self.OnBtnEdit, id=btn.GetId())
		
		## TODO: this spacer does not work
		btnsizer.AddStretchSpacer(1)
		
		btn = wx.Button( self, wx.NewId(), 'Close' )
		btn.SetToolTip( wx.ToolTip("Close category editor.") )
		btn.Bind(wx.EVT_BUTTON, self.OnQuit, id=btn.GetId())
		btnsizer.Add(btn, 0, wx.ALIGN_RIGHT)
		
		sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT, 5)
		
		self.SetSizer(sizer)
		
		self.populateList()



	def populateList(self):
		
		self.list.DeleteAllItems()
		
		try:
			
			data = self.catalog.getCategories()
			
		except CatalogError, err:
			
			msg = wx.MessageDialog (self, "There was an error while trying to retrieve categories from catalog.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
			return
		
		# dis-connect events
		self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, None)
		
		for cat in data:
			
			idx = self.list.InsertStringItem(sys.maxint, unicode(cat.id), 0)
			self.list.SetStringItem(idx, 1, unicode(cat.name))
		
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		
		# connect event
		self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
		self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)


	def addCategory(self):
		
		dlg = wx.TextEntryDialog(self, "Insert category name", "Insert category pippo")
		dlg.ShowModal()
		
		value = unicode ( dlg.GetValue() )
		if  value != "":
			
			try:
				
				self.catalog.addCategory(value)
				
			except catalog.CatalogError, err:
				
				msg = wx.MessageDialog (self, "There was an error while adding new category.", "", wx.OK | wx.ICON_ERROR)
				msg.ShowModal()
				return
		
		self.populateList()
		
		# NOTE: At this poin catalog has been MODIFIED.


	def removeCategory(self):
		
		col = 0 # ID colum
		item = self.list.GetItem(self.curItemIdx, col)
		id = item.GetText()
		
		col = 1 # name colum
		item = self.list.GetItem(self.curItemIdx, col)
		name = item.GetText()		
		
		# request user confirmation
		msg = "Do you really want to delete %s category ?" % (name)
		msgDlg = wx.MessageDialog (self, msg, "", wx.YES_NO | wx.ICON_QUESTION)
		response = msgDlg.ShowModal()
		
		if response == wx.ID_NO:			
			
			return
		
		try: # to remove given category
			
			self.catalog.removeCategory(id)
			
		except catalog.CatalogError, err:
			
			msg = wx.MessageDialog (self, "There was an error while trying to remove given category.\nLook at log file for more info.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
		
		self.populateList()


	def editCategory(self):
		
		dlg = ImageBrowser(self, "images/silk")
		dlg.ShowModal()


	def OnBtnAdd(self, event):
		
		self.addCategory()

	def OnBtnRemove(self, event):
		
		if self.curItemIdx != None:
			
			self.removeCategory()
			
		else:
			
			msg = wx.MessageDialog (self, "You must select a category first.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()

	def OnBtnEdit(self, event):
		
		self.editCategory()

	def OnItemSelected(self, event):
		
		self.curItemIdx = event.m_itemIndex

	def OnItemDeselected(self, event):
		
		self.curItemIdx = None

	def OnQuit(self, event):
		
		self.Destroy()


class SearchDialog(wx.Dialog):
	"""	User dialog to search for strings in files stored in
		current catalog. """
	
	def __init__(	self, 
					parent, 
					ID, 
					catalog,
					title="Find in catalog", 
					size=(-1, -1), 
					pos=(-1,-1), 
					style=wx.CAPTION | wx.CLOSE_BOX | wx.RESIZE_BORDER
				):
		
		wx.Dialog.__init__	(	self, 
								parent, 
								ID, 
								title, 
								size, 
								pos, 
								style
							)
		
		self.catalog = catalog
		
		# main sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		# LINE 1 : text box
		upperSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.txtBox = wx.TextCtrl( self, -1, "", size=(-1,-1))
		self.txtBox.SetToolTip( wx.ToolTip("Insert a comma separated list of strings to search for.") )
		upperSizer.Add(self.txtBox, 1, wx.GROW|wx.ALL, 5)
		
		searchBtn = wx.Button(self, wx.ID_FIND)
		searchBtn.SetToolTip(wx.ToolTip('Search'))
		self.Bind(wx.EVT_BUTTON, self.OnSearch, id=searchBtn.GetId())
		upperSizer.Add(searchBtn, 0, wx.ALIGN_RIGHT, 5)
		
		sizer.Add(upperSizer, 0, wx.GROW|wx.ALL, 5)
		
		# LINE 2 : list
		
		self.list = wx.ListCtrl( self, wx.NewId(), style=wx.LC_REPORT|wx.LC_VRULES)
		
		# add columns
		self.list.InsertColumn(0, "name")
		self.list.InsertColumn(1, "device", wx.LIST_FORMAT_RIGHT)
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
		self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
		
		art = wx.ArtProvider() # create the art provider
		self.imageList = wx.ImageList(16, 16) # create the image list
		#
		# add images to list ( index starts counting from 0 )
		self.imageList.Add(art.GetBitmap('normal_file', wx.ART_MENU))
		self.imageList.Add(art.GetBitmap('folder', wx.ART_MENU))
		#
		self.list.AssignImageList(self.imageList, wx.IMAGE_LIST_SMALL) # bind image list to control
		
		# add list to sizer
		sizer.Add(self.list, 1, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		# LINE 3 : buttons
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
		
		self.SetSizer(sizer)
		
		# set focus to
		self.txtBox.SetFocus()


	def search(self):
		
		txt = self.txtBox.GetValue() # returned text is Unicode
		
		# CHECK if user inserted a valid string
		if not ( self.checkString(txt) ):
			
			msg = wx.MessageDialog (self, "Please insert a valid search string.", "", wx.OK | wx.ICON_INFORMATION)
			msg.ShowModal()
			self.txtBox.SetFocus()
			return
		
		# empty list
		self.list.DeleteAllItems()
		
		# split user input in a string tuple
		stringList = txt.split(";")
		
		
		try: # try to search dirs in catalog for given strings
			
			resultSet = self.catalog.searchForDirs(stringList)
			
		except catalog.Error, err:
			
			msg = wx.MessageDialog (self, "There was an error while searching current catalog.\nLook at error log for more infos.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
			return
		
		self.loadList(resultSet)
		
		try: # try to search files in catalog for given strings
			
			resultSet = self.catalog.searchForFiles(stringList)
			
		except catalog.Error, err:
			
			msg = wx.MessageDialog (self, "There was an error while searching current catalog.\nLook at error log for more infos.", "", wx.OK | wx.ICON_ERROR)
			msg.ShowModal()
			return
		
		self.loadList(resultSet)


	def loadList(self, items):
		
		# load results on list
		for entry in items:
			
			# choose proper image for item
			if entry.type == 'dir':
				
				idx = self.list.InsertImageStringItem(sys.maxint, entry.name, 1)
				
			else:
				
				idx = self.list.InsertImageStringItem(sys.maxint, entry.name, 0)
			
			self.list.SetStringItem(idx, 1, entry.devName)
		
		# resize colum
		self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)


	def checkString(self, string):
		
		# CHECK if text box is empty
		if string == "":
			
			return False
		
		# CHECK if there are only whitespaces
		if string.isspace():
			
			return False
		
		return True


	def OnSearch(self, event):
		
		self.search()


	def OnGeneric(self, event):
		
		print event


	def OnClose(self, event):
		
		self.Destroy()






class LogViewer(wx.Frame):


	def __init__(self, parent, id):
		
		self.setupGUI(parent, id)
		self.refreshLog()

	

	def setupGUI(self, parent, id):
	
		wx.Frame.__init__(self, parent, id, 'Log viewer', style=wx.CAPTION | wx.CLOSE_BOX | wx.RESIZE_BORDER)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		upperSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.textBox = wx.TextCtrl(self, -1, '', wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
		upperSizer.Add(self.textBox, 1, wx.EXPAND)
		
		lowerSizer = wx.BoxSizer(wx.HORIZONTAL)
		refreshBtn = wx.Button(self, wx.ID_REFRESH)
		refreshBtn.Bind(wx.EVT_BUTTON, self.OnRefreshBtn, id=wx.ID_REFRESH)
		closeBtn = wx.Button(self, wx.ID_CLOSE)
		closeBtn.Bind(wx.EVT_BUTTON, self.OnExit, id=wx.ID_CLOSE)
		lowerSizer.AddStretchSpacer()
		lowerSizer.Add(refreshBtn, 0)
		lowerSizer.Add(closeBtn, 0)
		
		mainSizer.Add(upperSizer, 1, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		mainSizer.Add(lowerSizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		self.SetSizer(mainSizer)
		
		self.Bind(wx.EVT_CLOSE, self.OnExit)



	def refreshLog(self):
		
		#clear textbox
		self.textBox.Clear()
		
		try: # to open log file
			
			logFile = open("pyCatalog.log", 'r')
			
		except Exception, e:
			
			d = wx.MessageDialog( self, " Error while trying to open log file.", wx.OK | wx.ICON_ERROR)
			d.ShowModal()
			return
		
		# scan log file and append lines to text box
		for line in logFile:
			
			try:
				
				self.textBox.AppendText(line)
				
			except UnicodeError, ue:
				
				self.textBox.AppendText("ERROR while parsing log file, try to open it in you favourite text viewer.\n")
		
		logFile.close()
	

	def OnRefreshBtn(self, event):
		
		self.refreshLog()
	

	def OnExit(self, event):
		
		self.Hide()

