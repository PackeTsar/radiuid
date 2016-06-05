#!/usr/bin/python

#####        RadiUID Server v1.1.0         #####
#####       Written by John W Kerns        #####
#####      http://blog.packetsar.com       #####
##### https://github.com/PackeTsar/radiuid #####


import os
import time
import re
import commands
import ConfigParser
import urllib
import urllib2

##### Inform RadiUID version here #####
version = "v1.1.0"


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
	##### Writes lines to the log file and prints them to the terminal #####
	##### Uses the logfile variable published to the global namespace #####
	##### Modes of use change what log_writer does when it encounters certain errors. Modes are normal #####
	def log_writer(self, mode, input):
		if mode == "normal":
			try:
				target = open(logfile, 'a')
				target.write(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n")
				print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n"
				target.close()
			except IOError:
				print self.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********CANNOT OPEN FILE: " + logfile + " ***********\n", self.red)
				print self.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********PLEASE MAKE SURE YOU RAN THE INSTALLER ('python radiuid.py install')***********\n", self.red)
				quit()
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



















class data_processing(object):
	def __init__(self):
		##### Instantiate external object dependencies #####
		self.ui = user_interface()
		####################################################
	##### Search list of files for a searchterm and uses deliniator term to count instances in file, then returns a dictionary where key=instance and value=line where term was found #####
	##### Used to search through FreeRADIUS log files for usernames and IP addresses, then turn them into dictionaries to be sent to the "push" function #####
	def search_to_dict(self, filelist, delineator, searchterm):
		dict = {}
		entry = 0
		for filename in filelist:
			self.ui.log_writer("normal", 'Searching File: ' + filename + ' for ' + searchterm)
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
		self.ui.log_writer("normal", "IP Address List Cleaned Up!")
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
		self.ui.log_writer("normal", "Username List Cleaned Up!")
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
		self.ui.log_writer("normal", "Dictionary values merged into one dictionary")
		return newdict
	##### Check that legit CIDR block was entered #####
	##### Used to check IP blocks entered into the wizard for configuration of FreeRADIUS #####
	def cidr_checker(self, cidr_ip_block):
		check = re.search("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-9]|1[0-9]|2[0-9]|3[0-2]?)$", cidr_ip_block)
		if check is None:
			result = "no"
		else:
			result = "yes"
		return result


















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
		nestedlist = re.findall("^(.+)/([^/]+)$", filepath)
		templist = nestedlist[0]
		tempfilepath = templist[0]
		filepath = self.directory_slash_add(tempfilepath)
		filename = templist[1]
		resultlist = []
		resultlist.append(filepath)
		resultlist.append(filename)
		return resultlist
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
				self.ui.log_writer("normal", "Found File: " + entry + "...   Adding to file list")
		if len(filelist) == 0:
			self.ui.log_writer("normal", "No Accounting Logs Found. Nothing to Do.")
			return filelist
		else:
			return filelist
	##### Delete all files in provided list #####
	##### Used to remove the FreeRADIUS log files so the next iteration of RadiUID doesn't pick up redundant information #####
	def remove_files(self, filelist):
		for filename in filelist:
			os.remove(filename)
			self.ui.log_writer("normal", "Removed file: " + filename)
	##### Writes the new config data to the config file #####
	##### Used at the end of the wizard when new config values have been defined and need to be written to a config file #####
	def write_file(self, filepath, filedata):
		try:
			f = open(filepath, 'w')
			f.write(filedata)
			f.close()
		except IOError:
			print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********CANNOT OPEN FILE: " + filepath + " ***********\n", self.ui.red)
			print self.ui.color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********PLEASE MAKE SURE YOU RAN THE INSTALLER ('python radiuid.py install')***********\n", self.ui.red)
			quit()
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
	##### Pull logfile location from configfile #####
	def get_logfile(self):
		configfile = self.find_config("quiet")
		parser = ConfigParser.SafeConfigParser()
		parser.read(configfile)
		f = open(configfile, 'r')
		config_file_data = f.read()
		f.close()
		logfile = parser.get('Paths_and_Files', 'logfile')
		return logfile












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
	def xml_formatter_v67(self, ipanduserdict):
		if panosversion == '7' or panosversion == '6':
			ipaddresses = ipanduserdict.keys()
			xmllist = []
			for ip in ipaddresses:
				entry = '<entry name="%s\%s" ip="%s" timeout="%s">' % (userdomain, ipanduserdict[ip], ip, timeout)
				xmllist.append(entry)
				entry = ''
			return xmllist
		else:
			self.ui.log_writer("normal", self.ui.color("PAN-OS version not supported for XML push!", self.ui.red))
			quit()
	##### Accepts a list of XML-formatted IP-to-User mappings and produces a list of complete and encoded URLs which are used to push UID data #####
	##### Each URL will contain no more than 100 UID mappings which can all be pushed at the same time by the push_uids method #####
	def xml_assembler_v67(self, ipuserxmllist):
		if panosversion == '7' or panosversion == '6':
			finishedurllist = []
			xmluserdata = ""
			iterations = 0
			while len(ipuserxmllist) > 0:
				for entry in ipuserxmllist[:100]:
					xmluserdata = xmluserdata + entry + "\n</entry>\n"
					ipuserxmllist.remove(entry)
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
				finishedurllist.append('https://' + hostname + '/api/?key=' + pankey + extrastuff + urljunk)
				xmluserdata = ""
			return finishedurllist
		else:
			self.ui.log_writer("normal", self.ui.color("PAN-OS version not supported for XML push!", self.ui.red))
			quit()
	#######################################################
	#######         PAN Interaction Methods         #######
	#######        Used for PAN Interaction         #######
	#######################################################
	##### Function to pull API key from firewall to be used for REST HTTP calls #####
	##### Used during initialization of the RadiUID main process to generate the API key #####
	def pull_api_key(self, username, password):
		encodedusername = urllib.quote_plus(username)
		encodedpassword = urllib.quote_plus(password)
		url = 'https://' + hostname + '/api/?type=keygen&user=' + encodedusername + '&password=' + encodedpassword
		response = urllib2.urlopen(url).read()
		self.ui.log_writer("normal", "Pulling API key using PAN credentials: " + username + "\\" + password + "\n")
		if 'success' in response:
			self.ui.log_writer("normal", self.ui.color(response, self.ui.green) + "\n")
			stripped1 = response.replace("<response status = 'success'><result><key>", "")
			stripped2 = stripped1.replace("</key></result></response>", "")
			pankey = stripped2
			return pankey
		else:
			log_writer("normal", self.ui.color('ERROR: Username\\password failed. Please re-enter in config file...' + '\n', self.ui.red))
			quit()
	##### Accepts IP-to-User mappings as a dict in, uses the xml-formatter and xml-assembler to generate a list of URLS, then opens those URLs and logs response codes  #####
	def push_uids(self, ipanduserdict, filelist):
		xml_list = self.xml_formatter_v67(ipanduserdict)
		urllist = self.xml_assembler_v67(xml_list)
		self.ui.log_writer("normal", "Pushing the below IP : User mappings via " + str(len(urllist)) + " API calls")
		for entry in ipanduserdict:
			self.ui.log_writer("normal", "IP Address: " + self.ui.color(entry, self.ui.cyan) + "\t\tUsername: " + self.ui.color(ipanduserdict[entry], self.ui.cyan))
		for eachurl in urllist:
			response = urllib2.urlopen(eachurl).read()
			self.ui.log_writer("normal", self.ui.color(response, self.ui.green) + "\n")
		self.filemgmt.remove_files(filelist)
















##### Initialize method used to pull all necessary RadiUID information from the config file and dump the data into variables in the global namespace #####
##### This method runs once during the initial startup of the program #####
def initialize():
	##### Instantiate external object dependencies #####
	ui = user_interface()
	filemgmt = file_management()
	pafi = palo_alto_firewall_interaction()
	####################################################
	print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********MAIN PROGRAM INITIALIZATION KICKED OFF...***********" + "\n"
	global logfile
	global radiuslogpath
	global hostname
	global panosversion
	global panuser
	global panpassword
	global extrastuff
	global ipaddressterm
	global usernameterm
	global delineatorterm
	global userdomain
	global timeout
	##### Check if config file exists. Fail program if it doesn't #####
	configfile = filemgmt.find_config("noisy")
	checkfile = filemgmt.file_exists(configfile)
	if checkfile == 'no':
		print color(time.strftime(
			"%Y-%m-%d %H:%M:%S") + ":   " + "ERROR: CANNOT FIND RADIUID CONFIG FILE IN TYPICAL PATHS. QUITTING PROGRAM. RE-RUN INSTALLER ('python radiuid.py install')" + "\n", red)
		quit()
	if checkfile == 'yes':
		print time.strftime(
			"%Y-%m-%d %H:%M:%S") + ":   " + "***********USING CONFIG FILE " + configfile + " TO START RADIUID APPLICATION***********" + "\n"
		print time.strftime(
			"%Y-%m-%d %H:%M:%S") + ":   " + "***********READING IN RADIUID LOGFILE INFORMATION. ALL SUBSEQUENT OUTPUT WILL BE LOGGED TO THE LOGFILE***********" + "\n"
	##### Open the config file and read in the logfile location information #####
	parser = ConfigParser.SafeConfigParser()
	parser.read(configfile)
	logfile = parser.get('Paths_and_Files', 'logfile')
	##### Initial log entry and help for anybody starting the .py program without first installing it #####
	ui.log_writer("normal", "***********INITIAL WRITE TO THE LOG FILE: " + logfile + "...***********")
	ui.log_writer("normal", "***********RADIUID INITIALIZING... IF PROGRAM FAULTS NOW, MAKE SURE YOU SUCCESSFULLY RAN THE INSTALLER ('python radiuid.py install')***********")
	##### Suck in all variables from config file (only run when program is initially started, not during while loop) #####
	ui.log_writer("normal", "***********INITIALIZING VARIABLES FROM CONFIG FILE: " + configfile + "...***********")
	ui.log_writer("normal", "Initialized variable:" "\t" + "logfile" + "\t\t\t\t" + "with value:" + "\t" + ui.color(logfile, ui.green))
	radiuslogpath = parser.get('Paths_and_Files', 'radiuslogpath')
	ui.log_writer("normal", "Initialized variable:" "\t" + "radiuslogpath" + "\t\t\t" + "with value:" + "\t" + ui.color(radiuslogpath, ui.green))
	hostname = parser.get('Palo_Alto_Target', 'hostname')
	ui.log_writer("normal", "Initialized variable:" "\t" + "hostname" + "\t\t\t" + "with value:" + "\t" + ui.color(hostname, ui.green))
	panosversion = parser.get('Palo_Alto_Target', 'panosversion')
	ui.log_writer("normal", "Initialized variable:" "\t" + "panosversion" + "\t\t\t" + "with value:" + "\t" + ui.color(panosversion, ui.green))
	panuser = parser.get('Palo_Alto_Target', 'username')
	ui.log_writer("normal", "Initialized variable:" "\t" + "panuser" + "\t\t\t\t" + "with value:" + "\t" + ui.color(panuser, ui.green))
	panpassword = parser.get('Palo_Alto_Target', 'password')
	ui.log_writer("normal", "Initialized variable:" "\t" + "panpassword" + "\t\t\t" + "with value:" + "\t" + ui.color(panpassword, ui.green))
	extrastuff = parser.get('URL_Stuff', 'extrastuff')
	ui.log_writer("normal", "Initialized variable:" "\t" + "extrastuff" + "\t\t\t" + "with value:" + "\t" + ui.color(extrastuff, ui.green))
	ipaddressterm = parser.get('Search_Terms', 'ipaddressterm')
	ui.log_writer("normal", "Initialized variable:" "\t" + "ipaddressterm" + "\t\t\t" + "with value:" + "\t" + ui.color(ipaddressterm, ui.green))
	usernameterm = parser.get('Search_Terms', 'usernameterm')
	ui.log_writer("normal", "Initialized variable:" "\t" + "usernameterm" + "\t\t\t" + "with value:" + "\t" + ui.color(usernameterm, ui.green))
	delineatorterm = parser.get('Search_Terms', 'delineatorterm')
	ui.log_writer("normal", "Initialized variable:" "\t" + "delineatorterm" + "\t\t\t" + "with value:" + "\t" + ui.color(delineatorterm, ui.green))
	userdomain = parser.get('UID_Settings', 'userdomain')
	ui.log_writer("normal", "Initialized variable:" "\t" + "userdomain" + "\t\t\t" + "with value:" + "\t" + ui.color(userdomain, ui.green))
	timeout = parser.get('UID_Settings', 'timeout')
	ui.log_writer("normal", "Initialized variable:" "\t" + "timeout" + "\t\t\t\t" + "with value:" + "\t" + ui.color(timeout, ui.green))
	##### Explicitly pull PAN key now and store API key in the main namespace #####
	ui.log_writer("normal", "***********************************CONNECTING TO PALO ALTO FIREWALL TO EXTRACT THE API KEY...***********************************")
	ui.log_writer("normal", "********************IF PROGRAM FREEZES/FAILS RIGHT NOW, THEN THERE IS LIKELY A COMMUNICATION PROBLEM WITH THE FIREWALL********************")
	global pankey
	pankey = pafi.pull_api_key(panuser, panpassword)
	ui.log_writer("normal", "Initialized variable:" "\t" + "pankey" + "\t\t\t\t" + "with value:" + "\t" + pankey)
	ui.log_writer("normal", "*******************************************CONFIG FILE SETTINGS INITIALIZED*******************************************")
	ui.log_writer("normal", "***********************************RADIUID SERVER STARTING WITH INITIALIZED VARIABLES...******************************")









##### RadiUID looper method which initializes the namespace with config variables and loops the main RadiUID program #####
def radiuid_looper():
	##### Instantiate external object dependencies #####
	filemgmt = file_management()
	pafi = palo_alto_firewall_interaction()
	dpr = data_processing()
	####################################################
	####################################################
	######### SET DEFAULT CONFIG FILE LOCATION #########
	####################################################
	global etcconfigfile
	etcconfigfile = '/etc/radiuid/radiuid.conf'
	####################################################
	configfile = filemgmt.find_config("noisy")
	initialize()
	while __name__ == "__main__":
		filelist = filemgmt.list_files(radiuslogpath)
		if len(filelist) > 0:
			usernames = dpr.search_to_dict(filelist, delineatorterm, usernameterm)
			ipaddresses = dpr.search_to_dict(filelist, delineatorterm, ipaddressterm)
			usernames = dpr.clean_names(usernames)
			ipaddresses = dpr.clean_ips(ipaddresses)
			ipanduserdict = dpr.merge_dicts(ipaddresses, usernames)
			pafi.push_uids(ipanduserdict, filelist)
			del filelist
			del usernames
			del ipaddresses
			del ipanduserdict
		time.sleep(10)








