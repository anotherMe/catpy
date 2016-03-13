

#######################################################################
#	import section
#######################################################################

import logging
import ConfigParser



#######################################################################
#	Exception classes
#######################################################################


class Error(Exception):
	"""Base class for exceptions in this module."""
	
	def __init__ ( self, message):
		""" Every error must describe problem to upper level (GUI) in 
			human readable form.
		"""
		
		self.msg = message




#######################################################################
#	ConfigurationFileParser class
#######################################################################


class ConfigurationFileParser:
	
	
	def __init__(self, fileName):
		
		# setup logging
		self.log = logging.getLogger('pyCatalog.ConfigurationFileParser')
		
		# parser variable initially empty
		self.parser = None
		
		# set global name of INI file
		self.fileName = fileName
	
	
	def load(self):
		
		try: # create new SafeConfigParser parser instance
			
			self.parser = ConfigParser.SafeConfigParser()
			
		except Exception, ex:
			
			self.log.error("Error while trying to instantiate new parser:" + ex.args[1])
			raise Error("Error while trying to instantiate new parser.")
		
		try: # open file ----------------------------------------------
			
			f = open (self.fileName, 'r')
			
		except Exception, err:
			
			self.log.error("Error while trying to open option file: " + err.args[1])
			raise Error("Error while trying to open option file.")
		
		
		try: # parse file ---------------------------------------------
			
			self.parser.readfp(f)
			
		except Exception, err:
			
			self.log.error("Error while trying to parse option file:" + err.args[1])
			raise Error("Error while trying to parse option file.")
		
		try: # close file
			
			f.close()
			
		except Exception, ex:
			
			self.log.error("Error while trying to close option file:" + ex.args[1])
			raise Error("Error while trying to close option file.")
	
	
	def getOption (self, section, option):
		""" get ( section, option[, raw[, vars]] )
    		Get an option value for the named section. All the "%" 
    		interpolations are expanded in the return values, based on 
    		the defaults passed into the constructor, as well as the 
    		options vars provided, unless the raw argument is true.
		"""
		
		if self.parser == None:
			
			self.log.error("Error while trying to get option: parser not initialized.")
			raise Error("Parser has not been initialized.")
		
		# CHECK if given section exists
		if self.parser.has_section(section):
			
			pass
			
		else:
			
			self.log.error("Error while trying to get option: cannot find given section.")
			raise Error("There is no section named '%s'." % (section, ) )
		
		try: # retrieve requested option
			
			value = self.parser.get (section, option)
			
		except Exception, ex:
			
			self.log.error("Error while trying to get option " + option + " - " + ex.args[1])
			raise Error("Error while trying to get option '%s'." % (option,) )
		
		return value


	def getItems(self, section):
		""" Return a list of (name, value) pairs for each option in 
			the given section.
		"""
		
		if self.parser == None:
			
			self.log.error("Error while trying to get items: parser not initialized.")
			raise Error("Parser has not been initialized.")
		
		# CHECK if given section exists
		if self.parser.has_section(section):
			
			pass
			
		else:
			
			self.log.error("Error while trying to get items: cannot find given section.")
			raise Error("There is no section named '%s'." % (section, ) )
		
		try: # retrieve requested data
			
			itemsList = self.parser.items(section)
			
		except Exception, ex:
			
			self.log.error("Error while trying to get items in section " + section + " - " + ex.args[1])
			raise Error("Error while trying to get items in section '%s'." % (section,) )
		
		return itemsList



	def setOption (self, section, option, value):
		""" If the given section exists, set the given option to the 
			specified value; otherwise raise NoSectionError. value must 
			be a string (str or unicode); if not, TypeError is raised.
		"""
		
		if self.parser == None:
			
			self.log.error("Error while trying to set option: parser not initialized.")
			raise Error("Parser has not been initialized.")
		
		# CHECK if given section exists
		if self.parser.has_section(section):
			
			pass
			
		else:
			
			self.log.error("Error while trying to set option: cannot find given section.")
			raise Error("There is no section named '%s'." % (section, ) )
		
		# CHECK if given option exists
		if self.parser.has_option(section, option):
			
			pass
			
		else:
			
			self.log.error("Error while trying to set option: cannot find given option.")
			raise Error("There is no option named '%s'." % (option, ) )		
		
		try: # set option
			
			self.parser.set (section, option, value)
			
		except Exception, ex:
			
			self.log.error("Error while trying to get option. " + ex.args[1])
			raise Error("Error while trying to get option '%s'." % (option,) )
		
		try: # open file ----------------------------------------------
			
			f = open (self.fileName, 'w')
			
		except Exception, err:
			
			self.log.error("Error while trying to open option file. " + err.args[1])
			raise Error("Error while trying to open option file.")
		
		try: # commit change ------------------------------------------
			
			self.parser.write (f)
			
		except Exception, ex:
			
			self.log.error("Error while commiting changes to option file." + ex.args[1])
			raise Error("Error while commiting changes to option file %s" % (self.fileName,) )
		
		try: # close file
			
			f.close()
			
		except Exception, ex:
			
			self.log.error("Error while trying to close option file: " + ex.args[1])
			raise Error("Error while trying to close option file.")


