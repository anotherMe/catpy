#!/usr/bin/env python


import sqlite3 as sqlite
import logging



class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class GenericError(Error):
	
	"""Exception raised when executing statements.

	Attributes:
		msg -- explanation of the error
	"""

	def __init__(self, message):
		
		self.msg = message

class ExecutionError(Error):
	
	"""Exception raised when executing statements.

	Attributes:
		stmt -- SQL statement we were trying to execute
		msg -- explanation of the error
	"""

	def __init__(self, statement, message):
		
		self.stmt = statement
		self.msg = message



class liteIterator:
	""" Iterator used to store arguments for multiple statements execution. """
	
	def __init__(self):
		
		self.list = []
		self.idx = 0

	def __iter__(self):
		
		return self
	
	def addItem (self, item):
		
		self.list.append( item )
	
	def clear(self):
		""" Empty list """
		
		self.list = []

	def next(self):
		
		if self.idx == len(self.list):
			
			raise StopIteration
		
		self.idx += 1		
		return  self.list[self.idx - 1] 




class liteDB:


	def __init__(self, path):
		
		self.conn = sqlite.connect(path)
		self.log = logging.getLogger('pyCatalog.liteDB')
		
		# return bytestrings instead of unicode for the TEXT data type
		##self.conn.text_factory = str


	
	def execStmt(self, stmt, values=None):
		
		cur = self.conn.cursor()
		
		# if no arguments were passed
		if values == None:
			
			try:
				
				cur.execute(stmt)
				
			except sqlite.Error, e:
				
				self.log.error( "Error occurred while in execStmt().")
				self.log.error( "Raised error was : %s" % (e.args[0]) )
				raise ExecutionError(stmt, e.args[0])
			
		else:
			
			try:
				
				cur.execute(stmt, values)
				
			except sqlite.Error, e:
				
				self.log.error( "Error occurred while in execStmt(args*).")
				self.log.error( "Raised error was : %s" % (e.args[0]) )
				raise ExecutionError(stmt, e.args[0])
		
		data = cur.fetchall()
		self.conn.commit() ## redundant ?
		cur.close()
		return data



	def execMany(self, stmt, iterator):
		
		cur = self.conn.cursor()
		
		try:
			
			cur.executemany(stmt, iterator)
			
		except sqlite.Error, e:
			
			self.log.error( "Error occurred while in execMany()." )
			self.log.error( "Raised error was : %s" % (e.args[0]) )
			raise ExecutionError(stmt, e.args[0])
		
		self.conn.commit()
		return True


	
	def closeConnection(self):
		
		self.conn.close()



