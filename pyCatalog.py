#!/usr/bin/env python

import logging
import catalog
import optparse
import sys


LOGFILENAME = 'pyCatalog.log'



class pyCatalog:


	def __init__(self):
		
		# initialize variables
		self.catalogSaved = True
		self.catalog = None
		
		# parse command line arguments
		self.parseArgs()
		
		# set up log
		self.logSetup() # set up log globally
		
		# set up local log
		self.log = logging.getLogger('pyCatalog.main') 
		
		# notify DEBUG turned ON
		self.log.debug("DEBUG messages turned ON.") 
		
		# load catalog
		if self.loadCatalog():
			
			self.interact()
			
		else:
			
			print "\nCannot load catalog, quitting."
		
		print '\nbye\n'
		sys.exit()



	def loadCatalog(self):
		
		# if user passed a catalog name, try to open it
		if self.options.catalogToOpen != '':
			
			self.catalog = catalog.Catalog()
			
			try:
				
				self.catalog.openCatalog(self.options.catalogToOpen)
				
			except catalog.Error, e:
				
				print "\nError while trying to open new catalog."
				return False
		
		
		# if user choose to open new catalog
		if self.options.catalog != '':
			
			self.catalog = catalog.Catalog()
			
			try:
				
				self.catalog.createNew(self.options.catalog)
				
			except catalog.Error, e:
				
				print "\nError while creating new catalog."
				return False
		
			try:
				
				self.catalog.openCatalog(self.options.catalog)
				
			except catalog.Error, e:
				
				print "\nError while trying to open newly created catalog."
				return False
		
		return True



	def interact(self):
		
		print '\n'
		print 'Go ahead, make my day:\n'
		print '	1. Add new device'
		print '	2. Search db for file.'
		print '	3. List stored devices.'
		print '	4. Delete device with given id.'
		print '	5. Save current catalog.'
		print '	0. Quit'
		
		try:
			
			response = raw_input(': ')
			
		except KeyboardInterrupt:
			
			self.log.info ("KeyboardInterrupt catched, quitting.")
			self.quitApp()
		
		
		# Insert new device #
		if response == '1': self.addDevice()
		
		# Search for string in files#
		if response == '2': self.search()
		
		# List devices #
		if response == '3': self.getDevices()
		
		# Delete device #
		if response == '4': self.deleteDevice()
		
		# save catalog
		if response == '5': self.saveCatalog()
		
		# quit
		if response == '0': self.quitApp()
		
		self.interact()


	def addDevice(self):
		
		try: # GET device name
			
			devName = raw_input('\nInsert preferred name for new device: ')
			
		except KeyboardInterrupt:
			
			self.log.info ("KeyboardInterrupt catched.")
			return
		
		try: # retrieve list of device types
			
			types = self.catalog.getDeviceTypes()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to retrieve device types.")
			return
		
		# loop until a valid device type is selected
		devType = ""
		while True:
			
			# print device types
			print "\n"
			for t in types:
				
				print ("\t %d. %s" % t)
			
			try: # GET device type
				
				devType = raw_input('\nInsert type of device to add: ')
				
			except KeyboardInterrupt:
				
				self.log.info ("KeyboardInterrupt catched.")
				break
			
			# check if user selected a valid type
			test = False
			for t in types:
				
				if devType == str(t[0]):
					
					print ( "\nYou have selected : %s\n" % (t[1],) )
					test = True
			
			if test == True:
				
				break
				
			else:
				
				print "\nPlease review your choice:\n"
		
		
		# check type
		if devType == "":
			
			# user made no choice or aborted
			return
		
		
		try: # GET path to device
			
			devPath = raw_input('Insert path to add: ')
			
		except KeyboardInterrupt:
			
			self.log.info ("KeyboardInterrupt catched.")
			return
		
		if ( devName != '' and devPath != ''):
			
			try:
				
				c = self.catalog.addDevice(devName, devType, devPath)
				
			except catalog.Error, e:
				
				self.log.error ( str(e.msg) )
				return
				
			except KeyboardInterrupt:
				
				self.log.info ( "Device scan aborted by user." )
				print ( "\nDevice scan aborted by user." )
				return
			
			print ( "\nParsed %d files." % (c) )
			
			self.catalogSaved = False



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


	def search (self):
		
		try: # request user input
			
			print ('\nInsert string to search for (use spaces to separate multiple strings).')
			searchString = raw_input (': ')
			
		except KeyboardInterrupt:
			
			self.log.info ("KeyboardInterrupt catched.")
			return
		
		# if no input from user
		if searchString == '':
			
			return
		
		# split user input in a string tuple
		searchList = searchString.split()
		
		try: # search in files
			
			resultFiles = self.catalog.searchForFiles(searchList)
			
		except catalog.Error, e:
			
			self.log.error( "There was an error trying to commit your search to DB." )
			return
		
		try: # search in dirs
			
			resultDirs = self.catalog.searchForDirs(searchList)
			
		except catalog.Error, e:
			
			self.log.error( "There was an error trying to commit your search to DB." )
			return
		
		
		print ( "\nFound %d file matches:\n" % (len(resultFiles)) )
		for row in resultFiles:
			
			print ("---\tFILE =  %s: \n\tDEVICE = %s \n" % row)
		
		print ( "\nFound %d directory matches:\n" % (len(resultDirs)) )
		for row in resultDirs:
			
			print ("---\tDIR = %s \n\t DEVICE = %s \n" % row)


	def getDevices(self):
		
		try: # to retrieve devices stored in catalog
			
			devices = self.catalog.getDevices()
			
		except catalog.Error, e:
			
			self.log.error("Error while trying to retrieve stored devices.")
			return
		
		print '\nThese are currently stored devices:\n'
		print ( "ID\t\tNAME (type)" )
		print ( "-------------------------------------------" )
		for d in devices:
			
			print ("%s.\t\t%s (%s)" % (d[0], d[1], d[3]) )	


	
	def deleteDevice(self):
		
		try: # retrieve stored devices
			
			devices = self.catalog.getDevices()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to retrieve stored devices.")
			return
		
		# list stored devices
		print 'These are currently stored devices:\n'
		print ( "ID\t\tNAME (type)" )
		print ( "-------------------------------------------" )
		for d in devices:
			
			print ("%s.\t\t%s\t(%s)" % (d[0], d[1], d[3]) )
		
		# loop until user choice
		while True:
			
			try: # USER INPUT: ask for device id
				
				delenda = int ( raw_input ("\nPlease insert ID of device to remove: ") )
				
			except Exception, e:
				
				print "\nPlease insert only numeric values.\n"
				continue
				
			except KeyboardInterrupt:
				
				self.log.info ("Keyboard interrupt catched.")
				break
			
			# loop through stored devices and CHECK if selected device exists
			deviceFound = False
			for d in devices:
				
				if delenda == d[0]:
					
					deviceFound = True
					break
			
			# check if user selected an existing device
			if deviceFound == False:
				
				print "\nChosen device does not exists in current catalog."
				
			else:
				
				try: # USER INPUT: confirm deletion
					
					res = raw_input ( "\nDo you really want to delete \"%s\" device ? " % ( d[1], ) )
					
				except KeyboardInterrupt:
					
					self.log.info ("KeyboardInterrupt catched.")
					print "\nAborted by user."
					return
				
				if res in ("yes", "y"):
					
					try:
						
						self.catalog.removeDevice( delenda )
						
					except catalog.Error, e:
						
						self.log.error("\nErrors while trying to remove given device.")
						print "Check log file for more details."
						break
					
					print "\nDevice removed."
					self.catalogSaved = False
					break
					
				else:
					
					print "\nAborted by user."
					break



	def parseArgs(self):
		
		# create new parser object
		parser = optparse.OptionParser()
		
		# set help message
		parser.usage = "usage: %prog [options] [catalog to open]"
		
		parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Set debug messages ON.", default=False)
		parser.add_option("-c", "--create", dest="catalog", help="Create new catalog.", default="")
		
		(self.options, args) = parser.parse_args()
		
		# initialize variable
		self.options.catalogToOpen = ''
		
		# if user did not choose to create a new catalog
		if self.options.catalog == "":
			
			# if no arguments were passed
			if ( len(args) == 0 ):
				
				parser.print_help()
				self.quitApp()
			
			# recuperiamo l'eventuale nome del catalogo da aprire
			if ( len(args) > 0 ):
				
				self.options.catalogToOpen = args[0]


	def saveCatalog(self):
		
		try: # save current catalog 
			
			self.catalog.saveCatalog()
			
		except catalog.Error, e:
			
			self.log.error ("Error while trying to save catalog.")
			print ("Error while trying to save catalog.")
			return
		
		self.catalogSaved = True


	def quitApp(self):		
		
		if self.catalog != None:
			
			if self.catalogSaved == False:
				
				try: # USER INPUT: confirm quitting without saving
					
					res = raw_input ( "\nDo you really want to quit without saving current catalog ? " )
					
				except KeyboardInterrupt:
					
					self.log.info ("KeyboardInterrupt catched.")
					print "\nAborted by user."
					return
				
				if res not in ("yes", "y"):		
					
					return
			
			self.catalog.close()
		
		print '\nbye\n'
		
		sys.exit()




if __name__=='__main__':

    newInstance = pyCatalog()
