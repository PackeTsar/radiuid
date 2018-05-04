#!/usr/bin/python

#####        RadiUID Server v2.5.0         #####
#####       Written by John W Kerns        #####
#####      http://blog.packetsar.com       #####
##### https://github.com/PackeTsar/radiuid #####

import os
import re
import sys
import ssl
import time
import shutil
import urllib
import urllib2
import commands
import platform
import xml.etree.ElementTree as ElementTree

##### Inform RadiUID version here #####
version = "v2.5.0"

##### Set some internal settings #####
etcconfigfile = '/etc/radiuid/radiuid.conf'
maxtimeout = 1440
maxuidspercall = 50






#########################################################################
########################## USER INTERFACE CLASS #########################
#########################################################################
#######      Used by most other classes and methods to output     #######
#######         data to stdout and to write to the logfile        #######
#########################################################################
class user_interface(object):
	def __init__(self):
		##### ANSI Colors for use in CLI and logs #####
		self.black = '\033[0m'
		self.red = '\033[91m'
		self.green = '\033[92m'
		self.yellow = '\033[93m'
		self.blue = '\033[94m'
		self.magenta = '\033[95m'
		self.cyan = '\033[96m'
		self.white = '\033[97m'
	##### To be used like "print 'this is ' + color('green', green) + ' is it not?'" #####
	##### Easy method to write color to a str output then switch back to default black color #####
	def color(self, input, inputcolor):
		result = inputcolor + input + self.black
		return result
	##### Show progress bar #####
	##### The most awesome method in this program. Also the most useless #####
	def progress(self, message, seconds):
		timer = float(seconds) / 50
		currentwhitespace = 50
		currentblackspace = 0
		while currentwhitespace > -1:
			sys.stdout.flush()
			sys.stdout.write("\r" + message + "    [")
			sys.stdout.write("=" * currentblackspace)
			sys.stdout.write(" " * currentwhitespace)
			sys.stdout.write("]")
			currentwhitespace = currentwhitespace - 1
			currentblackspace = currentblackspace + 1
			time.sleep(timer)
		print "\n"
	##### Ask a 'yes' or 'no' question and check answer #####
	##### Accept 'yes', 'no', 'y', or 'n' in any case #####
	def yesorno(self, question):
		answer = 'temp'
		while answer.lower() != 'yes' and answer.lower() != 'no' and answer.lower() != 'y' and answer.lower() != 'n':
			answer = raw_input(self.color("----- " + question + " [yes or no]:", self.cyan))
			if answer.lower() == "no":
				return answer.lower()
			elif answer.lower() == "yes":
				return answer.lower()
			elif answer.lower() == "n":
				answer = "no"
				return answer
			elif answer.lower() == "y":
				answer = "yes"
				return answer
			else:
				print self.color("'Yes' or 'No' dude...", self.red)
	##### Create a table of data from a list of dictionaries where the key in each dict is the header and the val is the column value #####
	##### The tabledata input is the list of dictionaries and the column order is an ordered list of how the columns should be displayed #####
	##### The output is a printable table with automatically spaced columns, centered headers and values #####
	def make_table(self, columnorder, tabledata):
		##### Check and fix input type #####
		if type(tabledata) != type([]): # If tabledata is not a list
			tabledata = [tabledata] # Nest it in a list
		##### Set seperators and spacers #####
		tablewrap = "#" # The character used to wrap the table
		headsep = "=" # The character used to seperate the headers from the table values
		columnsep = "|" # The character used to seperate each value in the table
		columnspace = "  " # The amount of space between the largest value and its column seperator
		##### Generate a dictionary which contains the length of the longest value or head in each column #####
		datalengthdict = {} # Create the dictionary for storing the longest values
		for columnhead in columnorder: # For each column in the columnorder input
			datalengthdict.update({columnhead: len(columnhead)}) # Create a key in the length dict with a value which is the length of the header
		for row in tabledata: # For each row entry in the tabledata list of dicts
			for item in columnorder: # For column entry in that row
				if len(re.sub(r'\x1b[^m]*m', "",  row[item])) > datalengthdict[item]: # If the length of this column entry is longer than the current longest entry
					datalengthdict[item] = len(row[item]) # Then change the value of entry
		##### Calculate total table width #####
		totalwidth = 0 # Initialize at 0
		for columnwidth in datalengthdict: # For each of the longest column values
			totalwidth += datalengthdict[columnwidth] # Add them all up into the totalwidth variable
		totalwidth += len(columnorder) * len(columnspace) * 2 # Account for double spaces on each side of each column value
		totalwidth += len(columnorder) - 1 # Account for seperators for each row entry minus 1
		totalwidth += 2 # Account for start and end characters for each row
		##### Build Header #####
		result = tablewrap * totalwidth + "\n" + tablewrap # Initialize the result with the top header, line break, and beginning of header line
		columnqty = len(columnorder) # Count number of columns
		for columnhead in columnorder: # For each column header value
			spacing = {"before": 0, "after": 0} # Initialize the before and after spacing for that header value before the columnsep
			spacing["before"] = int((datalengthdict[columnhead] - len(columnhead)) / 2) # Calculate the before spacing
			spacing["after"] = int((datalengthdict[columnhead] - len(columnhead)) - spacing["before"]) # Calculate the after spacing
			result += columnspace + spacing["before"] * " " + columnhead + spacing["after"] * " " + columnspace # Add the header entry with spacing
			if columnqty > 1: # If this is not the last entry
				result += columnsep # Append a column seperator
			del spacing # Remove the spacing variable so it can be used again
			columnqty -= 1 # Remove 1 from the counter to keep track of when we hit the last column
		del columnqty # Remove the column spacing variable so it can be used again
		result += tablewrap + "\n" + tablewrap + headsep * (totalwidth - 2) + tablewrap + "\n" # Add bottom wrapper to header
		##### Build table contents #####
		result += tablewrap # Add the first wrapper of the value table
		for row in tabledata: # For each row (dict) in the tabledata input
			columnqty = len(columnorder) # Set a column counter so we can detect the last entry in this row
			for column in columnorder: # For each value in this row, but using the correct order from column order
				spacing = {"before": 0, "after": 0} # Initialize the before and after spacing for that header value before the columnsep
				spacing["before"] = int((datalengthdict[column] - len(re.sub(r'\x1b[^m]*m', "",  row[column]))) / 2) # Calculate the before spacing
				spacing["after"] = int((datalengthdict[column] - len(re.sub(r'\x1b[^m]*m', "",  row[column]))) - spacing["before"]) # Calculate the after spacing
				result += columnspace + spacing["before"] * " " + row[column] + spacing["after"] * " " + columnspace # Add the entry to the row with spacing
				if columnqty == 1: # If this is the last entry in this row
					result += tablewrap + "\n" + tablewrap # Add the wrapper, a line break, and start the next row
				else: # If this is not the last entry in the row
					result += columnsep # Add a column seperator
				del spacing # Remove the spacing settings for this entry
				columnqty -= 1 # Keep count of how many row values are left so we know when we hit the last one
		result += tablewrap * (totalwidth - 1) # When all rows are complete, wrap the table with a trailer
		return result
	##### Add an indent to any string data #####
	##### Input is the indent you want to use and the data you want to indent #####
	##### Output is the inputdata indented with the indent #####
	def indenter(self, indent, inputdata):
		result = indent + inputdata # Prepend the indent to the first line
		result = result.replace("\n", "\n" + indent) # Add an indent to each new line
		return result
	##### Print out this ridiculous text-o-graph #####
	##### It took me like an hour to draw and I couldn't stand to just not use it #####
	def packetsar(self):
		print  self.color("\n                                ###############################################      \n\
			      #                                                 #    \n\
			    #                                                     #  \n\
			   #                                                       # \n\
			  #                                                         #\n\
			  #                            #                            #\n\
			  #                          # # #                          #\n\
			  #                         #  #  #                         #\n\
			  #                            #                            #\n\
			  # @@@@  @@  @@@@ @  @ @@@@ @@@@@  @@@@  @@  @@@@          #\n\
			  # @  @ @  @ @    @ @  @      @   @     @  @ @  @          #\n\
			  # @@@@ @@@@ @    @@   @@@    @   @ @ @ @@@@ @@@@          #\n\
			  # @    @  @ @    @ @  @      @       @ @  @ @ @           #\n\
			  # @    @  @ @@@@ @  @ @@@@   @   @@@@  @  @ @  @          #\n\
			  #                            #                            #\n\
			  #                                                         #\n\
			  #                      #           #                      #\n\
			  #                       #   ###   #                       #\n\
			  #    #####################  ###  #####################    #\n\
			  #                       #   ###   #                       #\n\
			  #                      #           #                      #\n\
			  #                                                         #\n\
			  #                            #                            #\n\
			  #                            #                            #\n\
			  #                            #                            #\n\
			  #                            #                            #\n\
			  #                            #                            #\n\
			  #                            #                            #\n\
			  #                            #                            #\n\
			  #                         #  #  #                         #\n\
		  	  #                          # # #                          #\n\
			  #                            #                            #\n\
			   #                                                       # \n\
			    #                                                     #  \n\
			      #                                                 #    \n\
			        ###############################################      \n", self.blue)








#########################################################################
################################ OS CHECKS ##############################
#########################################################################
#######            Used to check OS and module versions           #######
#########################################################################
#########################################################################
ui = user_interface()
##### Detect running command #####
if "radiuid.py" in sys.argv[0]:
	runcmd = "python " + sys.argv[0]
else:
	runcmd = "radiuid"
##### Check ETree Version #####
if float(ElementTree.VERSION[:3]) < 1.3:
	try:
		import xml.etree13.ElementTree as ElementTree
	except ImportError:
		print ui.color("***** WARNING: Looks like you are running an old version of the xml.etree.ElementTree module (" + ElementTree.VERSION + ") *****", ui.red)
		print ui.color("***** WARNING: RadiUID will not operate correctly without version 1.3.0 or later.", ui.red)
		print ui.color("Please run the command '", ui.red) + ui.color(runcmd + " request xml-update", ui.cyan) + ui.color("' to update the module for RadiUID\n\n", ui.red)
##### Check OS Version #####
osversion = ""
for each in platform.dist():
	osversion = osversion + each + " "
##### Check For SystemD #####
checksystemd = commands.getstatusoutput("systemctl")
if len(checksystemd[1]) > 50 and "Operation not permitted" not in checksystemd[1]:
	systemd = True
else:
	systemd = False
##### Check for Package Manager #####
checkpkgmgr = {}
checknames = ["yum", "apt", "apt-get"]
for mgr in checknames:
	checkpkgmgr.update({len(commands.getstatusoutput(mgr)[1]): mgr})
pkgmgr = checkpkgmgr[sorted(list(checkpkgmgr), key=int)[len(sorted(list(checkpkgmgr), key=int)) - 1]]
##### Check for FreeRADIUS Service Name #####
def check_rad_name():
	global radservicename
	checkradname = {}
	checknames = ["radiusd", "freeradius"]
	if systemd:
		for name in checknames:
			checkradname.update({len(commands.getstatusoutput("systemctl status " + name)[1]) - len(name): name})
	elif not systemd:
		for name in checknames:
			if "stopped" in commands.getstatusoutput("service " + name + " status")[1]:
				checkradname.update({1000: name})
			checkradname.update({len(commands.getstatusoutput("service " + name + " status")[1]) - len(name): name})
	radservicename = checkradname[sorted(list(checkradname), key=int)[len(sorted(list(checkradname), key=int)) - 1]]
	if len(checkradname) < 2: # If the result dictionary has only 1 key, then the service is likely not installed
		radservicename = "uninstalled"
	else:
		radservicename = checkradname[sorted(list(checkradname), key=int)[len(sorted(list(checkradname), key=int)) - 1]]
	return radservicename
check_rad_name()
##### Check for FreeRADIUS Client Config File Path #####
def check_rad_config():
	global clientconfpath
	confpaths = ['/etc/raddb/clients.conf', '/etc/freeradius/clients.conf']
	checkclientpath = {}
	for path in confpaths:
		checkclientpath.update({commands.getstatusoutput("ls " + path)[0]: path})
	try:
		clientconfpath = checkclientpath[0]
	except KeyError:
		clientconfpath = '/etc/raddb/clients.conf'
	return clientconfpath
check_rad_config()
##### Check if we are operating in a container #####
incontainer = False
def check_for_container():
	global osversion
	global version
	global incontainer
	if "No such" in commands.getstatusoutput("ls /.dockerenv")[1]:
		pass
	else:
		incontainer = True
		osversion = osversion + "(Docker Container)"
check_for_container()






