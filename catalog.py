#!/usr/bin/env python

import logging
import sqlitetoolkit
import os
import sys
import shutil

import mimetypes

BATCHFILENAME = 'schema.sql'



class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class GenericError(Error):
	
	def __init__(self, message):
		
		self.msg = message	


class CatalogError(Error):
	
	def __init__(self, message):
		
		self.msg = message
		## Temporary disabled
		##self.log = logging.getLogger('pyCatalog.catalogError')
		##self.log.error ( message )


class FileError(Error):
	
	def __init__(self, message):
		
		self.msg = message


class DeviceItem():
	"""	Generic container to make more readable the values associated 
		with every device.
		
		This class is also used to store instance of category objects:
		categories are considered as special kind of device.
		
		NOTE: 'type' must be one of the string values provided in the 
		DAT_DeviceTypes table.
	"""
	
	def __init__(self, id, name, type, idCategory=None, category=None):
		
		self.id = id
		self.name = name
		self.type = type
		self.idCategory = idCategory
		self.category = category


class EntryItem():
	"""	Generic container to make more readable the values associated 
		with every dirs and files.
		
		NOTE: 'type' must be one of the two values: 'dir' / 'file'
	"""	
	
	def __init__(self, id, name, idParentDir, devId, devName, type, bits=0, userId=0, groupId=0, size=0, aTime=0, mTime=0, mime=''):
		
		assert type in ('dir', 'file')
		
		# we assume directories have no size
		if type == 'dir': size = 0
		
		self.id = id
		self.name = name
		self.idParentDir = idParentDir
		self.devId = devId
		self.devName = devName
		self.type = type
		self.bits = bits
		self.userId = userId
		self.groupId = groupId
		self.size = size
		self.aTime = aTime
		self.mTime = mTime
		self.mime = mime


