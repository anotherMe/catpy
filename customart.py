

import wx
import logging
import os.path




class CustomArtProvider (wx.ArtProvider):

	def __init__(self, iconDict):
		
		# set up local log
		self.log = logging.getLogger('pyCatalog.customart')
		
		# init
		wx.ArtProvider.__init__(self)
		
		# 
		self.iconDict = iconDict


	def CreateBitmap(self, artName, client, size):
		
		# if no custom icon set was specified, use default icon set
		if self.iconDict == None:
			
			bmp = wx.NullBitmap
			
			if artName == 'add':
				return self.GetBitmap(wx.ART_ADD_BOOKMARK, client)
			
			elif artName == 'new':
				return self.GetBitmap(wx.ART_NEW, client)
				
			elif artName == 'open':
				return self.GetBitmap(wx.ART_FILE_OPEN, client)
			
			elif artName == 'save':
				return self.GetBitmap(wx.ART_FILE_SAVE, client)
			
			elif artName == 'remove':
				return self.GetBitmap(wx.ART_DEL_BOOKMARK, client)
			
			elif artName == 'find':
				return self.GetBitmap(wx.ART_FIND, client)
			
			elif artName == 'quit':
				return self.GetBitmap(wx.ART_QUIT, client)
			
			elif artName == 'folder':
				return self.GetBitmap(wx.ART_FOLDER, client)
			
			elif artName == 'folder_open':
				#return self.GetBitmap(wx.ART_FOLDER_OPEN, client)
				return self.GetBitmap(wx.ART_FILE_OPEN, client)
			
			elif artName == 'normal_file':
				return self.GetBitmap(wx.ART_NORMAL_FILE, client)
			
			elif artName == 'floppy':
				return self.GetBitmap(wx.ART_FLOPPY, client)
			
			elif artName == 'cdrom':
				return self.GetBitmap(wx.ART_CDROM, client)
			
			elif artName == 'dvd':
				return self.GetBitmap(wx.ART_CDROM, client)
			
			elif artName == 'harddisk':
				return self.GetBitmap(wx.ART_HARDDISK, client)
			
			elif artName == 'removable':
				return self.GetBitmap(wx.ART_REMOVABLE, client)
			
			elif artName == 'category':
				return self.GetBitmap(wx.ART_HELP_BOOK, client)
			
			else:
				return self.GetBitmap(wx.ART_WARNING, client)
			
			#FIXME: queste due istruzioni vengono mai usate ??!!
			bmp = wx.BitmapFromImage(image, -1)			
			return bmp
			
			
		else:
			
			path = self.iconDict[artName]
			if os.path.exists(path) == False:
				self.log.error("Image path not recognized:")
				self.log.error(path)
			
			try:
				
				image = wx.Image(path, wx.BITMAP_TYPE_PNG)
				
			except Exception, ex:
				
				self.log.error("Error while loading image.")
				self.log.error(ex)
			
			bmp = wx.NullBitmap
			bmp = wx.BitmapFromImage(image, -1)
			
			if bmp.Ok():
				
				return bmp
				
			else:
				
				self.log.error("Bitmap creation problem with image:")
				self.log.error(path)


