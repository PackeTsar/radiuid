#!/usr/bin/python

#####        RadiUID Server v2.0.0         #####
#####       Written by John W Kerns        #####
#####      http://blog.packetsar.com       #####
##### https://github.com/PackeTsar/radiuid #####

import os
import re
import sys
import time
import urllib
import urllib2
import commands
import xml.etree.ElementTree

##### Inform RadiUID version here #####
version = "dev2.0.0"

##### Set some default configs #####
etcconfigfile = '/etc/radiuid/radiuid.conf'
extrastuff = '&type=user-id&vsys=vsys1&cmd='
maxtimeout = 1440





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
			characterregex = "^[a-zA-Z0-9_]+$" # A list of the valid username characters
			for entry in re.findall(characterregex, userorpassinput): # For each string in the list returned by re.findall
				if entry == userorpassinput: # If one of the strings in the returned list equals the full domainname string
					result["status"] = "pass" # Then all its characters are legal and it passes the check
					result["messages"].append({"OK": "No illegal characters found in username"}) # Append a message to the result
			if len(re.findall(characterregex, userorpassinput)) == 0:
				result["status"] = "fail" # Then all its characters are legal and it passes the check
				result["messages"].append({"FATAL": "Illegal characters found in username. Valid characters are alphanimeric and underscore (_)"}) # Append a message to the result
		elif inputtype == "password":
			characterregex = "\&|\<|\>" # A list of the invalid password characters
			if len(re.findall(characterregex, userorpassinput)) > 0: # For each string in the list returned by re.findall
				result["status"] = "fail"
				result["messages"].append({"FATAL": "Illegal characters found in password. Characters '&', '<', and '>' are not allowed "}) # Append a message to the result
			else:
				result["status"] = "pass" # Then all its characters are legal and it passes the check
				result["messages"].append({"OK": "No illegal characters found in password"}) # Append a message to the result
		return result
	def check_version(self, inputversion):
		result = {"status": "fail", "messages": []} # Start with a failed result
		if inputversion == "6" or inputversion == "7":
			result["status"] = "pass"
			result["messages"].append({"OK": "Version is allowed"})
		else:
			result["status"] = "fail"
			result["messages"].append({"FATAL": "Only versions 6 and 7 allowed"})
		return result
	def check_targets(self, targetdict):
		result = {}
		for target in targetdict:
			result.update({target["hostname"]: {"status": "working"}})
			##### Check hostname #####
			result[target["hostname"]].update({"hostnamecheck": {"status": "working", "messages": []}})
			if self.ip_checker("address", target["hostname"]) == "pass":
				result[target["hostname"]]["hostnamecheck"]["status"] = "pass"
				result[target["hostname"]]["hostnamecheck"]["messages"].append({"OK": "Target hostname is valid IPv4 address"})
			else:
				result[target["hostname"]]["hostnamecheck"] = self.check_domainname(target["hostname"])
			##### Check Username and Password #####
			try:
				result[target["hostname"]].update({"usernamecheck": self.check_userpass("user", target["username"])})
			except KeyError:
				result[target["hostname"]].update({"usernamecheck": {"status": "fail", "messages": [{"FATAL": "<username> parameter does not exist for this target"}]}})
			try:
				result[target["hostname"]].update({"passwordcheck": self.check_userpass("password", target["password"])})
			except KeyError:
				result[target["hostname"]].update({"passwordcheck": {"status": "fail", "messages": [{"FATAL": "<password> parameter does not exist for this target"}]}})
			##### Check Version #####
			try:
				result[target["hostname"]].update({"versioncheck": self.check_version(target["version"])})
			except KeyError:
				result[target["hostname"]].update({"versioncheck": {"status": "fail", "messages": [{"FATAL": "<version> parameter does not exist for this target"}]}})
			##### Read Results #####
			warnings = 0
			for check in result[target["hostname"]].keys():
				if check != "status":
					if result[target["hostname"]][check]["status"] == "fail":
						result[target["hostname"]]["status"] = "fail"
						break
					elif result[target["hostname"]][check]["status"] == "warning":
						warnings = warnings + 1
					elif result[target["hostname"]][check]["status"] == "pass":
						result[target["hostname"]]["status"] = "pass"
			if warnings > 0:
				result[target["hostname"]]["status"] = "warning"
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
							if badtarget["hostname"] == target:
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
	def list_files(self, path):
		filelist = []
		for root, directories, filenames in os.walk(path):
			for filename in filenames:
				entry = os.path.join(root, filename)
				filelist.append(entry)
				self.logwriter("normal", "Found File: " + entry + "...   Adding to file list")
		if len(filelist) == 0:
			self.logwriter("normal", "No Accounting Logs Found. Nothing to Do.")
			return filelist
		else:
			return filelist
	##### Delete all files in provided list #####
	##### Used to remove the FreeRADIUS log files so the next iteration of RadiUID doesn't pick up redundant information #####
	def remove_files(self, filelist):
		for filename in filelist:
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
			self.root = xml.etree.ElementTree.fromstring(self.cleanedxml)
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
			self.root = xml.etree.ElementTree.fromstring(self.cleanedxml)
	##### Publish all settings to variables in the global namespace for use by other processes #####
	##### All variables are set to strings with the exception of the targets, which is a list of dictionary items #####
	def publish_config(self, mode):
		global configdict
		global radiuslogpath
		global logfile
		global userdomain
		global timeout
		global ipaddressterm
		global usernameterm
		global delineatorterm
		global targets
		if mode == 'noisy':# to be used to initialize the RadiUID main app
			##### Suck config values into a dictionary #####
			configdict = self.tinyxml2dict_starter()
			##### Publish individual global settings values variables in main namespace #####
			try:
				logfile = configdict['globalsettings']['paths']['logfile']
				self.logwriter("normal", "***********INITIAL WRITE TO THE LOG FILE: " + logfile + "...***********")
				self.logwriter("normal", "***********INITIALIZING VARIABLES FROM CONFIG FILE...***********")
				self.logwriter("normal", "Initialized variable:" "\t" + "logfile" + "\t\t\t\t" + "with value:" + "\t" + self.ui.color(logfile, self.ui.green))
				radiuslogpath = configdict['globalsettings']['paths']['radiuslogpath']
				self.logwriter("normal", "Initialized variable:" "\t" + "radiuslogpath" + "\t\t\t" + "with value:" + "\t" + self.ui.color(radiuslogpath, self.ui.green))
				ipaddressterm = configdict['globalsettings']['searchterms']['ipaddressterm']
				self.logwriter("normal", "Initialized variable:" "\t" + "ipaddressterm" + "\t\t\t" + "with value:" + "\t" + self.ui.color(ipaddressterm, self.ui.green))
				usernameterm = configdict['globalsettings']['searchterms']['usernameterm']
				self.logwriter("normal", "Initialized variable:" "\t" + "usernameterm" + "\t\t\t" + "with value:" + "\t" + self.ui.color(usernameterm, self.ui.green))
				delineatorterm = configdict['globalsettings']['searchterms']['delineatorterm']
				self.logwriter("normal", "Initialized variable:" "\t" + "delineatorterm" + "\t\t\t" + "with value:" + "\t" + self.ui.color(delineatorterm, self.ui.green))
				userdomain = configdict['globalsettings']['uidsettings']['userdomain']
				self.logwriter("normal", "Initialized variable:" "\t" + "userdomain" + "\t\t\t" + "with value:" + "\t" + self.ui.color(userdomain, self.ui.green))
				timeout = configdict['globalsettings']['uidsettings']['timeout']
				self.logwriter("normal", "Initialized variable:" "\t" + "timeout" + "\t\t\t\t" + "with value:" + "\t" + self.ui.color(timeout, self.ui.green))
				##### Publish list of firewall targets into main namespace #####
				self.logwriter("normal", "***********INITIALIZING TARGETS...***********")
				targets = configdict['targets']['target']
				if type(targets) != type([]):
					targets = [targets]
				for target in targets:
					self.logwriter("normal", self.ui.color("[IMPORTED]", self.ui.cyan) + "   HOSTNAME: " + self.ui.color(target['hostname'], self.ui.green) + "\t\tUSERNAME: " + self.ui.color(target['username'], self.ui.green) + "\t\tPASSWORD: " + self.ui.color(target['password'], self.ui.green) + "\t\tVERSION: " + self.ui.color(target['version'], self.ui.green))
			except KeyError:
				print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************WARNING: Could not import some important settings****************\n", self.ui.yellow)
		if mode == 'quiet':
			##### Suck config values into a dictionary #####
			configdict = self.tinyxml2dict_starter()
			##### Publish individual global settings values variables in main namespace #####
			try:
				logfile = configdict['globalsettings']['paths']['logfile']
				radiuslogpath = configdict['globalsettings']['paths']['radiuslogpath']
				userdomain = configdict['globalsettings']['uidsettings']['userdomain']
				timeout = configdict['globalsettings']['uidsettings']['timeout']
				ipaddressterm = configdict['globalsettings']['searchterms']['ipaddressterm']
				usernameterm = configdict['globalsettings']['searchterms']['usernameterm']
				delineatorterm = configdict['globalsettings']['searchterms']['delineatorterm']
				##### Publish list of firewall targets into main namespace #####
				targets = configdict['targets']['target']
				if type(targets) != type([]):
					targets = [targets]
			except KeyError:
				return "WARNING: Could not import some important settings"
	##### Show formatted configuration item #####
	def show_config_item(self, mainmode, submode, itemname):
		if mainmode == "xml":
			for value in self.root.iter(itemname):
				xmldata = xml.etree.ElementTree.tostring(value, encoding="us-ascii", method="xml")
				regexnewline = "\n.*[a-z]"
				newline = re.findall(regexnewline, xmldata, flags=0)
				if len(newline) > 0:
					regexlastline = ".*</%s>" % itemname
					#print regexlastline
					regexlastelement = "</%s>" % itemname
					lastline = re.findall(regexlastline, xmldata, flags=0)[0]
					#print lastline
					lastelement = re.findall(regexlastelement, xmldata, flags=0)[0]
					#print lastelement
					indent = lastline.replace(lastelement, "")
					print indent + xmldata
				else:
					print "\t\t" + xmldata
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
			for target in targets:
				setparams = ""
				for param in target:
					if param != "hostname":
						setparams = setparams + param + " " + target[param] + " "
				rawtargetsetlist.append(" set target " + target["hostname"] + " " + setparams)
			#### Compile set commands for uninstalled and installed CLI format ####
			settargets = ""
			for settarget in rawtargetsetlist:
				settargets = settargets + prepend + settarget + "\n!\n"
			setcommands = \
				"" + prepend + " set radiuslogpath " + radiuslogpath + "\n!\n"\
				"" + prepend + " set logfile " + logfile + "\n!\n"\
				"" + prepend + " set userdomain " + userdomain + "\n!\n"\
				"" + prepend + " set timeout " + timeout + "\n!\n"
			#### Compile all set commands for different formats ####
			textconfig = header + "!\n" + setcommands + "!\n" + prepend + " clear target all\n!\n" + settargets + "!\n!\n###########################################################\n###########################################################\n"
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
	##### Add or edit target firewalls in XML configuration elements #####
	##### Input is a list of dictionaries which contain any number of parameters for a firewall target, but a hostname parameter is required #####
	##### Method will detect if the 'targets' element already exists and will create it if it doesn't #####
	##### Result is a dictionary where keys are the hostnames of the processed targets with messages in the values #####
	def add_targets(self, targetlist):
		result = {} # Initialize Result
		if len(self.root.findall('.//target')) == 0: # If <target> XML elements do not exist
			targets = xml.etree.ElementTree.SubElement(self.root, 'targets') # Mount new <targets> element as variable
		targets = self.root.findall('.//targets')[0] # Mount targets element as targets
		for targetitem in targetlist: # For each dict entry in the target list input as an arg...
			currenttargethostname = targetitem["hostname"]
			result[currenttargethostname] = {"status": "processing", "messages": []} # Create a new key in the result for this targetitem
			##### Does this target already exist, or do we need to create it new? #####
			targetalreadyexists = False # Initialize variable to determine if the target already exists
			for existingtarget in self.root.findall('.//target'): # For each existing target object in a list (empty list returned if none found)
				for parameter in existingtarget: # For each parameter in the existing target entry
					if targetitem["hostname"] == parameter.text: # If the hostname of the target to be edited matches this existing targets hostname...
						targetalreadyexists = True # Then set the targetalreadyexists value as True
						target = existingtarget # And mount the existing target (where the hostname matched) as target
			##### If the target to be edited exists already #####
			if targetalreadyexists: # If target exists..
				result[currenttargethostname]["messages"].append("Editing existing target") # Create feedback message
				targetitem.pop("hostname") # Remove the 'hostname' parameter from the list of edits to be made
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
						currentelement = xml.etree.ElementTree.SubElement(target, parameter) # Create the parameter in the target element
						currentelement.text = targetitem[parameter] # Set the value of the parameter
						result[currenttargethostname]["messages"].append("Created new <" + parameter + "> parameter with value '" + targetitem[parameter] + "'") # Create feedback message
			else: # If target doesn't yet exist
				target = xml.etree.ElementTree.SubElement(targets, 'target') # mount new target element as variable
				result[currenttargethostname]["messages"].append("Created new target") # Create feedback message
				##### Add the different elements for the target #####
				hostname = xml.etree.ElementTree.SubElement(target, 'hostname') # Create and mount the hostname parameter for the target
				hostname.text = targetitem['hostname'] # Set the hostname parameter value for the target
				del hostname # Unmount the hostname parameter element
				del targetitem['hostname'] # Remove the hostname parameter
				for parameter in targetitem: # For each of the parameter edits
					currentelement = xml.etree.ElementTree.SubElement(target, parameter) # Create the parameter in the target element
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
		targetpointer = len(targets.getchildren()) # Get the number of child <target> elements
		for target in targets.getchildren(): # For each <target> element in <targets>
			target.text = "\n\t\t\t" # Set the indent of the first parameter
			parameterpointer = len(target.getchildren()) # Get the number of child parameter elements
			for parameter in target.getchildren(): # For each parameter element
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
	##### Method accepts a list of dictionaries which contain at least the hostname key/value pair of the target #####
	def remove_targets(self, targetlist):
		result = ["fail"] # Start with failed result
		if len(self.root.findall('.//target')) == 0: # If no targets exist in config, return error
			result.append("No firewall targets exist. Nothing to remove")
		else: # if some targets do exist in config
			for removalitem in targetlist: # for each host listed for removal
				hostresult = 'failure' # initialize hostresult in case host is not found for removal
				for target in self.root.findall('.//target'): # for each target element 
					for element in target.getchildren(): # list out children (atttributes) of the target (like hostname, username, etc)
						if element.text == removalitem['hostname']: # check child elements of target element for hostname listed for removal
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
		self.newconfig = self.configcomment + "\n" + xml.etree.ElementTree.tostring(self.root)
		f = open(configfile, 'w')
		f.write(self.newconfig)
		f.close()
	##### Basic XML to Dict converter used to pull configuration info from the config file #####
	def tinyxml2dict(self, node):
		if "\n" not in node.text:
			result = node.text
		else:
			result = dict()
			for child in node:
				if child.tag not in result.keys():
					result[child.tag] = self.tinyxml2dict(child)
				else:
					if type(result[child.tag]) != type([]):
						result[child.tag] = [result[child.tag], self.tinyxml2dict(child)]
					else:
						result[child.tag].append(self.tinyxml2dict(child))
		return result
	##### Simple starter method for the XML to Dict conversion process #####
	def tinyxml2dict_starter(self):
		return self.tinyxml2dict(self.root)