class Catalog:

	
	def __init__(self, callback):
		
		# set up local log
		self.log = logging.getLogger('pyCatalog.catalog')
		
		# callback function to notify catalog changes
		self.callback = callback


	def setStatus (self, status):
		"""
			Notify if catalog has been modified.
		"""
		
		assert status in (False, True)
		
		# set new status
		self.saved = status
		
		# notify status change 
		self.callback(status)


	def openCatalog( self, path ):
		
		# TEST if path is not empty
		if path == "":
			
			self.log.warning("No valid catalog name provided:")
			self.log.warning(path)
			raise FileError ("No valid catalog name provided:")
		
		# TEST if catalog file exists
		if not( self.checkExistence(path) ):
			
			self.log.warning('Given file doesn\'t exist.')
			raise FileError ('Given file doesn\'t exist.')
		
		# TEST if given file is a valid catalog
		if not (self.checkDb(path)):
			
			self.log.warning('Given file doesn\'t seem to be a valid catalog.')
			raise CatalogError("Given file doesn\'t seem to be a valid catalog.")
		
		# set path to current catalog
		self.path = path
		
		# set name of current catalog
		self.name = os.path.split(path)[1]
		
		
		# set path to working copy of current catalog
		self.workPath = path + "~"
		
		try: # make a work copy of catalog
			
			shutil.copy2(path, self.workPath)
			
		except Exception, e:
			
			self.log.error ("Error while trying to make work copy of catalog")
			raise FileError ("Error while trying to make work copy of catalog")
		
		# open SQLite connection to work copy
		self.db = sqlitetoolkit.liteDB(self.workPath)
		self.log.info('Catalog ' + path +' is open.')
		
		self.setStatus (True)



	def checkExistence(self, path):
		""" Check if given path leads to catalog """
		
		# test if file exists
		if not ( os.path.exists(path) ):
			
			return False
			
		else:
			
			return True


	def checkDb(self, path):
		""" Test if given file is a catalog """
		
		testDb = sqlitetoolkit.liteDB(path)
		
		try:
			
			testDb.execStmt("select id, name, idDeviceType, idCategory from DAT_Devices limit 1;")
			
		except sqlitetoolkit.ExecutionError, e:
			
			# Problems while executing statement, file is not recognized as a catalog
			self.log.warning ("CHECK 1 - Given file is not recognized as a valid catalog.")
			return False
		
		try:
			
			testDb.execStmt("select id, idDevice, idParentDir, name, bits, userId, groupId, size, aTime, mTime, mime from DAT_Files limit 1;")
			
		except sqlitetoolkit.ExecutionError, e:
			
			# Problems while executing statement, file is not recognized as a catalog
			self.log.warning ("CHECK 2 - Given file is not recognized as a valid catalog.")
			return False
		
		try:
			
			testDb.execStmt("select id , idDevice , idParentDir , name , bits , userId , groupId , aTime , mTime from DAT_Dirs limit 1;")
			
		except sqlitetoolkit.ExecutionError, e:
			
			# Problems while executing statement, file is not recognized as a catalog
			self.log.warning ("CHECK 3 - Given file is not recognized as a valid catalog.")
			return False
		
		try:
			
			testDb.execStmt("select id, name from DAT_Categories limit 1;")
			
		except sqlitetoolkit.ExecutionError, e:
			
			# Problems while executing statement, file is not recognized as a catalog
			self.log.warning ("CHECK 4 - Given file is not recognized as a valid catalog.")
			return False
		
		testDb.closeConnection()
		return True

	
	def getDeviceTypes (self):
		""" Retrieve device types"""
		
		stmt = "select id, name from DAT_DeviceTypes;"
		
		try:
			
			data = self.db.execStmt(stmt)
			
		except sqlitetoolkit.Error, e:
			
			self.log.error ("Error while trying to retrieve device types.")
			raise CatalogError ("Error while trying to retrieve device types.")
		
		return data


	def getCategories (self):
		""" Retrieve categories """
		
		stmt = "select id, name from DAT_Categories;"
		
		try:
			
			data = self.db.execStmt(stmt)
			
		except sqlitetoolkit.Error, e:
			
			self.log.error ("Error while trying to retrieve categories.")
			raise CatalogError ("Error while trying to retrieve categories.")
		
		cats = []
		for d in data:
			
			## DeviceItem (id, name, type, idCategory=None, category=None)
			cats.append( DeviceItem( d[0], d[1], 'category' ) )
		
		return cats


	def createNew(self, fileName):
		""" Create empty database """
		
		# test if batch file exists
		if not( os.path.exists (BATCHFILENAME) ):
			
			self.log.error('IO error detected while trying to open database creation script.')
			raise FileError( 'IO error detected while trying to open database creation script.' )
		
		
		# before creating new DB we must delete eventual preexistent catalog
		if os.path.exists( fileName ):
			
			self.log.warning ('A file with the same name already exists.')
			raise FileError ('A file with the same name already exists.')
		
		# create new DB
		tmpDb = sqlitetoolkit.liteDB(fileName)
		
		try: # open SQL batch file
			
			file = open(BATCHFILENAME, 'r')
			
		except FileExceptionError, e:
			
			self.log.error ("Error while trying to open batch file.")
			raise FileError ("Error while trying to open batch file.")
		
		for line in file:
			
			try:
				
				tmpDb.execStmt(line)
				
			except sqlitetoolkit.ExecutionError, e:
				
				file.close()
				raise CatalogError("Error while parsing SQL batch file.")
		
		# close SQL batch file
		file.close()
		
		# close SQLite catalog
		tmpDb.closeConnection()



	def searchForFiles(self, stringList):
		""" Search files for given strings. 
		
			Returned values:
			
				- file name
				- device name
		"""
		
		# check that string list is not empty
		if len(stringList) == 0:
			
			self.log.warning ("String list is empty.")
			raise GenericError("String list is empty.")
		
		searchString = "DAT_Files.name like '%" + stringList[0] + "%'"
		if len(stringList) > 1:
			
			idx = 1
			while idx < len(stringList):
				
				searchString += " and DAT_Files.name like '%" + stringList[idx] + "%'"
				idx += 1
		
		searchString += ";"
		
		stmt = """
				select 
							  DAT_Files.id
							, DAT_Files.name as name
							, DAT_Files.idParentDir
							, DAT_Devices.id as devId
							, DAT_Devices.name as devName
							, DAT_Files.bits 
							, DAT_Files.userId
							, DAT_Files.groupId 
							, DAT_Files.aTime 
							, DAT_Files.mTime
				from 
							DAT_Devices
				inner join 
							DAT_Files on DAT_Files.idDevice = DAT_Devices.id
				where  
						""" + searchString
		
		
		try:
			
			data = self.db.execStmt(stmt)
			
		except sqlitetoolkit.Error, e:
			
			raise CatalogError ("Error while trying to execute search statement.")
		
		files = []
		for d in data:
			
			files.append( EntryItem( id=d[0], name=d[1], idParentDir=d[2], devId=d[3], devName=d[4], type='file', bits=d[5], userId=d[6], groupId=d[7], aTime=d[8], mTime=d[9] ) )
		
		return files



	def searchForDirs(self, stringList):
		""" Search directories for given strings. 
			
			Returned values:
				
				A list of entryItems.
		
		"""
		
		# check that string list is not empty
		if len(stringList) == 0:
			
			self.log.warning ("String list is empty.")
			raise GenericError("String list is empty.")
		
		searchString = "DAT_Dirs.name like '%" + stringList[0] + "%'"
		if len(stringList) > 1:
			
			idx = 1
			while idx < len(stringList):
				
				searchString += " and DAT_Dirs.name like '%" + stringList[idx] + "%'"
				idx += 1
		
		searchString += ";"
		
		stmt = """
				select 
							  DAT_Dirs.id
							, DAT_Dirs.name as name
							, DAT_Dirs.idParentDir
							, DAT_Devices.id as devId
							, DAT_Devices.name as devName
							, DAT_Dirs.bits 
							, DAT_Dirs.userId
							, DAT_Dirs.groupId 
							, DAT_Dirs.aTime 
							, DAT_Dirs.mTime
				from 
							DAT_Devices
				inner join 
							DAT_Dirs on DAT_Dirs.idDevice = DAT_Devices.id
				where  
						""" + searchString
		
		
		try:
			
			data = self.db.execStmt(stmt)
			
		except sqlitetoolkit.Error, e:
			
			raise CatalogError ("Error while trying to execute search statement.")
		
		dirs = []
		for d in data:
			
			dirs.append( EntryItem( id=d[0], name=d[1], idParentDir=d[2], devId=d[3], devName=d[4], type='dir', bits=d[5], userId=d[6], groupId=d[7], aTime=d[8], mTime=d[9] ) )
		
		return dirs


	def addCategory(self, name):
		
		try: # insert new device
			
			self.db.execStmt( "insert into DAT_Categories (name) values (?);", (name,) )
			
		except Exception, e:
			
			self.log.error ("Error while inserting new category.")
			raise CatalogError("Error while inserting new category.")
		
		self.setStatus(False)


	def addDevice(self, name, type, path, idCategory = None):
		""" Store SQL statements in file and then read from it."""
		
		# CHECK if given path exists
		if not ( os.path.exists(path) ):
			
			self.log.warning("Given path does not exists.")
			raise FileError("Given path does not exists.")
		
		# CHECK if user has read permission on given path
		if not ( os.access(path, os.R_OK) ):
			
			self.log.warning("Cannot read from specified path.")
			raise FileError("Cannot read from specified path.")
		
		# WORKAROUND: if user passes 'F:' instead of F:\
		drive = os.path.splitdrive(path)[0]
		tail = os.path.splitdrive(path)[1]
		if drive != "" and tail == "":
			
			path = drive + "\\"
		
		if idCategory == None:
			
			try: # insert new device
				
				self.db.execStmt( "insert into DAT_Devices (name, idDeviceType) values (?, ?);", (name, type) )
				
			except Exception, e:
				
				self.log.error ("Error while inserting new device.")
				raise CatalogError("Error while inserting new device.")
			
		else:
			
			try: # insert new device
				
				self.db.execStmt( "insert into DAT_Devices (name, idDeviceType, idCategory) values (?, ?, ?);", (name, type, idCategory) )
				
			except Exception, e:
				
				self.log.error ("Error while inserting new device.")
				raise CatalogError("Error while inserting new device.")
		
		
		try: # retrieve id of inserted device
			
			curDevIdList = self.db.execStmt("select max(id) from DAT_Devices;")
			
		except sqlitetoolkit.Error, e:
			
			self.log.error ( e.msg )
			raise CatalogError("Error while retrieving current device ID.")
		
		
		# set globally ID of current device
		self.currentDeviceId = curDevIdList[0][0]		
		
		# set global counter for UnicodeDecodeErrors
		self.unicodeErrors = 0		
		
		# set global counter for parsed files
		self.fileCounter = 0
		
		# set global counter for parsed dirs
		self.dirCounter = 0
		
		# create the iterator we are going to fill up with files
		self.fileIterator = sqlitetoolkit.liteIterator() 
		
		# create the iterator we are going to fill up with directories
		self.dirIterator = sqlitetoolkit.liteIterator() 
		
		# start parsing filesystem tree (will add entries to above iterators)
		self.log.info ( "Parsing path :: " + path)
		
		self.parseDir(path, 0)
		
		
		# insert files into device table (using the above iterator)
		try:
			
			self.db.execMany("insert into DAT_Dirs (id, idDevice, idParentDir, name, bits, userId, groupId, aTime, mTime) values (?, ?, ?, ?, ?, ?, ?, ?, ?);", self.dirIterator)
			
		except sqlitetoolkit.Error, e:
			
			self.log.error("Error in parseDir() method, while trying to add files to catalog.")
			raise CatalogError(stmt, e.args[0])
			return		
		
		
		# insert files into device table (using the above iterator)
		try:
			
			self.db.execMany("insert into DAT_Files (idDevice, idParentDir, name, bits, userId, groupId, size, atime, mtime, mime) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", self.fileIterator)
			
		except sqlitetoolkit.Error, e:
			
			self.log.error("Error in parseDir() method, while trying to add files to catalog.")
			raise CatalogError(stmt, e.args[0])
			return		
		
		# Catalog has been modified
		self.setStatus (False)
		
		self.log.info( "Parsed %d files." % (self.fileCounter, ) )
		return self.fileCounter



	def parseDir(self, path, parentDirId):
		
		# CHECK read permission of given path
		if not ( os.access(path, os.R_OK) ):
			
			self.log.warning ("Cannot read from specified path.")
			self.log.warning (path)
			return
		
		try: # retrieve entries in given path
			
			entries = os.listdir( path )
			
		except WindowsError, ex:
			
			self.log.error("Catched WindowsError while trying to parse dir:")
			self.log.error(path)
			return
			
		except Exception, ex:
			
			self.log.error("Catched generic Exception while trying to parse dir:")
			self.log.error(path)
			return			
		
		# loop through entries in given path
		for e in entries:
			
			try: # to join given path to current entry
				
				curPath = os.path.join(path, e)
				
			except UnicodeError, ex:
				
				self.unicodeErrors += 1
				self.log.error ( "Unicode error while trying to join path, skipping entry: " )
				self.log.error ( e )
				continue
				
			except Exception, ex:
				
				self.log.error ( "Generic error while trying to join path, skipping entry: %s" % (e, ) )
				self.log.warning ( "Error was: %s" % (ex,) )
				continue
			
			
			# CHECK that current entry is not a link
			if os.path.islink( curPath ) == True:
				
				self.log.warning("Specified path is a link.")
				continue
			
			# CHECK if current entry is a directory
			if os.path.isdir( curPath ) == True:			
				
				self.dirCounter += 1
				
				# retrieve file stat (see below for more info):
				stat = os.lstat ( curPath )
				
				# add new triple to directory iterator
				self.dirIterator.addItem ( ( 
								self.dirCounter, # id integer
								self.currentDeviceId, # idDevice integer
								parentDirId, # idParentDir integer
								e, # name text
								stat[0], # bits integer
								stat[4], # userId integer
								stat[5], # groupId integer
								stat[7], # aTime real
								stat[8] # mTime real
							) )	
				
				# self 
				self.parseDir( curPath, self.dirCounter)
				
			# CHECK if entry is a file
			elif os.path.isfile( curPath ) == True:
				
				# increase file counter
				self.fileCounter += 1
				
				# retrieve file stats:
				#
				# 0. st_mode (protection bits)
				# 1. st_ino (inode number)
				# 2. st_dev (device)
				# 3. st_nlink (number of hard links)
				# 4. st_uid (user ID of owner)
				# 5. st_gid (group ID of owner)
				# 6. st_size (size of file, in bytes)
				# 7. st_atime (time of most recent access)
				# 8. st_mtime (time of most recent content modification)
				# 9. st_ctime (platform dependent; time of most recent metadata change on Unix, or the time of creation on Windows)				
				
				stat = os.lstat ( curPath )
				
				# guess MIME type
				mime = mimetypes.guess_type(curPath, strict=True)[0]
				
				# add new triple to iterator
				self.fileIterator.addItem ( ( 
								self.currentDeviceId, # idDevice integer
								parentDirId, # idParentDir integer
								e, # name text
								stat[0], # bits integer
								stat[4], # userId integer 
								stat[5], # groupId integer
								stat[6], # size integer
								stat[7], # aTime real
								stat[8], # mTime real
								mime
							) )
				
			else:
				
				self.log.warning ("File not recognized:")
				self.log.warning ("PATH: " + path)
				self.log.warning ("FILE: " + e)



	def removeCategory (self, id):
		""" Remove category with given ID.
		
			NOTE: id argument is a string.
		"""
		
		try: # reset devices related to give category
			
			self.db.execStmt( "update DAT_Devices set idCategory = NULL where idCategory = ?;", (id,) )
			
		except sqlitetoolkit.Error, e:
			
			self.log.error( "Error while updating devices with category id = %s" % (id) )
			raise CatalogError ( "Error while updating devices." )
		
		self.log.info ( "Devices correctly updated." )		
		
		try: # remove selected category
			
			self.db.execStmt( "delete from DAT_Categories where id = ?;", (id,) )
			
		except sqlitetoolkit.Error, e:
			
			self.log.error( "Error while deleting category with id = %s" % (id) )
			raise CatalogError ( "Error while removing category." )
		
		self.log.info( "Category with id = %s, correctly deleted." % (id) )
		
		self.setStatus(False)



	def removeDevice(self, id):
		
		try: # delete files related to given device
			
			self.db.execStmt( "delete from DAT_Files where idDevice = ?;", (id,) )
			
		except sqlitetoolkit.Error, e:
			
			self.log.error( "Error while deleting files for idDevice = %d" % (id) )
			raise CatalogError ( "Error while deleting files." )
		
		self.log.info( "Files related with device number %d correctly deleted." % (id) )
		
		try: # delete dirs related to given device
			
			self.db.execStmt( "delete from DAT_Dirs where idDevice = ?;", (id,) )
			
		except sqlitetoolkit.Error, e:
			
			self.log.error( "Error while deleting dirs for idDevice = %d" % (id) )
			raise CatalogError ( "Error while deleting dirs." )
		
		self.log.info( "Dirs related with device number %d correctly deleted." % (id) )		
		
		try: # delete device
			
			self.db.execStmt( "delete from DAT_Devices where id = ?", (id,) )
			
		except sqlitetoolkit.Error, e:
			
			self.log.error( "Error while deleting device with id = %d" % (id) )
			raise CatalogError ( "Error while deleting device." )
		
		# Catalog has been modified
		self.setStatus (False)
		
		self.log.info( "Device with id %d correctly removed." % (id) )



	def getDevices (self, idCategory=None):
		"""
			Retrieve devices from catalog:
			
			if (idCategory = None) then retrieve all devices in catalog;
			if (idCategory = 0) then retrieve only devices that have no category;
			if (idCategory > 0) then retrieve all devices in given category.
		"""
		
		# retrieve ALL devices
		if idCategory == None:
			
			stmt = 	"""	select 
								DAT_Devices.id, 
								DAT_Devices.name as deviceName, 
								DAT_DeviceTypes.name as typeName,
								DAT_Categories.id,
								DAT_Categories.name
						from 
								DAT_Devices 
								
						inner join 
								DAT_DeviceTypes on DAT_Devices.idDeviceType = DAT_DeviceTypes.id
								
						left join
								DAT_Categories on DAT_Categories.id = DAT_Devices.idCategory
								
						order by 
								DAT_Devices.name; 
					"""
			
			try:
				
				devs = self.db.execStmt ( stmt )
				
			except sqlitetoolkit.Error, err:
				
				self.log.error ("Error while retrieving devices from catalog.")
				self.log.error (err)
				raise CatalogError ("Error while retrieving devices from catalog.")			
			
		elif idCategory == 0:
			
			stmt = 	"""	select 
								DAT_Devices.id, 
								DAT_Devices.name as deviceName, 
								DAT_DeviceTypes.name as typeName,
								DAT_Categories.id,
								DAT_Categories.name
						from 
								DAT_Devices 

						inner join 
								DAT_DeviceTypes on DAT_Devices.idDeviceType = DAT_DeviceTypes.id
								
						left join
								DAT_Categories on DAT_Categories.id = DAT_Devices.idCategory
								
						where 
								idCategory is null
						order by 
								DAT_Devices.name; 
					"""
			
			try:
				
				devs = self.db.execStmt ( stmt )
				
			except sqlitetoolkit.Error, err:
				
				self.log.error ("Error while retrieving devices from catalog.")
				self.log.error (err)
				raise CatalogError ("Error while retrieving devices from catalog.")						
			
		else: # retrieve only devices in given category
			
			stmt = 	"""	select 
								DAT_Devices.id, 
								DAT_Devices.name as deviceName, 
								DAT_DeviceTypes.name as typeName,
								DAT_Categories.id,
								DAT_Categories.name
						from 
								DAT_Devices 
								
						inner join 
								DAT_DeviceTypes on DAT_Devices.idDeviceType = DAT_DeviceTypes.id
								
						left join
								DAT_Categories on DAT_Categories.id = DAT_Devices.idCategory
								
						where 
								idCategory = ?
								
						order by 
								DAT_Devices.name; 
					"""
			
			try:
				
				devs = self.db.execStmt ( stmt, (idCategory,) )
				
			except sqlitetoolkit.Error, err:
				
				self.log.error ("Error while retrieving devices from catalog.")
				self.log.error (err)
				raise CatalogError ("Error while retrieving devices from catalog.")
		
		# create a list of devices
		devices = []
		for dev in devs:
			
			# DeviceItem( id, name, type )
			devices.append( DeviceItem ( dev[0], dev[1], dev[2] ) )
		
		return devices


	## wxCatalog
	def getChildrenDirs(self, idDevice, parentId):
		"""	Returns children dirs of given node in given device.
		"""
		
		stmt = """	select 
							DAT_Dirs.id, 
							DAT_Dirs.name,
							DAT_Dirs.idParentDir,
							DAT_Devices.id,
							DAT_Devices.name
					from 
							DAT_Dirs 
					inner join
							DAT_Devices on DAT_Devices.id = DAT_Dirs.idDevice
					where 
							DAT_Devices.id = ?
						and DAT_Dirs.idParentDir = ?
					order by
						DAT_Dirs.name; """
		
		try: 
			
			dirChildren = self.db.execStmt ( stmt, (idDevice, parentId) )
			
		except sqlitetoolkit.ExecutionError, e:
			
			self.log.error("Execution error while trying to retrieve dir children.")
			raise CatalogError("Execution error while trying to retrieve dir children.")
			
		except sqlitetoolkit.Error, e:
			
			self.log.error("Generic error while trying to retrieve dir children.")
			raise CatalogError("Generic error while trying to retrieve dir children.")
		
		# create a list of entry from the query-returned dirs
		entryList = []
		for e in dirChildren:
			
			## id, name, idParentDir, devId, devName, type
			entryList.append ( EntryItem( e[0], e[1], e[2], e[3], e[4], 'dir') )
		
		return entryList


	## wxCatalog
	def getChildrenFiles(self, idDevice, parentId):
		"""	Returns children files of given node in given device.
		"""
		
		stmt = """	select 
							DAT_Files.id, 
							DAT_Files.name,
							DAT_Files.idParentDir,
							DAT_Devices.id,
							DAT_Devices.name
					from 
							DAT_Files 
					inner join
							DAT_Devices on DAT_Devices.id = DAT_Files.idDevice
					where 
							DAT_Devices.id = ?
						and DAT_Files.idParentDir = ? 
					order by
							DAT_Files.name; """
		
		try: 
			
			fileChildren = self.db.execStmt ( stmt, (idDevice, parentId) )
			
		except sqlitetoolkit.ExectuionError, e:
			
			self.log.error("Execution error while trying to retrieve file children.")
			raise CatalogError("Execution error while trying to retrieve file children.")
			
		except sqlitetoolkit.Error, e:
			
			self.log.error("Generic error while trying to retrieve file children.")
			raise CatalogError("Generic error while trying to retrieve file children.")
		
		
		# create a list of entry from the query-returned files
		entryList = []
		for e in fileChildren:
			
			## id, name, idParentDir, devId, devName, type
			entryList.append ( EntryItem( e[0], e[1], e[2], e[3], e[4], 'file') )
		
		return entryList



	def saveCatalogAs(self, path):
		
		# close connection of current working copy
		self.db.closeConnection()
		
		try: # copy working copy to given path
			
			shutil.copy2 ( self.workPath, path )
			
		except Exception, e:
			
			self.log.error("Error while trying to copy catalog file.")
			self.log.error(e.args[0])
			self.openCatalog(self.path) # re-open connection to current catalog
			raise FileError("Error while trying to copy catalog file.")	
		
		# change current catalog
		self.path = path
		
		# reload catalog
		self.openCatalog(self.path)


	
	def saveCatalog(self):
		
		try: # remove old catalog file
			
			os.remove(self.path)
			
		except Exception, e:
			
			self.log.error("Error while trying to remove old catalog file.")
			self.log.error(e.args[0])
			raise FileError("Error while trying to remove old catalog file.")
		
		# close db
		self.db.closeConnection()
		
		try: # overwrite old catalog with working copy
			
			os.rename ( self.workPath, self.path )
			
		except Exception, e:
			
			self.log.error("Error while trying to overwrite old catalog file.")
			self.log.error(e.args[0])
			raise FileError("Error while trying to overwrite old catalog file.")	
		
		# reload catalog
		self.openCatalog(self.path)


	def close(self):
		
		self.log.info("Closing database.")
		
		try: # remove catalog working copy
			
			os.remove(self.workPath)
			
		except Exception, e:
			
			self.log.error("Error while trying to remove catalog working copy.")
			self.log.error(e.args[0])
			raise FileError("Error while trying to remove catalog working copy.")
		
		self.db.closeConnection()