#########################################################################
########################## FILE MANAGEMENT CLASS ########################
#########################################################################
#######     Used by the main RadiUID methods to for changing,     #######
#######    checking, and maintaining files in the file system     #######
#########################################################################
class file_management(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
	#######################################################
	####### File/Path-Based Data Processing Methods #######
	#######       No Direct File Interaction        #######
	#######################################################
	##### Add '/' to directory path if not included #####
	def directory_slash_add(self, directorypath):
		check = re.search("^.*\/$", directorypath)
		if check is None:
			result = directorypath + "/"
			return result
		else:
			result = directorypath
			return result
	##### Take filepath and give back directory path and filename in list where list[0] is directory path, list[1] is filename #####
	def strip_filepath(self, filepath):
		nestedlist = re.findall("^(.+)/([^/]+)$", filepath) # Split filepath into a tuple where tuple[0] is the dir name and tuple[1] is the filename
		if len(nestedlist) > 0: # If the regex returns a tuple, then process the path
			templist = nestedlist[0]
			tempfilepath = templist[0]
			filepath = self.directory_slash_add(tempfilepath) # Add the / at the end of the directory path
			filename = templist[1]
			resultlist = [] # Put path info into list for return
			resultlist.append(filepath)
			resultlist.append(filename)
		else: # If nothing is returned from regex search, then file is in root dir
			resultlist = []
			resultlist.append("/") # Add root dir as directory path
			resultlist.append(filepath.replace("/", "")) # Remove / from filepath and set that as file name
		return resultlist
	##### Check a Unix/Linux file or directory path for illegal patterns/characters and for required patterns #####
	##### The inputtype arg can be "dir" or "file" (depending on if the input is a file path or a directory path). The input arg is a str of the file or dir path #####
	##### The returned data is a list of strings where result[0] equals either "pass" or "fail" and result[1:] equals the error message(s) if input is determined to be bad ####
	def check_path(self, pathtype, path):
		result = ['pass'] # set initial result as "pass"
		regexblacklistdict = {"space character": " ", "double forward slash (//)": "\/\/", 'double quote (")': '"', "single quote (')": "'", "pipe character (|)": "\|", "double period (..)": "\.\.", "comma (,)": ",", "exclamation point (!)": "!", "grave accent(`)": "`", "ampersand (&)": "&", "asterisk (*)": "\*", "left parenthesis [(]": "\(", "right parenthesis [)]": "\)"} # Set common blacklist characters and patterns with keys as friendly names and values as the regex patterns
		regexrequiredict = {"begins with /":"^\/"} # Set common required patterns with keys as friendly names and values as the regex patterns
		if pathtype == "dir": # if the path type is "dir"
			regexrequiredict.update({"ends with /": "\/$"}) # add additional patterns to requirements dict
		elif pathtype == "file": # if the path type is "file"
			regexblacklistdict.update({"ends with /": "\/$"}) # add additional patterns to blacklist dict
		for key in regexblacklistdict: # For every entry in the blacklist dict
			if len(re.findall(regexblacklistdict[key], path)) > 0: # If a pattern from the blacklist dict is matched in the path data
				result[0] = 'fail' # Set the result to fail
				result.append("Pattern Not Allowed: " + key) # Append an error message to a failed result
		for key in regexrequiredict: # For every entry in the requirement dict
			if len(re.findall(regexrequiredict[key], path)) == 0: # If the pattern is not found in the path
				result[0] = 'fail' # Set the result to fail
				result.append("Pattern Required: " + key) # Append an error message to a failed result
		return result
	##### Check that input is a legal fully qualified domain name (FQDN) #####
	##### The input is a str of the FQDN #####
	##### The returned data is a list of strings where result[0] equals either "pass" or "fail" and result[1:] equals the error message(s) if input is determined to be bad ####
	def check_domainname(self, domainname):
		result = {"status": "pass", "messages": []} # Start with a passing result
		##### 1. Check that only legal characters are in name (RFC883 and RFC952) #####
		characterregex = "^[a-zA-Z0-9\-\.]+$" # A list of the valid domain-name characters in a domain name
		for entry in re.findall(characterregex, domainname): # For each string in the list returned by re.findall
			if entry == domainname: # If one of the strings in the returned list equals the full domainname string
				charactercheck = "pass" # Then all its characters are legal and it passes the check
				result["messages"].append({"OK": "No illegal characters found"}) # Append a message to the result
		if charactercheck == "fail": # If the check failed
			result["messages"].append({"FATAL": "Illegal character found. Only a-z, A-Z, 0-9, period (.), and hyphen (-) allowed."})
		##### 2. Check the Length Restrictions: 63 max char per label, 253 max total (RFC1035) #####
		if len(domainname) <= 253: # If total length of domain name is 253 char or less
			result["messages"].append({"OK": "Domain total length is good"})
			labelcheck = {'passlength': 0, 'faillength': 0} # Start a tally of passed and failed labels
			for label in domainname.split("."): # Split the domain into its labels and for each label
				if len(label) <= 63: # If the individual label is less than or equal to 63 characters...
					labelcheck['passlength'] = labelcheck['passlength'] + 1 # Add it as a passed label in the tally
				else: # If it is longer than 63 characters
					labelcheck['faillength'] = labelcheck['faillength'] + 1 # Add it as a failed label in the tally
					result["messages"].append({"FATAL": "Label: " + label + " exceeds max label length of 63 characters"})
			if labelcheck['faillength'] == 0: # If there are NOT any failed labels in the tally
				maxlengthcheck = "pass" # Then all labels are passed and the check passes
		##### 3. Check that first and last character are not a hyphen or period #####
		firstcharregex = "^[a-zA-Z0-9]" # Match a first character of upper or lower A-Z and any digit (no hyphens or periods)
		lastcharregex = "[a-zA-Z0-9]$" # Match a last character of upper or lower A-Z and any digit (no hyphens or periods)
		if len(re.findall(firstcharregex, domainname)) > 0: # If the first characters produces a match
			result["messages"].append({"OK": "Domain first character is legal"})
			if len(re.findall(lastcharregex, domainname)) > 0: # And the last characters produces a match
				result["messages"].append({"OK": "Domain last character is legal"})
				firstlastcheck = "pass" # Then first and last characters are legal and the check passes
			else:
				result["messages"].append({"FATAL": "First and last character in domain must be alphanumeric"})
		else:
			result["messages"].append({"FATAL": "First and last character in domain must be alphanumeric"})
		##### 4. Check that no labels begin or end with hyphens (https://www.icann.org/news/announcement-2000-01-07-en) #####
		beginendhyphenregex = "\.\-|\-\." # Match any instance where a hyphen follows a period or vice-versa
		if len(re.findall(beginendhyphenregex, domainname)) == 0: # If the regex does NOT make a match anywhere
			result["messages"].append({"OK": "No labels begin or end with hyphens"})
			beginendhyphencheck = "pass" # Then no names begin with a hyphen and the check passes
		else:
			result["messages"].append({"FATAL": "Each label in the domain name must begin and end with an alphanumeric character. No hyphens"})
		##### 5. No double periods or triple-hyphens exist (RFC5891 for double-hyphens) #####
		nomultiplesregex = "\.\.|\-\-\-" # Match any instance where a double period (..) or a triple hyphen (---) exist
		if len(re.findall(nomultiplesregex, domainname)) == 0: # If the regex does NOT make a match anywhere
			result["messages"].append({"OK": "No double periods or triple hyphens found"})
			nomultiplescheck = "pass" # Then no double periods or triple hyphens exist and the check passes
		else:
			result["messages"].append({"FATAL": "No double-periods (..) or triple-hyphens (---) allowed in domain name"})
		##### 6. There is at least one period in the domain name #####
		periodinnameregex = "\." # Match any instance of a period
		if len(re.findall(periodinnameregex, domainname)) > 0: # If there is at least one period in the domain name...
			periodinnamecheck = "pass"
			result["messages"].append({"OK": "At least one period found in the domain name"})
		else:
			result["messages"].append({"WARNING": "No period (.) found in domain name. FQDNs are preferred but not required."})
		##### Make sure all checks are passed #####
		for listentry in result["messages"]:
			for key in listentry:
				if key == "FATAL":
					result["status"] = "fail"
		return result
	def check_userpass(self, inputtype, userorpassinput):
		result = {"status": "fail", "messages": []} # Start with a failed result
		if inputtype == "user":
			characterregex = "^[a-zA-Z0-9_\.]+$" # A list of the valid username characters
			for entry in re.findall(characterregex, userorpassinput): # For each string in the list returned by re.findall
				if entry == userorpassinput: # If one of the strings in the returned list equals the full domainname string
					result["status"] = "pass" # Then all its characters are legal and it passes the check
					result["messages"].append({"OK": "No illegal characters found in username"}) # Append a message to the result
			if len(re.findall(characterregex, userorpassinput)) == 0:
				result["status"] = "fail" # Then all its characters are legal and it passes the check
				result["messages"].append({"FATAL": "Illegal characters found in username. Valid characters are alphanimeric, underscore (_), and Period (.)"}) # Append a message to the result
		elif inputtype == "password":
			characterregex = "\&|\<|\>" # A list of the invalid password characters
			if len(re.findall(characterregex, userorpassinput)) > 0: # For each string in the list returned by re.findall
				result["status"] = "fail"
				result["messages"].append({"FATAL": "Illegal characters found in password. Characters '&', '<', and '>' are not allowed "}) # Append a message to the result
			else:
				result["status"] = "pass" # Then all its characters are legal and it passes the check
				result["messages"].append({"OK": "No illegal characters found in password"}) # Append a message to the result
		return result
	def check_targets(self, targetdict):
		result = {}
		for target in targetdict:
			targetname = target["hostname"] + ":vsys" + target["vsys"]
			result.update({targetname: {"status": "working"}})
			##### Check hostname #####
			result[targetname].update({"hostnamecheck": {"status": "working", "messages": []}})
			if self.ip_checker("address", targetname) == "pass":
				result[targetname]["hostnamecheck"]["status"] = "pass"
				result[targetname]["hostnamecheck"]["messages"].append({"OK": "Target hostname is valid IPv4 address"})
			else:
				result[targetname]["hostnamecheck"] = self.check_domainname(target["hostname"])
			##### Check Username and Password #####
			try:
				result[targetname].update({"usernamecheck": self.check_userpass("user", target["username"])})
			except KeyError:
				result[targetname].update({"usernamecheck": {"status": "fail", "messages": [{"FATAL": "<username> parameter does not exist for this target"}]}})
			try:
				result[targetname].update({"passwordcheck": self.check_userpass("password", target["password"])})
			except KeyError:
				result[targetname].update({"passwordcheck": {"status": "fail", "messages": [{"FATAL": "<password> parameter does not exist for this target"}]}})
			##### Read Results #####
			warnings = 0
			for check in result[targetname].keys():
				if check != "status":
					if result[targetname][check]["status"] == "fail":
						result[targetname]["status"] = "fail"
						break
					elif result[targetname][check]["status"] == "warning":
						warnings = warnings + 1
					elif result[targetname][check]["status"] == "pass":
						result[targetname]["status"] = "pass"
			if warnings > 0:
				result[targetname]["status"] = "warning"
		return result
	def scrub_targets(self, mainmode, submode):
		if mainmode == "noisy":
			checkdict = self.check_targets(targets)
			for target in checkdict:
				if checkdict[target]["status"] == "pass":
					#self.logwriter("normal", "***********TARGET " + target + " settings verified***********")
					none = None
				else:
					for check in checkdict[target]:
						if check != "status":
							for message in checkdict[target][check]["messages"]:
								if message.keys()[0] == "WARNING":
									self.logwriter("normal", self.ui.color("***********TARGET " + target + ": " + message.keys()[0] + ": " + message.values()[0] + " ***********", self.ui.yellow))
								elif message.keys()[0] == "FATAL":
									self.logwriter("normal", self.ui.color("***********TARGET " + target + ": " + message.keys()[0] + ": " + message.values()[0] + " ***********", self.ui.red))
				if submode == "scrub":
					if checkdict[target]["status"] == "fail":
						targetindex = 0
						for badtarget in targets:
							if badtarget["hostname"] + ":vsys" + badtarget["vsys"] == target:
								self.logwriter("normal", self.ui.color("***********Excluding " + target + " from loaded firewall targets***********", self.ui.red))
								targets.pop(targetindex)
							else:
								targetindex += 1
				elif submode == "report":
					if checkdict[target]["status"] == "fail":
							self.logwriter("normal", self.ui.color("***********Target " + target + " configuration is incomplete***********", self.ui.red))
	##### Check that legit IP address or CIDR block was entered #####
	##### The mode of "cidr" or "address" is entered as the first arg. Input is second arg and is a string of the IPv4 address or CIDR block. #####
	##### Result is a simple string containing "pass" or "fail" #####
	def ip_checker(self, iptype, ip_block):
		if iptype == "address":
			ipregex = "^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
		elif iptype == "cidr":
			ipregex = "^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-9]|1[0-9]|2[0-9]|3[0-2]?)$"
		check = re.search(ipregex, ip_block)
		if check is None:
			result = "fail"
		else:
			result = "pass"
		return result
	##### Simple two-choice logic method to pick a preferred input over another #####
	##### Used to decide whether to use the radiuid.conf file in the 'etc' location, or the one in the local working directory #####
	def file_chooser(self, firstchoice, secondchoice):
		firstexists = self.file_exists(firstchoice)
		secondexists = self.file_exists(secondchoice)
		if firstexists == "yes" and secondexists == "yes":
			return firstchoice
		if firstexists == "yes" and secondexists == "no":
			return firstchoice
		if firstexists == "no" and secondexists == "yes":
			return secondchoice
		if firstexists == "no" and secondexists == "no":
			return "CHOOSERFAIL"
			quit()
	#######################################################
	#######        File Manipulation Methods        #######
	#######         Direct File Interaction         #######
	#######################################################
	##### List all files in a directory path and subdirs #####
	##### Used to enumerate files in the FreeRADIUS accounting log path #####
	def list_files(self, mode, path):
		filelist = []
		for root, directories, filenames in os.walk(path):
			for filename in filenames:
				entry = os.path.join(root, filename)
				filelist.append(entry)
				if mode == "noisy":
					self.logwriter("normal", "Found File: " + entry + "...   Adding to file list")
		if len(filelist) == 0:
			if mode == "noisy":
				self.logwriter("normal", "No Accounting Logs Found. Nothing to Do.")
			return filelist
		else:
			return filelist
	def acct_copy(self, filename):
		file = os.path.split(filename)[1]
		newpath = os.path.join(acctlogcopypath, file)
		if os.path.isfile(newpath):
			self.logwriter("normal", "Appending file %s to %s " % (filename, newpath))
			f = open(filename, "r")
			g = open(newpath, "a")
			g.write("\n\n")
			g.write(f.read())
			f.close()
			g.close()
		else:
			self.logwriter("normal", "Copying file %s to %s " % (filename, acctlogcopypath))
			shutil.copy2(filename, acctlogcopypath)
	##### Delete all files in provided list #####
	##### Used to remove the FreeRADIUS log files so the next iteration of RadiUID doesn't pick up redundant information #####
	def remove_files(self, filelist):
		for filename in filelist:
			if acctlogcopypath:
				self.acct_copy(filename)
			os.remove(filename)
			self.logwriter("normal", "Removed file: " + filename)
	##### Writes the new config data to the config file #####
	##### Used at the end of the wizard when new config values have been defined and need to be written to a config file #####
	def write_file(self, filepath, filedata):
		f = open(filepath, 'w')
		f.write(filedata)
		f.close()
	##### Check if specific file exists #####
	def file_exists(self, filepath):
		checkdata = commands.getstatusoutput("ls " + filepath)
		exists = ""
		for line in checkdata:
			line = str(line)
			if "No such" in line:
				exists = "no"
			else:
				exists = "yes"
		return exists
	##### Get the current working directory #####
	##### Used when radiuid.py is run manually using the 'python radiuid.py <arg>' to get the working directory to help find the config file #####
	def get_working_directory(self):
		listoutput = commands.getstatusoutput("pwd")
		result = listoutput[1]
		result = self.directory_slash_add(result)
		return result
	##### Config file finder method with two modes, one to report on its activity, and one to operate silently #####
	##### Noisy mode used for verbose logging when running or starting the primary RadiUID program #####
	##### Quiet mode used for purposes like the command interface when verbose output is not desired #####
	def find_config(self, mode):
		localconfigfile = self.get_working_directory() + "radiuid.conf"
		if mode == "noisy":
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********LOOKING FOR RADIUID CONFIG FILE...***********" + "\n"
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********DETECTED WORKING DIRECTORY: " + self.get_working_directory() + "***********" + "\n"
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********CHECKING LOCATION: PREFERRED LOCATION - " + etcconfigfile + "***********" + "\n"
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********CHECKING LOCATION: ALTERNATE LOCATION IN LOCAL DIRECTORY - " + localconfigfile + "***********" + "\n"
			configfile = self.file_chooser(etcconfigfile, localconfigfile)
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********FOUND CONFIG FILE IN LOCATION: " + configfile + "***********" + "\n"
			return configfile
		if mode == "quiet":
			configfile = self.file_chooser(etcconfigfile, localconfigfile)
			return configfile
		else:
			print "Need to set mode for find_config to 'noisy' or 'quiet'"
			quit()
	##### Core IO method for logwriter operations. Excludes mode awareness #####
	def logwriter_core(self, file, input):
		target = open(file, 'a')
		target.write(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n")
		target.close()
	##### Writes lines to the log file in different modes #####
	##### Uses the logfile variable published to the global namespace #####
	##### Modes of use change what log_writer does when it encounters certain errors. Modes are normal #####
	def logwriter(self, mode, input):
		if mode == "normal": # Only use normal mode if you have already initialized the logfile to global namespace
			try:
				target = open(logfile, 'a')
				target.write(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n")
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n"
				target.close()
			except IOError:
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********CANNOT OPEN FILE: " + logfile + " ***********\n", self.ui.red)
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********PLEASE MAKE SURE YOU RAN THE INSTALLER ('python radiuid.py install')***********\n", self.ui.red)
				quit()
			except NameError:
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"*********** LOGFILE VARIABLE NOT FOUND! ***********\n", self.ui.red)
				quit()
		if mode == "cli":
			self.initialize_config("quiet")
			self.publish_config("quiet")
			if self.file_exists(logfile) == "no":
				print self.ui.color("***** WARNING: Could not write CLI accounting info to log file *****", self.ui.yellow)
			elif self.file_exists(logfile) == "yes":
				self.logwriter_core(logfile, input)
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n"
		if mode == "quiet":
			self.initialize_config("quiet")
			self.publish_config("quiet")
			if self.file_exists(logfile) == "yes":
				self.logwriter_core(logfile, input)
				# no printing to console
		if maxloglines != "0":
			self.log_trimmer(logfile, int(maxloglines))
	#######################################################
	#######    Configuration Management Methods     #######
	#######################################################
	#######    Used to read/edit/write/show the     #######
	#######   configuration from the config file    #######
	#######################################################
	##### Initiate the object by reading in config file, pulling out comment (for use later by save_config), and parsing to element tree #####
	##### All methods in this class rely on searching/writing to/parsing the element tree "self.root" #####
	def initialize_config(self, mode):
		global configfile
		if mode == 'noisy':
			configfile = self.find_config(mode)
			with open(configfile, 'r') as self.filetext:
				self.xmldata = self.filetext.read()
			self.regex = "(?s)<!--.*-->"
			self.configcomment = re.findall(self.regex, self.xmldata, flags=0)[0]
			self.cleanedxml = self.xmldata.replace(self.configcomment, "")
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********EXTRACTED XML CONFIG DATA FROM CONFIG FILE " + configfile + "***********" + "\n"
			self.root = ElementTree.fromstring(self.cleanedxml)
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********" + self.ui.color("SUCESSFULLY MOUNTED CONFIG XML ELEMENT-TREE", self.ui.green) + "***********\n"
		if mode == 'quiet':
			configfile = self.find_config(mode)
			if configfile == 'CHOOSERFAIL':
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********ERROR: Config file (radiuid.conf) not found in preferred location (/etc/radiuid/) or in working directory***********", self.ui.red)
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********Please put a copy of the radiuid.conf config file in one of these directories***********", self.ui.red)
				quit()
			with open(configfile, 'r') as self.filetext:
				self.xmldata = self.filetext.read()
			self.regex = "(?s)<!--.*-->"
			self.configcomment = re.findall(self.regex, self.xmldata, flags=0)[0]
			self.cleanedxml = self.xmldata.replace(self.configcomment, "")
			self.root = ElementTree.fromstring(self.cleanedxml)
	##### Publish all settings to variables in the global namespace for use by other processes #####
	##### All variables are set to strings with the exception of the targets, which is a list of dictionary items #####
	def publish_config(self, mode):
		global configdict
		global radiuslogpath
		global acctlogcopypath
		global logfile
		global maxloglines
		global userdomain
		global timeout
		global looptime
		global tlsversion
		global radiusstopaction
		global ipaddressterm
		global usernameterm
		global delineatorterm
		global targets
		global mungeconfig
		global tomunge
		if mode == 'noisy':# to be used to initialize the RadiUID main app
			##### Suck config values into a dictionary #####
			configdict = self.tinyxmltodict(self.root)['config']
			##### Publish individual global settings values variables in main namespace #####
			try:
				mungeconfig = configdict['globalsettings']['munge']
				tomunge = True
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********SUCCESSFULLY IMPORTED THE MUNGE CONFIGURATION***********\n", self.ui.green)
			except KeyError:
				tomunge = False
			try:
				logfile = configdict['globalsettings']['paths']['logfile']
				self.logwriter("normal", "***********INITIAL WRITE TO THE LOG FILE: " + logfile + "...***********")
				self.logwriter("normal", "***********INITIALIZING VARIABLES FROM CONFIG FILE...***********")
				self.logwriter("normal", "Initialized variable:" "\t" + "logfile" + "\t\t\t\t" + "with value:" + "\t" + self.ui.color(logfile, self.ui.green))
				radiuslogpath = configdict['globalsettings']['paths']['radiuslogpath']
				self.logwriter("normal", "Initialized variable:" "\t" + "radiuslogpath" + "\t\t\t" + "with value:" + "\t" + self.ui.color(radiuslogpath, self.ui.green))
				acctlogcopypath = configdict['globalsettings']['paths']['acctlogcopypath']
				self.logwriter("normal", "Initialized variable:" "\t" + "acctlogcopypath" + "\t\t\t" + "with value:" + "\t" + self.ui.color(str(acctlogcopypath), self.ui.green))
				maxloglines = configdict['globalsettings']['logging']['maxloglines']
				self.logwriter("normal", "Initialized variable:" "\t" + "maxloglines" + "\t\t\t" + "with value:" + "\t" + self.ui.color(maxloglines, self.ui.green))
				ipaddressterm = configdict['globalsettings']['searchterms']['ipaddressterm']
				self.logwriter("normal", "Initialized variable:" "\t" + "ipaddressterm" + "\t\t\t" + "with value:" + "\t" + self.ui.color(ipaddressterm, self.ui.green))
				usernameterm = configdict['globalsettings']['searchterms']['usernameterm']
				self.logwriter("normal", "Initialized variable:" "\t" + "usernameterm" + "\t\t\t" + "with value:" + "\t" + self.ui.color(usernameterm, self.ui.green))
				delineatorterm = configdict['globalsettings']['searchterms']['delineatorterm']
				self.logwriter("normal", "Initialized variable:" "\t" + "delineatorterm" + "\t\t\t" + "with value:" + "\t" + self.ui.color(delineatorterm, self.ui.green))
				userdomain = configdict['globalsettings']['uidsettings']['userdomain']
				self.logwriter("normal", "Initialized variable:" "\t" + "userdomain" + "\t\t\t" + "with value:" + "\t" + self.ui.color(str(userdomain), self.ui.green))
				timeout = configdict['globalsettings']['uidsettings']['timeout']
				self.logwriter("normal", "Initialized variable:" "\t" + "timeout" + "\t\t\t\t" + "with value:" + "\t" + self.ui.color(timeout, self.ui.green))
				looptime = configdict['globalsettings']['misc']['looptime']
				self.logwriter("normal", "Initialized variable:" "\t" + "looptime" + "\t\t\t" + "with value:" + "\t" + self.ui.color(looptime, self.ui.green))
				tlsversion = configdict['globalsettings']['misc']['tlsversion']
				self.logwriter("normal", "Initialized variable:" "\t" + "tlsversion" + "\t\t\t" + "with value:" + "\t" + self.ui.color(tlsversion, self.ui.green))
				radiusstopaction = configdict['globalsettings']['misc']['radiusstopaction']
				self.logwriter("normal", "Initialized variable:" "\t" + "radiusstopaction" + "\t\t" + "with value:" + "\t" + self.ui.color(radiusstopaction, self.ui.green))
			except KeyError:
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************WARNING: Could not import some important settings****************\n", self.ui.yellow)
			try:
				##### Publish list of firewall targets into main namespace #####
				self.logwriter("normal", "***********INITIALIZING TARGETS...***********")
				targets = configdict['targets']['target']
				if type(targets) != type([]):
					targets = [targets]
			except KeyError:
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************WARNING: No Targets Exist in Configuration****************\n", self.ui.yellow)
		if mode == 'quiet':
			##### Suck config values into a dictionary #####
			configdict = self.tinyxmltodict(self.root)['config']
			##### Publish individual global settings values variables in main namespace #####
			try:
				mungeconfig = configdict['globalsettings']['munge']
				tomunge = True
			except KeyError:
				tomunge = False
			try:
				logfile = configdict['globalsettings']['paths']['logfile']
				radiuslogpath = configdict['globalsettings']['paths']['radiuslogpath']
				maxloglines = configdict['globalsettings']['logging']['maxloglines']
				userdomain = configdict['globalsettings']['uidsettings']['userdomain']
				timeout = configdict['globalsettings']['uidsettings']['timeout']
				looptime = configdict['globalsettings']['misc']['looptime']
				tlsversion = configdict['globalsettings']['misc']['tlsversion']
				radiusstopaction = configdict['globalsettings']['misc']['radiusstopaction']
				ipaddressterm = configdict['globalsettings']['searchterms']['ipaddressterm']
				usernameterm = configdict['globalsettings']['searchterms']['usernameterm']
				delineatorterm = configdict['globalsettings']['searchterms']['delineatorterm']
				acctlogcopypath = configdict['globalsettings']['paths']['acctlogcopypath']
			except Exception as e:
				return "WARNING: Could not import some important settings"
			try:
				##### Publish list of firewall targets into main namespace #####
				targets = configdict['targets']['target']
				if type(targets) != type([]):
					targets = [targets]
			except KeyError:
				return "WARNING: No Targets Exist in Configuration"
	##### Show formatted configuration item #####
	def show_config_item(self, mainmode, submode, itemname):
		if mainmode == "xml":
			try:
				for value in self.root.iter(itemname):
					xmldata = self.formatxml(ElementTree.tostring(value, encoding="us-ascii", method="xml"))
					regexnewline = "\n.*[a-z]"
					newline = re.findall(regexnewline, xmldata, flags=0)
					if len(newline) > 0:
						regexlastline = ".*</%s>" % itemname
						regexlastelement = "</%s>" % itemname
						lastline = re.findall(regexlastline, xmldata, flags=0)[0]
						lastelement = re.findall(regexlastelement, xmldata, flags=0)[0]
						indent = lastline.replace(lastelement, "")
						print indent + xmldata
					else:
						print "\t\t" + xmldata
			except AttributeError:
				print self.ui.color("\n\n***** FATAL ERROR ****\n", self.ui.red)
				print self.ui.color("You are running an old version of xml.etree.ElementTree. Please run " + runcmd + " request xml-update\n", self.ui.red)
				print self.ui.color("Please run the command '", self.ui.red) + self.ui.color(runcmd + " request xml-update", self.ui.cyan) + self.ui.color("' to update the module for RadiUID\n\n", self.ui.red)
		elif mainmode == "set":
			if submode == "installed":
				prepend = "radiuid"
				header = "\n"\
					"#######################################################\n"\
					"#### Set Commands to use when RadiUID is installed ####\n"\
					"#######################################################\n"
			elif submode == "uninstalled":
				prepend = "python radiuid.py"
				header = "\n"\
					"###########################################################\n"\
					"#### Set Commands to use when RadiUID is NOT installed ####\n"\
					"###########################################################\n"
			elif submode == "auto":
				prepend = runcmd
				header = "\n"\
					"##################################################\n"\
					"#### Set Commands to use to configure RadiUID ####\n"\
					"##################################################\n"
			rawtargetsetlist = []
			try:
				for target in targets:
					setparams = ""
					for param in target:
						if param != "hostname" and param != "vsys":
							setparams = setparams + param + " " + target[param] + " "
					rawtargetsetlist.append(" set target " + target["hostname"] + ":vsys" + target["vsys"] + " " + setparams)
			except NameError:
				rawtargetsetlist = False
			#### Compile set commands for FreeRADIUS clients ####
			clients = self.freeradius_client_editor("show", "")
			setclientlist = []
			if "FATAL" not in clients:
				setclientlist = []
				for client in clients:
					setclientlist.append(" set client " + client['Family'] + " " + client['IP Block'] + " " + client['Shared Secret'])
			#### Compile set commands for uninstalled and installed CLI format ####
			setmunge = ""
			if tomunge:
				for line in self.show_munge_config_set():
					setmunge += prepend + " " + line + "\n!\n"
			settargets = ""
			if rawtargetsetlist:
				for settarget in rawtargetsetlist:
					settargets += prepend + settarget + "\n!\n"
			setclients = ""
			if setclientlist != []:
				for setclient in setclientlist:
					setclients += prepend + setclient + "\n!\n"
			if userdomain == None:
				userdomaintext = "none"
			else:
				userdomaintext = userdomain
			setcommands = \
				"" + prepend + " set radiuslogpath " + radiuslogpath + "\n!\n"\
				"" + prepend + " set acctlogcopypath " + str(acctlogcopypath) + "\n!\n"\
				"" + prepend + " set logfile " + logfile + "\n!\n"\
				"" + prepend + " set maxloglines " + maxloglines + "\n!\n"\
				"" + prepend + " set userdomain " + userdomaintext + "\n!\n"\
				"" + prepend + " set timeout " + timeout + "\n!\n"\
				"" + prepend + " set looptime " + looptime + "\n!\n"\
				"" + prepend + " set tlsversion " + tlsversion + "\n!\n"\
				"" + prepend + " set radiusstopaction " + radiusstopaction + "\n!\n"
			#### Compile all set commands for different formats ####
			textconfig = ""
			textconfig += header + "!\n" + setcommands + "!\n"
			textconfig += prepend + " clear client all\n!\n" + setclients + "!\n"
			if tomunge:
				textconfig += prepend + " clear munge all\n!\n" + setmunge + "!\n"
			textconfig += prepend + " clear target all\n!\n" + settargets
			textconfig += "!\n!\n###########################################################\n"
			textconfig += "###########################################################\n"
			return textconfig
	##### Pull individual configuration item and return to calling function #####
	def get_globalconfig_item(self, elementname):
		for value in self.root.iter(elementname):
			return str(value.text)
	##### Change individual configuration item to a different value #####
	##### Do not use for targets. Only global settings #####
	def change_config_item(self, itemname, newvalue):
		for value in self.root.iter(itemname):
			value.text = newvalue
	##### Update the configuration file schema with new required elements #####
	def extend_config_schema(self):
		for element in list(self.root):  # For each XML element in the config root
			if element.tag == 'globalsettings':  # If its tag is 'globalsettings'
				globalsettings = element  # Mount that element as the globalsettings variable
		##### Get current munge rules #####
		if len(self.root.findall('.//misc')) == 0: # If <misc> XML elements do not exist
			self.ui.progress("Extending Config Schema: ", 1)
			misc = ElementTree.SubElement(globalsettings, 'misc')  # Mount a new misc element in the config
			looptime = ElementTree.SubElement(misc, 'looptime')
			looptime.text = "10"
			tlsversion = ElementTree.SubElement(misc, 'tlsversion')
			tlsversion.text = "1.2"
			stop_action = ElementTree.SubElement(misc, 'radiusstopaction')
			stop_action.text = "clear"
		if len(self.root.findall('.//acctlogcopypath')) == 0: # If <acctlogcopypath> XML elements do not exist
			self.ui.progress("Extending Config Schema: ", 1)
			for element in list(globalsettings):
				if element.tag == 'paths':
					paths = element
			acctlogcopypath = ElementTree.SubElement(paths, 'acctlogcopypath')
			acctlogcopypath.text = None

	##### Add or edit target firewalls in XML configuration elements #####
	##### Input is a list of dictionaries which contain any number of parameters for a firewall target, but a hostname parameter is required #####
	##### Method will detect if the 'targets' element already exists and will create it if it doesn't #####
	##### Result is a dictionary where keys are the hostnames of the processed targets with messages in the values #####
	def add_targets(self, targetlist):
		result = {} # Initialize Result
		if len(self.root.findall('.//target')) == 0: # If <target> XML elements do not exist
			targets = ElementTree.SubElement(self.root, 'targets') # Mount new <targets> element as variable
		targets = self.root.findall('.//targets')[0] # Mount targets element as targets
		for targetitem in targetlist: # For each dict entry in the target list input as an arg...
			currenttargethostname = targetitem["hostname"]
			currenttargetvsys = targetitem["vsys"]
			result[currenttargethostname] = {"status": "processing", "messages": []} # Create a new key in the result for this targetitem
			##### Does this target already exist, or do we need to create it new? #####
			targetalreadyexists = False # Initialize variable to determine if the target already exists
			for existingtarget in self.root.findall('.//target'): # For each existing target object in a list (empty list returned if none found)
				if targetitem["hostname"] == existingtarget.findall("hostname")[0].text and targetitem["vsys"] == existingtarget.findall("vsys")[0].text:
					targetalreadyexists = True # Then set the targetalreadyexists value as True
					target = existingtarget # And mount the existing target (where the hostname matched) as target
			##### If the target to be edited exists already #####
			if targetalreadyexists: # If target exists..
				result[currenttargethostname]["messages"].append("Editing existing target") # Create feedback message
				targetitem.pop("hostname") # Remove the 'hostname' parameter from the list of edits to be made
				targetitem.pop("vsys") # Remove the 'vsys' parameter from the list of edits to be made
				#### Make edits to already existing parameters first #####
				for parameter in list(targetitem): # For each of the parameters to be edited for the current target to be edited..
					for existingparameter in target: # And for each existing parameter in the existing target
						if existingparameter.tag == parameter: # If the parameter to be edited matches an existing parameter in the existing target...
							result[currenttargethostname]["messages"].append("Changed existing <" + parameter + "> parameter from '" + existingparameter.text + "' to '" + targetitem[parameter] + "'") # Create feedback message
							existingparameter.text = targetitem[parameter] # Edit the value of the parameter in place
							del targetitem[parameter] # Then delete this parameter edit from the list
				##### Then create the not-yet-existing parameters and set the appropriately #####
				if targetitem > 0: # If there are parameter edits which didn't yet exist
					for parameter in targetitem: # For each of those parameter edits
						currentelement = ElementTree.SubElement(target, parameter) # Create the parameter in the target element
						currentelement.text = targetitem[parameter] # Set the value of the parameter
						result[currenttargethostname]["messages"].append("Created new <" + parameter + "> parameter with value '" + targetitem[parameter] + "'") # Create feedback message
			else: # If target doesn't yet exist
				target = ElementTree.SubElement(targets, 'target') # mount new target element as variable
				result[currenttargethostname]["messages"].append("Created new target") # Create feedback message
				##### Add the different elements for the target #####
				hostname = ElementTree.SubElement(target, 'hostname') # Create and mount the hostname parameter for the target
				hostname.text = targetitem['hostname'] # Set the hostname parameter value for the target
				del hostname # Unmount the hostname parameter element
				del targetitem['hostname'] # Remove the hostname parameter
				vsys = ElementTree.SubElement(target, 'vsys') # Create and mount the vsys parameter for the target
				vsys.text = targetitem['vsys'] # Set the vsys parameter value for the target
				del vsys # Unmount the vsys parameter element
				del targetitem['vsys'] # Remove the hostname parameter
				for parameter in targetitem: # For each of the parameter edits
					currentelement = ElementTree.SubElement(target, parameter) # Create the parameter in the target element
					currentelement.text = targetitem[parameter] # Set the value of the parameter
					result[currenttargethostname]["messages"].append("Created new <" + parameter + "> parameter with value '" + targetitem[parameter] + "'") # Create feedback message
			del targetalreadyexists
			del target
			del currenttargethostname
		del targets
		##### Format Targets #####
		globalsettings = self.root.findall('.//globalsettings')[0] # Mount the <globalsettings> element
		globalsettings.tail = "\n\t" # Set the tail to properly indent "<targets>"
		del globalsettings # Unmount the globalsettings element
		targets = self.root.findall('.//targets')[0] # Mount the <targets> element
		targets.text = "\n\t\t" # Set proper indent for first child <target> element
		targets.tail = "\n" # Set proper indent for ending </config> element
		targetpointer = len(list(targets)) # Get the number of child <target> elements
		for target in list(targets): # For each <target> element in <targets>
			target.text = "\n\t\t\t" # Set the indent of the first parameter
			parameterpointer = len(list(target)) # Get the number of child parameter elements
			for parameter in list(target): # For each parameter element
				if parameterpointer == 1: # If this is the last parameter in the target
					parameter.tail = "\n\t\t" # Set smaller indent
				else: # If this is NOT the last parameter in the target
					parameter.tail = "\n\t\t\t" # Set larger indent
					parameterpointer = parameterpointer - 1 # And subtract one from the pointer
			if targetpointer == 1: # If this is the last target in targets
				target.tail = "\n\t" # Set smaller indent
			else: # If this is NOT the last target in targets
				target.tail = "\n\t\t" # Set larger indent
				targetpointer = targetpointer - 1 # And subtract one from the pointer
		del targets
		del parameterpointer
		del targetpointer
		return result
	##### Remove specific list of targets from config #####
	##### Method accepts a list of dictionaries which contain at least the hostname key/value pair anbd vsys id of the target #####
	def remove_targets(self, targetlist):
		result = ["fail"] # Start with failed result
		if len(self.root.findall('.//target')) == 0: # If no targets exist in config, return error
			result.append("No firewall targets exist. Nothing to remove")
		else: # if some targets do exist in config
			for removalitem in targetlist: # for each host listed for removal
				hostresult = 'failure' # initialize hostresult in case host is not found for removal
				for target in self.root.findall('.//target'): # for each target element
					if target.findall("hostname")[0].text == removalitem['hostname'] and target.findall("vsys")[0].text == removalitem['vsys']:
						targets = self.root.findall('.//targets')[0] # mount <targets> element
						targets.remove(target) # remove this <target> element from the <targets> element
						del targets # unmount <targets> element
						hostresult = 'success' # set successful hostresult
						result[0] = "pass"
				if hostresult == 'failure': # if we did not find the target to be removed
					result.append("Could not find target" + removalitem['hostname']) # return an error message
		##### If we did not remove the last <target> element from <targets>, then set the proper tail indent on last <target> element
		if len(self.root.findall('.//target')) > 0:
			lasttarget = self.root.findall('.//target')[len(self.root.findall('.//target')) - 1] # mount the last existing <target> element as variable
			lasttarget.tail = "\n\t" # adjust formatting on tail of last </target> element
			del lasttarget # unmount last <target> element
		else: # If we just removed the last <target> element from <targets>
			self.clear_targets() # use the 'clear_targets' method to remove the left over elements from the config
		if result[0] == "pass" and len(result) > 1:
			result[0] = "partial"
		return result
	##### Delete all firewall targets in mounted config #####
	def clear_targets(self):
		for item in self.root.iter('targets'):
			self.root.remove(item)
		for item in self.root.iter('globalsettings'):
			item.tail = '\n'
	##### Recombine comment and XML config data into single string and write to config file #####
	def save_config(self):
		self.newconfig = self.configcomment + "\n" + self.formatxml(ElementTree.tostring(self.root))
		f = open(configfile, 'w')
		f.write(self.newconfig)
		f.close()
	##### Self-recursive method for XML conversion #####
	def tinyxmltodict_recurse(self, node):
		attributekey = "attributes" # Set the dictionary key name which will store XML attributes
		if len(list(node)) == 0 and len(node.items()) == 0: # If there are no more child elements, and no element attributes
			result = node.text # Set the element text as the result and return it
		else: # If there are children and/or attributes
			result = {} # Start with empty dict
			if len(node.items()) > 0: # If attributes exist for the element
				result.update({attributekey: {}}) # Create a nested dictionary which will store the attribute(s)
				result[attributekey].update(dict(node.items())) # Add the attributes to attribute dictionary
			for child in node: # For each child of this element node
				if child.tag not in list(result): # If this child element does not have an existing key
					result[child.tag] = self.tinyxmltodict_recurse(child) # Add the key and iterate again
				else: # If this child element does have an existing key
					if type(result[child.tag]) != type([]): # And it is not already a list
						result[child.tag] = [result[child.tag], self.tinyxmltodict_recurse(child)] # Nest it in a list and iterate again
					else: # If it is already a list
						result[child.tag].append(self.tinyxmltodict_recurse(child)) # Append to that list
		return result
	##### Simple starter method for the XML to Dict conversion process #####
	def tinyxmltodict(self, inputdata):
		if "<" not in str(inputdata): # If the 'less than' symbol is not in the inputdata, it is likely a file path (don't use "<" in your file names, damnit!)
			with open(inputdata, 'r') as filetext: # Open file in read mode
				xmldata = filetext.read() # Suck in text of file
				filetext.close() # And close the file
		elif 'class' in str(type(inputdata)):
			xmldata = ElementTree.tostring(inputdata)
		else: # If "<" is in the inputdata, then you are likely inputting XML data as a string
			xmldata = inputdata # So set the xmldata variable as your string input
		root = ElementTree.fromstring(xmldata) # Mount the root element
		return {root.tag: self.tinyxmltodict_recurse(root)} # Set root element name as key and start first iteration
	def tinydicttoxml_recurse(self, node, dictdata):
		attributekey = "attributes" # Set the dictionary key name you used to store XML attributes
		for element in dictdata: # For each element in the input dictionary
			if element == attributekey: # If this dictionary key matches the key used to store XML element attributes
				for attribute in dictdata[element]: # For each attribute in the dictionary
					node.set(attribute, dictdata[element][attribute]) # Set the attribute for the element
			elif type(dictdata[element]) == type(None): # If this is an empty element
				newnode = ElementTree.SubElement(node, element) # Create a new XML subelement named by the input dict key
			elif type(dictdata[element]) == type(""): # If this value is a string
				newnode = ElementTree.SubElement(node, element) # Create a new XML subelement named by the input dict key
				newnode.text = dictdata[element] # And set the text of the element as the string value
			elif type(dictdata[element]) == type({}): # If this value is a dictionary
				newnode = ElementTree.SubElement(node, element) # Create a new XML subelement named by the dict key
				ElementTree.SubElement(newnode, self.tinydicttoxml_recurse(newnode, dictdata[element])) # And re-run the method with dict value as input
			elif type(dictdata[element]) == type([]): # If this value is a list
				for entry in dictdata[element]: # For each entry in the list
					if type(entry) == type({}): # If the list entry is a dict
						newnode = ElementTree.SubElement(node, element) # Create a new XML subelement named by the dict key
						ElementTree.SubElement(newnode, tinydicttoxml_recurse(newnode, entry)) # And re-run the method with list entry as input
					elif type(entry) == type(""):# If the list entry is a string
						newnode = ElementTree.SubElement(node, element) # Create a new XML subelement named by the input dict key
						newnode.text = entry # And set the element text as the string entry
	def tinydicttoxml(self, dictdata):
		if type(dictdata) != type({}) or len(list(dictdata)) > 1: # If the input is not a dict or has multiple keys
			dictdata = {"root": dictdata} # Nest it in a new dictionary with one key named 'root'
		xmlroot = ElementTree.Element(list(dictdata)[0]) # Create the root element using the dict key as the tag
		self.tinydicttoxml_recurse(xmlroot, dictdata[list(dictdata)[0]]) # Run the recursive method to iterate the dictionary
		return ElementTree.tostring(xmlroot).decode('UTF-8') # Then return a string output of the assembled XML object
	def formatxml_recurse(self, node):
		global currentindent,formatroot # Set indent length and text as global variables
		currentindent += 1 # Add 1 to the indentation length
		nodenum = len(list(node)) # Count the number of child elements in the current node
		if nodenum != 0: # If there are children
			for child in list(node): # For each child in the current node
				if (child.text == None or len(child.text) == (child.text.count(" ")+
				child.text.count("\n")+child.text.count("\t"))) and len(list(child)) != 0: # If the child element has no value data and grandchildren exist
					child.text = "\n" + currentindent * indenttext # Set the indent for the next grandchild element
				if nodenum == 1: # If this is the last child in the list of children
					child.tail = "\n" + (currentindent - 2) * indenttext # Set a shortened indent for the end of the parent tag
				else: # If this is not the last child in the list of children
					child.tail = "\n" + (currentindent - 1) * indenttext # Set a slightly shortened indent for the next child
				nodenum -= 1 # Subtract one from the number of children
				self.formatxml_recurse(child) # Reiterate the method on each child element
		currentindent -= 1 # Subtract one from the current indentation length
		return node
	def formatxml(self, xmldata):
		global currentindent,indenttext # Set indent length and text as global variables
		##### Set XML formatting info #####
		indenttext = "\t" # Set the text to use for indenting here
		###################################
		currentindent = 1 # Initialize indentation as 1
		root = ElementTree.fromstring(xmldata) # Mount the XML data to an element tree as "root"
		if len(list(root)) != 0: # If there are children in this element
			root.text = "\n" + indenttext # Set initial indent of first child element
		result = ElementTree.tostring(self.formatxml_recurse(root)) # Set the result text by calling the recursive method
		del currentindent,indenttext # Delete the temporary indent variables
		return result.decode('UTF-8') # Return the formatted text decoded to UTF-8
	##### Method to trim the top off a file to meet a certain line length #####
	def log_trimmer(self, filepath, linecount):
		report = {"status": "processing", "messages": {}}
		try:
			linelist = open(filepath).readlines(  )
			if len(linelist) > linecount:
				firstline = len(linelist) - linecount
				newtext = ""
				for index in range(len(linelist))[firstline + 1:]:
					newtext += linelist[index]
				newfile = open(filepath, "w")
				newfile.write(newtext)
				newfile.close
				report["messages"].update({"OK": "File " + filepath + " trimmed by " + str(firstline) + " lines"})
				report["status"] = "SUCCESS"
			else:
				report["messages"].update({"OK": "File " + filepath + " is under max size. Leaving it alone"})
				report["status"] = "SUCCESS"
		except IOError:
			report["messages"].update({"FATAL": "File " + filepath + " does not exist"})
			report["status"] = "FAIL"
		return report
	##### Mode can be append, clear, or show #####
	def freeradius_client_editor(self, mode, enteredclients):
		try:
			clientfilelines = open(clientconfpath).readlines(  )
		except IOError:
			return "FATAL: File " + clientconfpath + " does not exist"
		firstline = 1
		for line in clientfilelines:
			if line == "###################### RadiUID Generated Settings #####################\n":
				break
			else:
				firstline += 1
		radclientdatalist = clientfilelines[firstline - 1:]
		if mode == "append":
			if len(clientfilelines) == firstline - 1:
				clientfilelines.append("###################### RadiUID Generated Settings #####################\n")
				clientfilelines.append("################### Be Careful When Changing Manually #################\n")
			for entry in enteredclients:
				if entry["Family"] == "ipv4":
					fam = "ipv4addr"
				elif entry["Family"] == "ipv6":
					fam = "ipv6addr"
				else:
					return "FATAL: Unknown IP family %s" % entry["Family"]
				clientfilelines.append('\n')
				clientfilelines.append('client ' + entry["IP Block"] + ' {\n')
				clientfilelines.append('    '+fam+'    = ' + entry["IP Block"] + '\n')
				clientfilelines.append('    secret      = ' + entry["Shared Secret"] + '\n')
				clientfilelines.append('    shortname   = Created_By_RadiUID\n')
				clientfilelines.append(' }\n')
			newfiledata = ""
			for line in clientfilelines:
				newfiledata += line
			f = open(clientconfpath, "w")
			f.write(newfiledata)
			f.close()
			return "SUCCESS"
		if mode == "show":
			del radclientdatalist[0:3]
			result = []
			while len(radclientdatalist) > 0:
				if "    ipv" in radclientdatalist[1]:
					ipwords = radclientdatalist[1].split(" ")
					ipblock = ipwords[len(ipwords)-1]
					ipblock = ipblock.replace("\n", "")
					family = ipwords[4]
					family = family.replace("addr", "")
					secwords = radclientdatalist[2].split(" ")
					secret = secwords[len(secwords)-1]
					secret = secret.replace("\n", "")
					result.append({"IP Block": ipblock, "Shared Secret": secret, "Family": family})
					del ipblock,secret,radclientdatalist[0:6]
				else:
					ipblock = radclientdatalist[0]
					ipblock = ipblock.replace("client ", "")
					ipblock = ipblock.replace(" {\n", "")
					secret = radclientdatalist[1]
					secret = secret.replace("    secret      = ", "")
					secret = secret.replace("\n", "")
					result.append({"IP Block": ipblock, "Shared Secret": secret, "Family": "ipv4"})
					del ipblock,secret,radclientdatalist[0:5]
			return result
		if mode == "showraw":
			del radclientdatalist[0:3]
			result = ""
			for line in radclientdatalist:
				result += line
			return result
		if mode == "clear":
			if enteredclients == []:
				newfiledata = ""
				for line in clientfilelines[:firstline - 1]:
					newfiledata += line
				f = open(clientconfpath, "w")
				f.write(newfiledata)
				f.close()
			elif type(enteredclients) == type([]):
				currentclients = self.freeradius_client_editor("show", "")
				newclients = []
				for currentclient in currentclients:
					if currentclient["IP Block"] != enteredclients[0]["IP Block"]:
						newclients.append(currentclient)
				self.freeradius_client_editor("clear", [])
				self.freeradius_client_editor("append", newclients)
			return "SUCCESS"
	##### Sort string values in a list by the numerical values in those strings #####
	##### Input is a list of strings, each string having numbers, output is a sorted list #####
	##### Used to sort index values for the munge method #####
	def sortlist(self, list):
		nums = []  # Initialize a list for the numbers
		mappings = {}  # Initialize a mapping KV store for numbers mapped to the original strings
		result = []  # Initialize the result
		nonums = []  # Initialize a list for entries with no numbers
		for entry in list:  # For each entry in the list of strings
			if len(re.findall('[0-9]+', entry)) != 0:  # If there are numbers in this entry
				num = int(re.search('[0-9]+', entry).group(0))  # Grab the first set of contiguous digits as a value
				mappings.update({num: entry})  # Enter that integer as a key in the KV store with the original string as the value
				nums.append(int(num))  # Enter that integer in a list to be sorted later
			else:  # If there are no numbers in this entry
				nonums.append(entry)  # Append it to the list of entries with no numbers
		nums.sort()  # Sort the list of integers by their decimal value
		for num in nums:  # For each integer in the list of numbers
			result.append(mappings[num])  # Look up its mapping and put the original value in the result list
		for nonum in nonums:
			result.append(nonum)
		return result
	def show_munge_config_set(self):
		result = []
		for element in list(self.root):  # For each XML element in the config root
			if element.tag == 'globalsettings':  # If its tag is 'globalsettings'
				globalsettings = element  # Mount that element as the globalsettings variable
		mungeexists = False
		for element in list(globalsettings):
			if element.tag == 'munge':
				munge = element
				mungeexists = True
		if not mungeexists:
			return []
		else:
			for rule in list(munge):
				rulenum = rule.tag.replace("rule", "")
				for step in rule:
					setvar = False
					if step.tag == 'match':
						if list(step)[0].tag == 'any':
							result.append("set munge "+rulenum+".0 match any")
						else:
							for element in step:
								if element.tag == "criterion":
									criterion = element.text
								elif element.tag == "regex":
									if "\\" in element.text:  # Adjust backslashes so it presents correctly as a set command
										regexlist = list(element.text)
										newregex = ""
										index = 0
										for each in regexlist:
											if each == "\\":
												regexlist[index] = "\\\\"
												index += 1
											else:
												index += 1
										for each in regexlist:
											newregex += each
										regex = newregex
									else:
										regex = element.text
							result.append('set munge '+rulenum+'.0 match "'+regex+'" '+criterion)
					else:
						stepnum = step.tag.replace("step", "")
						simpleactions = ['accept', 'discard']
						for entry in list(step):
							if entry.tag in simpleactions:
								result.append('set munge '+rulenum+'.'+stepnum+' '+entry.tag)
							else:
								if 'from-match' in entry.tag and len(list(entry)) > 0:
									setvar = True
									sourcetype = entry.tag
									source = "any"
								elif 'from-' in entry.tag:
									setvar = True
									sourcetype = entry.tag
									source = entry.text
									if "\\" in source:  # Adjust backslashes so it presents correctly as a set command
										regexlist = list(source)
										newregex = ""
										index = 0
										for each in regexlist:
											if each == "\\":
												break
											else:
												index += 1
										regexlist[index] = "\\\\"
										for each in regexlist:
											newregex += each
										source = newregex
								elif 'set-variable' in entry.tag:
									setvar = True
									var = entry.text
								elif 'assemble' in entry.tag:
									vardict = {}
									varstring = ""
									for variable in list(entry):
										vardict.update({variable.tag: variable.text})
									for var in self.sortlist(vardict.keys()):
										varstring += " "+vardict[var]
									result.append('set munge '+rulenum+'.'+stepnum+' assemble'+varstring)

					if setvar:
						if source == "any":
							result.append('set munge '+rulenum+'.'+stepnum+' set-variable '+var+' '+sourcetype+' '+source)
						else:
							result.append('set munge '+rulenum+'.'+stepnum+' set-variable '+var+' '+sourcetype+' "'+source+'"')


		return result
	def munge_config(self, input):
		result = {'status': 'working', 'messages': []} # Initialize Result Status Information
		##### Mount the globalsettings element #####
		for element in list(self.root):  # For each XML element in the config root
			if element.tag == 'globalsettings':  # If its tag is 'globalsettings'
				globalsettings = element  # Mount that element as the globalsettings variable
		##### Get current munge rules #####
		if len(self.root.findall('.//munge')) == 0: # If <munge> XML elements do not exist
			if 'clear' in input.keys():
				currentconfig = {'munge': {}}
			else:
				result['messages'].append({'OK': 'No munge config found. Created new munge config'})
				currentconfig = {'munge': input}  # Set the current munge config to the input
		else:  # If the <munge> element does exist
			result['messages'].append({'OK': 'Existing munge config found. Editing that config'})
			currentconfig = self.tinyxmltodict(ElementTree.tostring(self.root.findall('.//munge')[0]).decode('UTF-8'))  # Set the current config to the current rulebase
			result['messages'].append({'OK': 'Deleting all munge config to prepare for XML rebuild'})
			globalsettings.remove(globalsettings.findall('.//munge')[0])  # Remove the munge XML rules so they can be rebuilt
		if input == {}:
			result['messages'].append({'OK': 'Terminating before XML rebuild to remove all munge config'})
			result['status'] = 'OK'
			return result
		elif 'clear' in input.keys():
			if type(input['clear']) == type(''):  # If we are deleting a full rule
				try:
					rulename = input['clear']
					del currentconfig['munge'][input['clear']]
					result['messages'].append({'OK': 'Removed rule '+rulename+' from configuration'})
				except KeyError:
					result['messages'].append({'FATAL': 'Rule '+rulename+' does not exist in configuration!'})
			elif type(input['clear']) == type({}):  # If we are deleting just one step in a rule
				try:
					rulename = input['clear'].keys()[0]
					stepname = input['clear'][rulename]
					del currentconfig['munge'][rulename][stepname]
					result['messages'].append({'OK': 'Removed rule '+rulename+', step '+stepname+' from configuration'})
				except KeyError:
					result['messages'].append({'FATAL': 'Rule '+rulename+', step '+stepname+' does not exist in configuration!'})
		else:
			for rulename in input:
				if rulename in currentconfig['munge'].keys():
					result['messages'].append({'OK': 'Rule '+rulename+' already exists in configuration. Updating it'})
					currentconfig['munge'][rulename].update(input[rulename])
				else:
					result['messages'].append({'OK': "Rule "+rulename+" doesn't exist yet. Creating it"})
					currentconfig['munge'].update(input)  # Update the current config with the new information
		##############################
		###### BUILD XML CONFIG ######
		##############################
		if currentconfig['munge'] == {}:  # If the config is just empty
			result['messages'].append({'OK': "Last rule removed. Terminating XML rebuild"})
		else:
			result['messages'].append({'OK': "Beginning rebuild of XML configuration"})
			result['messages'].append({'OK': "Config to build: "+str(currentconfig)})
			munge = ElementTree.SubElement(globalsettings, 'munge')  # Mount a new munge element in the config
			rulelist = self.sortlist(currentconfig['munge'].keys())  # Create a sorted list of rule names
			for rulename in rulelist:
				if rulename == 'debug':
					rule = ElementTree.SubElement(munge, rulename)
				else:
					rule = ElementTree.SubElement(munge, rulename)
					### Set the rules match statement ###
					match = ElementTree.SubElement(rule, 'match')
					if 'any' in currentconfig['munge'][rulename]['match'].keys():
						any = ElementTree.SubElement(match, 'any')
					else:
						regex = ElementTree.SubElement(match, 'regex')
						regex.text = currentconfig['munge'][rulename]['match']['regex']
						criterion = ElementTree.SubElement(match, 'criterion')
						criterion.text = currentconfig['munge'][rulename]['match']['criterion']
					### Walk through rule steps ###
					steplist = self.sortlist(currentconfig['munge'][rulename].keys())  # Create a sorted list of step names
					for stepname in steplist:
						if 'step' in stepname:
							step = ElementTree.SubElement(rule, stepname)
							### Set the parameters of this step ###
							steprules = currentconfig['munge'][rulename][stepname]
							for item in steprules:
								if item == "assemble":
									assemblevars = currentconfig['munge'][rulename][stepname][item]
									assemble = ElementTree.SubElement(step, item)
									for var in assemblevars:
										varelement = ElementTree.SubElement(assemble, var)
										varelement.text = currentconfig['munge'][rulename][stepname][item][var]
								elif item == "from-match" and type(currentconfig['munge'][rulename][stepname][item]) == type({}):  # If it is a 'from-match any'
									srule = ElementTree.SubElement(step, item)
									srule = ElementTree.SubElement(srule, 'any')
								else:
									srule = ElementTree.SubElement(step, item)
									srule.text = currentconfig['munge'][rulename][stepname][item]
		return result







################################################
########################## DATA PROCESSING CLASS ########################
#########################################################################
#######       Used by the main RadiUID methods to munge data      #######
#########################################################################
#########################################################################
class data_processing(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
		self.filemgmt = file_management()
		####################################################
	##### Search list of files for a searchterm and uses deliniator differentiate between log entries within the same file, then returns a dictionary where key=instance and value=line where term was found #####
	##### Used to search through FreeRADIUS log files for usernames and IP addresses, then turn them into dictionaries to be sent to the "push" function #####
	##### When the "[PARAGRAPH]" value is used as the delineatorterm value, it seperates the log entries using the empty "\n" line in between paragraphs
	def search_to_dict(self, filelist, delineator, searchterm):
		dict = {}
		entry = 0
		if delineator == "[PARAGRAPH]": # If the "[PARAGRAPH]" value is used as the delineatorterm value in the config file, use an empty line as the delineatorterm (paragraph seperation)
			for filename in filelist:
				self.filemgmt.logwriter("normal", 'Searching File: ' + filename + ' for ' + searchterm)
				filetext = open(filename).readlines(  )
				for line in filetext:
					if searchterm in line:
						dict[entry] = line
					elif line == "\n":
						entry = entry + 1
		else: # If the "[PARAGRAPH]" value is NOT used as the delineatorterm value in the config file
			for filename in filelist:
				self.filemgmt.logwriter("normal", 'Searching File: ' + filename + ' for ' + searchterm)
				with open(filename, 'r') as filetext:
					for line in filetext:
						if delineator in line:
							entry = entry + 1
						if searchterm in line:
							dict[entry] = line
		return dict
	##### Clean up IP addresses in dictionary #####
	##### Removes unwanted data from the lines with useful IP addresses in them #####
	def clean_ips(self, dictionary):
		newdict = {}
		ipaddress_regex = "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
		for key, value in dictionary.iteritems():
			cleaned = re.findall(ipaddress_regex, value, flags=0)[0]
			newdict[key] = cleaned
		self.filemgmt.logwriter("normal", "IP Address List Cleaned Up!")
		return newdict
	##### Clean up user names in dictionary #####
	##### Removes unwanted data from the lines with useful usernames in them #####
	def clean_names(self, dictionary):
		newdict = {}
		for key, value in dictionary.iteritems():
			if "'" in value:
				username_regex = "(\'.*\')"
				removequote = "'"
			elif '"' in value:
				username_regex = '(\".*\")'
				removequote = '"'
			words = value.split(" ")
			cleaned = words[len(words)-1]
			cleaned = cleaned[1:len(cleaned)-2]
			newdict[key] = cleaned
		self.filemgmt.logwriter("normal", "Username List Cleaned Up!")
		return newdict
	##### Clean up statuses in dictionary #####
	##### Removes unwanted data from the lines with useful statuses in them #####
	def clean_statuses(self, dictionary):
		newdict = {}
		for key, value in dictionary.iteritems():
			if "update" in value.lower():
				cleaned = "update"
			elif "start" in value.lower():
				cleaned = "start"
			elif "stop" in value.lower():
				cleaned = "stop"
			try:
				newdict[key] = cleaned
			except UnboundLocalError:
				self.filemgmt.logwriter("normal", self.ui.color("Unrecognized RADIUS Accounting status type! Dumping User-ID!", self.ui.red))
				self.filemgmt.logwriter("normal", self.ui.color("Status: '%s'" % value, self.ui.red))
		self.filemgmt.logwriter("normal", "Status List Cleaned Up!")
		return newdict
	##### Merge dictionary values from two dictionaries into one dictionary and remove duplicates #####
	##### Used to compile the list of users into a dictionary for use in the push function #####
	##### Deduplication is not explicitly written but is just a result of pushing the same data over and over to a dictionary #####
	def merge_dicts(self, ipdict, unamedict, statusdict):
		newdict = {}
		keydictkeylist = ipdict.keys()
		for each in keydictkeylist:
			try:
				uname = unamedict[each]
				ip = ipdict[each]
				status = statusdict[each]
				newdict[ip] = {"username": uname, "status": status}
			except KeyError:
				self.filemgmt.logwriter("normal", self.ui.color("Error detected in FreeRADIUS log. Looks like there were log entries missing the username, IP address, or delineatorterm", self.ui.red))
				self.filemgmt.logwriter("normal", self.ui.color("Skipping entry. Dump of dictionaries shown below.", self.ui.red))
				self.filemgmt.logwriter("normal", self.ui.color(str(ipdict), self.ui.red))
				self.filemgmt.logwriter("normal", self.ui.color(str(unamedict), self.ui.red))
		self.filemgmt.logwriter("normal", "Dictionary values merged into one dictionary")
		return newdict
	##### Search an ordered list of values for a list of search queries and return the indices for the locations of the queries #####
	##### Input is a list of search queries and the list of data to search through #####
	##### Output is a dictionary with found queries as keys and indices as the vals #####
	def find_index_in_list(self, querylist, listinput):
		result = {} # Initialize result as a dictionary
		for query in querylist: # For each search query, we run through the list once
			indexpointer = 0 # Start the indexpointer at the 0 index for this search of the list
			for entry in listinput:	# For each entry in the list...
				if query == entry:	# If the query value is the same as this entry in the list
					result.update({query: indexpointer}) # Add the query (key) and index location of where it was found
				indexpointer = indexpointer + 1 # Then update the indexpointer
		return result
	def map_consistency_check(self, uidxmldict):
		precordict = {}
		for uidset in uidxmldict:
			precordict.update({uidset: {}})
			currentuidset = ElementTree.fromstring(uidxmldict[uidset])
			if type(self.filemgmt.tinyxmltodict(currentuidset)['response']['result']) != type({}) or "<count>0</count>" in uidxmldict[uidset]:
				none = None
			else:
				if type(self.filemgmt.tinyxmltodict(currentuidset)['response']['result']['entry']) != type([]):
					uidentry = self.filemgmt.tinyxmltodict(currentuidset)['response']['result']['entry']
					precordict[uidset].update({uidentry['ip']: uidentry['user']})
				else:
					for uidentry in self.filemgmt.tinyxmltodict(currentuidset)['response']['result']['entry']:
						precordict[uidset].update({uidentry['ip']: uidentry['user']})
		###### Replace Fw Names with IDs and create master UID list #######
		fwidlist = []
		uiddict = {}
		alluids = []
		fwid = 1
		for fwname in precordict:
			fwidlist.append(str(fwid) + ":  " + fwname)
			uiddict.update({str(fwid): precordict[fwname]})
			for uid in precordict[fwname]:
				if uid + " : " + precordict[fwname][uid] not in alluids:
					alluids.append(uid + " : " + precordict[fwname][uid])
			fwid += 1
		###### Create corrolation dict #######
		corlist = []
		for uid in alluids:
			tempdict = {"UID": uid}
			for firewall in uiddict:
				entryexists = False
				for entry in uiddict[firewall]:
					if entry + " : " + uiddict[firewall][entry] == uid:
						entryexists = True
				if entryexists:
					tempdict.update({firewall: "X"})
				else:
					tempdict.update({firewall: " "})
			corlist.append(tempdict)
			del tempdict
			del uid
		###### Colorize entries ######
		for row in corlist:
			consistent = True
			for column in row:
				if column != "UID":
					if row[column] != "X":
						consistent = False
			if consistent:
				row["UID"] = self.ui.color(row["UID"], self.ui.green)
			else:
				row["UID"] = self.ui.color(row["UID"], self.ui.red)
			del consistent
		###### Create columnorder list ######
		columnorder = ["UID"]
		for column in range(len(uiddict) + 1)[1:]:
			columnorder.append(str(column))
		result = "################ FIREWALL IDENTIFIERS ################\n\n"
		for firewall in fwidlist:
			result += self.ui.color(firewall, self.ui.cyan) + "\n\n"
		result += "\n\n\n\n\n\n################ CONSISTENCY TABLE ################\n\n"
		result += self.ui.make_table(columnorder, corlist)
		return result
	##### Sort string values in a list by the numerical values in those strings #####
	##### Input is a list of strings, each string having numbers, output is a sorted list #####
	##### Used to sort index values for the munge method #####
	def sortlist(self, list):
		nums = []  # Initialize a list for the numbers
		mappings = {}  # Initialize a mapping KV store for numbers mapped to the original strings
		result = []  # Initialize the result
		nonums = []  # Initialize a list for entries with no numbers
		for entry in list:  # For each entry in the list of strings
			if len(re.findall('[0-9]+', entry)) != 0:  # If there are numbers in this entry
				num = int(re.search('[0-9]+', entry).group(0))  # Grab the first set of contiguous digits as a value
				mappings.update({num: entry})  # Enter that integer as a key in the KV store with the original string as the value
				nums.append(int(num))  # Enter that integer in a list to be sorted later
			else:  # If there are no numbers in this entry
				nonums.append(entry)  # Append it to the list of entries with no numbers
		nums.sort()  # Sort the list of integers by their decimal value
		for num in nums:  # For each integer in the list of numbers
			result.append(mappings[num])  # Look up its mapping and put the original value in the result list
		for nonum in nonums:
			result.append(nonum)
		return result
	##### Munge (manipulate) and filter strings from a list based on a rule set #####
	##### Input is a list of strings and a dictionary-based rule-set #####
	##### Output is a modified list of strings which have been manipulated based on the rule-set #####
	def munge(self, inputdatalist, mungeruledict):
		result = []  # Initialize the result list
		ruleindex = {'rules': []}  # Initialize the index of rules. Used to order the rules according to their values
		if 'debug' in mungeruledict.keys():  # If the 'debug' config element is present in the rule-set
			debug = True  # Set the debug variable as true
		else:  # Otherwise
			debug = False  # Set the debug variable as false
		for rule in mungeruledict:  # For each rule in the provided rule-set
			if 'rule' in rule:  # If the term 'rule' is in the key
				ruleindex['rules'].append(rule)  # Append that value to the index under 'rules'
				ruleindex.update({rule: []})  # Initialize a new key in the index with the rule name
				for step in mungeruledict[rule]:  # For each step in this rule
					if 'step' in step:  # If the term 'step' is in the key
						ruleindex[rule].append(step)  # Add the step to the list of steps under the current rule
				ruleindex[rule] = self.sortlist(ruleindex[rule])  # After all steps have been added to the rule, sort them
		ruleindex['rules'] = self.sortlist(ruleindex['rules'])  # After all rules have been added to the index, sort them
		if debug:  # If we are debugging
			print "\n\n----- Sorted index of rules and steps: %s -----" % str(ruleindex)  # Print the index of rules and steps
		for input in inputdatalist:  # For each input in the input list
			if debug:  # If we are debugging
				print "\n\n\n\n\n\n\n\n----- Input String: %s -----" % str(input)  # Notify of the input
			inputresult = input  # Set the modifiable variable for the current input
			added = False  # Create a variable to track if this input is done and has been added to the result list
			interrupt = "none"  # Create a variable to allow interruption of operations based on a rule step
			variables = {}  # Initialize a dictionary of variables for the current input (can be used across rules in the same input)
			for rule in ruleindex['rules']:  # For each rule in the provided rule-set
				if debug:  # If we are debugging
					print "\n\n\n\t----- %s -----" % str(rule)  # Print a header of the rule name
					print "\t\t----- Rule beginning with input: %s -----" % str(inputresult)  # Print th input being fed into this rule
				if interrupt == 'accept' or interrupt == 'discard':  # If something has set the interrupt to 'accept' or 'discard'
						break  # And break the loop for this rule so the modified input can be added to the result list
				currentrule = mungeruledict[rule]  # Pull the data for the current rule
				if debug:  # If we are debugging
					rulexml = self.filemgmt.formatxml(self.filemgmt.tinydicttoxml(currentrule))  # Convert the current rule to formatted XML
					rulexml = rulexml.replace("\n", "\n\t\t\t")  # Indent the XML lines
					rulexml = "\t\t\t" + rulexml  # Indent the first XML line
					print "\t\t----- Loaded Rule: -----"  # Print a header for the XML rule
					print rulexml  # And print the formatted rule
				if 'any' in currentrule['match'].keys():  # If the current rules match statement is a config element (which means it is 'any')
					inputmatches = True  # Notify that the input matches the rule's entry match pattern
				else:  # Otherwise
					if debug:  # If we are debugging
						matched = re.findall(currentrule['match']['regex'], str(inputresult))  # Set the regex match return value
						if matched == []:  # If it returned nothing
							matched = "None"  # Set it to a none string
						print "\t\t----- Rule match statement regex returned: -----"  # Print a header for the XML rule
						print "\t\t\t" + str(matched)  # Print out what regex returned for debugging
					if currentrule['match']['criterion'] == 'complete':  # If this rule requires a complete match of the input
						if str(inputresult) in re.findall(currentrule['match']['regex'], str(inputresult)):  # If the regex match returns the whole input
							inputmatches = True  # Notify that the input matches the match pattern
						else:  # Otherwise
							inputmatches = False # Notify that the input does not match the rule's entry match pattern
					elif currentrule['match']['criterion'] == 'partial':  # If this rule allows a partial match of the input
						if len(re.findall(currentrule['match']['regex'], str(inputresult))) > 0:  # If the regex match anything at all
							inputmatches = True  # Notify that the input matches the match pattern
						else:  # Otherwise
							inputmatches = False # Notify that the input does not match the rule's entry match pattern
				if inputmatches:  # If the input matched the rule entry match pattern
					if debug:  # If we are debugging
						print "\n\t\t----- Matched pattern %s for %s in input %s -----" % (str(currentrule['match']), str(rule),
						str(inputresult))  # Print that the input matched the rule entry match pattern and we have started rule processing
					for step in ruleindex[rule]:  # For each step in the current rule
						currentstep = mungeruledict[rule][step]  # Pull the data for the current step in this rule
						if debug:  # If we are debugging
							print "\n\t\t----- Loaded %s: %s -----" % (str(step), str(currentstep))  # Print the step configuration
						### NOTE: An 'accept' stops the munge on the current input and immediately adds it to the result list ###
						if currentstep.keys()[0] == 'accept':  # If the step is an 'accept'
							interrupt = "accept"  # Set the interrupt to 'accept'
							if debug:  # If we are debugging
								print "\t\t\t----- 'Accept' interrupt detected and set, breaking out of rule-set and adding input to result -----"  # Notify debug
							break  # Break out of the current step without continuing
						### NOTE: A 'discard' stops all processing and discards the current input ###
						elif currentstep.keys()[0] == 'discard':  # If the step is an 'discard'
							interrupt = "discard"  # Set the interrupt to 'discard'
							if debug:  # If we are debugging
								print "\t\t\t----- 'Discard' interrupt detected and set, breaking out of rule-set and discarding input -----"  # Notify debug
							break  # Break out of the current step without continuing
						elif 'set-variable' in currentstep.keys():  # If the current step sets a variable
							variablename = currentstep['set-variable']  # Grab the name of the variable
							if 'from-string' in currentstep.keys():  # If we are setting from a static string
								variablevalue = currentstep['from-string']  # Set the value based on the configured string
							elif 'from-match' in currentstep.keys():  # If we are setting the variable based on a regex match
								if type(currentstep['from-match']) == type({}):  # If the match statement is a config element (which means it is 'any')
									matches = True  # Notify that the input matches
									variablevalue = inputresult  # And set the value to the full input string
								else:  # Otherwise
									try:  # Try a regex search for the match
										if re.findall(currentstep['from-match'], inputresult)[0] != '':  # If regex returns anything but an empty string
											variablevalue = re.findall(currentstep['from-match'], inputresult)[0]  # Set the value as the returned string
									except IndexError:  # If regex returns nothing
										variablevalue = ''  # Set an empty string for the variable
							variables.update({variablename: variablevalue})  # And update the dictionary of variables
							if debug:  # If we are debugging
								if variablevalue == '':
									print "\t\t\t----- No match from regex, setting an empty string value for variable %s -----" % (str(variablename))  # Notify of variable name and new value
								else:
									print "\t\t\t----- Setting variable %s as value %s -----" % (str(variablename), str(variablevalue))  # Notify of variable name and new value
								print "\t\t\t----- Current variables in the variable list: %s -----" % str(variables)  # Print out current variables
						elif currentstep.keys()[0] == 'assemble':  # If the current step reassembles the input from some variables
							variableindex = currentstep['assemble'].keys()  # Grab the list of config elements assigned to the variable names
							variableindex = self.sortlist(variableindex)  # Sort the list of variable elements so we assemble them in the right order
							if debug:  # If we are debugging
								print "\t\t\t----- Assembling Variables: %s -----" % str(variableindex)  # Print list of variables for assembly
							assembleresult = ''  # Initialize the result of the assembly process
							for variableid in variableindex:  # For each variable config element name (ie: 'variable1') in the index
								try:  # Try statement to handle a keyerror exception in case we are trying to access a variable which hasnt been assigned
									variablename = currentstep['assemble'][variableid]  # Look up the name of the variable from the config
									variablevalue = variables[variablename]  # Look up the current value of the variable from the current dictionary
									assembleresult += variablevalue  # Append the current variable to the assembly result
								except KeyError:  # If we recieve a keyerror
									### NOTE: A KeyError will occur when the config tries to assemble from a variable which has not been configured in a previous step or rule
									if debug:  # If we are debugging
										print "\t\t\t#######  ERROR  ######: CANNOT FIND VARIABLE %s" % str(variablename)  # Print info about the error
										print "\t\t\t#######  ERROR  ######: MAKE SURE YOU HAVE A PREVIOUS STEP CONFIGURED TO CREATE IT"  # Print info about the error
							if debug:  # If we are debugging
								print "\t\t\t----- Assemble Result: %s -----" % str(assembleresult)  # Print the result of the assembly
							inputresult = assembleresult  # Set the result of the munge to the result of the assembly
				else:  # If the input did not match the rule entry match pattern
					if debug:  # If we are debugging
						print "\t\t----- No match in %s for input %s -----" % (str(rule), str(inputresult))  # Notify that no match was made for this input
			if interrupt != "discard":  # If the interrupt is not set to 'discard'
				if not added:  # And the input has not been added to the result list
					result.append(inputresult)  # Add the modified input to the result list
					added = True  # Notify that it has been added
					if debug:  # If we are debugging
						if interrupt == "accept":
							print "\t----- Input %s added to result due to 'accept' interrupt -----" % str(inputresult)  # Print of addition
						else:
							print "\t----- Input %s added to result due to implicit 'accept' at end of rules -----" % str(inputresult)  # Print of addition
						print "\t----- Current result list: -----"  # Header
						print "\t----- %s -----" % str(result)  # Print the current result list
		return result





#########################################################################
##################### PAN FIREWALL INTERACTION CLASS ####################
#########################################################################
#######     Used by the main RadiUID methods to for creating      #######
#######       and making REST API calls to the PAN Firewalls      #######
#########################################################################
class palo_alto_firewall_interaction(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
		self.filemgmt = file_management() #push_uids uses flmgmt to remove files after push
		self.dpr = data_processing()
	#######################################################
	#######         XML Processing Methods          #######
	####### Used for PAN Interaction XML Generation #######
	#######################################################
	##### Accepts a list of IP addresses (keys) and usernames (vals) in a dictionary and outputs a list of XML formatted entries as a list #####
	##### This method outputs a list which is utilized by the xml_assembler_v67 method #####
	def xml_formatter_v67(self, ipanduserdict, targetlist):
		xmldict = {}
		for target in targetlist:
			hostname = target['hostname'] + ":vsys" + target['vsys']
			xmldict[hostname] = []
			ipaddresses = ipanduserdict.keys()
			for ip in ipaddresses:
				username = ipanduserdict[ip]["username"]
				if userdomain == None:
					entry = '<entry name="%s" ip="%s" timeout="%s">' % (username, ip, timeout)
				else:
					entry = '<entry name="%s\%s" ip="%s" timeout="%s">' % (userdomain, username, ip, timeout)
				xmldict[hostname].append(entry)
				entry = ''
		return xmldict
	##### Accepts a list of XML-formatted IP-to-User mappings and produces a list of complete and encoded URLs which are used to push UID data #####
	##### Each URL will contain no more than 100 UID mappings which can all be pushed at the same time by the push_uids method #####
	def xml_assembler_v67(self, ipuserxmldict, targetlist):
		finishedurldict = {}
		for host in targetlist:
			xmluserdata = ""
			hostname = host['hostname']
			vsys = host['vsys']
			if "port" in host:
				port = host['port']
			else:
				port = "443"
			hostxmlentries = ipuserxmldict[hostname + ":vsys" + vsys]
			finishedurllist = []
			while len(hostxmlentries) > 0:
				for entry in hostxmlentries[:maxuidspercall]:
					xmluserdata = xmluserdata + entry + "\n</entry>\n"
					hostxmlentries.remove(entry)
				urldecoded = '<uid-message>\n\
	<version>1.0</version>\n\
	<type>update</type>\n\
	<payload>\n\
	<login>\n\
	' + xmluserdata + '\
	</login>\n\
	</payload>\n\
	</uid-message>'
				urljunk = urllib.quote_plus(urldecoded)
				finishedurllist.append('https://' + hostname + ":" + port + '/api/?key=' + host['apikey'] + '&type=user-id&vsys=vsys' + vsys +'&cmd=' + urljunk)
				xmluserdata = ""
			finishedurldict.update({hostname + ":vsys" + vsys: finishedurllist})
			del hostname
			del hostxmlentries
			del vsys
		return finishedurldict
	#######################################################
	#######         PAN Interaction Methods         #######
	#######        Used for PAN Interaction         #######
	#######################################################
	##### Function to pull API key from firewall to be used for REST HTTP calls #####
	##### Used during initialization of the RadiUID main process to generate the API key #####
	def pull_api_key(self, mode, targetlist):
		if type(targetlist) != type([]):
			self.filemgmt.logwriter("normal", self.ui.color('ERROR: API Key function requires a list as input' + '\n', self.ui.red))
			quit()
		for target in targetlist:
			encodedusername = urllib.quote_plus(target['username'])
			encodedpassword = urllib.quote_plus(target['password'])
			if "port" in target:
				port = target['port']
			else:
				port = "443"
			url = 'https://' + target['hostname'] + ":" + port + '/api/?type=keygen&user=' + encodedusername + '&password=' + encodedpassword
			try:
				try:
					gcontext = ssl.SSLContext(tlsobj)
					gcontext.check_hostname = False
					gcontext.verify_mode = ssl.CERT_NONE
					response = urllib2.urlopen(url, context=gcontext).read()
				except AttributeError:
					response = urllib2.urlopen(url).read()
			except urllib2.URLError:
				response = "FATAL: Firewall Inaccessible"
			if mode == "noisy":
				self.filemgmt.logwriter("normal", "Pulling API key using PAN from " + target['hostname'] + ":vsys" + target['vsys'] + " using credentials: " + target['username'] + "\\" + target['password'])
			if 'success' in response:
				if mode == "noisy":
					self.filemgmt.logwriter("normal", self.ui.color(response, self.ui.green))
				stripped1 = response.replace("<response status = 'success'><result><key>", "")
				stripped2 = stripped1.replace("</key></result></response>", "")
				pankey = stripped2
				target['apikey'] = pankey
				if mode == "noisy":
					self.filemgmt.logwriter("normal", "Added 'apikey': " + pankey + " attribute to host: " + target['hostname'] + ":vsys" + target['vsys'])
			elif "Firewall Inaccessible" in response:
				self.filemgmt.logwriter("normal", self.ui.color('ERROR: Firewall ' + target['hostname'] + ":vsys" + target['vsys'] + ' cannot be accessed at this time. Removing it as an active target' + '\n', self.ui.red))
				targetlist.remove(target)
				self.pull_api_key(mode, targetlist)
			elif "Invalid credentials" in response:
				self.filemgmt.logwriter("normal", self.ui.color('ERROR: Username\\password failed. Please re-enter in config file...' + '\n', self.ui.red))
				self.filemgmt.logwriter("normal", self.ui.color('Removing ' + target['hostname'] + ":vsys" + target['vsys'] + ' as an active target' + '\n', self.ui.red))
				targetlist.remove(target)
				self.pull_api_key(mode, targetlist)
	##### Accepts IP-to-User mappings as a dict in, uses the xml-formatter and xml-assembler to generate a list of URLS, then opens those URLs and logs response codes  #####
	def push_uids(self, ipanduserdict, filelist):
		removelist = []
		if radiusstopaction == "clear":
			self.filemgmt.logwriter("normal", "Processing RADIUS stop messages: Removing them from Palo Altos and clearing them from push tables")
			for entry in ipanduserdict:
				if ipanduserdict[entry]["status"] == "stop":
					removelist.append(entry)
					self.filemgmt.logwriter("normal", "Removing IP Address: " + self.ui.color(entry, self.ui.yellow) + "\t\tUsername: " + self.ui.color(ipanduserdict[entry]["username"], self.ui.yellow))
					response = self.clear_uids(targets, entry)
					for target in response:
						result = ""
						for table in response[target]:
							if "success" in response[target][table]:
								result += "      " + table + ":  " + self.ui.color("success", self.ui.green)
							else:
								result += "      " + table + ":  " + self.ui.color(response[target][table], self.ui.red)
						self.filemgmt.logwriter("normal", result)
		elif radiusstopaction == "ignore":
			self.filemgmt.logwriter("normal", "Ignoring RADIUS stop messages. Removing them from push table")
			for entry in ipanduserdict:
				if ipanduserdict[entry]["status"] == "stop":
					self.filemgmt.logwriter("normal", "Removing IP Address: " + self.ui.color(entry, self.ui.yellow) + "\t\tUsername: " + self.ui.color(ipanduserdict[entry]["username"], self.ui.yellow))
					removelist.append(entry)
		elif radiusstopaction == "push":
			self.filemgmt.logwriter("normal", "Pushing RADIUS stop messages. Leaving them in the push table")
		for rmentry in removelist:
			del ipanduserdict[rmentry]
		if tomunge:
			modipanduserdict = {}
			for entry in ipanduserdict:
				try:
					newuname = self.dpr.munge([ipanduserdict[entry]["username"]], mungeconfig)[0]
					status = ipanduserdict[entry]["status"]
					modipanduserdict.update({entry: {"username": newuname, "status": status}})
					if newuname == ipanduserdict[entry]["username"]:
						self.filemgmt.logwriter("normal", "Munge Engine left input: "+self.ui.color(ipanduserdict[entry]["username"], self.ui.cyan)+" alone")
					else:
						self.filemgmt.logwriter("normal", "Munge Engine modified input: "+self.ui.color(ipanduserdict[entry]["username"], self.ui.cyan)+"    into: "+self.ui.color(newuname, self.ui.cyan))
				except IndexError:
					self.filemgmt.logwriter("normal", "Munge Engine discarded input: "+self.ui.color(ipanduserdict[entry]["username"], self.ui.cyan))
		else:
			modipanduserdict = ipanduserdict
		xml_dict = self.xml_formatter_v67(modipanduserdict, targets)
		urldict = self.xml_assembler_v67(xml_dict, targets)
		for host in urldict:
			numofcalls = len(urldict[host])
			numofcallsorig = numofcalls
			self.filemgmt.logwriter("normal", "Pushing the below IP : User mappings to " + host + " via " + str(numofcalls) + " API calls")
			urllist = urldict[host]
			for entry in modipanduserdict:
				self.filemgmt.logwriter("normal", "IP Address: " + self.ui.color(entry, self.ui.cyan) + "\t\tUsername: " + self.ui.color(modipanduserdict[entry]["username"], self.ui.cyan))
			for eachurl in urllist:
				try:
					try:
						gcontext = ssl.SSLContext(tlsobj)
						gcontext.check_hostname = False
						gcontext.verify_mode = ssl.CERT_NONE
						response = urllib2.urlopen(eachurl, context=gcontext).read()
					except AttributeError:
						response = urllib2.urlopen(eachurl).read()
				except urllib2.HTTPError:
					response = "FATAL: Firewall Hung"
				except urllib2.URLError:
					response = "FATAL: Firewall Inaccessible"
				if "success" in response:
					self.filemgmt.logwriter("normal", self.ui.color("Successful UID push to " + host + " (" + str(numofcallsorig - numofcalls + 1) + "/" + str(numofcallsorig) + ")", self.ui.green))
				elif "Firewall Inaccessible" in response:
					self.filemgmt.logwriter("normal", self.ui.color('ERROR: Firewall ' + host + ' cannot be accessed at this time. Skipping it', self.ui.red))
				elif "Invalid credentials" in response:
					self.filemgmt.logwriter("normal", self.ui.color('ERROR: Username\\password failed. Please re-enter in config file...', self.ui.red))
					self.filemgmt.logwriter("normal", self.ui.color('Skipping the ' + host + ' target', self.ui.red))
				elif "Firewall Hung" in response:
					self.filemgmt.logwriter("normal", self.ui.color('ERROR: Firewall '+ host + ' seems to be hung. We will come back to it', self.ui.red))
					self.filemgmt.logwriter("normal", self.ui.color('Skipping the ' + host + ' target', self.ui.red))
				else:
					self.filemgmt.logwriter("normal", self.ui.color("Something may have gone wrong in push to " + host, self.ui.yellow))
					self.filemgmt.logwriter("normal", "REST call: " + self.ui.color(urllib.unquote(re.sub('https:.*api', "", eachurl)), self.ui.yellow))
					self.filemgmt.logwriter("normal", "Response: " + self.ui.color(response, self.ui.yellow))
				numofcalls -= 1
		self.filemgmt.remove_files(filelist)
	def pull_uids (self, targetlist):
		encodedcall = urllib.quote_plus("<show><user><ip-user-mapping><all></all></ip-user-mapping></user></show>")
		result = {}
		for target in targetlist:
			if "port" in target:
				port = target['port']
			else:
				port = "443"
			url = 'https://' + target['hostname'] + ":" + port + '/api/?key=' + target['apikey'] + "&type=op&vsys=vsys" + target['vsys'] + "&cmd=" + encodedcall
			try:
				gcontext = ssl.SSLContext(tlsobj)
				gcontext.check_hostname = False
				gcontext.verify_mode = ssl.CERT_NONE
				result.update({target['hostname'] + ":vsys" + target['vsys']: urllib2.urlopen(url, context=gcontext).read()})
			except AttributeError:
				result.update({target['hostname'] + ":vsys" + target['vsys']: urllib2.urlopen(url).read()})
			self.filemgmt.logwriter("normal", self.ui.color("Successfully pulled UID's from " + target['hostname'] + ":vsys" + target['vsys'], self.ui.green))
		return result
	def clear_uids (self, targetlist, userip):
		if userip == "all":
			encodedcall1 = "&type=op&cmd=" + urllib.quote_plus("<clear><user-cache><all></all></user-cache></clear>")
			encodedcall2 = "&type=op&cmd=" + urllib.quote_plus("<clear><user-cache-mp><all></all></user-cache-mp></clear>")
		else:
			encodedcall1 = urllib.quote_plus("<clear><user-cache><ip>" + userip + "</ip></user-cache></clear>")
			encodedcall2 = urllib.quote_plus("<clear><user-cache-mp><ip>" + userip + "</ip></user-cache-mp></clear>")
		result = {}
		for target in targetlist:
			if "port" in target:
				port = target['port']
			else:
				port = "443"
			url1 = 'https://' + target['hostname'] + ":" + port + '/api/?key=' + target['apikey'] + "&type=op&vsys=vsys" + target['vsys'] + "&cmd=" + encodedcall1
			url2 = 'https://' + target['hostname'] + ":" + port + '/api/?key=' + target['apikey'] + "&type=op&vsys=vsys" + target['vsys'] + "&cmd=" + encodedcall2
			result.update({target['hostname'] + ":vsys" + target['vsys']: {}})
			try:
				gcontext = ssl.SSLContext(tlsobj)
				gcontext.check_hostname = False
				gcontext.verify_mode = ssl.CERT_NONE
				result1 = urllib2.urlopen(url1, context=gcontext).read()
				result2 = urllib2.urlopen(url2, context=gcontext).read()
			except Exception as e:
				print(e)
				result1 = urllib2.urlopen(url1).read()
				result2 = urllib2.urlopen(url2).read()
			result[target['hostname'] + ":vsys" + target['vsys']].update({"DP-CLEAR": result1})
			result[target['hostname'] + ":vsys" + target['vsys']].update({"MP-CLEAR": result2})
		return result








#########################################################################
####################### RADIUID MAIN PROCESS CLASS ######################
#########################################################################
#######     Contains the primary elements which pulls config      #######
#######     variables, collects log data, and pushes mappings     #######
#########################################################################
class radiuid_main_process(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
		self.dpr = data_processing()
		self.pafi = palo_alto_firewall_interaction()
		self.filemgmt = file_management()
		####################################################
	##### Initialize method used to pull all necessary RadiUID information from the config file and dump the data into variables in the global namespace #####
	##### This method runs once during the initial startup of the program #####
	def initialize(self):
		print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********MAIN PROGRAM INITIALIZATION KICKED OFF...***********" + "\n"
		##### Scrub targets for any which have incomplete settings in the 'target' variable #####
		self.filemgmt.logwriter("normal", "***********STARTING UP USING RADIUID VERSION " + self.ui.color(version, self.ui.green) + "***********")
		self.filemgmt.logwriter("normal", "***********CHECKING TARGETS FOR INCOMPLETE OR INCORRECT CONFIGS***********")
		self.filemgmt.scrub_targets("noisy", "scrub")
		self.filemgmt.logwriter("normal", "***********LOADED THE BELOW TARGETS***********")
		self.filemgmt.logwriter("normal", "\n" + self.ui.indenter("\t\t\t", self.ui.make_table(["hostname", "vsys", "username", "password"], targets)))
		##### Initial log entry and help for anybody starting the .py program without first installing it #####
		self.filemgmt.logwriter("normal", "***********RADIUID INITIALIZING... IF PROGRAM FAULTS NOW, MAKE SURE YOU SUCCESSFULLY RAN THE INSTALLER ('python radiuid.py install')***********")
		##### Explicitly pull PAN key now and store API key in the main namespace #####
		self.filemgmt.logwriter("normal", "***********************************CONNECTING TO PALO ALTO FIREWALL TO EXTRACT THE API KEY...***********************************")
		self.filemgmt.logwriter("normal", "********************IF PROGRAM FREEZES/FAILS RIGHT NOW, THEN THERE IS LIKELY A COMMUNICATION PROBLEM WITH THE FIREWALL********************")
		pankey = self.pafi.pull_api_key("noisy", targets)
		self.filemgmt.logwriter("normal", "********************SUCCESSFULLY INITIALIZED THE FOLLOWING FIREWALLS********************")
		targetnum = 1
		for target in targets:
			self.filemgmt.logwriter("normal", str(targetnum) + ": " + (self.ui.color(target['hostname'] + ":vsys" + target['vsys'], self.ui.green)))
		self.filemgmt.logwriter("normal", "*******************************************CONFIG FILE SETTINGS INITIALIZED*******************************************")
		self.filemgmt.logwriter("normal", "***********************************RADIUID SERVER STARTING WITH INITIALIZED VARIABLES...******************************")
	##### RadiUID looper method which initializes the namespace with config variables and loops the main RadiUID program #####
	def looper(self):
		self.filemgmt.initialize_config("noisy")
		self.filemgmt.publish_config("noisy")
		self.initialize()
		while __name__ == "__main__":
			filelist = self.filemgmt.list_files("noisy", radiuslogpath)
			if len(filelist) > 0:
				usernames = self.dpr.search_to_dict(filelist, delineatorterm, usernameterm)
				ipaddresses = self.dpr.search_to_dict(filelist, delineatorterm, ipaddressterm)
				statustypes = self.dpr.search_to_dict(filelist, delineatorterm, "Acct-Status-Type")
				usernames = self.dpr.clean_names(usernames)
				ipaddresses = self.dpr.clean_ips(ipaddresses)
				statustypes = self.dpr.clean_statuses(statustypes)
				ipanduserdict = self.dpr.merge_dicts(ipaddresses, usernames, statustypes)
				self.pafi.push_uids(ipanduserdict, filelist)
				del filelist
				del usernames
				del ipaddresses
				del ipanduserdict
			time.sleep(int(looptime))






#########################################################################
################### INSTALLER/MAINTENANCE METHODS CLASS #################
#########################################################################
#######            Contains methods which are used by the         #######
#######                 Installer/Maintenance Utility             #######
#########################################################################
class imu_methods(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
		self.filemgmt = file_management()
		####################################################
	#######################################################
	#######          OS Interaction Methods           #####
	### Runs commands on the OS without file interaction ##
	#######################################################
	##### Get currently logged in user #####
	def currentuser(self):
		checkdata = commands.getstatusoutput("whoami")[1]
		return checkdata
	def get_processes(self, service):
		procdata = commands.getstatusoutput("ps -e")[1].splitlines()
		proclist = []
		index = 1
		for line in procdata[1:]:
			line = line.split(" ")
			while "" in line:
				line.remove("")
			if line[0] == str(os.getpid()):
				myline = str(index)
			else:
				proclist.append(line)
			index += 1
		matchlist = []
		for proc in proclist:
			if proc[3] == service:
				matchlist.append(proc[0])
		modprocdata = ""
		index = 0
		for line in procdata:
			if str(index) == myline:
				pass
			else:
				modprocdata += line + "\n"
			index += 1
		return {"procdata": procdata, "proclist": proclist, "matchlist": matchlist, "modprocdata": modprocdata}
	##### Multi Operating System Service Control #####
	##### Used to start, stop, restart, and check status of OS services (mainly freeradius and radiuid) #####
	##### Input is action (start, stop, restart, status) and service name #####
	##### Output is a dictionary of commands run, BASH output for each command, and service status #####
	def service_control(self, action, service):
		if systemd: # If the OS has SystemD
			mode = "commands"
			beforecmd = "systemctl status " + service # Set proper command to run before the action
			actioncmd = "systemctl " + action + " " + service # Set command which will perform the action
			aftercmd = "systemctl status " + service # Set proper command to run after the action
			activewords = ["active (running)"] # Set the keyword to recognize for a running service
			deadwords = ["inactive (dead)"] # Set the keyword to recognize for a stopped service
			notfoundwords = ["not-found"] # Set the keyword to recognize for a unrecognized/not installed service
		elif incontainer:
			mode = "os"
			beforecmd = "ps -e"
			aftercmd = "ps -e"
			activewords = [service]
			deadwords = [""]
			notfoundwords = []
			matchlist = self.get_processes(service)["matchlist"]
			if action == "stop":
				if matchlist == []:
					print self.ui.color("****************" + service + " is not running!****************\n", self.ui.red)
					actioncmd = "cd"
				else:
					actioncmd = ""
					for pid in matchlist:
						actioncmd += "kill " + pid + "; "
			elif action == "start":
				if matchlist != []:
					print self.ui.color("****************" + service + " is already running! Stop it First!****************\n", self.ui.red)
					actioncmd = "cd"
				else:
					if service == "radiuid":
						actioncmd = "radiuid run >> /dev/null &"
					elif service == radservicename:
						actioncmd = radservicename
			elif action == "restart":
				if service == "radiuid":
					actioncmd = ""
					for pid in matchlist:
						actioncmd += "kill " + pid + "; "
					actioncmd += "radiuid run >> /dev/null &"
				elif service == radservicename:
					for pid in matchlist:
						actioncmd += "kill " + pid + "; "
					actioncmd += radservicename
			elif action == "status":
				actioncmd = "cd"
		else:
			mode = "commands"
			beforecmd = "service " + service + " status"
			actioncmd = "service " + service + " " + action
			aftercmd = "service " + service + " status"
			activewords = ["running"]
			deadwords = ["stopped", "dead"]
			notfoundwords = ["unrecognized service"]
		before = commands.getstatusoutput(beforecmd) # Run the before command
		if mode == "commands":
			action = commands.getstatusoutput(actioncmd) # Run the action command
			after = commands.getstatusoutput(aftercmd) # Run the after command
		elif mode == "os":
			os.system(actioncmd)
			action = (0, self.get_processes(service)["modprocdata"])
			after = (0, self.get_processes(service)["modprocdata"])
		status = "unknown"
		for word in deadwords:
			if word in after[1]: # If the 'service dead' keyword is seen in the output
				status = "dead" # Set service status to 'dead'
		for word in activewords:
			if word in after[1]: # If the 'service running' keyword is seen in the output
				status = "running" # Set service status to 'running'
		for word in notfoundwords:
			if word in after[1]: # If the 'not found' keyword is seen in the output
				status = "not-found" # Set service status to 'not-found'
		result = {} # Create the result dictionary
		result.update({"beforecmd": beforecmd, "before": before[1]}) # Update the result with the pre-action information
		result.update({"actioncmd": actioncmd, "action": action[1]}) # Update the result with the action information
		result.update({"aftercmd": aftercmd, "after": after[1]}) # Update the result with the post-action information
		result.update({"status": status}) # Update the result with the recognized service status
		return result
	##### Install FreeRADIUS server #####
	def install_freeradius(self):
		os.system(pkgmgr + ' install freeradius -y')
		check_rad_name()
		self.service_control("start", radservicename)
		time.sleep(3)
		if self.service_control("status", radservicename)["status"] == "running":
			print self.ui.color("****************FreeRADIUS is Now Running!****************", self.ui.green)
			return "PASS"
		else:
			print self.ui.color("****************Something went wrong with the FreeRADIUS install****************", self.ui.red)
			print self.ui.color("****************You may need to run some system updates for it to install correctly****************", self.ui.red)
			return "FAIL"






	#######################################################
	#######           UI Question Methods           #######
	#######   Used for asking questions in the UI   #######
	#######################################################
	##### Change variables to change settings #####
	##### Used to ask questions and set new config settings in the install/maintenance utility #####
	def change_setting(self, setting, question):
		newsetting = raw_input(self.ui.color(">>>>> " + question + " [" + setting + "]: ", self.ui.cyan))
		if newsetting == '' or newsetting == setting:
			print self.ui.color("~~~ Keeping current setting...", self.ui.green)
			newsetting = setting
		else:
			print self.ui.color("~~~ Changed setting to: " + newsetting, self.ui.yellow)
		return str(newsetting)
	##### Create dictionary with client IP and shared password entries for FreeRADIUS server #####
	##### Used to ask questions during install about IP blocks and shared secret to use for FreeRADIUS server #####
	def freeradius_create_changes(self):
		##### Set variables for use later #####
		keepchanging = "yes"
		addips = []
		##### Ask for IP address blocks and append each entry to a list. User can accept the example though #####
		while keepchanging != "no":
			addipexample = "10.0.0.0/8"
			goround = raw_input(
				self.ui.color('\n>>>>> Enter the IP subnet to use for recognition of RADIUS accounting sources: [' + addipexample + ']:', self.ui.cyan))
			if goround == "":
				goround = addipexample
			ipcheck = self.filemgmt.ip_checker("cidr",goround)
			if ipcheck == 'fail':
				print self.ui.color("~~~ Nope. Give me a legit CIDR block...", self.ui.red)
			elif ipcheck == 'pass':
				addips.append(goround)
				print self.ui.color("~~~ Added " + goround + " to list\n", self.ui.yellow)
				keepchanging = self.ui.yesorno("Do you want to add another IP block to the list of trusted sources?")
		##### List out entries #####
		print "\n\n"
		print "List of IP blocks for accounting sources:"
		for each in addips:
			print self.ui.color(each, self.ui.yellow)
		print "\n\n"
		##### Have user enter shared secret to pair with all IP blocks in output dictionary #####
		radiussecret = ""
		radiussecret = raw_input(
			self.ui.color('>>>>> Enter a shared RADIUS secret to use with the accounting sources: [password123]:', self.ui.cyan))
		if radiussecret == "":
			radiussecret = "password123"
		print self.ui.color("~~~ Using '" + radiussecret + "' for shared secret\n", self.ui.yellow)
		##### Pair each IP entry with the shared secret and put in dictionary for output #####
		radiusclientdict = {}
		for each in addips:
			radiusclientdict[each] = radiussecret
		return radiusclientdict
	#######################################################
	#######        File Interaction Methods         #######
	#######   Used to create/change/delete files    #######
	#######################################################
	#### Copy RadiUID system and config files to appropriate paths for installation #####
	def copy_radiuid(self, mode):
		configfilepath = "/etc/radiuid/"
		binpath = "/bin/"
		os.system('mkdir -p ' + configfilepath)
		if mode == "replace-config":
			os.system('cp radiuid.conf ' + configfilepath + 'radiuid.conf')
		os.system('cp radiuid.py ' + binpath + 'radiuid')
		os.system('chmod 777 ' + binpath + 'radiuid')
		self.ui.progress("Copying Files: ", 2)
	#### Install RadiUID SystemD service #####
	def install_radiuid(self):
			systemd_startfile = '''[Unit]
Description=RadiUID User-ID Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/bin/bash -c 'cd /bin; python radiuid run'
Restart=on-abort


[Install]
WantedBy=multi-user.target'''

			nonsystemd_startfile = '''#!/bin/bash
# radiuid daemon
# chkconfig: 345 20 80
# description: RADIUS to Palo-Alto User-ID Engine
# processname: radiuid

DAEMON_PATH="/bin/"

DAEMON=radiuid
DAEMONOPTS="run"

NAME=RadiUID
DESC="RADIUS to Palo-Alto User-ID Engine"
PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME

case "$1" in
start)
	printf "%-50s" "Starting $NAME..."
	cd $DAEMON_PATH
	PID=`$DAEMON $DAEMONOPTS > /dev/null 2>&1 & echo $!`
	#echo "Saving PID" $PID " to " $PIDFILE
        if [ -z $PID ]; then
            printf "%s\n" "Fail"
        else
            echo $PID > $PIDFILE
            printf "%s\n" "Ok"
        fi
;;
status)
        if [ -f $PIDFILE ]; then
            PID=`cat $PIDFILE`
            if [ -z "`ps axf | grep ${PID} | grep -v grep`" ]; then
                printf "%s\n" "Process dead but pidfile exists"
            else
                echo "$DAEMON (pid $PID) is running..."
            fi
        else
            printf "%s\n" "$DAEMON is stopped"
        fi
;;
stop)
        printf "%-50s" "Stopping $NAME"
            PID=`cat $PIDFILE`
            cd $DAEMON_PATH
        if [ -f $PIDFILE ]; then
            kill -HUP $PID
            printf "%s\n" "Ok"
            rm -f $PIDFILE
        else
            printf "%s\n" "pidfile not found"
        fi
;;

restart)
  	$0 stop
  	$0 start
;;

*)
        echo "Usage: $0 {status|start|stop|restart}"
        exit 1
esac'''
			systemdpath = '/etc/systemd/system/radiuid.service'
			nonsystemdpath = '/etc/init.d/radiuid'
			if systemd:
				installpath = systemdpath
				installfile = systemd_startfile
			elif not systemd:
				installpath = nonsystemdpath
				installfile = nonsystemd_startfile
			self.ui.progress("Installing: ", 2)
			f = open(installpath, 'w')
			f.write(installfile)
			f.close()
			if systemd:
				os.system('systemctl enable radiuid')
			elif not systemd:
				os.system('chmod 777 /etc/init.d/radiuid')
				os.system('chkconfig radiuid on')
	def install_radiuid_completion(self):
		##### BASH SCRIPT DATA START #####
		bash_complete_script = """#!/bin/bash

#####  RadiUID Server BASH Complete Script  #####
#####        Written by John W Kerns        #####
#####       http://blog.packetsar.com       #####
#####  https://github.com/PackeTsar/radiuid #####

_radiuid_complete()
{
  local cur prev
  COMPREPLY=()
  cur=${COMP_WORDS[COMP_CWORD]}
  prev=${COMP_WORDS[COMP_CWORD-1]}
  prev2=${COMP_WORDS[COMP_CWORD-2]}
  if [ $COMP_CWORD -eq 1 ]; then
    COMPREPLY=( $(compgen -W "run install show set push tail clear edit service request version" -- $cur) )
  elif [ $COMP_CWORD -eq 2 ]; then
    case "$prev" in
      show)
        COMPREPLY=( $(compgen -W "log acct-logs run config clients status mappings" -- $cur) )
        ;;
      "set")
        COMPREPLY=( $(compgen -W "tlsversion radiusstopaction looptime logfile maxloglines radiuslogpath acctlogcopypath userdomain timeout target client munge" -- $cur) )
        ;;
      push)
        local targets=$(for target in `radiuid targets`; do echo $target ; done)
        COMPREPLY=( $(compgen -W "${targets} all" -- ${cur}) )
        ;;
      "tail")
        COMPREPLY=( $(compgen -W "log" -- $cur) )
        ;;
      "clear")
        COMPREPLY=( $(compgen -W "log acct-logs target mappings client munge" -- $cur) )
        ;;
      edit)
        COMPREPLY=( $(compgen -W "config clients" -- $cur) )
        ;;
      "service")
        COMPREPLY=( $(compgen -W "radiuid freeradius all" -- $cur) )
        ;;
      "request")
        COMPREPLY=( $(compgen -W "xml-update munge-test auto-complete reinstall freeradius-install" -- $cur) )
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 3 ]; then
    case "$prev" in
      run)
        COMPREPLY=( $(compgen -W "xml set <cr>" -- $cur) )
        ;;
      config)
        if [ "$prev2" == "show" ]; then
          COMPREPLY=( $(compgen -W "xml set <cr>" -- $cur) )
        fi
        ;;
      reinstall)
        if [ "$prev2" == "request" ]; then
          COMPREPLY=( $(compgen -W "replace-config keep-config" -- $cur) )
        fi
        ;;
      freeradius-install)
        if [ "$prev2" == "request" ]; then
          COMPREPLY=( $(compgen -W "<cr> no-confirm" -- $cur) )
        fi
        ;;
      munge-test)
        if [ "$prev2" == "request" ]; then
          COMPREPLY=( $(compgen -W "- <string-to-parse>" -- $cur) )
        fi
        ;;
      client)
        local clients=$(for client in `radiuid clients`; do echo $client ; done)
        if [ "$prev2" == "clear" ]; then
          COMPREPLY=( $(compgen -W "${clients} all" -- ${cur}) )
        elif [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "ipv4 ipv6" -- $cur) )
        fi
        ;;
      clients)
        if [ "$prev2" == "show" ]; then
          COMPREPLY=( $(compgen -W "file table <cr>" -- ${cur}) )
        fi
        ;;
      radiuslogpath)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<directory-path> -" -- $cur) )
        fi
        ;;
      acctlogcopypath)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<directory-path> None" -- $cur) )
        fi
        ;;
      logfile)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<file-path> -" -- $cur) )
        fi
        ;;
      maxloglines)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<number-of-lines> -" -- $cur) )
        fi
        ;;
      looptime)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<number-of-seconds> -" -- $cur) )
        fi
        ;;
      tlsversion)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "1.0 1.1 1.2" -- $cur) )
        fi
        ;;
      radiusstopaction)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "clear ignore push" -- $cur) )
        fi
        ;;
      userdomain)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<domain-name> none" -- $cur) )
        fi
        ;;
      timeout)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<number-of-minutes> -" -- $cur) )
        fi
        ;;
      freeradius|radiuid)
        if [ "$prev2" == "service" ]; then
          COMPREPLY=( $(compgen -W "start stop restart" -- $cur) )
        fi
        ;;
      log)
        if [ "$prev2" == "tail" ]; then
          COMPREPLY=( $(compgen -W "- <number-of-lines> <cr>" -- $cur) )
        fi
        ;;
      all)
        if [ "$prev2" == "service" ]; then
          COMPREPLY=( $(compgen -W "start stop restart" -- $cur) )
        elif [ "$prev2" == "push" ]; then
          COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
        fi
        ;;
      mappings)
        local targets=$(for target in `radiuid targets`; do echo $target ; done)
        if [ "$prev2" == "show" ]; then
          COMPREPLY=( $(compgen -W "${targets} all consistency" -- ${cur}) )
        elif [ "$prev2" == "clear" ]; then
          COMPREPLY=( $(compgen -W "${targets} all" -- ${cur}) )
        fi
        ;;
      target)
        local targets=$(for target in `radiuid targets`; do echo $target ; done)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "${targets} - <NEW-HOSTNAME>:<VSYS-ID>" -- ${cur}) )
        elif [ "$prev2" == "clear" ]; then
          COMPREPLY=( $(compgen -W "${targets} all" -- ${cur}) )
        fi
        ;;
      munge)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W " - <rule>.<step>" -- ${cur}) )
        elif [ "$prev2" == "clear" ]; then
          local rules=$(for rule in `radiuid munge-rules`; do echo $rule ; done)
          COMPREPLY=( $(compgen -W "${rules} all" -- ${cur}) )
        fi
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 4 ]; then
    prev3=${COMP_WORDS[COMP_CWORD-3]}
    if [ "$prev2" == "mappings" ]; then
      if [ "$prev3" == "clear" ]; then
        COMPREPLY=( $(compgen -W "all <uid-ip>" -- $cur) )
      fi
    fi
    if [ "$prev2" == "all" ]; then
      if [ "$prev3" == "push" ]; then
        COMPREPLY=( $(compgen -W "<ip-address> -" -- $cur) )
      fi
    fi
    if [ "$prev2" == "client" ]; then
      if [ "$prev3" == "set" ]; then
        COMPREPLY=( $(compgen -W "<ip-block> -" -- $cur) )
      fi
    fi
    if [ "$prev2" == "munge" ]; then
      if [ "$prev3" == "clear" ]; then
        if [ "$prev" != "all" ]; then
          local steps=$(for step in `radiuid munge-steps $prev`; do echo $step ; done)
          COMPREPLY=( $(compgen -W "${steps} all" -- $cur) )
        fi
      fi
    fi
    if [ "$prev2" == "munge-test" ]; then
      if [ "$prev3" == "request" ]; then
        COMPREPLY=( $(compgen -W "<cr> debug" -- $cur) )
      fi
    fi
    if [ "$prev2" == "munge" ]; then
      if [ "$prev3" == "set" ]; then
        IFS='.' read -a myarray <<< "$prev"
        if [ "${myarray[1]}" == "0" ]; then
          COMPREPLY=( $(compgen -W "match" -- $cur) )
        elif [ "${myarray[1]}" != "0" ]; then
          COMPREPLY=( $(compgen -W "accept assemble discard set-variable" -- $cur) )
        fi
      fi
    fi
    if [ "$prev2" == "reinstall" ]; then
      if [ "$prev3" == "request" ]; then
        COMPREPLY=( $(compgen -W "<cr> no-confirm" -- $cur) )
      fi
    fi
  elif [ $COMP_CWORD -eq 5 ]; then
    prev3=${COMP_WORDS[COMP_CWORD-3]}
    prev4=${COMP_WORDS[COMP_CWORD-4]}
    if [ "$prev4" == "push" ]; then
      if [ "$prev3" != "all" ]; then
        COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
      fi
    fi
    if [ "$prev3" == "munge" ]; then
      if [ "$prev" == "set-variable" ]; then
        COMPREPLY=( $(compgen -W "- <variable-name>" -- $cur) )
      fi
    fi
    if [ "$prev3" == "munge" ]; then
      if [ "$prev" == "assemble" ]; then
        COMPREPLY=( $(compgen -W "- <variable-name>" -- $cur) )
      fi
    fi
    if [ "$prev3" == "munge" ]; then
      if [ "$prev" == "match" ]; then
        IFS='.' read -a myarray <<< "$prev2"
        if [ "${myarray[1]}" == "0" ]; then
          COMPREPLY=( $(compgen -W "any <regex-pattern>" -- $cur) )
        fi
      fi
    fi
    if [ "$prev3" == "all" ]; then
      if [ "$prev4" == "push" ]; then
        COMPREPLY=( $(compgen -W "bypass-munge <cr>" -- $cur) )
      fi
    fi
    if [ "$prev3" == "client" ]; then
      if [ "$prev4" == "set" ]; then
        COMPREPLY=( $(compgen -W "<secret> -" -- $cur) )
      fi
    fi
  elif [ $COMP_CWORD -eq 6 ]; then
    prev2=${COMP_WORDS[COMP_CWORD-2]}
    prev3=${COMP_WORDS[COMP_CWORD-3]}
    prev4=${COMP_WORDS[COMP_CWORD-4]}
    prev5=${COMP_WORDS[COMP_CWORD-5]}
    if [ "$prev4" == "mappings" ]; then
      if [ "$prev5" == "clear" ]; then
        COMPREPLY=( $(compgen -W "all <uid-ip>" -- $cur) )
      fi
    elif [ "$prev5" == "push" ]; then
      COMPREPLY=( $(compgen -W "<ip-address> -" -- $cur) )
    fi
    if [ "$prev4" == "target" ]; then
      if [ "$prev5" == "set" ]; then
        COMPREPLY=( $(compgen -W "username password port" -- $cur) )
      fi
    fi
    if [ "$prev4" == "munge" ]; then
      if [ "$prev5" == "set" ]; then
        if [ "$prev2" == "assemble" ]; then
          COMPREPLY=( $(compgen -W "- <variable-name>" -- $cur) )
        fi
      fi
    fi
    if [ "$prev4" == "munge" ]; then
      if [ "$prev5" == "set" ]; then
        if [ "$prev2" == "set-variable" ]; then
          COMPREPLY=( $(compgen -W "from-match from-string" -- $cur) )
        fi
      fi
    fi
    if [ "$prev4" == "munge" ]; then
      if [ "$prev5" == "set" ]; then
        if [ "$prev2" == "match" ]; then
          IFS='.' read -a myarray <<< "$prev3"
          if [ "${myarray[1]}" == "0" ]; then
            if [ "$prev" != "any" ]; then
              COMPREPLY=( $(compgen -W "complete partial" -- $cur) )
            fi
          fi
        fi
      fi
    fi
  elif [ $COMP_CWORD -eq 8 ]; then
    case "$prev2" in
      username)
        COMPREPLY=( $(compgen -W "password port" -- $cur) )
        ;;
      password)
        COMPREPLY=( $(compgen -W "username port" -- $cur) )
        ;;
      port)
        COMPREPLY=( $(compgen -W "username password" -- $cur) )
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 10 ]; then
    prev4=${COMP_WORDS[COMP_CWORD-4]}
    case "$prev4" in
      username)
        if [ "$prev2" == "password" ]; then
            COMPREPLY=( $(compgen -W "port" -- $cur) )
        elif [ "$prev2" == "port" ]; then
            COMPREPLY=( $(compgen -W "password" -- $cur) )
        fi
        ;;
      password)
        if [ "$prev2" == "username" ]; then
            COMPREPLY=( $(compgen -W "port" -- $cur) )
        elif [ "$prev2" == "port" ]; then
            COMPREPLY=( $(compgen -W "username" -- $cur) )
        fi
        ;;
      port)
        if [ "$prev2" == "username" ]; then
            COMPREPLY=( $(compgen -W "password" -- $cur) )
        elif [ "$prev2" == "password" ]; then
            COMPREPLY=( $(compgen -W "username" -- $cur) )
        fi
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 7 ]; then
    if [ "$prev" == "username" ]; then
      COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
    fi
    if [ "$prev" == "password" ]; then
      COMPREPLY=( $(compgen -W "<password> -" -- $cur) )
    fi
    if [ "$prev" == "port" ]; then
      COMPREPLY=( $(compgen -W "<tcp-port-number> -" -- $cur) )
    fi
    if [ "$prev" == "from-match" ]; then
      COMPREPLY=( $(compgen -W "<regex-pattern> any" -- $cur) )
    fi
    if [ "$prev" == "from-string" ]; then
      COMPREPLY=( $(compgen -W "<string> -" -- $cur) )
    fi
    if [ "$prev5" == "push" ]; then
      COMPREPLY=( $(compgen -W "bypass-munge <cr>" -- $cur) )
    fi
  elif [ $COMP_CWORD -eq 9 ] || [ $COMP_CWORD -eq 11 ]; then
    case "$prev" in
      username)
        COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
        ;;
      password)
        COMPREPLY=( $(compgen -W "<password> -" -- $cur) )
        ;;
      port)
        COMPREPLY=( $(compgen -W "<tcp-port-number> -" -- $cur) )
        ;;
      from-match)
        COMPREPLY=( $(compgen -W "<regex-pattern> any" -- $cur) )
        ;;
      from-string)
        COMPREPLY=( $(compgen -W "<string> -" -- $cur) )
        ;;
      *)
        ;;
    esac
  fi
  return 0
} &&
complete -F _radiuid_complete radiuid &&
bind 'set show-all-if-ambiguous on'"""
		##### BASH SCRIPT DATA STOP #####
		##### Place script file #####
		installpath = '/etc/profile.d/radiuid-complete.sh'
		print "\n\n***** Installing BASH Auto-Complete Script to: " + installpath + "*****\n"
		time.sleep(2)
		self.ui.progress("Installing: ", 1)
		f = open(installpath, 'w')
		f.write(bash_complete_script)
		f.close()
		self.ui.progress("Setting Permissions on File", 1)
		os.system('chmod 777 /etc/profile.d/radiuid-complete.sh')
		print self.ui.color("All Done!\n", self.ui.green)
	##### Apply new settings as veriables in the namespace #####
	##### Used to write new setting values to namespace to be picked up and used by the write_file method to write to the config file #####
	def apply_setting(self, file_data, settingname, oldsetting, newsetting):
		if oldsetting == newsetting:
			print self.ui.color("***** No changes to  : " + settingname, self.ui.green)
			return file_data
		else:
			new_file_data = file_data.replace(settingname + " = " + oldsetting, settingname + " = " + newsetting)
			padlen = 50 - len("***** Changed setting: " + settingname)
			pad = " " * padlen
			print self.ui.color("***** Changed setting: " + settingname + pad + "|\tfrom: " + oldsetting + "\tto: " + newsetting, self.ui.yellow)
			return new_file_data
	##### Use dictionary of edits for FreeRADIUS and push them to the config file #####
	def freeradius_editor(self, dict_edits):
		iplist = dict_edits.keys()
		print "\n\n\n"
		print "#####About to append the below client data to the FreeRADIUS client.conf file#####"
		print "##################################################################################"
		for ip in iplist:
			newwrite = "\nclient " + ip + " {\n    secret      = " + dict_edits[
				ip] + "\n    shortname   = Created_By_RadiUID\n }\n"
			print newwrite
		oktowrite = self.ui.yesorno("OK to write to client.conf file?")
		if oktowrite == "yes":
			print "###############Writing the above to the FreeRADIUS client.conf file###############"
			print "##################################################################################"
			print "\n"
			self.ui.progress("Writing: ", 1)
			newclients = []
			for client in dict_edits:
				newclients.append({"IP Block": client, "Shared Secret": dict_edits[client]})
			self.filemgmt.freeradius_client_editor("append", newclients)
			print "\n\n\n"
			print "****************Restarting the FreeRADIUS service to effect changes...****************\n\n"
			self.ui.progress("Starting/Restarting: ", 1)
			checkservice = self.service_control("restart", radservicename)
			if checkservice["status"] != "running":
				print self.ui.color("\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to start back up.", self.ui.red)
				print self.ui.color("***** We may have made some adverse changes to the config file.", self.ui.red)
				print self.ui.color("***** Visit the FreeRADIUS config file at " + clientconfpath + " and remove the bad changes.", self.ui.red)
				print self.ui.color("***** Then try to start the FreeRADIUS service by issuing the 'radiuid restart freeradius' command", self.ui.red)
				raw_input(self.ui.color("Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
			else:
				print self.ui.color("\n\n***** Great Success!! Looks like FreeRADIUS restarted and is back up now!", self.ui.green)
				print self.ui.color("***** If you need to manually edit the FreeRADIUS config file, it is located at " + clientconfpath, self.ui.green)
				raw_input(self.ui.color("\nHit ENTER to continue...\n\n>>>>>", self.ui.cyan))
		elif oktowrite == "no":
			print "~~~ OK Not writing it"
	def update_xml_etree(self):
		for path in sys.path:
			check = re.findall(".*python[23]\..$", path)
			if len(check) > 0:
				installpath = check[0] + "/xml/etree13/"
		print "\n\n***** Selected "+ installpath + " for location of updated etree modules *****\n"
		commands.getstatusoutput("mkdir -p " + installpath)
		url = "http://www.packetsar.com/wp-content/uploads/"
		tarfilename = "xml-etree-elementtree-1.3.0.tar.gz"
		self.ui.progress("Downloading " + url + tarfilename, 1)
		urllib.urlretrieve (url + tarfilename, installpath + tarfilename)
		self.ui.progress("Extracting Files to " + installpath, 1)
		commands.getstatusoutput("tar -xzvf " + installpath + "xml-etree-elementtree-1.3.0.tar.gz -C " + installpath)
		print "***** Performing a test import of the new module xml.etree13.ElementTree *****\n"
		time.sleep(2)
		try:
			global ElementTree
			import xml.etree13.ElementTree as ElementTree
			print self.ui.color("***** Import successful *****\n", self.ui.green)
			self.ui.progress("Checking Module Version", 1)
			if float(ElementTree.VERSION[:3]) < 1.3:
				print self.ui.color("ERROR: Something went wrong. It imported, but is the wrong version", self.ui.red)
			elif float(ElementTree.VERSION[:3]) >= 1.3:
				print self.ui.color("SUCCESS: Successful import of xml.etree.ElementTree module version " + ElementTree.VERSION + "\n", self.ui.green)
		except ImportError:
			print self.ui.color("ERROR: Import of xml.etree13.ElementTree failed", self.ui.red)
		print self.ui.color("All Done!\n\n", self.ui.green)






#########################################################################
################### INSTALLER/MAINTENANCE UTILITY CLASS #################
#########################################################################
#######           Contains the main method which runs the         #######
#######                 Installer/Maintenance Utility             #######
#########################################################################
class installer_maintenance_utility(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
		self.filemgmt = file_management()
		self.imum = imu_methods()
		####################################################
	def im_utility(self):
		'''
		############# LEGEND FOR TEXUTAL CUES USED IN INSTALLER/MAINTENANCE UTILITY #############
		#########################################################################################
		****************Status....what program is doing..****************
		***** Informational
		----- Yes or No question
		~~~~~ Acknowledgement of an answer to a question
		>>>>> Command to enter information
		#########################################################################################
		'''
		self.ui.packetsar()
		self.ui.progress("Running RadiUID in Install/Maintenance Mode:", 3)
		print "\n\n\n\n\n\n\n\n"
		print '                       ##########################################################' \
				'\n' + '                       ##### Install\Maintenance Utility for RadiUID Server #####' \
				'\n' + '                       #####                 Version ' + version + '                  #####' \
				'\n' + '                       #####             Please Use Carefully!              #####' \
				'\n' + '                       ##########################################################' \
				'\n' + '                       ##########################################################' \
				'\n' + '                       ##########################################################' \
				'\n' + '                       ##########       Written by John W Kerns        ##########' \
				'\n' + '                       ##########      http://blog.packetsar.com       ##########' \
				'\n' + '                       ########## https://github.com/PackeTsar/radiuid ##########' \
				'\n' + '                       ##########################################################' \
				'\n' + '                       ##########################################################' \
				'\n' + '                       ##########################################################' \
	 \

		print "\n\n\n"
		print "****************First, we will check if FreeRADIUS and RadiUID are installed yet...****************\n"
		raw_input(self.ui.color("\n\n>>>>> Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
		print "\n\n\n\n\n\n\n"
		#########################################################################
		###Check if FreeRADIUS is installed and running already
		#########################################################################
		print "\n\n\n\n\n\n****************Checking if FreeRADIUS is installed...****************\n"
		radcheck = self.imum.service_control("status", radservicename)
		if radcheck["status"] == "running":
			print self.ui.color("***** Looks like the FreeRADIUS service is already installed and running...skipping the install of FreeRADIUS", self.ui.green)
		elif radcheck["status"] == "dead":
			freeradiusrestart = self.ui.yesorno("Looks like FreeRADIUS is installed, but not running....want to start it up?")
			if freeradiusrestart == 'yes':
				radcheck = self.imum.service_control("start", radservicename)
				if radcheck["status"] == "dead":
					print self.ui.color("***** It looks like FreeRADIUS failed to start up. You may need to change its settings and restart it manually...", self.ui.red)
					print self.ui.color("***** Use the command 'radiuid edit clients' to open and edit the FreeRADIUS client settings file manually", self.ui.red)
				if radcheck["status"] == "running":
					print self.ui.color("***** Very nice....Great Success!!!", self.ui.green)
			if freeradiusrestart == 'no':
				print self.ui.color("~~~ OK, leaving it off...", self.ui.yellow)
		elif radcheck["status"] == "not-found" or radcheck["status"] == "unknown":
			freeradiusinstall = self.ui.yesorno(
				"Looks like FreeRADIUS is not installed. It is required by RadiUID. Is it ok to install FreeRADIUS?")
			if freeradiusinstall == 'yes':
				radcheck = self.imum.install_freeradius()
				if radcheck == "FAIL":
					print self.ui.color("\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to install or start up.", self.ui.red)
					print self.ui.color("***** It is possible that the native package manager is not able to download the install files.", self.ui.red)
					print self.ui.color("***** Make sure that you have internet access and your package manager is able to download the FreeRADIUS install files", self.ui.red)
					raw_input(self.ui.color("Hit ENTER to quit the program...\n", self.ui.cyan))
					quit()
				elif radcheck == "PASS":
					print self.ui.color("\n\n***** Great Success!! Looks like FreeRADIUS installed and started up successfully.", self.ui.green)
					print self.ui.color("***** We will be adding client IP and shared secret info to FreeRADIUS later in this wizard.", self.ui.green)
					print self.ui.color("***** If you need to edit the FreeRADIUS clients later, you can use 'set clients' and 'clear clients' in the CLI", self.ui.green)
					print self.ui.color("***** You can also manually open the file for editing. It is located at /etc/raddb/clients.conf", self.ui.green)
					raw_input(self.ui.color("\n***** Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
			if freeradiusinstall == 'no':
				print self.ui.color("***** FreeRADIUS is required by RadiUID. Quitting the installer", self.ui.red)
				quit()
		#########################################################################
		###Check if RadiUID is installed and running already
		#########################################################################
		print "\n\n\n\n\n\n****************Checking if RadiUID is already installed...****************\n"
		uidcheck = self.imum.service_control("status", "radiuid")
		if uidcheck["status"] == "running":
			print self.ui.color("***** Looks like the RadiUID service is already installed and running...skipping the install of RadiUID\n", self.ui.green)
			radiuidreinstall = self.ui.yesorno("Do you want to re-install the RadiUID service?")
		elif uidcheck["status"] == "dead":
			print self.ui.color("\n***** Looks like RadiUID is installed, but not running....", self.ui.yellow)
			radiuidrestart = self.ui.yesorno("Do you want to start it up?")
			if radiuidrestart == 'yes':
				uidcheck = self.imum.service_control("start", "radiuid")
				self.ui.progress('Checking for Successful Startup', 3)
				if uidcheck["status"] == "running":
					print self.ui.color("***** Great Success!!! Successful startup of RadiUID", self.ui.green)
					radiuidreinstall = self.ui.yesorno("Do you want to re-install the RadiUID service?")
				if uidcheck["status"] != "running":
					print self.ui.color("***** Looks like the startup failed...", self.ui.red)
					radiuidreinstall = self.ui.yesorno("Do you want to re-install the RadiUID service?")
			elif radiuidrestart == 'no':
				print self.ui.color("~~~ OK, leaving it off...", self.ui.yellow)
				radiuidreinstall = self.ui.yesorno("Do you want to re-install the RadiUID service?")
		else:
			print self.ui.color("***** Looks like RadiUID is not yet installed...", self.ui.yellow)
			radiuidreinstall = self.ui.yesorno("Do you want to install the RadiUID service?")
		if radiuidreinstall == 'yes':
			print "\n\n****************Installing the RadiUID service...****************\n"
			self.imum.copy_radiuid("replace-config")
			self.imum.install_radiuid()
			print "\n"
			self.imum.install_radiuid_completion()
			raw_input(self.ui.color(">>>>> You will need to log out and log back in to activate the RadiUID CLI auto-completion functionality\n>>>>>", self.ui.cyan))
			print "\n\n****************We will start up the RadiUID service once we configure the .conf file****************\n"
		print "\n\n\n\n"
		print "****************Checking xml.etree.ElementTree version****************\n"
		if float(ElementTree.VERSION[:3]) < 1.3:
			print self.ui.color("***** It looks like your xml.etree.ElementTree python module is too old for RadiUID.", self.ui.yellow)
			xmlupdate = self.ui.yesorno("Is it OK to download and install a newer version from the PackeTsar site?")
			print "\n\n"
			if xmlupdate == "yes":
				self.imum.update_xml_etree()
			else:
				print self.ui.color("***** OK we won't update it. You will likely run into problems with RadiUID without this.\n", self.ui.yellow)
				raw_input(self.ui.color("Hit ENTER to acknowledge\n>>>>>", self.ui.cyan))
		#########################################################################
		###Read current .conf settings into interpreter
		#########################################################################
		print "\n\n\n\n"
		editradiuidconf = self.ui.yesorno("Do you want to edit the settings in the RadiUID .conf file (if you just installed or reinstalled RadiUID, then you should do this)?")
		if editradiuidconf == "yes":
			self.filemgmt.initialize_config("quiet")
			global configfile
			print "Configuring File: " + self.ui.color(configfile, self.ui.green) + "\n"
			print "\n\n\n****************Now, we will import the settings from the " + configfile + " file...****************\n"
			print "*****************The current values for each setting are [displayed in the prompt]****************\n"
			print "****************Leave the prompt empty and hit ENTER to accept the current value****************\n"
			raw_input(self.ui.color("\n\n>>>>> Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
			print "\n\n\n\n\n\n\n"
			print "**************** Reading in current settings from " + configfile + " ****************\n"
			self.ui.progress('Reading:', 1)
			self.filemgmt.publish_config("quiet")
			#########################################################################
			###Ask questions to the console for editing the .conf file settings
			#########################################################################
			print "\n\n\n\n\n\n****************Please enter values for the different settings in the radiuid.conf file****************\n"
			global logfile
			newlogfile = self.imum.change_setting(logfile, 'Enter full path to the new RadiUID Log File')
			print "\n"
			if radservicename == "radiusd":
				raddirname = "radius"
			else:
				raddirname = radservicename
			radiuslogpath = "/var/log/" + raddirname + "/radacct/"
			newradiuslogpath = self.imum.change_setting(radiuslogpath, 'Enter path to the FreeRADIUS Accounting Logs')
			print "\n"
			newuserdomain = self.imum.change_setting(userdomain, 'Enter the user domain to be prefixed to User-IDs')
			print "\n"
			newtimeout = self.imum.change_setting(timeout, 'Enter timeout period for pushed UIDs (in minutes)')
			#########################################################################
			###Ask questions to add/edit targets for the config file
			#########################################################################
			print "\n****************Checking for already configured firewall targets****************\n"
			self.ui.progress('Reading:', 1)
			try:
				self.filemgmt.scrub_targets("noisy", "scrub")
				print self.ui.make_table(["hostname", "vsys",  'username', 'password'], targets)
			except NameError:
				print self.ui.color("\n****************No firewall targets currently configured****************\n", self.ui.yellow)
			print "\n\n"
			changetargets = self.ui.yesorno("Do you want to delete any current targets and set up new ones?")
			if changetargets == 'no':
				print "~~~ OK. Leaving current targets alone..."
				newtargets = targets
			elif changetargets == 'yes':
				anothertarget = 'yes'
				newtargets = []
				while anothertarget == 'yes':
					print "\n\n\n"
					addhostname = self.imum.change_setting('192.168.1.1', 'Enter the IP ADDRESS or HOSTNAME of the target firewall to recieve User-ID mappings')
					addvsys = self.imum.change_setting('vsys1', 'Enter the Virtual System ID of the target firewall to recieve User-ID mappings').replace("vsys", "")
					addusername = self.imum.change_setting('admin', 'Enter the administrative USERNAME to use for authentication against the firewall')
					addpassword = self.imum.change_setting('admin', 'Enter the PASSWORD for the username you just entered')
					newtargets.append({'hostname': addhostname, 'vsys': addvsys, 'username': addusername, 'password': addpassword})
					print "\n\n"
					anothertarget = self.ui.yesorno("Do you want to add another target firewall?")
				print "\n****************New Targets Are:****************\n"
				print self.ui.make_table(["hostname", "vsys",  'username', 'password'], newtargets)
				print "\n\n\n"
			raw_input(self.ui.color("\n\n>>>>> Hit ENTER to see what the new config will look like...\n\n>>>>>", self.ui.cyan))
			print "\n\n\n"
			##### Apply global settings to mounted config #####
			self.filemgmt.change_config_item('logfile', newlogfile)
			self.filemgmt.change_config_item('radiuslogpath', newradiuslogpath)
			self.filemgmt.change_config_item('userdomain', newuserdomain)
			self.filemgmt.change_config_item('timeout', newtimeout)
			##### Apply target settings to mounted config #####
			self.filemgmt.clear_targets()
			self.filemgmt.add_targets(newtargets)
			##### Show Config #####
			self.filemgmt.show_config_item('xml', "none", 'config')
			print "\n\n\n"
			#########################################################################
			###Pushing settings to .conf file with the code below
			#########################################################################
			applysettings = self.ui.yesorno("Do you want to apply your entered settings to the config file and restart the RadiUID service?")
			if applysettings == 'no':
				print "~~~ OK. Disregarding config changes..."
			elif applysettings == 'yes':
				print "\n\n\n\n\n\n****************Applying entered settings into the radiuid.conf file...****************\n"
				self.ui.progress('Applying:', 1)
				self.filemgmt.save_config()
				newlogfiledir = self.filemgmt.strip_filepath(newlogfile)[0]
				print "\n\n****************Creating log directory: "+ newlogfiledir + "****************\n"
				os.system('mkdir -p ' + newlogfiledir)
				print "\n\n****************Starting/Restarting the RadiUID service...****************\n"
				radiuidrunning = self.imum.service_control("restart", "radiuid")
				if radiuidrunning["status"] == "running":
					print self.ui.color("***** RadiUID successfully started up!!!", self.ui.green)
					raw_input(self.ui.color(">>>>> Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
				else:
					print self.ui.color("***** Something went wrong. Looks like the installation or startup failed... ", self.ui.red)
					print self.ui.color("***** Please make sure you are installing RadiUID on a support platform", self.ui.red)
					print self.ui.color("***** You can manually edit the RadiUID config file by entering 'radiuid edit config' in the CLI", self.ui.red)
					raw_input(self.ui.color("Hit ENTER to quit the program...\n\n>>>>>", self.ui.cyan))
					quit()
		else:
			print "~~~ OK... Leaving the .conf file alone"
		#########################################################################
		###Make changes to FreeRADIUS config file
		#########################################################################
		clientconfpath = check_rad_config()
		print "\n\n\n\n\n\n****************Let's make some changes to the FreeRADIUS client config file****************\n"
		editfreeradius = self.ui.yesorno("Do you want to make changes to FreeRADIUS by adding some IP blocks for accepted accounting clients?")
		if editfreeradius == "yes":
			freeradiusedits = self.imum.freeradius_create_changes()
			self.imum.freeradius_editor(freeradiusedits)
		#########################################################################
		###Trailer/Goodbye
		#########################################################################
		print "\n\n\n\n\n\n***** Thank you for using the RadiUID installer/management utility"
		raw_input(self.ui.color(">>>>> Hit ENTER to see the tail of the RadiUID log file before you exit the utility\n\n>>>>>", self.ui.cyan))
		##### Read in logfile path from found config file #####
		self.filemgmt.initialize_config("quiet")
		self.filemgmt.publish_config("quiet")
		#######################################################
		print "\n\n############################## LAST 50 LINES FROM " + logfile + "##############################"
		print "########################################################################################################"
		os.system("tail -n 50 " + logfile)
		print "########################################################################################################"
		print "########################################################################################################"
		print "\n\n\n\n***** Looks like we are all done here...\n"
		raw_input(
			self.ui.color(">>>>> Hit ENTER to exit the Install/Maintenance Utility\n\n>>>>>", self.ui.cyan))
		quit()






#########################################################################
#################### RADIUID COMMAND LINE INTERPRETER ###################
#########################################################################
####### Contains the code which interprets arguments to the shell #######
#######       and runs the proper part of code in the source      #######
#########################################################################
class command_line_interpreter(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
		self.radiuid = radiuid_main_process()
		self.imu = installer_maintenance_utility()
		self.imum = imu_methods()
		self.filemgmt = file_management()
		self.dp = data_processing()
		self.pafi = palo_alto_firewall_interaction()
		####################################################
	##### Create str sentence out of list seperated by spaces and lowercase everything #####
	##### Used for recognizing arguments when running RadiUID from the CLI #####
	def cat_list(self, listname):
		result = ""
		counter = 0
		for word in listname:
			result = result + listname[counter].lower() + " "
			counter = counter + 1
		result = result[:len(result) - 1:]
		return result
	######################### RadiUID Command Interpreter #############################
	def interpreter(self):
		arguments = self.cat_list(sys.argv[1:])
		global runcmd
		global targets
		if "radiuid.py" in sys.argv[0]:
			runcmd = "python " + sys.argv[0]
		else:
			runcmd = "radiuid"
		self.filemgmt.initialize_config('quiet')
		self.filemgmt.publish_config('quiet')
		global configfile
		#### Set TLS Version ####
		global tlsobj
		try:
			if tlsversion == "1.0":
				tlsobj = ssl.PROTOCOL_TLSv1
			elif tlsversion == "1.1":
				tlsobj = ssl.PROTOCOL_TLSv1_1
			elif tlsversion == "1.2":
				tlsobj = ssl.PROTOCOL_TLSv1_2
		except NameError:
			tlsobj = ssl.PROTOCOL_TLSv1
		######################### RUN #############################
		if arguments == "run":
			self.radiuid.looper()
		######################### AUTO-COMPLETE USE #############################
		elif arguments == "targets":
			self.filemgmt.initialize_config("quiet")
			self.filemgmt.publish_config("quiet")
			try:
				for target in targets:
					print target["hostname"] + ":vsys" + target["vsys"]
			except NameError:
				null = None
		elif arguments == "clients":
			self.filemgmt.initialize_config("quiet")
			self.filemgmt.publish_config("quiet")
			clientinfo = self.filemgmt.freeradius_client_editor("show", "")
			if "FATAL" in clientinfo:
				return None
			else:
				for client in clientinfo:
					print client["IP Block"]
		elif arguments == "munge-rules":
			try:
				for rulename in configdict['globalsettings']['munge'].keys():
					print rulename
			except KeyError:
				None
		elif "munge-steps" in arguments:
			try:
				for stepname in configdict['globalsettings']['munge'][sys.argv[2]].keys():
					if stepname != "match":
						print stepname
			except KeyError:
				None
		elif arguments == "test":
			print configdict
		######################### INSTALL #############################
		elif arguments == "install":
			self.filemgmt.logwriter("quiet", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print "\n\n\n"
			self.imu.im_utility()
		######################### SHOW #############################
		elif arguments == "show" or arguments == "show ?":
			print "\n - show log                                                  |     Show the RadiUID log file"
			print " - show acct-logs                                            |     Show the log files currently in the FreeRADIUS accounting directory"
			print " - show run (xml | set)                                      |     Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show config (xml | set)                                   |     Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show clients (file | table)                               |     Show the FreeRADIUS client config file"
			print " - show status                                               |     Show the RadiUID and FreeRADIUS service statuses"
			print " - show mappings (<hostname>:<vsys-id> | all | consistency)  |     Show the current IP-to-User mappings of one or all targets or check consistency\n"
		elif arguments == "show config ?":
			print "\n - show config (xml | set)  |   Show the RadiUID configuration in XML format (default) or as set commands"
			print "                            |  "
			print "                            |   Examples: 'show config'"
			print "                            |             'show config xml'"
			print "                            |             'show config set'\n"
		elif arguments == "show run ?":
			print "\n - show run (xml | set)  |   Show the RadiUID configuration in XML format (default) or as set commands"
			print "                         |  "
			print "                         |   Examples: 'show run'"
			print "                         |             'show run xml'"
			print "                         |             'show run set'\n"
		elif arguments == "show mappings" or arguments == "show mappings ?":
			print "\n - show mappings (<hostname>:<vsys-id> | all | consistency)  |   Show the current IP-to-User mappings of one or all targets or"
			print "                                                             |    check the consistency of IP-to-User mappings in all targets"
			print "                                                             |  "
			print "                                                             |   Examples: 'show mappings 192.168.1.1:vsys1'"
			print "                                                             |             'show mappings pan1.domain.com'"
			print "                                                             |             'show mappings pan1.domain.com:4'"
			print "                                                             |             'show mappings all'"
			print "                                                             |             'show mappings consistency'\n"
		elif arguments == "show log":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			configfile = self.filemgmt.find_config("quiet")
			header = "########################## OUTPUT FROM FILE " + logfile + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("more " + logfile)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show acct-logs":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## FILES IN DIRECTORY " + radiuslogpath + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print "\n"
			filelist = self.filemgmt.list_files("quiet", radiuslogpath)
			if len(filelist) > 0:
				for file in filelist:
					print file
			else:
				print self.ui.color("***** Directory " + radiuslogpath + " is currently empty *****", self.ui.red)
			print "\n"
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show run set" or arguments == "show config set":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("NOTE:", self.ui.cyan) + "  Use command '" + self.ui.color(runcmd + " show config xml", self.ui.green) + "' to see configuration in XML format\n"
			header = "########################## OUTPUT FROM FILE " + configfile + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.filemgmt.show_config_item('set', "auto", 'config')
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show run" or arguments == "show run xml" or arguments == "show config" or arguments == "show config xml":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("NOTE:", self.ui.cyan) + "  Use command '" + self.ui.color(runcmd + " show config set", self.ui.green) + "' to see configuration in form of CLI commands\n"
			header = "########################## OUTPUT FROM FILE " + configfile + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print "\n"
			print "###############################################################"
			print "################### Main RadiUID XML Config ###################"
			print "###############################################################"
			self.filemgmt.show_config_item('xml', "none", 'config')
			print "###############################################################"
			print "###############################################################"
			print "\n\n"
			clientconfig =  self.filemgmt.freeradius_client_editor("showraw", "")
			if "FATAL" not in clientconfig:
				print "###############################################################"
				print "################### FreeRADIUS Client Config ##################"
				print "###############################################################"
				print self.filemgmt.freeradius_client_editor("showraw", "")
				print "###############################################################"
				print "###############################################################"
				print "\n"
			else:
				print self.ui.color("********** FreeRADIUS config file doesn't exist **********", self.ui.yellow)
				print "\n"
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show clients" or arguments == "show clients table":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT FREERADIUS RADIUS CLIENTS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print "\n"
			clientinfo = self.filemgmt.freeradius_client_editor("show", "")
			if "FATAL" in clientinfo:
				self.filemgmt.logwriter("cli", self.ui.color(clientinfo, self.ui.red))
				print "\n\n"
				print self.ui.color("Something Went Wrong!", self.ui.red)
			else:
				print self.ui.make_table(["IP Block", "Family", "Shared Secret"], clientinfo)
				print "\n\n"
				print self.ui.color("Success!", self.ui.green)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show clients file":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## OUTPUT FROM FILE /etc/raddb/clients.conf ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("more " + clientconfpath)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show status":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			radiuidstatus = self.imum.service_control("status", "radiuid")
			freeradiusstatus = self.imum.service_control("status", radservicename)
			################## RADIUID CHECK ##################
			header = "########################## CHECKING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print radiuidstatus["action"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if radiuidstatus["status"] == "not-found":
				print self.ui.color("\n\n********** RADIUID IS NOT INSTALLED YET **********\n\n", self.ui.yellow)
			elif radiuidstatus["status"] == "running":
				print self.ui.color("\n\n********** RADIUID IS CURRENTLY RUNNING **********\n\n", self.ui.green)
			elif radiuidstatus["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID IS CURRENTLY NOT RUNNING **********\n\n", self.ui.yellow)
			################## FREERADIUS CHECK ##################
			header = "########################## CHECKING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print freeradiusstatus["action"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if freeradiusstatus["status"] == "not-found":
				print self.ui.color("\n\n********** FREERADIUS IS NOT INSTALLED YET **********\n\n", self.ui.yellow)
			elif freeradiusstatus["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS IS CURRENTLY RUNNING **********\n\n", self.ui.green)
			elif freeradiusstatus["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS IS CURRENTLY NOT RUNNING **********\n\n", self.ui.yellow)
		elif self.cat_list(sys.argv[1:3]) == "show mappings" and re.findall("^[0-9A-Za-z]", sys.argv[3]) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if ":" in sys.argv[3]:
				hostname = sys.argv[3].split(":")[0]
				vsys = sys.argv[3].split(":")[1].replace("vsys", "")
			else:
				hostname = sys.argv[3]
				vsys = "1"
			keepgoing = "yes"
			pulluids = "yes"
			##### Check target hostname against config and check for necessary parameters #####
			if keepgoing == "yes":
				if hostname.lower() != "all" and hostname.lower() != "consistency":
					keepgoing = "no"
					for target in targets:
						if target['hostname'] == hostname and target['vsys'] == vsys:
							keepgoing = "yes"
							targets = [target]
					if keepgoing == "no":
						self.filemgmt.logwriter("cli", self.ui.color("********************* ERROR: Target ", self.ui.red) + self.ui.color(sys.argv[3], self.ui.cyan) + self.ui.color(" does not exist in config. Please configure it.********************", self.ui.red))
						pulluids = "no"
			##### Check parameters for proper data and report errors #####
			if keepgoing == "yes":
				self.filemgmt.scrub_targets("noisy", "scrub") # Scrub the targets for any bad configs
				pankey = self.pafi.pull_api_key("quiet", targets) # Pull the API keys for each target
				uidxmldict = self.pafi.pull_uids(targets) # Pull the mappings for each target
				print "\n\n"
				if hostname.lower() == "consistency":
					print self.dp.map_consistency_check(uidxmldict)
					print "\n\n"
				else:
					for uidset in uidxmldict:
						currentuidset = ElementTree.fromstring(uidxmldict[uidset])
						print "************" + uidset + "************"
						if type(self.filemgmt.tinyxmltodict(currentuidset)['response']['result']) != type({}) or "<count>0</count>" in uidxmldict[uidset]:
							print "\n" + self.ui.color("************No current mappings************", self.ui.yellow)
						else:
							print self.ui.make_table(["ip", "user",  'type', 'idle_timeout', 'timeout', 'vsys'], self.filemgmt.tinyxmltodict(currentuidset)['response']['result']['entry'])
						print "\n\n"
			if pulluids == "yes":
				print self.ui.color("Success!", self.ui.green)
			elif pulluids == "no":
				print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### SET #############################
		elif arguments == "set" or arguments == "set ?":
			print "\n - set logfile <file path>                       |     Set the RadiUID logfile path"
			print " - set radiuslogpath <directory path>            |     Set the path used to find FreeRADIUS accounting log files"
			print " - set acctlogcopypath <directory path>          |     Set the path where RadiUID should copy acct log files before deletion"
			print " - set maxloglines <number-of-lines>             |     Set the max number of lines allowed in the log ('0' turns circular logging off)"
			print " - set userdomain (none | <domain name>)         |     Set the domain name prepended to User-ID mappings"
			print " - set timeout <minutes>                         |     Set the timeout (in minutes) for User-ID mappings sent to the firewall targets"
			print " - set looptime <seconds>                        |     Set the waiting loop time (in seconds) to pause between checks of the RADIUS logs"
			print " - set tlsversion (1.0 | 1.1 | 1.2)              |     Set the version of TLS used for XML API communication with the firewall targets"
			print " - set radiusstopaction (clear | ignore | push)  |     Set the action taken by RadiUID when RADIUS stop messages are received"
			print " - set client (ipv4|ipv6) <ip-block> <secret>    |     Set configuration elements for RADIUS clients to send accounting data FreeRADIUS"
			print " - set munge <rule>.<step> [parameters]          |     Set munge (string processing rules) for User-IDs"
			print " - set target <hostname>:<vsys-id> [parameters]  |     Set configuration elements for existing or new firewall targets\n"
		elif arguments == "set logfile" or arguments == "set logfile ?":
			print "\n - set logfile <file path>  |  Example: 'set logfile /etc/radiuid/radiuid.log'\n"
		elif arguments == "set radiuslogpath" or arguments == "set radiuslogpath ?":
			print "\n - set radiuslogpath <directory path>  |  Example: 'set radiuslogpath /var/log/radius/radacct/'\n"
		elif arguments == "set acctlogcopypath" or arguments == "set acctlogcopypath ?":
			print "\n - set acctlogcopypath <directory path>  |  Example: 'set acctlogcopypath /root/logs/acctlogs/'\n"
		elif arguments == "set maxloglines" or arguments == "set maxloglines ?":
			print "\n - set maxloglines <number-of-lines>  |  Examples: 'set maxloglines 1000'   (circular logging enabled at 1000 lines)"
			print "                                      |            'set maxloglines 0'      (circular logging disabled)"
		elif arguments == "set userdomain" or arguments == "set userdomain ?":
			print "\n - set userdomain (none | <domain name>)  |  Examples: 'set userdomain domain.com'"
			print "                                          |            'set userdomain none'\n"
		elif arguments == "set timeout" or arguments == "set timeout ?":
			print "\n - set timeout <minutes>  |  Example: 'set timeout 60'\n"
		elif arguments == "set looptime" or arguments == "set looptime ?":
			print "\n - set looptime <seconds>  |  Example: 'set looptime 10'\n"
		elif arguments == "set tlsversion" or arguments == "set tlsversion ?":
			print "\n - set tlsversion (1.0 | 1.1 | 1.2)  |  Example: 'set tlsversion 1.2'\n"
		elif arguments == "set radiusstopaction" or arguments == "set radiusstopaction ?":
			print "\n - set radiusstopaction (clear | ignore | push)  |  Example: 'set radiusstopaction clear'\n"
		elif arguments == "set client" or arguments == "set client ?":
			print "\n - set client (ipv4|ipv6) <ip-block> <secret>  |  Example: 'set client ipv4 10.0.0.0/8 password123'\n"
		elif arguments == "set target" or arguments == "set target ?":
			print "\n - set target <hostname>:<vsys-id> [parameters]  |  Parameters: hostname and vsys <hostname>:<vsys-id>"
			print "                                                 |              username <username> "
			print "                                                 |              password <password> "
			print "                                                 |              port  <TCP port number>"
			print "                                                 |              "
			print "                                                 |  Examples:   'set target 192.168.1.1 username admin'"
			print "                                                 |              'set target pan1.domain.com:vsys1 password P@s$w0rd'"
			print "                                                 |              'set target 10.0.0.10:2 username admin password P@ssword"
			print "                                                 |              'set target 10.0.0.10:2 username admin password P@ssword port 4433\n"
		elif arguments == "set munge" or arguments == "set munge ?":
			print "\n - set munge <rule>.<step> [parameters] |  Parameters: match (any | <regex>) (complete | partial)"
			print "                                        |              set-variable <variable name> (from-match | from-string) <regex or string>"
			print "                                        |              assemble <variable name> <variable name> ... "
			print "                                        |              accept"
			print "                                        |              discard"
			print "                                        |              "
			print "                                        |  Examples:   The below rule-set would allow through any user with the domain \"safedomain.com\" in their User-ID,"
			print "                                        |              then it would append the domain \"dangerous.com\" to any others"
			print "                                        |"
			print "                                        |              set munge 1.0 match \".*safedomain.com.*\" complete"
			print "                                        |              set munge 1.1 accept"
			print "                                        |              set munge 2.0 match any"
			print "                                        |              set munge 2.1 set-variable user from-match \".*\""
			print "                                        |              set munge 2.2 set-variable dngr from-string \"dangerous.com\""
			print "                                        |              set munge 2.3 set-variable slsh from-string \"\\\\\""
			print "                                        |              set munge 2.4 assemble dngr slsh user"
		##### SET LOGFILE #####
		elif self.cat_list(sys.argv[1:3]) == "set logfile" and len(re.findall("^(\/*)", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if self.filemgmt.get_globalconfig_item('logfile') == sys.argv[3]:
				print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value is the same as current value****************\n", self.ui.green)
			else:
				pathcheck = self.filemgmt.check_path("file",sys.argv[3])
				if pathcheck[0] == "fail":
					for error in pathcheck[1:]:
						print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: " + error + "****************", self.ui.red)
				elif pathcheck[0] == "pass":
					newlogfiledir = self.filemgmt.strip_filepath(sys.argv[3])[0]
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Making sure directory: "+ newlogfiledir + " exists...creating if not****************\n"
					os.system('mkdir -p ' + newlogfiledir)
					try:
						self.filemgmt.write_file(sys.argv[3], "***********Logfile created via RadiUID command by " + self.imum.currentuser() + "***********\n")
						self.filemgmt.change_config_item('logfile', sys.argv[3])
						print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
						self.filemgmt.save_config()
						print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<logfile> configuration element changed to :\n"
						self.filemgmt.show_config_item('xml', "none", 'logfile')
					except IOError:
						print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: One of the directory names already exists as a file or vice-versa****************\n", self.ui.red)
				if self.filemgmt.get_globalconfig_item('logfile') == sys.argv[3]:
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET MAXLOGLINES #####
		elif self.cat_list(sys.argv[1:3]) == "set maxloglines" and len(re.findall("^(\/*)", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if self.filemgmt.get_globalconfig_item('maxloglines') == sys.argv[3]:
				print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value is the same as current value****************\n", self.ui.green)
			else:
				try:
					int(sys.argv[3])
					keepgoing = True
				except ValueError:
					print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value must be a number****************\n", self.ui.red)
					keepgoing = False
				if keepgoing:
					newlogfiledir = self.filemgmt.strip_filepath(sys.argv[3])[0]
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Making sure directory: "+ newlogfiledir + " exists...creating if not****************\n"
					os.system('mkdir -p ' + newlogfiledir)
					self.filemgmt.change_config_item('maxloglines', sys.argv[3])
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<maxloglines> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'maxloglines')
				if self.filemgmt.get_globalconfig_item('maxloglines') == sys.argv[3]:
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET RADIUSLOGPATH #####
		elif self.cat_list(sys.argv[1:3]) == "set radiuslogpath" and len(re.findall("^(\/*)", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if self.filemgmt.get_globalconfig_item('radiuslogpath') == sys.argv[3]:
				print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value is the same as current value****************\n", self.ui.green)
			else:
				pathcheck = self.filemgmt.check_path("dir",sys.argv[3])
				if pathcheck[0] == "fail":
					for error in pathcheck[1:]:
						print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: " + error + "****************", self.ui.red)
				elif pathcheck[0] == "pass":
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Making sure directory: "+ sys.argv[3] + " exists****************\n"
					pathexists = self.filemgmt.file_exists(sys.argv[3])
					if pathexists == "no":
						print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************WARNING: Directory path doesn't exist. You may need to install FreeRADIUS****************\n", self.ui.yellow)
					self.filemgmt.change_config_item('radiuslogpath', sys.argv[3])
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<radiuslogpath> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'radiuslogpath')
				if self.filemgmt.get_globalconfig_item('radiuslogpath') == sys.argv[3]:
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET ACCTLOGCOPYPATH #####
		elif self.cat_list(sys.argv[1:3]) == "set acctlogcopypath" and len(re.findall("^(\/*)", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if self.filemgmt.get_globalconfig_item('acctlogcopypath') == sys.argv[3]:
				print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value is the same as current value****************\n", self.ui.green)
			else:
				if sys.argv[3].lower() != "none":
					pathcheck = self.filemgmt.check_path("dir",sys.argv[3])
				else:
					pathcheck = ["pass"]
				if pathcheck[0] == "fail":
					for error in pathcheck[1:]:
						print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: " + error + "****************", self.ui.red)
				elif pathcheck[0] == "pass":
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Making sure directory: "+ sys.argv[3] + " exists****************\n"
					if sys.argv[3].lower() != "none":
						pathexists = self.filemgmt.file_exists(sys.argv[3])
						if pathexists == "no":
							print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************WARNING: Directory path doesn't exist****************\n", self.ui.yellow)
					if sys.argv[3].lower() == "none":
						self.filemgmt.change_config_item('acctlogcopypath', None)
					else:
						self.filemgmt.change_config_item('acctlogcopypath', sys.argv[3])
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<acctlogcopypath> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'acctlogcopypath')
				if self.filemgmt.get_globalconfig_item('acctlogcopypath') == sys.argv[3]:
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET USERDOMAIN #####
		elif self.cat_list(sys.argv[1:3]) == "set userdomain" and len(re.findall("^(.*)", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			entereduserdomain = sys.argv[3]
			if self.filemgmt.get_globalconfig_item('userdomain') == entereduserdomain:
				print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value is the same as current value****************\n", self.ui.green)
			else:
				domaincheck = self.filemgmt.check_domainname(entereduserdomain)
				if domaincheck["status"] == "fail":
					for message in domaincheck["messages"]:
						if message.keys()[0] == "FATAL":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.red)
						elif message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
				elif domaincheck["status"] == "pass":
					if entereduserdomain != "none":
						for message in domaincheck["messages"]:
							if message.keys()[0] == "WARNING":
								print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					else:
						entereduserdomain = None
					self.filemgmt.change_config_item('userdomain', entereduserdomain)
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<userdomain> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'userdomain')
				if str(self.filemgmt.get_globalconfig_item('userdomain')) == str(entereduserdomain):
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET TIMEOUT #####
		elif self.cat_list(sys.argv[1:3]) == "set timeout" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			try:
				timeoutval = int(sys.argv[3])
				if timeoutval == 0:
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Timeout value must be a number between 1 and 1440****************\n", self.ui.red)
				elif int(self.filemgmt.get_globalconfig_item('timeout')) == timeoutval:
					print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value is the same as current value****************\n", self.ui.green)
				elif timeoutval > maxtimeout:
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Timeout cannot exceed 1440 minutes (24 hours)****************\n", self.ui.red)
				else:
					self.filemgmt.change_config_item('timeout', sys.argv[3])
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<timeout> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'timeout')
					if self.filemgmt.get_globalconfig_item('timeout') == sys.argv[3]:
						print self.ui.color("Success!", self.ui.green)
					else:
						print self.ui.color("Something Went Wrong!", self.ui.red)
			except ValueError:
				print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Timeout value must be a number between 1 and 1440****************\n", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET LOOPTIME #####
		elif self.cat_list(sys.argv[1:3]) == "set looptime" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			try:
				int(sys.argv[3])
				inputgood = True
			except ValueError:
				inputgood = False
				print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Looptime value must be an integer****************\n", self.ui.red)
			if inputgood:
					self.filemgmt.extend_config_schema()
					self.filemgmt.change_config_item('looptime', sys.argv[3])
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<looptime> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'looptime')
					if self.filemgmt.get_globalconfig_item('looptime') == sys.argv[3]:
						print self.ui.color("Success!", self.ui.green)
					else:
						print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET TLSVERSION #####
		elif self.cat_list(sys.argv[1:3]) == "set tlsversion" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
				self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
				header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
				print self.ui.color(header, self.ui.magenta)
				print self.ui.color("#" * len(header), self.ui.magenta)
				if sys.argv[3].lower() != "1.0" and sys.argv[3].lower() != "1.1" and sys.argv[3].lower() != "1.2":
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Acceptable versions are '1.0', '1.1', and '1.2'****************\n", self.ui.red)
				else:
					self.filemgmt.extend_config_schema()
					self.filemgmt.change_config_item('tlsversion', sys.argv[3].lower())
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<tlsversion> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'tlsversion')
					if self.filemgmt.get_globalconfig_item('tlsversion') == sys.argv[3].lower():
						print self.ui.color("Success!", self.ui.green)
					else:
						print self.ui.color("Something Went Wrong!", self.ui.red)
				print self.ui.color("#" * len(header), self.ui.magenta)
				print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET RADIUSSTOPACTION #####
		elif self.cat_list(sys.argv[1:3]) == "set radiusstopaction" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
				self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
				header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
				print self.ui.color(header, self.ui.magenta)
				print self.ui.color("#" * len(header), self.ui.magenta)
				if sys.argv[3].lower() != "clear" and sys.argv[3].lower() != "ignore" and sys.argv[3].lower() != "push":
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Acceptable actions are 'clear' and 'ignore'****************\n", self.ui.red)
				else:
					self.filemgmt.extend_config_schema()
					self.filemgmt.change_config_item('radiusstopaction', sys.argv[3].lower())
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<radiusstopaction> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'radiusstopaction')
					if self.filemgmt.get_globalconfig_item('radiusstopaction') == sys.argv[3].lower():
						print self.ui.color("Success!", self.ui.green)
					else:
						print self.ui.color("Something Went Wrong!", self.ui.red)
				print self.ui.color("#" * len(header), self.ui.magenta)
				print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET CLIENTS #####
		elif self.cat_list(sys.argv[1:3]) == "set client" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			family = sys.argv[3]
			if family == "ipv4" or family == "ipv6":
				if len(sys.argv) > 4:
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"**************** " + sys.argv[3] + " looks like a legit IPv4 CIDR Block****************\n"
					newclient = self.filemgmt.freeradius_client_editor("append", [{'Shared Secret': sys.argv[5], 'IP Block': sys.argv[4], "Family": sys.argv[3]}])
					if "FATAL" in newclient:
						self.filemgmt.logwriter("cli", self.ui.color(newclient, self.ui.red))
						print "\n\n"
						print self.ui.color("Something Went Wrong!", self.ui.red)
					else:
						print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"**************** New clients added ****************\n"
						print self.ui.make_table(["IP Block", "Family", "Shared Secret"], self.filemgmt.freeradius_client_editor("show", ""))
						print "\n\n"
						print self.ui.color("Success!", self.ui.green)
				else:
					print "\n"
					print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"**************** Please enter a shared secret to use for this set of clients ****************\n", self.ui.red)
					print "\n"
					print self.ui.color("Something Went Wrong!", self.ui.red)
			else:
				print "\n"
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"**************** " + sys.argv[3] + " is not a legit IP family****************\n", self.ui.red)
				print "\n"
				print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET TARGET #####
		elif self.cat_list(sys.argv[1:3]) == "set target" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			keepgoing = "yes"
			###################################
			## Check Input Hostname and VSYS ##
			###################################
			inputcheck = {}
			if ":" in sys.argv[3]:
				words = sys.argv[3].split(":")
				hostname = words[0]
				vsys = words[1].replace("vsys", "")
			else:
				hostname = sys.argv[3]
				vsys = "1"
			if self.filemgmt.ip_checker("address", hostname) == "pass":
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Hostname " + hostname + " looks like legit IPv4 address****************\n"
				inputcheck.update({"hostnamecheck": "pass"})
			else:
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Hostname " + hostname + " looks like a domain name****************\n"
				domaincheck = self.filemgmt.check_domainname(hostname)
				if domaincheck["status"] == "fail":
					for message in domaincheck["messages"]:
						if message.keys()[0] == "FATAL":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.red)
						elif message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"hostnamecheck": "fail"})
				elif domaincheck["status"] == "pass":
					for message in domaincheck["messages"]:
						if message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"hostnamecheck": "pass"})
			try:
				if int(vsys) <= 255 and int(vsys) >= 1:
					inputcheck.update({"vsyscheck": "pass"})
				else:
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "**************** FATAL: Invalid VSYS ID. Please use a number between 1 and 255****************\n", self.ui.red)
					inputcheck.update({"vsyscheck": "fail"})
			except ValueError:
				print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "**************** FATAL: Invalid VSYS ID. Please use a number between 1 and 255****************\n", self.ui.red)
				inputcheck.update({"vsyscheck": "fail"})
			##############################
			## Check other input values ##
			##############################
			## Compile arguments ##
			targetparams = {'hostname': hostname, "vsys": vsys}
			searchqueries = ['username', 'password', 'port']
			cliparams = sys.argv[4:]
			targetindices = self.dp.find_index_in_list(searchqueries, cliparams)
			for key in targetindices:
				try:
					targetparams.update({key: cliparams[targetindices[key] + 1]})
				except IndexError:
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************WARNING: You didn't enter the value for " + key + "****************\n", self.ui.yellow)
			## Check inputs ##
			try:
				usercheck = self.filemgmt.check_userpass("user", targetparams["username"])
				if usercheck["status"] == "fail":
					for message in usercheck["messages"]:
						if message.keys()[0] == "FATAL":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.red)
						elif message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"usercheck": "fail"})
				else:
					for message in usercheck["messages"]:
						if message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"usercheck": "pass"})
			except KeyError:
				null = None
			try:
				passwordcheck = self.filemgmt.check_userpass("password", targetparams["password"])
				if passwordcheck["status"] == "fail":
					for message in passwordcheck["messages"]:
						if message.keys()[0] == "FATAL":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.red)
						elif message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"passwordcheck": "fail"})
				else:
					for message in passwordcheck["messages"]:
						if message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"passwordcheck": "pass"})
			except KeyError:
				null = None
			###########################################
			## Eval input checks and continue or not ##
			###########################################
			applysettings = "yes"
			for check in inputcheck.values():
				if check == "fail":
					applysettings = "no"
			if applysettings == "yes":
				status = "pass"
				results = self.filemgmt.add_targets([targetparams])
				for message in results[hostname]["messages"]:
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************"+ message + "****************\n"
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
				self.filemgmt.save_config()
				self.filemgmt.show_config_item('xml', "none", 'targets')
				#### Republish config/targets and run targets through scrubber #####
				self.filemgmt.publish_config('quiet')
				self.filemgmt.scrub_targets("noisy", "report")
			if applysettings == "yes":
				print self.ui.color("Success!", self.ui.green)
			elif applysettings == "no":
				print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### SET MUNGE #####
		elif self.cat_list(sys.argv[1:3]) == "set munge" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			#########################
			###### HELPERS AND ######
			###### INPUT CHECKS #####
			#########################
			helper = "\n - set munge <rule>.<step> [parameters] |  Parameters: match (any | <regex>)"\
						"\n                                        |              set-variable <variable name> (from-match | from-string) <regex or string>"\
						"\n                                        |              assemble <variable name> <variable name> ... "\
						"\n                                        |              accept"\
						"\n                                        |              discard"\
						"\n                                        |              "\
						"\n                                        |  Examples:   The below rule-set would allow through any user with the domain \"safedomain.com\" in their User-ID,"\
						"\n                                        |              then it would append the domain \"dangerous.com\" to any others"\
						"\n                                        |"\
						"\n                                        |              set munge 1.0 match \".*safedomain.com.*\" complete"\
						"\n                                        |              set munge 1.1 accept"\
						"\n                                        |              set munge 2.0 match any"\
						"\n                                        |              set munge 2.1 set-variable user from-match \".*\""\
						"\n                                        |              set munge 2.2 set-variable dngr from-string \"dangerous.com\""\
						"\n                                        |              set munge 2.3 set-variable slsh from-string \"\\\\\""\
						"\n                                        |              set munge 2.4 assemble dngr slsh user"
			### CHECK RULE AND STEP NUMBERS ###
			try:
				if "." in sys.argv[3]:
					rulenum = sys.argv[3].split(".")[0]
					stepnum = sys.argv[3].split(".")[1]
					if rulenum == re.findall('[0-9]+', rulenum)[0] and stepnum == re.findall('[0-9]+', stepnum)[0]:
						keepgoing = True
					else:
						print self.ui.color("\n\nRule and step numbers must be numerical and seperated by a period (ie: set munge 1.0 ...)\n\n", self.ui.red)
						print helper
						keepgoing = False
					if len(stepnum) > 1 and stepnum[0] == "0":
						print self.ui.color("\n\nNo leading zeros in step numbers dammit!\n\n", self.ui.red)
						keepgoing = False
				elif sys.argv[3] == 'debug':
					configinput = {'debug': None}
					self.filemgmt.munge_config(configinput)
					self.filemgmt.save_config()
					self.filemgmt.show_config_item('xml', "none", 'munge')
				else:
					print self.ui.color("\n\nRule and step numbers must be numerical and seperated by a period (ie: set munge 1.0 ...)\n\n", self.ui.red)
					print helper
					keepgoing = False
			except IndexError:
				print self.ui.color("\n\nRule and step numbers must be numerical and seperated by a period (ie: set munge 1.0 ...)\n\n", self.ui.red)
				print helper
				keepgoing = False
			### INTERCEPT BAD OR INCOMPLETE INPUTS AND SHOW HELPERS ###
			if keepgoing:
				acceptableactions = ['accept', 'discard', 'set-variable', 'assemble']
				acceptablepatterns = ['complete', 'partial']
				if len(sys.argv) == 4:
					if stepnum == "0":
						print "\n\n - set munge "+sys.argv[3]+" match (any | <regex pattern>) (complete | partial)\n\n"
						print "        NOTE: The match statement on the '0' step is used to determine when to process the rule"
						print "              The rule can be activated on either a partial or complete regex match\n\n"
					else:
						print "\n\n - set munge "+sys.argv[3]+" (accept | assemble | discard | set-variable) [parameters]\n\n"
				elif len(sys.argv) == 5 and sys.argv[4] == "set-variable" and stepnum != "0":
					print "\n\n - set munge "+sys.argv[3]+" set-variable <variable name> (from-match | from-string) (any | <regex | <string>)\n\n"
				elif len(sys.argv) == 6 and sys.argv[4] == "set-variable" and stepnum != "0":
					print "\n\n - set munge "+sys.argv[3]+" set-variable "+sys.argv[5]+" (from-match | from-string) (any | <regex | <string>)\n\n"
				elif len(sys.argv) == 7 and sys.argv[4] == "set-variable" and stepnum != "0":
					acceptablesourcetypes = ['from-match', 'from-string']
					if sys.argv[6] not in acceptablesourcetypes:
						print self.ui.color("\n\nAcceptable source types are 'from-match', and 'from-string'\n\n", self.ui.red)
					else:
						if sys.argv[6] == "from-match":
							print "\n\n - set munge "+sys.argv[3]+" set-variable "+sys.argv[5]+" "+sys.argv[6]+" (any | \"<regex pattern>\")\n"
							print "        NOTE: Make sure to wrap your regex pattern in quotes\n\n"
						elif sys.argv[6] == "from-string":
							print "\n\n - set munge "+sys.argv[3]+" set-variable "+sys.argv[5]+" "+sys.argv[6]+" \"<string>\"\n"
							print "        NOTE: Make sure to wrap your string in quotes\n\n"
				elif len(sys.argv) == 5 and sys.argv[4] == "assemble" and stepnum != "0":
					print "\n\n - set munge "+sys.argv[3]+" assemble <variable name> <variable name> ... \n"
					print "        NOTE: Enter the variables you would like to assemble in the order in which they should be assembled\n\n"
				elif len(sys.argv) == 5 and sys.argv[4] == "match" and stepnum == "0":
					print "\n\n - set munge "+sys.argv[3]+" match (any | <regex pattern>) (complete | partial) \n"
					print "        NOTE: The 'any' match statement will always process the rule. A regex pattern will only process the rule when matched.\n\n"
				elif len(sys.argv) == 6 and sys.argv[4] == "match" and stepnum == "0" and sys.argv[5] != 'any':
					print "\n\n - set munge "+sys.argv[3]+" match "+ sys.argv[5] +" (complete | partial) \n"
					print "        NOTE: The 'complete' statement will require the regex pattern to return a match of the whole User-ID to activate the rule."
					print "        NOTE: The 'partial' statement will allow the regex pattern to return a partial match of the User-ID to activate the rule.\n\n"
				elif len(sys.argv) == 7 and sys.argv[4] == "match" and stepnum == "0" and sys.argv[6] not in acceptablepatterns:
					print self.ui.color("\n\nUnrecognized return criterion\n", self.ui.red)
					print self.ui.color("A rule's match return criterion activates a rule either when the regex pattern match is COMPLETE or PARTIAL\n\n", self.ui.red)
					print "\n\n###### Acceptable match criteria: ######\n"
					print "\n - set munge "+sys.argv[3]+" match "+ sys.argv[5] +" (complete | partial) \n\n"
				elif len(sys.argv) == 5 and sys.argv[4] != "match" and stepnum == "0":
					print self.ui.color("\n\nA rule's '0' step (X.0) must be a match statement (ie: set munge 1.0 match \"[a-z]+$\")\n", self.ui.red)
					print self.ui.color("The rule's match statement is used to match a certain input and activate processing of the rule\n\n", self.ui.red)
					print "\n\n###### Acceptable actions for this step number: ######\n"
					print "\n - set munge "+sys.argv[3]+" match (any | <regex pattern>)\n\n"
				elif len(sys.argv) == 6 and sys.argv[4] != "match" and stepnum == "0":
					print self.ui.color("\n\nA rule's '0' step (X.0) must be a match statement (ie: set munge 1.0 match \"[a-z]+$\")\n", self.ui.red)
					print self.ui.color("The rule's match statement is used to match a certain input and activate processing of the rule\n\n", self.ui.red)
					print "\n\n###### Acceptable actions for this step number: ######\n"
					print "\n\n - set munge "+sys.argv[3]+" match (any | <regex pattern>)\n\n"
				elif len(sys.argv) >= 5 and sys.argv[4] == "match" and stepnum != "0":
					print self.ui.color("\n\nOnly the rule's '0' step (X.0) is allowed to be a match statement (ie: set munge 1.0 match '[a-z]+')\n", self.ui.red)
					print self.ui.color("The rule's match statement is used to match a certain input and activate processing of the rule\n\n", self.ui.red)
					print "\n\n###### Acceptable actions for this step number: ######\n"
					print " - set munge "+sys.argv[3]+" (accept | assemble | discard | set-variable) [parameters]\n\n"
				elif len(sys.argv) == 5 and stepnum != "0" and sys.argv[4] not in acceptableactions:
					print self.ui.color("\n\nUnrecognized action. Allowed simple actions are 'accept', and 'discard'", self.ui.red)
					print self.ui.color("\nAllowed complex actions are 'set-variable', and 'assemble'\n\n", self.ui.red)
					print "\n\n###### Acceptable actions for this step number: ######\n"
					print "\n\n - set munge "+sys.argv[3]+" (accept | assemble | discard | set-variable) [parameters]\n\n"
				elif stepnum == "0" and sys.argv[4] != "match":
					print self.ui.color("\n\nA rule's '0' step (X.0) must be a match statement (ie: set munge 1.0 match \"[a-z]+$\")\n", self.ui.red)
					print self.ui.color("The rule's match statement is used to match a certain input and activate processing of the rule\n\n", self.ui.red)
					print "\n\n###### Acceptable actions for this step number: ######\n"
					print "\n\n - set munge "+sys.argv[3]+" match (any | <regex pattern>)\n\n"
				else:
					###############################
					######## PROCESS INPUT ########
					###############################
					self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
					header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
					print self.ui.color(header, self.ui.magenta)
					print self.ui.color("#" * len(header), self.ui.magenta)
					print "\n"
					rule = 'rule' + rulenum
					step = 'step' + stepnum
					action = sys.argv[4]
					### Check that initial match statement exists ##
					if stepnum != "0":
						keepgoing = False
						try:
							for each in configdict['globalsettings']['munge'][rule]:
								if each == "match":
									keepgoing = True
						except KeyError:
							print self.ui.color("\n\nRule does not have initial 'match' statement yet", self.ui.red)
							print self.ui.color("\nAll rules must begin with a step '0' and a match statement (ie: 'set munge %s.0 match any')\n\n", self.ui.red) % (str(rulenum))
					###### Parse and enter command ######
					if keepgoing:
						if len(sys.argv) == 5 and step != "0":
							configinput = {rule: {step: {action: None}}}
						elif len(sys.argv) == 6 and action == "match":
							if sys.argv[5] == 'any':
								configinput = {rule: {'match': {'any': None}}}
						elif len(sys.argv) == 7 and action == "match":
							try:
								re.findall(sys.argv[5], "")
								regexgood = True
							except Exception as e:
								print self.ui.color("\n\nInvalid regular expression. Please check it and re-enter", self.ui.red)
								print self.ui.color("\nERROR: " + str(e), self.ui.red)
								regexgood = False
							if regexgood:
								configinput = {rule: {'match': {'regex': sys.argv[5], 'criterion': sys.argv[6]}}}
							else:
								keepgoing = False
						elif len(sys.argv) == 8 and action == 'set-variable':
							variable = sys.argv[5]
							sourcetype = sys.argv[6]
							source = sys.argv[7]
							if source == "any":
								configinput = {rule: {step: {sourcetype: {source: None}, action: variable}}}
							elif sourcetype == "from-string":
								configinput = {rule: {step: {sourcetype: source, action: variable}}}
							else:
								try:
									re.findall(source, "")
									regexgood = True
								except Exception as e:
									print self.ui.color("\n\nInvalid regular expression. Please check it and re-enter", self.ui.red)
									print self.ui.color("\nERROR: " + str(e), self.ui.red)
									regexgood = False
								if regexgood:
									configinput = {rule: {step: {sourcetype: source, action: variable}}}
								else:
									keepgoing = False
						elif len(sys.argv) > 5 and action == 'assemble':
							variables = sys.argv[5:]
							variablenum = 1
							configinput = {rule: {step: {'assemble': {}}}}
							for variable in variables:
								configinput[rule][step]['assemble'].update({'variable' + str(variablenum): variable})
								variablenum += 1
						if keepgoing:
							self.filemgmt.munge_config(configinput)
							self.filemgmt.save_config()
							self.filemgmt.show_config_item('xml', "none", 'munge')
					print "\n"
					if keepgoing:
						print self.ui.color("Success!", self.ui.green)
					else:
						print self.ui.color("Something Went Wrong!", self.ui.red)
					print self.ui.color("#" * len(header), self.ui.magenta)
					print self.ui.color("#" * len(header), self.ui.magenta)
		######################### PUSH #############################
		elif arguments == "push" or arguments == "push ?":
			print "\n - push (<hostname>:<vsys-id> | all) [parameters]  |  Parameters: (<username>, <ip address>, bypass-munge)"
			print "                                                   |              "
			print "                                                   |  Examples:   'push 192.168.1.1:vsys1 administrator 10.0.0.1 bypass-munge'"
			print "                                                   |              'push pan1.domain.com:3 jsmith 172.30.50.100'"
			print "                                                   |              'push all jsmith 172.30.50.100'\n"
		elif self.cat_list(sys.argv[1:2]) == "push" and len(re.findall("[0-9A-Za-z]", sys.argv[2])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			keepgoing = "yes"
			pushuser = "yes"
			if len(sys.argv) > 5:
				if sys.argv[5] == 'bypass-munge':
					global tomunge
					tomunge = False
			##### Check target hostname against config and check for necessary parameters #####
			if len(sys.argv[3:5]) != 2:
				self.filemgmt.logwriter("cli", self.ui.color("********************* ERROR: Some parameters are missing. Use '", self.ui.red) + self.ui.color(runcmd + " push ?", self.ui.cyan) + self.ui.color("' to see proper use and examples.********************", self.ui.red))
				pushuser = "no"
				keepgoing = "no"
			if ":" in sys.argv[2]:
				hostname = sys.argv[2].split(":")[0]
				vsys = sys.argv[2].split(":")[1].replace("vsys", "")
			else:
				hostname = sys.argv[2]
				vsys = "1"
			if keepgoing == "yes":
				if hostname.lower() != "all":
					keepgoing = "no"
					for target in targets:
						if target['hostname'] == hostname and target['vsys'] == vsys:
							keepgoing = "yes"
							targets = [target]
					if keepgoing == "no":
						self.filemgmt.logwriter("cli", self.ui.color("********************* ERROR: Target ", self.ui.red) + self.ui.color(hostname + ":vsys" + vsys, self.ui.cyan) + self.ui.color(" does not exist in config. Please configure it.********************", self.ui.red))
						pushuser = "no"
			##### Check parameters for proper data and report errors #####
			if keepgoing == "yes":
				#### Removed so that any input can be used in the push command ####
				#usercheck = self.filemgmt.check_userpass("user", sys.argv[3])
				#if usercheck["status"] != "pass":
				#	for message in usercheck["messages"]:
				#		if message.keys()[0] == "FATAL":
				#			self.filemgmt.logwriter("cli", self.ui.color("****************" + message.keys()[0] + ": " + message.values()[0] + "****************", self.ui.red))
				#			pushuser = "no"
				#		elif message.keys()[0] == "WARNING":
				#			self.filemgmt.logwriter("cli", self.ui.color("****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow))
				if self.filemgmt.ip_checker("address", sys.argv[4]) != "pass":
					self.filemgmt.logwriter("cli", self.ui.color("****************FATAL: Bad IP Address****************", self.ui.red))
					pushuser = "no"
				if pushuser == "yes":
					self.filemgmt.scrub_targets("noisy", "scrub")
					pankey = self.pafi.pull_api_key("noisy", targets)
					self.pafi.push_uids({sys.argv[4]: {"username": sys.argv[3], "status": "start"}}, [])
			if pushuser == "yes":
				print self.ui.color("Success!", self.ui.green)
			elif pushuser == "no":
				print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### TAIL #############################
		elif arguments == "tail" or arguments == "tail ?":
			print "\n - tail log (<# of lines>)    |     Watch the RadiUID log file in real time\n"
		elif self.cat_list(sys.argv[1:3]) == "tail log":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## OUTPUT FROM FILE " + logfile + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if len(sys.argv) == 3:
				os.system("tail -fn 25 " + logfile)
			else:
				try:
					lineqty = int(sys.argv[3])
					os.system("tail -fn " + str(lineqty) + " " + logfile)
				except ValueError:
					self.filemgmt.logwriter("cli", self.ui.color("****************FATAL: '" + sys.argv[3] + "' is a bad input for number of lines. Please input a number****************", self.ui.red))
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### CLEAR #############################
		elif arguments == "clear" or arguments == "clear ?":
			print "\n - clear log                                                   |     Delete the content in the log file"
			print " - clear acct-logs                                             |     Delete the log files currently in the FreeRADIUS accounting directory"
			print " - clear client (<ip-block> | all)                             |     Delete one or all RADIUS client IP blocks in FreeRADIUS config file"
			print " - clear munge (<rule> | all) (<step> | all)                   |     Delete one or all munge rules in the config file"
			print " - clear target (<hostname>:<vsys-id> | all)                   |     Delete one or all firewall targets in the config file"
			print " - clear mappings (<hostname>:<vsys-id> | all) (<ip> | all)    |     Remove one or all IP-to-User mappings from one or all firewalls\n"
		elif arguments == "clear client" or arguments == "clear client ?":
			print "\n - clear client (<ip-block> | all) |  Examples: 'clear client 10.0.0.0/8'"
			print "                                   |            'clear client all'\n"
		elif arguments == "clear munge" or arguments == "clear munge ?":
			print "\n - clear munge (<rule> | all) (<step> | all)  |  Examples: 'clear munge rule1'"
			print "                                              |            'clear munge rule10 step3'"
			print "                                              |            'clear munge all'\n"
		elif arguments == "clear target" or arguments == "clear target ?":
			print "\n - clear target (<hostname>:<vsys-id> | all)  |  Examples: 'clear target 192.168.1.1:vsys1'"
			print "                                              |            'clear target pan1.domain.com:2'"
			print "                                              |            'clear target all'\n"
		elif arguments == "clear mappings" or arguments == "clear mappings ?":
			print "\n - clear mappings (<hostname>:<vsys-id> | all) (<ip> | all)     |  Examples: 'clear mappings pan1.domain.com:vsys1 10.0.0.1'"
			print "                                                                |            'clear mappings 192.168.1.1:2 all'"
			print "                                                                |            'clear mappings all all'\n"
		##### CLEAR LOG #####
		elif arguments == "clear log":
			print self.ui.color("********************* You are about to clear out the RadiUID log file... (" + logfile + ") ********************", self.ui.yellow)
			raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
			os.system("rm -f "+ logfile)
			self.filemgmt.write_file(logfile, "***********Logfile cleared via RadiUID command by " + self.imum.currentuser() + "***********\n")
			print self.ui.color("********************* Cleared logfile: " + logfile + " ********************", self.ui.yellow)
		##### CLEAR ACCT-LOGS #####
		elif arguments == "clear acct-logs":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print "\n"
			filelist = self.filemgmt.list_files("quiet", radiuslogpath)
			if len(filelist) > 0:
				for file in filelist:
					print file
				print "\n\n"
				print self.ui.color("********************* You are about to delete all files, listed above, in directory... (" + radiuslogpath + ") ********************", self.ui.yellow)
				raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
				print "\n\n"
				self.filemgmt.remove_files(filelist)
				self.filemgmt.logwriter("cli", "##### FreeRADIUS accounting files deleted by user '" + self.imum.currentuser()+ "' #####")
				print "\n"
				print self.ui.color("Success!", self.ui.green)
			else:
				print self.ui.color("***** Directory " + radiuslogpath + " is currently empty *****", self.ui.red)
				print self.ui.color("***** Nothing to do *****", self.ui.red)
			print "\n"
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### CLEAR CLIENT #####
		elif self.cat_list(sys.argv[1:3]) == "clear client" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if sys.argv[3] == "all":
				print "\n"
				self.filemgmt.logwriter("cli", "**************** Removing all RADIUS client IP blocks ****************")
				clearresult = self.filemgmt.freeradius_client_editor("clear", [])
				if "FATAL" in clearresult:
					print "\n"
					self.filemgmt.logwriter("cli", self.ui.color(clearresult, self.ui.red))
					print "\n\n"
					print self.ui.color("Something Went Wrong!", self.ui.red)
				else:
					print self.ui.make_table(["IP Block", "Family", "Shared Secret"], self.filemgmt.freeradius_client_editor("show", ""))
					print "\n"
					print self.ui.color("Success!", self.ui.green)
			else:
				existingclient = False
				currentclients = self.filemgmt.freeradius_client_editor("show", "")
				if "FATAL" in currentclients:
					print "\n"
					self.filemgmt.logwriter("cli", self.ui.color(currentclients, self.ui.red))
					print "\n\n"
					print self.ui.color("Something Went Wrong!", self.ui.red)
				else:
					for client in currentclients:
						if client['IP Block'] == sys.argv[3]:
							existingclient = True
					if existingclient:
						print "\n"
						self.filemgmt.logwriter("cli", "**************** Removing client IP block " + sys.argv[3] + " ****************")
						self.filemgmt.freeradius_client_editor("clear", [{'IP Block': sys.argv[3]}])
						print self.ui.make_table(["IP Block", "Family", "Shared Secret"], self.filemgmt.freeradius_client_editor("show", ""))
						print "\n"
						print self.ui.color("Success!", self.ui.green)
					else:
						self.filemgmt.logwriter("cli", self.ui.color("**************** " + sys.argv[3] + " does not exist as a current client IP block ****************", self.ui.yellow))
						print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### CLEAR MUNGE ALL #####
		elif arguments == "clear munge all":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print "\n\n"
			print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"**************** Removing all munge configuration ****************\n"
			if self.filemgmt.get_globalconfig_item('munge') == None:
				print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: No munge configuration currently exist in config****************\n", self.ui.red)
			else:
				print "\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Deleting configuration items: ****************\n"
				self.filemgmt.show_config_item('xml', "none", 'munge')
				self.filemgmt.munge_config({})
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
				self.filemgmt.save_config()
			print "\n"
			print self.ui.color("Success!", self.ui.green)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### CLEAR MUNGE SPECIFIC #####
		elif self.cat_list(sys.argv[1:3]) == "clear munge" and re.findall("^[0-9A-Za-z]", sys.argv[3]) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			itemexists = False
			if len(sys.argv) >= 4:
				rulelist = []
				steplist = ['all']
				try:
					for rulename in configdict['globalsettings']['munge'].keys():
						rulelist.append(rulename)
				except KeyError:
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: No munge configuration currently exist in config****************\n", self.ui.red)
				if sys.argv[3] in rulelist:
					itemexists = True
				if itemexists:
					rule = sys.argv[3]
					if len(sys.argv) >= 5:
						for stepname in configdict['globalsettings']['munge'][rule].keys():
							if stepname != "match":
								steplist.append(stepname)
						if sys.argv[4] in steplist:
							itemexists = True
						else:
							itemexists = False
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: That step does not exist in "+rule+"****************\n", self.ui.red)
						if itemexists:
							step = sys.argv[4]
				else:
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: That rule does not exist****************\n", self.ui.red)
				if itemexists:
					if len(sys.argv) > 4 and sys.argv[4] == "all":
						print "\n\n"
						print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Removing munge "+ rule + "****************\n"
						self.filemgmt.munge_config({'clear': rule})
						print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
						self.filemgmt.save_config()
					elif len(sys.argv) > 4:
						print "\n\n"
						print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Removing munge "+ rule + " "+step+"****************\n"
						self.filemgmt.munge_config({'clear': {rule: step}})
						print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
						self.filemgmt.save_config()
					else:
						itemexists = False
						print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Missing <step> or 'all' term after rule name****************\n", self.ui.red)
					if itemexists:
						print "\n"
						print self.ui.color("Success!", self.ui.green)
				else:
					print "\n"
					print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### CLEAR TARGET ALL #####
		elif arguments == "clear target all":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if self.filemgmt.get_globalconfig_item('target') == None:
				print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: No targets currently exist in config****************\n", self.ui.red)
			else:
				print "\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Deleting configuration items: ****************\n"
				self.filemgmt.show_config_item('xml', "none", 'targets')
				self.filemgmt.clear_targets()
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
				self.filemgmt.save_config()
				if self.filemgmt.get_globalconfig_item('target') == None:
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### CLEAR TARGET <HOSTNAME> #####
		elif self.cat_list(sys.argv[1:3]) == "clear target" and re.findall("^[0-9A-Za-z]", sys.argv[3]) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			targetexists = "no"
			if ":" in sys.argv[3]:
				hostname = sys.argv[3].split(":")[0]
				vsys = sys.argv[3].split(":")[1].replace("vsys", "")
			else:
				hostname = sys.argv[3]
				vsys = "1"
			try:
				for target in targets:
					if target['hostname'] == hostname and target['vsys'] == vsys:
						targetexists = "yes"
				if targetexists == "no":
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Target " + hostname + ":vsys" + vsys + " doesn't currently exist in config****************\n", self.ui.red)
				elif targetexists == "yes":
					print "\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Deleting target: " + sys.argv[3] + " ****************\n"
					targetremove = self.filemgmt.remove_targets([{'hostname': hostname, "vsys": vsys}])
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					if targetremove[0] == "pass":
						print self.ui.color("Success!", self.ui.green)
					else:
						print self.ui.color("Something Went Wrong!", self.ui.red)
			except NameError:
				print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: No targets currently exist in config****************\n", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		##### CLEAR MAPPINGS #####
		elif self.cat_list(sys.argv[1:3]) == "clear mappings" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if ":" in sys.argv[3]:
				hostname = sys.argv[3].split(":")[0]
				vsys = sys.argv[3].split(":")[1].replace("vsys", "")
			else:
				hostname = sys.argv[3]
				vsys = "1"
			keepgoing = "yes"
			##### Check target hostname against config and check for necessary parameters #####
			if len(sys.argv[3:5]) != 2:
				self.filemgmt.logwriter("cli", self.ui.color("********************* ERROR: Some parameters are missing. Use '", self.ui.red) + self.ui.color(runcmd + " clear mappings ?", self.ui.cyan) + self.ui.color("' to see proper use and examples.********************", self.ui.red))
				keepgoing = "no"
			if keepgoing == "yes":
				if hostname.lower() != "all":
					keepgoing = "no"
					for target in targets:
						if target['hostname'] == hostname and target['vsys'] == vsys:
							keepgoing = "yes"
							targets = [target]
					if keepgoing == "no":
						self.filemgmt.logwriter("cli", self.ui.color("********************* ERROR: Target ", self.ui.red) + self.ui.color(hostname + ":vsys" + vsys, self.ui.cyan) + self.ui.color(" does not exist in config. Please configure it.********************", self.ui.red))
			if keepgoing == "yes":
				if sys.argv[4].lower() != "all":
					if self.filemgmt.ip_checker("address", sys.argv[4]) != "pass":
						self.filemgmt.logwriter("cli", self.ui.color("****************FATAL: Bad IP Address****************", self.ui.red))
						keepgoing = "no"
			if keepgoing == "yes":
				print "\n\n",self.ui.color("********************* You are about to remove IP-to-User mappings. Please confirm... ********************", self.ui.yellow)
				raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
				self.filemgmt.scrub_targets("noisy", "scrub")
				print "\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Removing IP-to-User Mappings... ****************\n"
				if sys.argv[4].lower() == "all":
					pankey = self.pafi.pull_api_key("quiet", targets)
					tempresult = self.pafi.clear_uids(targets, "all")
				else:
					pankey = self.pafi.pull_api_key("quiet", targets)
					tempresult = self.pafi.clear_uids(targets, sys.argv[4])
				resultlist = []
				debug = ""
				for target in tempresult:
					tempdict = {"hostname": target}
					for command in tempresult[target]:
						if 'status="success"' in tempresult[target][command]:
							tempdict.update({command: self.ui.color("success", self.ui.green)})
						else:
							tempdict.update({command: self.ui.color("failed", self.ui.red)})
							debug += tempresult[target][command] + "\n\n"
					resultlist.append(tempdict)
					del tempdict
				print "\n"
				print self.ui.make_table(["hostname", "DP-CLEAR", "MP-CLEAR"], resultlist).replace("hostname", "HOSTNAME")
				if debug != "":
					print "\n\n" + self.ui.color(debug, self.ui.red)
				print "\n"
			if keepgoing == "yes":
				print self.ui.color("Success!", self.ui.green)
			elif keepgoing == "no":
				print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### EDIT #############################
		elif arguments == "edit" or arguments == "edit ?":
			print "\n - edit config      |     Edit the RadiUID config file"
			print " - edit clients     |     Edit RADIUS client config file for FreeRADIUS\n"
		elif arguments == "edit config":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("****************** You are about to edit the RadiUID config file in VI ******************", self.ui.yellow)
			print self.ui.color("**************** It is recommend you use 'set' commands instead of this *****************", self.ui.yellow)
			print self.ui.color("********************* Confirm that you know how to use the VI editor ********************", self.ui.yellow)
			raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
			os.system("vi " + configfile)
		elif arguments == "edit clients":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("****************** You are about to edit the FreeRADIUS client file in VI ******************", self.ui.yellow)
			print self.ui.color("***** It is recommend you use 'set client' and 'clear client' commands instead of this *****", self.ui.yellow)
			print self.ui.color("*********************** Confirm that you know how to use the VI editor *********************", self.ui.yellow)
			raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
			os.system("vi " + clientconfpath)
		######################### SERVICE CONTROL #############################
		elif arguments == "service" or arguments == "service ?":
			print "\n - Usage: radiuid service (radiuid | freeradius | all) (start | stop | restart)"
			print "----------------------------------------------------------------------------------"
			print "\n - service radiuid (start | stop | restart)      |     Control the RadiUID system service"
			print " - service freeradius (start | stop | restart)   |     Control the FreeRADIUS system service"
			print " - service all (start | stop | restart)          |     Control the RadiUID and FreeRADIUS system services\n"
		elif arguments == "service radiuid" or arguments == "service radiuid ?":
			print "\n - service radiuid start        |     Start the RadiUID system service"
			print " - service radiuid stop         |     Stop the RadiUID system service"
			print " - service radiuid restart      |     Restart the RadiUID system service\n"
		elif arguments == "service freeradius" or arguments == "service freeradius ?":
			print "\n - service freeradius start        |     Start the FreeRADIUS system service"
			print " - service freeradius stop         |     Stop the FreeRADIUS system service"
			print " - service freeradius restart      |     Restart the FreeRADIUS system service\n"
		elif arguments == "service all" or arguments == "service all ?":
			print "\n - service all start        |     Start the RadiUID and FreeRADIUS system services"
			print " - service all stop         |     Stop the RadiUID and FreeRADIUS system services"
			print " - service all restart      |     Restart the RadiUID and FreeRADIUS system services\n"
		############ RADIUID SERVICE CONTROL ############
		elif arguments == "service radiuid start":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			svcctloutput = self.imum.service_control("start", "radiuid")
			header = "########################## STARTING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		elif arguments == "service radiuid stop":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("\n***** ARE YOU SURE YOU WANT TO STOP IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			svcctloutput = self.imum.service_control("stop", "radiuid")
			header = "########################## STOPPING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		elif arguments == "service radiuid restart":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("\n***** ARE YOU SURE YOU WANT TO RESTART IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			svcctloutput = self.imum.service_control("stop", "radiuid")
			header = "########################## STOPPING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
			svcctloutput = self.imum.service_control("start", "radiuid")
			header = "########################## STARTING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID RESTART UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		############ FREERADIUS SERVICE CONTROL ############
		elif arguments == "service freeradius start":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			svcctloutput = self.imum.service_control("start", radservicename)
			header = "########################## STARTING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		elif arguments == "service freeradius stop":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("\n***** ARE YOU SURE YOU WANT TO STOP IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			svcctloutput = self.imum.service_control("stop", radservicename)
			header = "########################## STOPPING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		elif arguments == "service freeradius restart":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("\n***** ARE YOU SURE YOU WANT TO RESTART IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			svcctloutput = self.imum.service_control("stop", radservicename)
			header = "########################## STOPPING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
			svcctloutput = self.imum.service_control("start", radservicename)
			header = "########################## STARTING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS RESTART UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		############ COMBINED SERVICE CONTROL ############
		elif arguments == "service all start":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			svcctloutput = self.imum.service_control("start", "radiuid")
			header = "########################## STARTING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
			svcctloutput = self.imum.service_control("start", radservicename)
			header = "########################## STARTING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		elif arguments == "service all stop":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("\n***** ARE YOU SURE YOU WANT TO STOP BOTH SERVICES?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			svcctloutput = self.imum.service_control("stop", "radiuid")
			header = "########################## STOPPING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
			svcctloutput = self.imum.service_control("stop", radservicename)
			header = "########################## STOPPING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		elif arguments == "service all restart":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("\n***** ARE YOU SURE YOU WANT TO RESTART BOTH SERVICES?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			svcctloutput = self.imum.service_control("stop", "radiuid")
			header = "########################## STOPPING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
			svcctloutput = self.imum.service_control("stop", radservicename)
			header = "########################## STOPPING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS IS STILL RUNNING! **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS SHUTDOWN SUCCESSFUL **********\n\n", self.ui.yellow)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
			svcctloutput = self.imum.service_control("start", "radiuid")
			header = "########################## STARTING RADIUID ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** RADIUID RESTART UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
			svcctloutput = self.imum.service_control("start", radservicename)
			header = "########################## STARTING FREERADIUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print svcctloutput["after"]
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if svcctloutput["status"] == "running":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif svcctloutput["status"] == "dead":
				print self.ui.color("\n\n********** FREERADIUS RESTART UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			elif svcctloutput["status"] == "not-found":
				print self.ui.color("\n\n********** LOOKS LIKE FREERADIUS IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
		######################### REQUEST #############################
		elif arguments == "request" or arguments == "request ?":
			print "\n - request xml-update                                            |     Update the Python XML.etree modules (for compatibility on old Python versions)"
			print " - request munge-test <string-to-parse> (debug)                  |     Test and debug the Munge Engine using a provided string"
			print " - request auto-complete                                         |     Manually install the RadiUID BASH Auto-Completion feature"
			print " - request freeradius-install (no-confirm)                       |     Manually install the FreeRADIUS service for use by RadiUID"
			print " - request reinstall (replace-config | keep-config) (no-confirm) |     Reinstall RadiUID with or without replacing the current RadiUID configuration\n"
		elif arguments == "request reinstall" or arguments == "request reinstall ?":
			print "\n - request reinstall replace-config (no-confirm)               |     Reinstall RadiUID and REPLACE current configuration with default configuration"
			print " - request reinstall keep-config (no-confirm)                  |     Reinstall RadiUID and KEEP current configuration with default configuration\n"
		elif arguments == "request munge-test" or arguments == "request munge-test ?":
			print "\n - request munge-test <string-to-parse> (debug)\n"
		elif self.cat_list(sys.argv[1:3]) == "request munge-test" and re.findall("^[0-9A-Za-z]", sys.argv[3]) > 0:
			if len(sys.argv) > 4:
				if sys.argv[4] == 'debug':
					try:
						mungeconfig.update({'debug': None})
					except NameError:
						pass
			header = "########################## MUNGE TEST ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			try:
				returnedstring = self.dp.munge([sys.argv[3]], mungeconfig)[0]
				print "\n\n"
				print "String input from command line:  " + self.ui.color(sys.argv[3], self.ui.cyan)
				print "\n"
				print "String returned by Munge Engine: " + self.ui.color(returnedstring, self.ui.cyan)
			except NameError:
				print self.ui.color("\n\n********** NO MUNGE RULES CURRENTLY CONFIGURED! **********\n\n", self.ui.red)
			except IndexError:
				print self.ui.color("\n\nNo string returned by Munge Engine. It was discarded", self.ui.yellow)
			print "\n\n"
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif self.cat_list(sys.argv[1:3]) == "request xml-update":
			header = "########################## XML ETREE UPDATE ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("\n\n***** This will download and install Python XML ETree module 1.3.0 from the PackeTsar site *****", self.ui.yellow)
			answer = raw_input(self.ui.color(">>>>> Hit CTRL-C to cancel or ENTER to confirm >>>>", self.ui.yellow))
			self.imum.update_xml_etree()
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif self.cat_list(sys.argv[1:3]) == "request auto-complete":
			header = "########################## AUTO-COMPLETE INSTALL ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			self.imum.install_radiuid_completion()
			raw_input(self.ui.color("\nYou will need to log out and log back in to enable the RadiUID Auto-Complete feature\nHit ENTER to Complete>>>>>", self.ui.cyan))
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif self.cat_list(sys.argv[1:4]) == "request reinstall replace-config":
			confirm = True
			if len(sys.argv) > 4:
				if sys.argv[4].lower() == "no-confirm":
					confirm = False
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## RADIUID REINSTALL/UPGRADE ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if confirm:
				print self.ui.color("\n\n***** Are you sure you want to re-install/upgrade RadiUID using version " + version + "?*****", self.ui.yellow)
				print self.ui.color("***** This will overwrite your current RadiUID configuration with the default configuration.*****", self.ui.yellow)
				answer = raw_input(self.ui.color(">>>>> If you are sure you want to do this, type in 'CONFIRM' and hit ENTER >>>>", self.ui.yellow))
				if answer.lower() == "confirm":
					print "\n\n****************Re-installing/upgrading the RadiUID service...****************\n"
					self.imum.copy_radiuid("replace-config")
					self.imum.install_radiuid()
					svcctloutput = self.imum.service_control("restart", "radiuid")
					print svcctloutput["after"]
					if svcctloutput["status"] == "running":
						print self.ui.color("\n\n********** RADIUID STARTED UP! **********\n\n", self.ui.green)
					elif svcctloutput["status"] == "dead":
						print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL! **********\n\n", self.ui.red)
					elif svcctloutput["status"] == "not-found":
						print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
					print "\n"
					self.imum.install_radiuid_completion()
					raw_input(self.ui.color(">>>>> You will need to log out and log back in to activate the RadiUID CLI auto-completion functionality\n>>>>> Hit ENTER to finish\n>>>>>", self.ui.cyan))
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("\n\n***** Reinstall\Upgrade of RadiUID Cancelled *****\n", self.ui.yellow)
			else:
				print "\n\n****************Re-installing/upgrading the RadiUID service...****************\n"
				self.imum.copy_radiuid("replace-config")
				self.imum.install_radiuid()
				svcctloutput = self.imum.service_control("restart", "radiuid")
				print svcctloutput["after"]
				if svcctloutput["status"] == "running":
					print self.ui.color("\n\n********** RADIUID STARTED UP! **********\n\n", self.ui.green)
				elif svcctloutput["status"] == "dead":
					print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL! **********\n\n", self.ui.red)
				elif svcctloutput["status"] == "not-found":
					print self.ui.color("\n\n********** LOOKS LIKE RADIUID IS NOT INSTALLED. YOU NEED TO INSTALL IT **********\n\n", self.ui.red)
				print "\n"
				self.imum.install_radiuid_completion()
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif self.cat_list(sys.argv[1:4]) == "request reinstall keep-config":
			confirm = True
			if len(sys.argv) > 4:
				if sys.argv[4].lower() == "no-confirm":
					confirm = False
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## RADIUID REINSTALL/UPGRADE ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if confirm:
				print self.ui.color("\n\n***** Are you sure you want to re-install/upgrade RadiUID using version " + version + "?*****", self.ui.yellow)
				print self.ui.color("***** This will keep your current RadiUID configuration.*****", self.ui.yellow)
				answer = raw_input(self.ui.color(">>>>> If you are sure you want to do this, type in 'CONFIRM' and hit ENTER >>>>", self.ui.yellow))
				if answer.lower() == "confirm":
					print "\n\n****************Re-installing/upgrading the RadiUID service...****************\n"
					self.imum.copy_radiuid("keep-config")
					self.imum.install_radiuid()
					print "\n\n****************Checking Config File Schema****************\n"
					self.filemgmt.extend_config_schema()
					self.filemgmt.save_config()
					print "\n"
					self.imum.install_radiuid_completion()
					raw_input(self.ui.color(">>>>> You will need to log out and log back in to activate the RadiUID CLI auto-completion functionality\n>>>>> Hit ENTER to finish\n>>>>>", self.ui.cyan))
					print self.ui.color("Success!", self.ui.green)
				else:
					print self.ui.color("\n\n***** Reinstall\Upgrade of RadiUID Cancelled *****\n", self.ui.yellow)
			else:
				print "\n\n****************Re-installing/upgrading the RadiUID service...****************\n"
				self.imum.copy_radiuid("keep-config")
				self.imum.install_radiuid()
				print "\n\n****************Checking Config File Schema****************\n"
				self.filemgmt.extend_config_schema()
				self.filemgmt.save_config()
				print "\n"
				self.imum.install_radiuid_completion()
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif self.cat_list(sys.argv[1:3]) == "request freeradius-install":
			confirm = True
			if len(sys.argv) > 3:
				if sys.argv[3].lower() == "no-confirm":
					confirm = False
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## FREERADIUS MANUAL INSTALL ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if confirm:
				print self.ui.color("\n\n***** Are you sure you want to install/reinstall FreeRADIUS?*****", self.ui.yellow)
				answer = raw_input(self.ui.color(">>>>> If you are sure you want to do this, type in 'CONFIRM' and hit ENTER >>>>", self.ui.yellow))
				if answer.lower() == "confirm":
					self.imum.install_freeradius()
				else:
					print self.ui.color("\n\n***** Install/Reinstall of FreeRADIUS Cancelled *****\n", self.ui.yellow)
			else:
				self.imum.install_freeradius()
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### VERSION #############################
		elif arguments == "version":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT RADIUID AND FREERADIUS VERSIONS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print "-------------------------------------- OPERATING SYSTEM --------------------------------------"
			print "***** Current OS is " + self.ui.color(osversion, self.ui.green) + "*****"
			print "----------------------------------------------------------------------------------------------\n"
			print "------------------------------------------ RADIUID -------------------------------------------"
			print "***** Currently running RadiUID "+ self.ui.color(version, self.ui.green) + " *****"
			print "----------------------------------------------------------------------------------------------\n"
			print "----------------------------------------- FREERADIUS -----------------------------------------"
			os.system(radservicename + " -v | grep ersion")
			print "----------------------------------------------------------------------------------------------\n"
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### GUIDE #############################
		else:
			print self.ui.color("\n\n\n########################## Below are the supported RadiUID Commands: ##########################", self.ui.magenta)
			print self.ui.color("###############################################################################################\n\n", self.ui.magenta)
			print self.ui.color(" - Usage if installed: ", self.ui.white) + self.ui.color("radiuid [arguments]", self.ui.green) + "\n"
			print self.ui.color(" - Usage if NOT installed: ", self.ui.white) + self.ui.color("python radiuid.py [arguments]", self.ui.green) + "\n"
			print "-------------------------------------------------------------------------------------------------------------------------------"
			print "                     ARGUMENTS                    |                                  DESCRIPTIONS"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - run                                            |  Run the RadiUID main program in shell mode begin pushing User-ID information"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - install                                        |  Run RadiUID Install/Maintenance Utility"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - show log                                       |  Show the RadiUID log file"
			print " - show acct-logs                                 |  Show the log files currently in the FreeRADIUS accounting directory"
			print " - show run (xml | set)                           |  Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show config (xml | set)                        |  Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show clients (file | table)                    |  Show the FreeRADIUS clients and config file"
			print " - show status                                    |  Show the RadiUID and FreeRADIUS service statuses"
			print " - show mappings (<target> | all | consistency)   |  Show the current IP-to-User mappings of one or all targets or check consistency"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - set logfile                                    |  Set the RadiUID logfile path"
			print " - set radiuslogpath <directory path>             |  Set the path used to find FreeRADIUS accounting log files"
			print " - set acctlogcopypath <directory path>           |  Set the path where RadiUID should copy acct log files before deletion"
			print " - set maxloglines <number-of-lines>              |  Set the max number of lines allowed in the log ('0' turns circular logging off)"
			print " - set userdomain (none | <domain name>)          |  Set the domain name prepended to User-ID mappings"
			print " - set timeout                                    |  Set the timeout (in minutes) for User-ID mappings sent to the firewall targets"
			print " - set looptime                                   |  Set the waiting loop time (in seconds) to pause between checks of the RADIUS logs"
			print " - set tlsversion (1.0 | 1.1 | 1.2)               |  Set the version of TLS used for XML API communication with the firewall targets"
			print " - set radiusstopaction (clear | ignore | push)   |  Set the action taken by RadiUID when RADIUS stop messages are received"
			print " - set client (ipv4|ipv6) <ip-block> <secret>     |  Set configuration elements for RADIUS clients to send accounting data FreeRADIUS"
			print " - set munge <rule>.<step> [parameters]           |  Set munge (string processing rules) for User-IDs"
			print " - set target <hostname>:<vsys-id> [parameters]   |  Set configuration elements for existing or new firewall targets"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - push (<hostname>:<vsys-id> | all) [parameters] |  Manually push a User-ID mapping to one or all firewall targets"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - tail log (<# of lines>)                        |  Watch the RadiUID log file in real time"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - clear log                                      |  Delete the content in the log file"
			print " - clear acct-logs                                |  Delete the log files currently in the FreeRADIUS accounting directory"
			print " - clear client (<ip-block> | all)                |  Delete one or all RADIUS client IP blocks in FreeRADIUS config file"
			print " - clear munge (<rule> | all) (<step> | all)      |  Delete one or all munge rules in the config file"
			print " - clear target (<hostname>:<vsys-id> | all)      |  Delete one or all firewall targets in the config file"
			print " - clear mappings [parameters]                    |  Remove one or all IP-to-User mappings from one or all firewalls"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - edit config                                    |  Edit the RadiUID config file"
			print " - edit clients                                   |  Edit RADIUS client config file for FreeRADIUS"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - service [parameters]                           |  Control the RadiUID and FreeRADIUS system services"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - request [parameters]                           |  Make system-level changes for RadiUID service"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - version                                        |  Show the current version of RadiUID and FreeRADIUS"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print self.ui.color("###############################################################################################", self.ui.magenta)
			print self.ui.color("###############################################################################################", self.ui.magenta)


if __name__ == "__main__":
	cli = command_line_interpreter()
	cli.interpreter()