#########################################################################
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
	##### Search list of files for a searchterm and uses deliniator term to count instances in file, then returns a dictionary where key=instance and value=line where term was found #####
	##### Used to search through FreeRADIUS log files for usernames and IP addresses, then turn them into dictionaries to be sent to the "push" function #####
	def search_to_dict(self, filelist, delineator, searchterm):
		dict = {}
		entry = 0
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
		username_regex = "(\'.*\')"
		for key, value in dictionary.iteritems():
			clean1 = re.findall(username_regex, value, flags=0)[0]
			cleaned = clean1.replace("'", "")
			newdict[key] = cleaned
		self.filemgmt.logwriter("normal", "Username List Cleaned Up!")
		return newdict
	##### Merge dictionary values from two dictionaries into one dictionary and remove duplicates #####
	##### Used to compile the list of users into a dictionary for use in the push function #####
	##### Deduplication is not explicitly written but is just a result of pushing the same data over and over to a dictionary #####
	def merge_dicts(self, keydict, valuedict):
		newdict = {}
		keydictkeylist = keydict.keys()
		for each in keydictkeylist:
			v = valuedict[each]
			k = keydict[each]
			newdict[k] = v
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
	#######################################################
	#######         XML Processing Methods          #######
	####### Used for PAN Interaction XML Generation #######
	#######################################################
	##### Accepts a list of IP addresses (keys) and usernames (vals) in a dictionary and outputs a list of XML formatted entries as a list #####
	##### This method outputs a list which is utilized by the xml_assembler_v67 method #####
	def xml_formatter_v67(self, ipanduserdict, targetlist):
		xmldict = {}
		for target in targetlist:
			if target['version'] == '7' or target['version'] == '6':
				xmldict[target['hostname']] = []
				ipaddresses = ipanduserdict.keys()
				for ip in ipaddresses:
					entry = '<entry name="%s\%s" ip="%s" timeout="%s">' % (userdomain, ipanduserdict[ip], ip, timeout)
					xmldict[target['hostname']].append(entry)
					entry = ''
			else:
				self.filemgmt.logwriter("normal", self.ui.color("PAN-OS version not supported for XML push!", self.ui.red))
				quit()
		return xmldict
	##### Accepts a list of XML-formatted IP-to-User mappings and produces a list of complete and encoded URLs which are used to push UID data #####
	##### Each URL will contain no more than 100 UID mappings which can all be pushed at the same time by the push_uids method #####
	def xml_assembler_v67(self, ipuserxmldict, targetlist):
		finishedurldict = {}
		for host in targetlist:
			if host['version'] == '7' or host['version'] == '6':
				xmluserdata = ""
				hostname = host['hostname']
				hostxmlentries = ipuserxmldict[hostname]
				finishedurllist = []
				while len(hostxmlentries) > 0:
					for entry in hostxmlentries[:100]:
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
					finishedurllist.append('https://' + hostname + '/api/?key=' + host['apikey'] + extrastuff + urljunk)
					xmluserdata = ""
				finishedurldict.update({hostname: finishedurllist})
				del hostname
				del hostxmlentries
			else:
				self.filemgmt.logwriter("normal", self.ui.color("PAN-OS version not supported for XML push!", self.ui.red))
				quit()
		return finishedurldict
	#######################################################
	#######         PAN Interaction Methods         #######
	#######        Used for PAN Interaction         #######
	#######################################################
	##### Function to pull API key from firewall to be used for REST HTTP calls #####
	##### Used during initialization of the RadiUID main process to generate the API key #####
	def pull_api_key(self, targetlist):
		if type(targetlist) != type([]):
			self.filemgmt.logwriter("normal", self.ui.color('ERROR: API Key function requires a list as input' + '\n', self.ui.red))
			quit()
		for target in targetlist:
			encodedusername = urllib.quote_plus(target['username'])
			encodedpassword = urllib.quote_plus(target['password'])
			url = 'https://' + target['hostname'] + '/api/?type=keygen&user=' + encodedusername + '&password=' + encodedpassword
			response = urllib2.urlopen(url).read()
			self.filemgmt.logwriter("normal", "Pulling API key using PAN from " + target['hostname'] + " using credentials: " + target['username'] + "\\" + target['password'])
			if 'success' in response:
				self.filemgmt.logwriter("normal", self.ui.color(response, self.ui.green))
				stripped1 = response.replace("<response status = 'success'><result><key>", "")
				stripped2 = stripped1.replace("</key></result></response>", "")
				pankey = stripped2
				target['apikey'] = pankey
				self.filemgmt.logwriter("normal", "Added 'apikey': " + pankey + " attribute to host: " + target['hostname'])
			else:
				self.filemgmt.logwriter("normal", self.ui.color('ERROR: Username\\password failed. Please re-enter in config file...' + '\n', self.ui.red))
				quit()
	##### Accepts IP-to-User mappings as a dict in, uses the xml-formatter and xml-assembler to generate a list of URLS, then opens those URLs and logs response codes  #####
	def push_uids(self, ipanduserdict, filelist):
		xml_dict = self.xml_formatter_v67(ipanduserdict, targets)
		urldict = self.xml_assembler_v67(xml_dict, targets)
		for host in urldict:
			self.filemgmt.logwriter("normal", "Pushing the below IP : User mappings to " + host + " via " + str(len(urldict[host])) + " API calls")
			urllist = urldict[host]
			for entry in ipanduserdict:
				self.filemgmt.logwriter("normal", "IP Address: " + self.ui.color(entry, self.ui.cyan) + "\t\tUsername: " + self.ui.color(ipanduserdict[entry], self.ui.cyan))
			for eachurl in urllist:
				response = urllib2.urlopen(eachurl).read()
				self.filemgmt.logwriter("normal", self.ui.color(response, self.ui.green) + "\n")
		self.filemgmt.remove_files(filelist)






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
		self.filemgmt.logwriter("normal", "***********CHECKING TARGETS FOR INCOMPLETE OR INCORRECT CONFIGS***********")
		self.filemgmt.scrub_targets("noisy", "scrub")
		##### Initial log entry and help for anybody starting the .py program without first installing it #####
		self.filemgmt.logwriter("normal", "***********RADIUID INITIALIZING... IF PROGRAM FAULTS NOW, MAKE SURE YOU SUCCESSFULLY RAN THE INSTALLER ('python radiuid.py install')***********")
		##### Explicitly pull PAN key now and store API key in the main namespace #####
		self.filemgmt.logwriter("normal", "***********************************CONNECTING TO PALO ALTO FIREWALL TO EXTRACT THE API KEY...***********************************")
		self.filemgmt.logwriter("normal", "********************IF PROGRAM FREEZES/FAILS RIGHT NOW, THEN THERE IS LIKELY A COMMUNICATION PROBLEM WITH THE FIREWALL********************")
		pankey = self.pafi.pull_api_key(targets)
		self.filemgmt.logwriter("normal", "*******************************************CONFIG FILE SETTINGS INITIALIZED*******************************************")
		self.filemgmt.logwriter("normal", "***********************************RADIUID SERVER STARTING WITH INITIALIZED VARIABLES...******************************")
	##### RadiUID looper method which initializes the namespace with config variables and loops the main RadiUID program #####
	def looper(self):
		self.filemgmt.initialize_config("noisy")
		self.filemgmt.publish_config("noisy")
		self.initialize()
		while __name__ == "__main__":
			filelist = self.filemgmt.list_files(radiuslogpath)
			if len(filelist) > 0:
				usernames = self.dpr.search_to_dict(filelist, delineatorterm, usernameterm)
				ipaddresses = self.dpr.search_to_dict(filelist, delineatorterm, ipaddressterm)
				usernames = self.dpr.clean_names(usernames)
				ipaddresses = self.dpr.clean_ips(ipaddresses)
				ipanduserdict = self.dpr.merge_dicts(ipaddresses, usernames)
				self.pafi.push_uids(ipanduserdict, filelist)
				del filelist
				del usernames
				del ipaddresses
				del ipanduserdict
			time.sleep(10)






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
		####################################################
	#######################################################
	#######          OS Interaction Methods           #####
	### Runs commands on the OS without file interaction ##
	#######################################################
	##### Get currently logged in user #####
	def currentuser(self):
		checkdata = commands.getstatusoutput("whoami")[1]
		return checkdata
	##### Check if a particular systemd service is installed #####
	##### Used to check if FreeRADIUS and RadiUID have already been installed #####
	def check_service_installed(self, service):
		checkdata = commands.getstatusoutput("systemctl status " + service)
		installed = 'temp'
		for line in checkdata:
			line = str(line)
			if 'not-found' in line:
				installed = 'no'
			else:
				installed = 'yes'
		return installed
	##### Check if a particular systemd service is running #####
	##### Used to check if FreeRADIUS and RadiUID are currently running #####
	def check_service_running(self, service):
		checkdata = commands.getstatusoutput("systemctl status " + service)
		running = 'temp'
		for line in checkdata:
			line = str(line)
			if 'active (running)' in line:
				running = 'yes'
			else:
				running = 'no'
		return running
	##### Restart a particular SystemD service #####
	def restart_service(self, service):
		commands.getstatusoutput("systemctl start " + service)
		commands.getstatusoutput("systemctl restart " + service)
		self.ui.progress("Starting/Restarting: ", 1)
		print "\n\n#########################################################################"
		os.system("systemctl status " + service)
		print "#########################################################################\n\n"
	##### Install FreeRADIUS server #####
	def install_freeradius(self):
		os.system('yum install freeradius -y')
		print "\n\n\n\n\n\n****************Setting FreeRADIUS as a system service...****************\n"
		self.ui.progress("Progress: ", 1)
		os.system('systemctl enable radiusd')
		os.system('systemctl start radiusd')
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
		return newsetting
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
	def copy_radiuid(self):
		configfilepath = "/etc/radiuid/"
		binpath = "/bin/"
		os.system('mkdir -p ' + configfilepath)
		os.system('cp radiuid.conf ' + configfilepath + 'radiuid.conf')
		os.system('cp radiuid.py ' + binpath + 'radiuid')
		os.system('chmod 777 ' + binpath + 'radiuid')
		self.ui.progress("Copying Files: ", 2)
	#### Install RadiUID SystemD service #####
	def install_radiuid(self):
		#### STARTFILE DATA START #####
		startfile = "[Unit]" \
		            "\n" + "Description=RadiUID User-ID Service" \
		                   "\n" + "After=network.target" \
		                          "\n" \
		                          "\n" + "[Service]" \
		                                 "\n" + "Type=simple" \
		                                        "\n" + "User=root" \
		                                               "\n" + "ExecStart=/bin/bash -c 'cd /bin; python radiuid run'" \
		                                                                                                         "\n" + "Restart=on-abort" \
		                                                                                                                "\n" \
		                                                                                                                "\n" \
		                                                                                                                "\n" + "[Install]" \
		                                                                                                                       "\n" + "WantedBy=multi-user.target" \
		##### STARTFILE DATA STOP #####
		f = open('/etc/systemd/system/radiuid.service', 'w')
		f.write(startfile)
		f.close()
		self.ui.progress("Installing: ", 2)
		os.system('systemctl enable radiuid')
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
		clientconfpath = '/etc/raddb/clients.conf'
		iplist = dict_edits.keys()
		print "\n\n\n"
		print "#####About to append the below client data to the FreeRADIUS client.conf file#####"
		print "##################################################################################"
		for ip in iplist:
			newwrite = "\nclient " + ip + " {\n    secret      = " + dict_edits[
				ip] + "\n    shortname   = Created_By_RadiUID\n }\n"
			f = open(clientconfpath, 'a')
			f.write(newwrite)
			f.close()
			print newwrite
		oktowrite = self.ui.yesorno("OK to write to client.conf file?")
		if oktowrite == "yes":
			print "###############Writing the above to the FreeRADIUS client.conf file###############"
			print "##################################################################################"
			print "\n"
			self.ui.progress("Writing: ", 1)
			print "\n\n\n"
			print "****************Restarting the FreeRADIUS service to effect changes...****************\n\n"
			self.ui.progress("Starting/Restarting: ", 1)
			os.system('systemctl restart radiusd')
			os.system('systemctl status radiusd')
			checkservice = self.check_service_running('radiusd')
			if checkservice == 'no':
				print self.ui.color("\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to start back up.", self.ui.red)
				print self.ui.color("***** We may have made some adverse changes to the config file.", self.ui.red)
				print self.ui.color("***** Visit the FreeRADIUS config file at " + clientconfpath + " and remove the bad changes.", self.ui.red)
				print self.ui.color("***** Then try to start the FreeRADIUS service by issuing the 'radiuid restart freeradius' command", self.ui.red)
				raw_input(self.ui.color("Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
			elif checkservice == 'yes':
				print self.ui.color("\n\n***** Great Success!! Looks like FreeRADIUS restarted and is back up now!", self.ui.green)
				print self.ui.color("***** If you need to manually edit the FreeRADIUS config file, it is located at " + clientconfpath, self.ui.green)
				raw_input(self.ui.color("\nHit ENTER to continue...\n\n>>>>>", self.ui.cyan))
		elif oktowrite == "no":
			print "~~~ OK Not writing it"






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
		freeradiusinstalled = self.imum.check_service_installed('radiusd')
		freeradiusrunning = self.imum.check_service_running('radiusd')
		if freeradiusinstalled == 'yes' and freeradiusrunning == 'yes':
			print self.ui.color("***** Looks like the FreeRADIUS service is already installed and running...skipping the install of FreeRADIUS", self.ui.green)
		if freeradiusinstalled == 'yes' and freeradiusrunning == 'no':
			freeradiusrestart = self.ui.yesorno("Looks like FreeRADIUS is installed, but not running....want to start it up?")
			if freeradiusrestart == 'yes':
				self.imum.restart_service('radiusd')
				freeradiusrunning = self.imum.check_service_running('radiusd')
				if freeradiusrunning == 'no':
					print self.ui.color("***** It looks like FreeRADIUS failed to start up. You may need to change its settings and restart it manually...", self.ui.red)
					print self.ui.color("***** Use the command 'radiuid edit clients' to open and edit the FreeRADIUS client settings file manually", self.ui.red)
				if freeradiusrunning == 'yes':
					print self.ui.color("***** Very nice....Great Success!!!", self.ui.green)
			if freeradiusrestart == 'no':
				print self.ui.color("~~~ OK, leaving it off...", self.ui.yellow)
		if freeradiusinstalled == 'no' and freeradiusrunning == 'no':
			freeradiusinstall = self.ui.yesorno(
				"Looks like FreeRADIUS is not installed. It is required by RadiUID. Is it ok to install FreeRADIUS?")
			if freeradiusinstall == 'yes':
				self.imum.install_freeradius()
				checkservice = self.imum.check_service_running('radiusd')
				if checkservice == 'no':
					print self.ui.color("\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to install or start up.", self.ui.red)
					print self.ui.color("***** It is possible that the native package manager is not able to download the install files.", self.ui.red)
					print self.ui.color("***** Make sure that you have internet access and your package manager is able to download the FreeRADIUS install files", self.ui.red)
					raw_input(self.ui.color("Hit ENTER to quit the program...\n", self.ui.cyan))
					quit()
				elif checkservice == 'yes':
					print self.ui.color("\n\n***** Great Success!! Looks like FreeRADIUS installed and started up successfully.", self.ui.green)
					print self.ui.color("***** We will be adding client IP and shared secret info to FreeRADIUS later in this wizard.", self.ui.green)
					print self.ui.color("***** If you need to manually edit the FreeRADIUS config file later, you can run 'radiuid edit clients' in the CLI", self.ui.green)
					print self.ui.color("***** You can also manually open the file for editing. It is located at /etc/raddb/clients.conf", self.ui.green)
					raw_input(self.ui.color("\n***** Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
			if freeradiusinstall == 'no':
				print self.ui.color("***** FreeRADIUS is required by RadiUID. Quitting the installer", self.ui.red)
				quit()
		#########################################################################
		###Check if RadiUID is installed and running already
		#########################################################################
		print "\n\n\n\n\n\n****************Checking if RadiUID is already installed...****************\n"
		radiuidinstalled = self.imum.check_service_installed('radiuid')
		radiuidrunning = self.imum.check_service_running('radiuid')
		if radiuidinstalled == 'yes' and radiuidrunning == 'yes':
			print self.ui.color("***** Looks like the RadiUID service is already installed and running...skipping the install of RadiUID\n", self.ui.green)
			radiuidreinstall = self.ui.yesorno("Do you want to re-install the RadiUID service?")
			if radiuidreinstall == 'yes':
				print self.ui.color("***** You are about to re-install the RadiUID service...", self.ui.yellow)
				print self.ui.color("***** If you continue, you will have to proceed with the wizard to the next step where we configure the settings in the config file...", self.ui.yellow)
				raw_input(self.ui.color(">>>>> Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
				print "\n\n****************Re-installing the RadiUID service...****************\n"
				self.imum.copy_radiuid()
				self.imum.install_radiuid()
				print "\n\n****************We will start up the RadiUID service once we configure the .conf file****************\n"
			if radiuidreinstall == 'no':
				print "~~~ Yea, probably best to leave it alone..."
		if radiuidinstalled == 'yes' and radiuidrunning == 'no':
			print "\n"
			print self.ui.color("***** Looks like RadiUID is installed, but not running....", self.ui.yellow)
			radiuidrestart = self.ui.yesorno("Do you want to start it up?")
			if radiuidrestart == 'yes':
				self.imum.restart_service('radiuid')
				self.ui.progress('Checking for Successful Startup', 3)
				os.system("systemctl status radiuid")
				radiuidrunning = self.imum.check_service_running('radiuid')
				if radiuidrunning == "yes":
					print self.ui.color("***** Very nice....Great Success!!!", self.ui.green)
				if radiuidrunning == "no":
					print self.ui.color("***** Looks like the startup failed...", self.ui.red)
					radiuidreinstall = self.ui.yesorno("Do you want to re-install the RadiUID service?")
					if radiuidreinstall == 'yes':
						print "\n\n****************Re-installing the RadiUID service...****************\n"
						self.imum.copy_radiuid()
						self.imum.install_radiuid()
						print "\n\n****************We will start up the RadiUID service once we configure the .conf file****************\n"
			if radiuidrestart == 'no':
				print self.ui.color("~~~ OK, leaving it off...", self.ui.yellow)
		if radiuidinstalled == 'no' and radiuidrunning == 'no':
			print "\n"
			radiuidinstall = self.ui.yesorno("Looks like RadiUID is not installed. Is it ok to install RadiUID?")
			if radiuidinstall == 'yes':
				print "\n\n****************Installing the RadiUID service...****************\n"
				self.imum.copy_radiuid()
				self.imum.install_radiuid()
				print "\n\n****************We will start up the RadiUID service once we configure the .conf file****************\n"
	
			if radiuidinstall == 'no':
				print self.ui.color("***** The install of RadiUID is required. Quitting the installer", self.ui.red)
				quit()
		print "\n\n\n\n"
		#########################################################################
		###Read current .conf settings into interpreter
		#########################################################################
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
			for target in targets:
				print "   HOSTNAME: " + self.ui.color(target['hostname'], self.ui.green) + "\t\tUSERNAME: " + self.ui.color(target['username'], self.ui.green) + "\t\tPASSWORD: " + self.ui.color(target['password'], self.ui.green) + "\t\tVERSION: " + self.ui.color(target['version'], self.ui.green)
			print "\n\n"
			changetargets = self.ui.yesorno("Do you want to delete the current targets and set up new ones?")
			if changetargets == 'no':
				print "~~~ OK. Leaving current targets alone..."
				newtargets = targets
			elif changetargets == 'yes':
				anothertarget = 'yes'
				newtargets = []
				while anothertarget == 'yes':
					print "\n\n\n"
					addhostname = self.imum.change_setting('192.168.1.1', 'Enter the IP ADDRESS or HOSTNAME of the target firewall to recieve User-ID mappings')
					addusername = self.imum.change_setting('admin', 'Enter the administrative USERNAME to use for authentication against the firewall')
					addpassword = self.imum.change_setting('admin', 'Enter the PASSWORD for the username you just entered')
					addversion = self.imum.change_setting('7', 'Enter the major software version running on the firewall')
					newtargets.append({'hostname': addhostname, 'username': addusername, 'password': addpassword, 'version': addversion})
					print "\n\n"
					anothertarget = self.ui.yesorno("Do you want to add another target firewall?")
				print "\n****************New Targets Are:****************\n"
				for target in newtargets:
					print "   HOSTNAME: " + self.ui.color(target['hostname'], self.ui.green) + "\t\tUSERNAME: " + self.ui.color(target['username'], self.ui.green) + "\t\tPASSWORD: " + self.ui.color(target['password'], self.ui.green) + "\t\tVERSION: " + self.ui.color(target['version'], self.ui.green)
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
				self.imum.restart_service('radiuid')
				radiuidrunning = self.imum.check_service_running('radiuid')
				if radiuidrunning == "yes":
					print self.ui.color("***** RadiUID successfully started up!!!", self.ui.green)
				raw_input(self.ui.color(">>>>> Hit ENTER to continue...\n\n>>>>>", self.ui.cyan))
				if radiuidrunning == "no":
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
		######################### RUN #############################
		if arguments == "run":
			self.radiuid.looper()
		######################### DEBUG #############################
		elif arguments == "debug":
			print targets
			print "\n\n"
			self.filemgmt.scrub_targets("noisy", "report")
			print "\n\n"
			print targets
			print "\n\n\n"
		######################### INSTALL #############################
		elif arguments == "install":
			self.filemgmt.logwriter("quiet", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print "\n\n\n"
			self.imu.im_utility()
		######################### SHOW #############################
		elif arguments == "show" or arguments == "show ?":
			print "\n - show log                |     Show the RadiUID log file"
			print " - show run (xml | set)    |     Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show config (xml | set) |     Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show clients            |     Show the FreeRADIUS client config file"
			print " - show status             |     Show the RadiUID and FreeRADIUS service statuses\n"
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
		elif arguments == "show log":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			configfile = self.filemgmt.find_config("quiet")
			header = "########################## OUTPUT FROM FILE " + logfile + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("more " + logfile)
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
			self.filemgmt.show_config_item('xml', "none", 'config')
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show clients":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## OUTPUT FROM FILE /etc/raddb/clients.conf ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("more /etc/raddb/clients.conf")
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		elif arguments == "show status":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## OUTPUT FROM COMMAND: 'systemctl status radiuid' ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiuid")
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			serviceinstalled = self.imum.check_service_installed("radiuid")
			if serviceinstalled == "no":
				print self.ui.color("\n\n********** RADIUID IS NOT INSTALLED YET **********\n\n", self.ui.yellow)
			elif serviceinstalled == "yes":
				checkservice = self.imum.check_service_running("radiuid")
				if checkservice == "yes":
					print self.ui.color("\n\n********** RADIUID IS CURRENTLY RUNNING **********\n\n", self.ui.green)
				elif checkservice == "no":
					print self.ui.color("\n\n********** RADIUID IS CURRENTLY NOT RUNNING **********\n\n", self.ui.yellow)
			header = "########################## OUTPUT FROM COMMAND: 'systemctl status radiusd' ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiusd")
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			serviceinstalled = self.imum.check_service_installed("radiusd")
			if serviceinstalled == "no":
				print self.ui.color("\n\n********** FREERADIUS IS NOT INSTALLED YET **********\n\n", self.ui.yellow)
			elif serviceinstalled == "yes":
				checkservice = self.imum.check_service_running("radiusd")
				if checkservice == "yes":
					print self.ui.color("\n\n********** FREERADIUS IS CURRENTLY RUNNING **********\n\n", self.ui.green)
				elif checkservice == "no":
					print self.ui.color("\n\n********** FREERADIUS IS CURRENTLY NOT RUNNING **********\n\n", self.ui.yellow)
		######################### SET #############################
		elif arguments == "set" or arguments == "set ?":
			print "\n - set logfile <file path>             |     Set the RadiUID logfile path"
			print " - set radiuslogpath <directory path>  |     Set the path used to find FreeRADIUS accounting log files"
			print " - set userdomain <domain name>        |     Set the domain name prepended to User-ID mappings"
			print " - set timeout <minutes>               |     Set the timeout (in minutes) for User-ID mappings sent to the firewall targets"
			print " - set target <hostname> [parameters]  |     Set configuration elements for existing or new firewall targets\n"
		elif arguments == "set logfile" or arguments == "set logfile ?":
			print "\n - set logfile <file path>  |  Example: 'set logfile /etc/radiuid/radiuid.log'\n"
		elif arguments == "set radiuslogpath" or arguments == "set radiuslogpath ?":
			print "\n - set radiuslogpath <directory path>  |  Example: 'set radiuslogpath /var/log/radius/radacct/'\n"
		elif arguments == "set userdomain" or arguments == "set userdomain ?":
			print "\n - set userdomain <domain name>  |  Example: 'set userdomain domain.com'\n"
		elif arguments == "set timeout" or arguments == "set timeout ?":
			print "\n - set timeout <minutes>  |  Example: 'set timeout 60'\n"
		elif arguments == "set target" or arguments == "set target ?":
			print "\n - set target <hostname> [parameters]  |  Parameters: (hostname <hostname> | username <username> | password <password> | version  <PAN-OS version #>)"
			print "                                       |              "
			print "                                       |  Examples:   'set target 192.168.1.1 username admin'"
			print "                                       |              'set target pan1.domain.com password P@s$w0rd'"
			print "                                       |              'set target 10.0.0.10 username admin password P@ssword version 6\n"
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
		##### SET USERDOMAIN #####
		elif self.cat_list(sys.argv[1:3]) == "set userdomain" and len(re.findall("^(.*)", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			if self.filemgmt.get_globalconfig_item('userdomain') == sys.argv[3]:
				print self.ui.color("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************Entered value is the same as current value****************\n", self.ui.green)
			else:
				domaincheck = self.filemgmt.check_domainname(sys.argv[3])
				if domaincheck["status"] == "fail":
					for message in domaincheck["messages"]:
						if message.keys()[0] == "FATAL":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.red)
						elif message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
				elif domaincheck["status"] == "pass":
					for message in domaincheck["messages"]:
						if message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					self.filemgmt.change_config_item('userdomain', sys.argv[3])
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Writing config change to: "+ configfile + "****************\n"
					self.filemgmt.save_config()
					print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"<userdomain> configuration element changed to :\n"
					self.filemgmt.show_config_item('xml', "none", 'userdomain')
				if self.filemgmt.get_globalconfig_item('userdomain') == sys.argv[3]:
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
		##### SET TARGET #####
		elif self.cat_list(sys.argv[1:3]) == "set target" and len(re.findall("[0-9A-Za-z]", sys.argv[3])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			keepgoing = "yes"
			##########################
			## Check Input Hostname ##
			##########################
			inputcheck = {}
			if self.filemgmt.ip_checker("address", sys.argv[3]) == "pass":
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Hostname " + sys.argv[3] + " looks like legit IPv4 address****************\n"
				inputcheck.update({"hostnamecheck": "pass"})
			else:
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Hostname " + sys.argv[3] + " looks like a domain name****************\n"
				domaincheck = self.filemgmt.check_domainname(sys.argv[3])
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
			##############################
			## Check other input values ##
			##############################
			## Compile arguments ##
			targetparams = {'hostname': sys.argv[3]}
			searchqueries = ['username', 'password', 'version']
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
			try:
				versioncheck = self.filemgmt.check_version(targetparams["version"])
				if versioncheck["status"] == "fail":
					for message in versioncheck["messages"]:
						if message.keys()[0] == "FATAL":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.red)
						elif message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"versioncheck": "fail"})
				else:
					for message in versioncheck["messages"]:
						if message.keys()[0] == "WARNING":
							print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow)
					inputcheck.update({"versioncheck": "pass"})
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
				for message in results[sys.argv[3]]["messages"]:
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
		######################### PUSH #############################
		elif arguments == "push" or arguments == "push ?":
			print "\n - push (<hostname> | all) [parameters]  |  Parameters: (<username>, <ip address>)"
			print "                                         |              "
			print "                                         |  Examples:   'push 192.168.1.1 administrator 10.0.0.1'"
			print "                                         |              'push pan1.domain.com jsmith 172.30.50.100'"
			print "                                         |              'push all jsmith 172.30.50.100'"
			print "                                         |              \n"
		elif self.cat_list(sys.argv[1:2]) == "push" and len(re.findall("[0-9A-Za-z]", sys.argv[2])) > 0:
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## EXECUTING COMMAND: " + arguments + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			keepgoing = "yes"
			pushuser = "yes"
			##### Check target hostname against config and check for necessary parameters #####
			if len(sys.argv[3:5]) != 2:
				self.filemgmt.logwriter("cli", self.ui.color("********************* ERROR: Some parameters are missing. Use '", self.ui.red) + self.ui.color(runcmd + " push ?", self.ui.cyan) + self.ui.color("' to see proper use and examples.********************", self.ui.red))
				pushuser = "no"
				keepgoing = "no"
			if keepgoing == "yes":
				if sys.argv[2].lower() != "all":
					keepgoing = "no"
					for target in targets:
						if target['hostname'] == sys.argv[2]:
							keepgoing = "yes"
							targets = [target]
					if keepgoing == "no":
						self.filemgmt.logwriter("cli", self.ui.color("********************* ERROR: Target ", self.ui.red) + self.ui.color(sys.argv[2], self.ui.cyan) + self.ui.color(" does not exist in config. Please configure it.********************", self.ui.red))
						pushuser = "no"
			##### Check parameters for proper data and report errors #####
			if keepgoing == "yes":
				usercheck = self.filemgmt.check_userpass("user", sys.argv[3])
				if usercheck["status"] != "pass":
					for message in usercheck["messages"]:
						if message.keys()[0] == "FATAL":
							self.filemgmt.logwriter("cli", self.ui.color("****************" + message.keys()[0] + ": " + message.values()[0] + "****************", self.ui.red))
							pushuser = "no"
						elif message.keys()[0] == "WARNING":
							self.filemgmt.logwriter("cli", self.ui.color("****************" + message.keys()[0] + ": " + message.values()[0] + "****************\n", self.ui.yellow))
				if self.filemgmt.ip_checker("address", sys.argv[4]) != "pass":
					self.filemgmt.logwriter("cli", self.ui.color("****************FATAL: Bad IP Address****************", self.ui.red))
					pushuser = "no"
				if pushuser == "yes":
					pankey = self.pafi.pull_api_key(targets)
					self.pafi.push_uids({sys.argv[4]: sys.argv[3]}, [])
			if pushuser == "yes":
				print self.ui.color("Success!", self.ui.green)
			elif pushuser == "no":
				print self.ui.color("Something Went Wrong!", self.ui.red)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### TAIL #############################
		elif arguments == "tail" or arguments == "tail ?":
			print "\n - tail log         |     Watch the RadiUID log file in real time\n"
		elif arguments == "tail log":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## OUTPUT FROM FILE " + logfile + " ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("tail -fn 25 " + logfile)
			print self.ui.color("#" * len(header), self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
		######################### CLEAR #############################
		elif arguments == "clear" or arguments == "clear ?":
			print "\n - clear log                       |     Delete the content in the log file"
			print " - clear target (<target> | all)     |     Delete one or all firewall targets in the config file\n"
		elif arguments == "clear target" or arguments == "clear target ?":
			print "\n - clear target (<target> | all)  |  Examples: 'clear target 192.168.1.1'"
			print "                                  |            'clear target pan1.domain.com'"
			print "                                  |            'clear target all'\n"
		##### CLEAR LOG #####
		elif arguments == "clear log":
			print self.ui.color("********************* You are about to clear out the RadiUID log file... (" + logfile + ") ********************", self.ui.yellow)
			raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
			os.system("rm -f "+ logfile)
			self.filemgmt.write_file(logfile, "***********Logfile cleared via RadiUID command by " + self.imum.currentuser() + "***********\n")
			print self.ui.color("********************* Cleared logfile: " + logfile + " ********************", self.ui.yellow)
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
			try:
				for target in targets:
					if target['hostname'] == sys.argv[3]:
						targetexists = "yes"
				if targetexists == "no":
					print "\n" + self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "****************ERROR: Target " + sys.argv[3] + " doesn't currently exist in config****************\n", self.ui.red)
				elif targetexists == "yes":
					print "\n" + time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"****************Deleting target: " + sys.argv[3] + " ****************\n"
					targetremove = self.filemgmt.remove_targets([{'hostname': sys.argv[3]}])
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
		######################### EDIT #############################
		elif arguments == "edit" or arguments == "edit ?":
			print "\n - edit config      |     Edit the RadiUID config file"
			print " - edit clients     |     Edit list of client IPs for FreeRADIUS\n"
		elif arguments == "edit config":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("****************** You are about to edit the RadiUID config file in VI ******************", self.ui.yellow)
			print self.ui.color("****************** It is recommend you use 'set' commands instead of this ******************", self.ui.yellow)
			print self.ui.color("********************* Confirm that you know how to use the VI editor ********************", self.ui.yellow)
			raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
			os.system("vi " + configfile)
		elif arguments == "edit clients":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			print self.ui.color("****************** You are about to edit the FreeRADIUS client file in VI ******************", self.ui.yellow)
			print self.ui.color("*********************** Confirm that you know how to use the VI editor ********************", self.ui.yellow)
			raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
			os.system("vi /etc/raddb/clients.conf")
		######################### RADIUID SERVICE CONTROL #############################
		elif arguments == "service" or arguments == "service ?":
			print "\n - Usage: radiuid service (radiuid | freeradius | all) (start | stop | restart)"
			print "----------------------------------------------------------------------------------"
			print "\n - service radiuid       |     Control the RadiUID system service"
			print " - service freeradius    |     Control the FreeRADIUS system service"
			print " - service all           |     Control the RadiUID and FreeRADIUS system services\n"
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
		elif arguments == "service radiuid start":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			os.system("systemctl start radiuid")
			os.system("systemctl status radiuid")
			checkservice = self.imum.check_service_running("radiuid")
			if checkservice == "yes":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
		elif arguments == "service radiuid stop":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiuid")
			print self.ui.color("\n\n***** ARE YOU SURE YOU WANT TO STOP IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			os.system("systemctl stop radiuid")
			os.system("systemctl status radiuid")
			print self.ui.color("\n\n********** RADIUID STOPPED **********\n\n", self.ui.yellow)
		elif arguments == "service radiuid restart":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiuid")
			print self.ui.color("\n\n***** ARE YOU SURE YOU WANT TO RESTART IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			os.system("systemctl stop radiuid")
			os.system("systemctl status radiuid")
			print self.ui.color("\n\n********** RADIUID STOPPED **********\n\n", self.ui.yellow)
			self.ui.progress("Preparing to Start Up:", 2)
			print "\n\n\n"
			os.system("systemctl start radiuid")
			os.system("systemctl status radiuid")
			checkservice = self.imum.check_service_running("radiuid")
			if checkservice == "yes":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
		######################### FREERADIUS SERVICE CONTROL #############################
		elif arguments == "service freeradius start":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			os.system("systemctl start radiusd")
			os.system("systemctl status radiusd")
			checkservice = self.imum.check_service_running("radiusd")
			if checkservice == "yes":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
		elif arguments == "service freeradius stop":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n***** ARE YOU SURE YOU WANT TO STOP IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			os.system("systemctl stop radiusd")
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n********** FREERADIUS STOPPED **********\n\n", self.ui.yellow)
		elif arguments == "service freeradius restart":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n***** ARE YOU SURE YOU WANT TO RESTART IT?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			os.system("systemctl stop radiusd")
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n********** FREERADIUS STOPPED **********\n\n", self.ui.yellow)
			self.ui.progress("Preparing to Start Up:", 2)
			print "\n\n\n"
			os.system("systemctl start radiusd")
			os.system("systemctl status radiusd")
			checkservice = self.imum.check_service_running("radiusd")
			if checkservice == "yes":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
		######################### COMBINED SERVICE CONTROL #############################
		elif arguments == "service all start":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			os.system("systemctl start radiusd")
			os.system("systemctl status radiusd")
			checkservice = self.imum.check_service_running("radiusd")
			if checkservice == "yes":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			print "\n\n\n"
			os.system("systemctl start radiuid")
			os.system("systemctl status radiuid")
			checkservice = self.imum.check_service_running("radiuid")
			if checkservice == "yes":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY STARTED UP! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
		elif arguments == "service all stop":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiuid")
			header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n***** ARE YOU SURE YOU WANT TO ALL SERVICES?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			os.system("systemctl stop radiuid")
			os.system("systemctl status radiuid")
			print self.ui.color("\n\n********** RADIUID STOPPED **********\n\n", self.ui.yellow)
			print "\n\n\n"
			os.system("systemctl stop radiusd")
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n********** FREERADIUS STOPPED **********\n\n", self.ui.yellow)
		elif arguments == "service all restart":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiuid")
			header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print self.ui.color("#" * len(header), self.ui.magenta)
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n***** ARE YOU SURE YOU WANT TO RESTART SERVICES?", self.ui.yellow)
			raw_input(self.ui.color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", self.ui.cyan))
			os.system("systemctl stop radiuid")
			os.system("systemctl status radiuid")
			print self.ui.color("\n\n********** RADIUID STOPPED **********\n\n", self.ui.yellow)
			self.ui.progress("Preparing to Start Up:", 2)
			print "\n\n\n"
			os.system("systemctl start radiuid")
			os.system("systemctl status radiuid")
			checkservice = self.imum.check_service_running("radiuid")
			if checkservice == "yes":
				print self.ui.color("\n\n********** RADIUID SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
			os.system("systemctl stop radiusd")
			os.system("systemctl status radiusd")
			print self.ui.color("\n\n********** FREERADIUS STOPPED **********\n\n", self.ui.yellow)
			self.ui.progress("Preparing to Start Up:", 2)
			print "\n\n\n"
			os.system("systemctl start radiusd")
			os.system("systemctl status radiusd")
			checkservice = self.imum.check_service_running("radiusd")
			if checkservice == "yes":
				print self.ui.color("\n\n********** FREERADIUS SUCCESSFULLY RESTARTED! **********\n\n", self.ui.green)
			elif checkservice == "no":
				print self.ui.color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", self.ui.red)
		######################### VERSION #############################
		elif arguments == "version":
			self.filemgmt.logwriter("cli", "##### COMMAND '" + arguments + "' ISSUED FROM CLI BY USER '" + self.imum.currentuser()+ "' #####")
			header = "########################## CURRENT RADIUID AND FREERADIUS VERSIONS ##########################"
			print self.ui.color(header, self.ui.magenta)
			print "------------------------------------------ RADIUID -------------------------------------------"
			print "***** Currently running RadiUID "+ self.ui.color(version, self.ui.green) + " *****"
			print "----------------------------------------------------------------------------------------------\n"
			print "----------------------------------------- FREERADIUS -----------------------------------------"
			os.system("radiusd -v | grep ersion")
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
			print "                  ARGUMENTS               |                                  DESCRIPTIONS"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - run                                    |     Run the RadiUID main program in shell mode begin pushing User-ID information"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - install                                |     Run the RadiUID Install/Maintenance Utility"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - show log                               |     Show the RadiUID log file"
			print " - show run (xml | set)                   |     Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show config (xml | set)                |     Show the RadiUID configuration in XML format (default) or as set commands"
			print " - show clients                           |     Show the FreeRADIUS client config file"
			print " - show status                            |     Show the RadiUID and FreeRADIUS service statuses"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - set logfile                            |     Set the RadiUID logfile path"
			print " - set radiuslogpath                      |     Set the path used to find FreeRADIUS accounting log files"
			print " - set userdomain                         |     Set the domain name prepended to User-ID mappings"
			print " - set timeout                            |     Set the timeout (in minutes) for User-ID mappings sent to the firewall targets"
			print " - set target [parameters]                |     Set configuration elements for existing or new firewall targets"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - push (<hostname> | all) [parameters]   |     Manually push a User-ID mapping to one or all firewall targets"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - tail log                               |     Watch the RadiUID log file in real time"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - clear log                              |     Delete the content in the log file"
			print " - clear target (<target> | all)          |     Delete one or all firewall targets in the config file"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - edit config                            |     Edit the RadiUID config file"
			print " - edit clients                           |     Edit list of client IPs for FreeRADIUS"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - service [parameters]                   |     Control the RadiUID and FreeRADIUS system services"
			print "                                          |     Usage: radiuid service (radiuid | freeradius | all) (start | stop | restart)"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print " - version                                |     Show the current version of RadiUID and FreeRADIUS"
			print "-------------------------------------------------------------------------------------------------------------------------------\n"
			print self.ui.color("###############################################################################################", self.ui.magenta)
			print self.ui.color("###############################################################################################", self.ui.magenta)


if __name__ == "__main__":
	cli = command_line_interpreter()
	cli.interpreter()
