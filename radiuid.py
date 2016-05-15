#!/usr/bin/python

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
import argparse
import ConfigParser


##########################Main RadiUID Functions#########################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
######################################################################### 


##### Color codes used in the program for easier CLI viewing #####
##### To be used like "print 'this is ' + color('green', green) + ' is it not?'" #####
black = '\033[0m'
red = '\033[91m'
green = '\033[92m'
yellow = '\033[93m'
blue = '\033[94m'
magenta = '\033[95m'
cyan = '\033[96m'
white = '\033[97m'

def color(input, inputcolor):
	result = inputcolor + input + black
	return result


##### Create str sentence out of list seperated by spaces and lowercase everything #####
##### Used for recognizing iarguments when running RadiUID from the CLI #####
def cat_list(listname):
	result = ""
	counter = 0
	#listlen = len(listname)
	for word in listname:
		result = result + listname[counter].lower() + " "
		counter = counter + 1
	result = result[:len(result) - 1:]
	return result


##### Check if specific file exists #####
##### Used??? #####!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def file_exists(filepath):
	checkdata = commands.getstatusoutput("ls " + filepath)
	exists = ""
	for line in checkdata:
		line = str(line)
		if "No such" in line:
			exists = "no"
		else:
			exists = "yes"
	return exists


##### Check if specific directory exists #####
def check_directory(directory):
	checkdata = commands.getstatusoutput("ls " + directory)
	exists = ''
	for line in checkdata:
		line = str(line)
		if 'cannot access' in line:
			exists = 'no'
		else:
			exists = 'yes'
	return exists


##### Writes lines to the log file and prints them to the terminal #####
def log_writer(filepath, input):
	target = open(filepath, 'a')
	target.write(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n")
	print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n"
	target.close()


##### Function to pull API key from firewall to be used for REST HTTP calls #####
##### Used during initialization of the RadiUID main process to generate the API key #####
def pull_api_key(username, password):
	url = 'https://' + hostname + '/api/?type=keygen&user=' + username + '&password=' + password
	response = urllib2.urlopen(url).read()
	log_writer(logfile, "Pulling API key using PAN credentials: " + username + "\\" + password + "\n")
	if 'success' in response:
		log_writer(logfile, color(response, green) + "\n")
		stripped1 = response.replace("<response status = 'success'><result><key>", "")
		stripped2 = stripped1.replace("</key></result></response>", "")
		return stripped2
	else:
		log_writer(logfile, color('ERROR: Username\\password failed. Please re-enter in config file...' + '\n', red))
		quit()


##### List all files in a directory path and subdirs #####
##### Used to enumerate files in the FreeRADIUS log path #####
def listfiles(path):
	filelist = []
	for root, directories, filenames in os.walk(path):
		for filename in filenames:
			entry = os.path.join(root, filename)
			filelist.append(entry)
			log_writer(logfile, "Found File: " + entry + "...   Adding to file list")
	if len(filelist) == 0:
		log_writer(logfile, "No Log Files Found. Nothing to Do.")
		return filelist
	else:
		return filelist


##### Search list of files for a searchterm and use deliniator term to count instances file, then return a dictionary where key=instance and value=line where term was found #####
##### Used to search through FreeRADIUS log files for usernames and IP addresses, then turn them into dictionaries to be sent to the "push" function #####
def search_to_dict(filelist, delineator, searchterm):
	dict = {}
	entry = 0
	for filename in filelist:
		log_writer(logfile, 'Searching File: ' + filename + ' for ' + searchterm)
		with open(filename, 'r') as filetext:
			for line in filetext:
				if delineator in line:
					entry = entry + 1
				if searchterm in line:
					dict[entry] = line
	return dict


##### Clean up IP addresses in dictionary #####
##### Removes unwanted data from the lines with useful IP addresses in them #####
def clean_ips(dictionary):
	newdict = {}
	for key, value in dictionary.iteritems():
		clean1 = value.replace("\t" + ipaddressterm + " = ", "")
		cleaned = clean1.replace("\n", "")
		newdict[key] = cleaned
	log_writer(logfile, "IP Address List Cleaned Up!")
	return newdict


##### Clean up user names in dictionary #####
##### Removes unwanted data from the lines with useful usernames in them #####
def clean_names(dictionary):
	newdict = {}
	for key, value in dictionary.iteritems():
		clean1 = value.replace("\t" + usernameterm + " = '", "")
		cleaned = clean1.replace("'\n", "")
		newdict[key] = cleaned
	log_writer(logfile, "Username List Cleaned Up!")
	return newdict


##### Merge dictionary values from two dictionaries into one dictionary and remove duplicates #####
##### Used to compile the list of users into a dictionary for use in the push function #####
##### Deduplication is not explicitly written but is just a result of pushing the same data over and over to a dictionary #####
def merge_dicts(keydict, valuedict):
	newdict = {}
	keydictkeylist = keydict.keys()
	for each in keydictkeylist:
		v = valuedict[each]
		k = keydict[each]
		newdict[k] = v
	log_writer(logfile, "Dictionary values merged into one dictionary")
	return newdict


##### Delete all files in provided list #####
##### Used to remove the FreeRADIUS log files so the next iteration of RadiUID doesn't pick up redundant information #####
def remove_files(filelist):
	for filename in filelist:
		os.remove(filename)
		log_writer(logfile, "Removed file: " + filename)


##### Encode username and IP address in to URL REST format for PAN #####
def url_converter_v7(username, ip):
	if panosversion == '7':
		urldecoded = '<uid-message>\
                <version>1.0</version>\
                <type>update</type>\
                <payload>\
                <login>\
                <entry name="%s\%s" ip="%s" timeout="%s">\
                </entry>\
                </login>\
                </payload>\
                </uid-message>' % (userdomain, username, ip, timeout)
		urljunk = urllib.quote_plus(urldecoded)
		finishedurl = 'https://' + hostname + '/api/?key=' + pankey + extrastuff + urljunk
		return finishedurl
	else:
		log_writer(logfile, color("PAN-OS version not supported for XML push!", red))
		quit()


##### Use urlconverter to encode the URL to acceptable format and use REST call to push UID info to PAN #####
def push_uids(ipanduserdict, filelist):
	iteration = 0
	ipaddresses = ipanduserdict.keys()
	for ip in ipaddresses:
		url = url_converter_v7(ipanduserdict[ip], ip)
		log_writer(logfile, "Pushing    |    " + userdomain + "\\" + ipanduserdict[ip] + ":" + ip)
		response = urllib2.urlopen(url).read()
		log_writer(logfile, response + "\n")
		iteration = iteration + 1
	remove_files(filelist)


#######################RadiUID Installer Functions#######################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
######################################################################### 

def file_chooser(firstchoice, secondchoice):
	firstexists = file_exists(firstchoice)
	secondexists = file_exists(secondchoice)
	if firstexists == "yes" and secondexists == "yes":
		return firstchoice
	if firstexists == "yes" and secondexists == "no":
		return firstchoice
	if firstexists == "no" and secondexists == "yes":
		return secondchoice
	if firstexists == "no" and secondexists == "no":
		return "NON-EXISTANT FILE"
		quit()


##### Take filepath and give back directory path and filename in list where list[0] is directory path, list[1] is filename #####
def strip_filepath(filepath):
	list = re.findall("^(.+)/([^/]+)$", filepath)
	return list


##### Check that legit CIDR block was entered #####
##### Used to check IP blocks entered into the wizard for configuration of FreeRADIUS #####
def cidr_checker(cidr_ip_block):
	check = re.search("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-9]|1[0-9]|2[0-9]|3[0-2]?)$", cidr_ip_block)
	if check is None:
		result = "no"
	else:
		result = "yes"
	return result


##### Add '/' to directory path if not included #####
def directory_slash_add(directorypath):
	check = re.search("^.*\/$", directorypath)
	if check is None:
		result = directorypath + "/"
		return result
	else:
		result = directorypath
		return result


##### Show progress bar #####
##### The most awesome method in here. Also the most useless #####
def progress(message, seconds):
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


##### Change variables to change settings #####
##### Used to ask questions in the installation wizard #####
def change_setting(setting, question):
	newsetting = raw_input(color(">>>>> " + question + " [" + setting + "]: ", cyan))
	if newsetting == '':
		print color("~~~ Keeping current setting...", green)
		newsetting = setting
	else:
		print color("~~~ Changed setting to: " + newsetting, yellow)
	return newsetting


##### Apply new setting to the .conf file #####
##### Applies the settings to the new or existing config file #####
def apply_setting(file_data, settingname, oldsetting, newsetting):
	if oldsetting == newsetting:
		print color("***** No changes to  : " + settingname, green)
		return file_data
	else:
		new_file_data = file_data.replace(settingname + " = " + oldsetting, settingname + " = " + newsetting)
		print color("***** Changed setting: " + settingname + "\t\t|\tfrom: " + oldsetting + "\tto: " + newsetting, yellow)
		return new_file_data


##### Writes the new config data to the config file #####
#####Used at the end of the wizard when new config values have been defined and need to be written to a config file #####
def write_file(filepath, filedata):
	f = open(filepath, 'w')
	f.write(filedata)
	f.close()


##### Check if a particular systemd service is installed #####
##### Used to check if FreeRADIUS and RadiUID have already been installed #####
def check_service_installed(service):
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
def check_service_running(service):
	checkdata = commands.getstatusoutput("systemctl status " + service)
	running = 'temp'
	for line in checkdata:
		line = str(line)
		if 'active (running)' in line:
			running = 'yes'
		else:
			running = 'no'
	return running


##### Install FreeRADIUS server #####
def install_freeradius():
	os.system('yum install freeradius -y')
	print "\n\n\n\n\n\n****************Setting FreeRADIUS as a system service...****************\n"
	progress("Progress: ", 1)
	os.system('systemctl enable radiusd')
	os.system('systemctl start radiusd')


#### Copy RadiUID system and config files to appropriate paths for installation#####
def copy_radiuid():
	configfilepath = "/etc/radiuid/"
	binpath = "/bin/"
	os.system('mkdir -p ' + configfilepath)
	os.system('cp radiuid.conf ' + configfilepath + 'radiuid.conf')
	os.system('cp radiuid.py ' + binpath + 'radiuid')
	os.system('chmod 777 ' + binpath + 'radiuid')
	progress("Copying Files: ", 2)


#### Install RadiUID SystemD service #####
def install_radiuid():
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
	progress("Installing: ", 2)
	os.system('systemctl enable radiuid')


##### Restart a particular SystemD service #####
def restart_service(service):
	commands.getstatusoutput("systemctl start " + service)
	commands.getstatusoutput("systemctl restart " + service)
	progress("Starting/Restarting: ", 1)
	print "\n\n#########################################################################"
	os.system("systemctl status " + service)
	print "#########################################################################\n\n"


##### Ask a 'yes' or 'no' question and check answer #####
##### Accept 'yes', 'no', 'y', or 'n' #####
def yesorno(question):
	answer = 'temp'
	while answer.lower() != 'yes' and answer.lower() != 'no' and answer.lower() != 'y' and answer.lower() != 'n':
		answer = raw_input(color("----- " + question + " [yes or no]:", cyan))
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
			print color("'Yes' or 'No' dude...", red)


##### Create dictionary with client IP and shared password entries for FreeRADIUS server #####
##### Used to ask questions during install about IP blocks and shared secret to use for FreeRADIUS server #####
def freeradius_create_changes():
	##### Set variables for use later #####
	keepchanging = "yes"
	addips = []
	##### Ask for IP address blocks and append each entry to a list. User can accept the example though #####
	while keepchanging != "no":
		addipexample = "10.0.0.0/8"
		goround = raw_input(
			color('\n>>>>> Enter the IP subnet to use for recognition of RADIUS accounting sources: [' + addipexample + ']:', cyan))
		if goround == "":
			goround = addipexample
		ipcheck = cidr_checker(goround)
		if ipcheck == 'no':
			print color("~~~ Nope. Give me a legit CIDR block...", red)
		elif ipcheck == 'yes':
			addips.append(goround)
			print color("~~~ Added " + goround + " to list\n", yellow)
			keepchanging = yesorno("Do you want to add another IP block to the list of trusted sources?")
	##### List out entries #####
	print "\n\n"
	print "List of IP blocks for accounting sources:"
	for each in addips:
		print color(each, yellow)
	print "\n\n"
	##### Have user enter shared secret to pair with all IP blocks in output dictionary #####
	radiussecret = ""
	radiussecret = raw_input(
		color('>>>>> Enter a shared RADIUS secret to use with the accounting sources: [password123]:', cyan))
	if radiussecret == "":
		radiussecret = "password123"
	print color("~~~ Using '" + radiussecret + "' for shared secret\n", yellow)
	##### Pair each IP entry with the shared secret and put in dictionary for output #####
	radiusclientdict = {}
	for each in addips:
		radiusclientdict[each] = radiussecret
	return radiusclientdict


##### Use dictionary of edits for FreeRADIUS and push them to the config file #####
def freeradius_editor(dict_edits):
	clientconfpath = '/etc/raddb/clients.conf'
	iplist = dict_edits.keys()
	print "\n\n\n"
	print "###############Writing the below to the FreeRADIUS client.conf file###############"
	print "##################################################################################"
	for ip in iplist:
		newwrite = "\nclient " + ip + " {\n    secret      = " + dict_edits[
			ip] + "\n    shortname   = Created_By_RadiUID\n }\n"
		f = open(clientconfpath, 'a')
		f.write(newwrite)
		f.close()
		print newwrite
	print "################################################################################"
	print "\n"
	progress("Writing: ", 1)
	print "\n\n\n"
	print "****************Restarting the FreeRADIUS service to effect changes...****************\n\n"
	progress("Starting/Restarting: ", 1)
	os.system('systemctl restart radiusd')
	os.system('systemctl status radiusd')
	checkservice = check_service_running('radiusd')
	if checkservice == 'no':
		print color("\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to start back up.", red)
		print color("***** We may have made some adverse changes to the config file.", red)
		print color("***** Visit the FreeRADIUS config file at " + clientconfpath + " and remove the bad changes.", red)
		print color("***** Then try to start the FreeRADIUS service by issuing the 'systemctl start radiusd' command", red)
		raw_input(color("Hit ENTER to continue...\n\n>>>>>", cyan))
	elif checkservice == 'yes':
		print color("\n\n***** Great Success!! Looks like FreeRADIUS restarted and is back up now!", green)
		print color("***** If you need to manually edit the FreeRADIUS config file, it is located at " + clientconfpath, green)
		raw_input(color("\nHit ENTER to continue...\n\n>>>>>", cyan))


##### Print out this ridiculous text-o-graph #####
##### It took me like an hour to draw and I couldn't stand to just not use it #####
def packetsar():
	print  color("\n                        ###############################################      \n\
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
		        ###############################################      \n", blue)


				
				
				
				
				
				
				
				
#######################Installer Running Function########################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

def installer():
	print "\n\n\n\n\n\n\n\n"
	print '                       ##################################################' \
			'\n' + '                       ########Install Utility for RadiUID Server########' \
			'\n' + '                       ##########    Please Use Carefully!    ###########' \
			'\n' + '                       ##################################################' \
			'\n' + '                       ##################################################' \
			'\n' + '                       ##################################################' \
			'\n' + '                       ######       Written by John W Kerns        ######' \
			'\n' + '                       ######      http://blog.packetsar.com       ######' \
			'\n' + '                       ###### https://github.com/PackeTsar/radiuid ######' \
			'\n' + '                       ##################################################' \
			'\n' + '                       ##################################################' \
			'\n' + '                       ##################################################' \
 \

	print "\n\n\n"
	print "****************First, we will check if FreeRADIUS and RadiUID are installed yet...****************\n"
	raw_input(color("\n\n>>>>> Hit ENTER to continue...\n\n>>>>>", cyan))
	print "\n\n\n\n\n\n\n"



	#########################################################################
	###Check if FreeRADIUS is installed and running already
	#########################################################################
	print "\n\n\n\n\n\n****************Checking if FreeRADIUS is installed...****************\n"
	freeradiusinstalled = check_service_installed('radiusd')
	freeradiusrunning = check_service_running('radiusd')

	if freeradiusinstalled == 'yes' and freeradiusrunning == 'yes':
		print color("***** Looks like the FreeRADIUS service is already installed and running...skipping the install of FreeRADIUS", green)

	if freeradiusinstalled == 'yes' and freeradiusrunning == 'no':
		freeradiusrestart = yesorno("Looks like FreeRADIUS is installed, but not running....want to start it up?")
		if freeradiusrestart == 'yes':
			restart_service('radiusd')
			freeradiusrunning = check_service_running('radiusd')
			if freeradiusrunning == 'no':
				print color("***** It looks like FreeRADIUS failed to start up. You may need to change its settings and restart it manually...", red)
				print color("***** Use the command 'radiuid edit clients' to open and edit the FreeRADIUS client settings file manually", red)
			if freeradiusrunning == 'yes':
				print color("***** Very nice....Great Success!!!", green)
		if freeradiusrestart == 'no':
			print color("~~~ OK, leaving it off...", yellow)

	if freeradiusinstalled == 'no' and freeradiusrunning == 'no':
		freeradiusinstall = yesorno(
			"Looks like FreeRADIUS is not installed. It is required by RadiUID. Is it ok to install FreeRADIUS?")
		if freeradiusinstall == 'yes':
			install_freeradius()
			checkservice = check_service_running('radiusd')
			if checkservice == 'no':
				print color("\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to install or start up.", red)
				print color("***** It is possible that the native package manager si not able to download the install files.", red)
				print color("***** Make sure that you have internet access and your package manager is able to download the FreeRADIUS install files", red)
				raw_input(color("Hit ENTER to quit the program...\n", cyan))
				quit()
			elif checkservice == 'yes':
				print color("\n\n***** Great Success!! Looks like FreeRADIUS installed and started up successfully.", green)
				print color("***** We will be adding client IP and shared secret info to FreeRADIUS later in this wizard.", green)
				print color("***** If you need to manually edit the FreeRADIUS config file later, you can run 'radiuid edit clients' in the CLI", green)
				print color("***** You can also manually open the file for editing. It is located at /etc/raddb/clients.conf", green)

				raw_input(color("\n***** Hit ENTER to continue...\n\n>>>>>", cyan))
		if freeradiusinstall == 'no':
			print color("***** FreeRADIUS is required by RadiUID. Quitting the installer", red)
			quit()

	#########################################################################
	###Check if RadiUID is installed and running already
	#########################################################################
	print "\n\n\n\n\n\n****************Checking if RadiUID is already installed...****************\n"
	radiuidinstalled = check_service_installed('radiuid')
	radiuidrunning = check_service_running('radiuid')

	if radiuidinstalled == 'yes' and radiuidrunning == 'yes':
		print color("***** Looks like the RadiUID service is already installed and running...skipping the install of RadiUID\n", green)
		radiuidreinstall = yesorno("Do you want to re-install the RadiUID service?")
		if radiuidreinstall == 'yes':
			print color("***** You are about to re-install the RadiUID service...", yellow)
			print color("***** If you continue, you will have to proceed with the wizard to the next step where we configure the settings in the config file...", yellow)
			raw_input(color(">>>>> Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>", cyan))
			print "\n\n****************Re-installing the RadiUID service...****************\n"
			copy_radiuid()
			install_radiuid()
			print "\n\n****************We will start up the RadiUID service once we configure the .conf file****************\n"
		if radiuidreinstall == 'no':
			print "~~~ Yea, probably best to leave it alone..."


	if radiuidinstalled == 'yes' and radiuidrunning == 'no':
		print "\n"
		print color("***** Looks like RadiUID is installed, but not running....", yellow)
		radiuidrestart = yesorno("Do you want to start it up?")
		if radiuidrestart == 'yes':
			restart_service('radiuid')
			radiuidrunning = check_service_running('radiuid')
			if radiuidrunning == "yes":
				print color("***** Very nice....Great Success!!!", green)
			if radiuidrunning == "no":
				print color("***** Looks like the startup failed...", red)
				radiuidreinstall = yesorno("Do you want to re-install the RadiUID service?")
				if radiuidreinstall == 'yes':
					print "\n\n****************Re-installing the RadiUID service...****************\n"
					copy_radiuid()
					install_radiuid()
					print "\n\n****************We will start up the RadiUID service once we configure the .conf file****************\n"
		if radiuidrestart == 'no':
			print color("~~~ OK, leaving it off...", yellow)

	if radiuidinstalled == 'no' and radiuidrunning == 'no':
		print "\n"
		radiuidinstall = yesorno("Looks like RadiUID is not installed. Is it ok to install RadiUID?")
		if radiuidinstall == 'yes':
			print "\n\n****************Installing the RadiUID service...****************\n"
			copy_radiuid()
			install_radiuid()
			print "\n\n****************We will start up the RadiUID service once we configure the .conf file****************\n"

		if radiuidinstall == 'no':
			print color("***** The install of RadiUID is required. Quitting the installer", red)
			quit()


	print "\n\n\n\n"

	#########################################################################
	###Read current .conf settings into interpreter
	#########################################################################
	editradiuidconf = yesorno("Do you want to edit the settings in the RadiUID .conf file (if you just installed RadiUID, then you need to do this)?")
	if editradiuidconf == "yes":
		configfile = find_config("noisy")
		checkfile = file_exists(configfile)
		if checkfile == 'no':
			print color("ERROR: Config file (radiuid.conf) not found. Make sure the radiuid.conf file exists in same directory as radiuid.py", red)
			quit()
		print "Configuring File: " + color(configfile, green) + "\n"
		print "\n\n\n****************Now, we will import the settings from the " + configfile + " file...****************\n"
		print "*****************The current values for each setting are [displayed in the prompt]****************\n"
		print "****************Leave the prompt empty and hit ENTER to accept the current value****************\n"
		raw_input(color("\n\n>>>>> Hit ENTER to continue...\n\n>>>>>", cyan))
		print "\n\n\n\n\n\n\n"
		print "**************** Reading in current settings from " + configfile + " ****************\n"
		progress('Reading:', 1)
		
		parser = ConfigParser.SafeConfigParser()
		parser.read(configfile)
		
		f = open(configfile, 'r')
		config_file_data = f.read()
		f.close()

		logfile = parser.get('Paths_and_Files', 'logfile')
		radiuslogpath = parser.get('Paths_and_Files', 'radiuslogpath')
		hostname = parser.get('Palo_Alto_Target', 'hostname')
		panosversion = parser.get('Palo_Alto_Target', 'OS_Version')
		username = parser.get('Palo_Alto_Target', 'username')
		password = parser.get('Palo_Alto_Target', 'password')
		extrastuff = parser.get('URL_Stuff', 'extrastuff')
		ipaddressterm = parser.get('Search_Terms', 'ipaddressterm')
		usernameterm = parser.get('Search_Terms', 'usernameterm')
		delineatorterm = parser.get('Search_Terms', 'delineatorterm')
		userdomain = parser.get('UID_Settings', 'userdomain')
		timeout = parser.get('UID_Settings', 'timeout')
		
		
		#########################################################################
		###Ask questions to the console for editing the .conf file settings
		#########################################################################
		print "\n\n\n\n\n\n****************Please enter values for the different settings in the radiuid.conf file****************\n"
		newlogfile = change_setting(logfile, 'Enter full path to the new RadiUID Log File')
		print "\n"
		newradiuslogpath = change_setting(radiuslogpath, 'Enter path to the FreeRADIUS Accounting Logs')
		print "\n"
		newhostname = change_setting(hostname, 'Enter IP address or hostname for target Palo Alto firewall')
		print "\n"
		newpanosversion = change_setting(panosversion,
										'Enter PAN-OS software version on target firewall (only PAN-OS 7 is currently supported)')
		print "\n"
		newusername = change_setting(username, 'Enter administrative username for Palo Alto firewall')
		print "\n"
		newpassword = change_setting(password,
									'Enter administrative password for Palo Alto firewall (entered text will be shown in the clear)')
		print "\n"
		newuserdomain = change_setting(userdomain, 'Enter the user domain to be prefixed to User-IDs')
		print "\n"
		newtimeout = change_setting(timeout, 'Enter timeout period for pushed UIDs (in minutes)')
		
		#########################################################################
		###Pushing settings to .conf file with the code below
		#########################################################################
		print "\n\n\n\n\n\n****************Applying entered settings into the radiuid.conf file...****************\n"
		new_config_file_data = config_file_data
		progress('Applying:', 1)
		new_config_file_data = apply_setting(new_config_file_data, 'logfile', logfile, newlogfile)
		new_config_file_data = apply_setting(new_config_file_data, 'radiuslogpath', radiuslogpath, newradiuslogpath)
		new_config_file_data = apply_setting(new_config_file_data, 'hostname', hostname, newhostname)
		new_config_file_data = apply_setting(new_config_file_data, 'panosversion', panosversion, newpanosversion)
		new_config_file_data = apply_setting(new_config_file_data, 'username', username, newusername)
		new_config_file_data = apply_setting(new_config_file_data, 'password', password, newpassword)
		new_config_file_data = apply_setting(new_config_file_data, 'userdomain', userdomain, newuserdomain)
		new_config_file_data = apply_setting(new_config_file_data, 'timeout', timeout, newtimeout)
		
		write_file(etcconfigfile, new_config_file_data)
		
		newlogfiledir = strip_filepath(newlogfile)[0][0]
		os.system('mkdir -p ' + newlogfiledir)
		
		print "\n\n****************Starting/Restarting the RadiUID service...****************\n"
		restart_service('radiuid')
		radiuidrunning = check_service_running('radiuid')
		if radiuidrunning == "yes":
			print color("***** RadiUID successfully started up!!!", green)
		raw_input(color(">>>>> Hit ENTER to continue...\n\n>>>>>", cyan))
		if radiuidrunning == "no":
			print color("***** Something went wrong. Looks like the installation or startup failed... ", red)
			print color("***** Please make sure you are installing RadiUID on a support platform", red)
			print color("***** You can manually edit the RadiUID config file by entering 'radiuid edit config' in the CLI", red)
			raw_input(color("Hit ENTER to quit the program...\n\n>>>>>", cyan))
			quit()
	else:
		print "~~~ OK... Leaving the .conf file alone"

	#########################################################################
	###Make changes to FreeRADIUS config file
	#########################################################################
	print "\n\n\n\n\n\n****************Let's make some changes to the FreeRADIUS client config file****************\n"
	editfreeradius = yesorno(
		"Do you want to make changes to FreeRADIUS by adding some IP blocks for accepted accounting clients?")

	if editfreeradius == "yes":
		freeradiusedits = freeradius_create_changes()
		freeradius_editor(freeradiusedits)

	#########################################################################
	###Trailer/Goodbye
	#########################################################################
	print "\n\n\n\n\n\n***** Thank you for using the RadiUID installer/management utility"
	raw_input(color(">>>>> Hit ENTER to see the tail of the RadiUID log file before you exit the utility\n\n>>>>>", cyan))
	
	##### Read in logfile path from found config file #####
	configfile = find_config("quiet")
	parser = ConfigParser.SafeConfigParser()
	parser.read(configfile)
	f = open(configfile, 'r')
	config_file_data = f.read()
	f.close()
	logfile = parser.get('Paths_and_Files', 'logfile')
	#######################################################

	print "\n\n############################## LAST 50 LINES FROM " + logfile + "##############################"
	print "########################################################################################################"
	os.system("tail -n 50 " + logfile)
	print "########################################################################################################"
	print "########################################################################################################"
	print "\n\n\n\n***** Looks like we are all done here...\n"
	raw_input(
		color(">>>>> Hit ENTER to exit the Install/Maintenance Utility\n\n>>>>>", cyan))
	quit()






#############Find the config file from two alternative paths#############
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

def get_working_directory():
	listoutput = commands.getstatusoutput("pwd")
	result = listoutput[1]
	result = directory_slash_add(result)
	return result


def find_config(mode):
	global configfile
	if mode == "noisy":
		print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********LOOKING FOR RADIUID CONFIG FILE...***********" + "\n"
		print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********DETECTED WORKING DIRECTORY: " + get_working_directory() + "***********" + "\n"
		print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********CHECKING LOCATION: PREFERRED LOCATION - " + etcconfigfile + "***********" + "\n"
		print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********CHECKING LOCATION: ALTERNATE LOCATION IN LOCAL DIRECTORY - " + localconfigfile + "***********" + "\n"
		configfile = file_chooser(etcconfigfile, localconfigfile)
		print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********FOUND CONFIG FILE IN LOCATION: " + configfile + "***********" + "\n"
		return configfile
	if mode == "quiet":
		configfile = file_chooser(etcconfigfile, localconfigfile)
		return configfile
	else:
		print "Need to set mode for find_config"
		quit()




#################Primary Running Function and Looper#####################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
######################################################################### 


def initialize():
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
	checkfile = file_exists(configfile)
	if checkfile == 'no':
		print time.strftime(
			"%Y-%m-%d %H:%M:%S") + ":   " + "ERROR: CANNOT FIND RADIUID CONFIG FILE IN TYPICAL PATHS. QUITTING PROGRAM. RE-RUN INSTALLER ('python radiuid.py install')" + "\n"
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
	
	log_writer(logfile, 
		"***********RADIUID INITIALIZING... IF PROGRAM FAULTS NOW, MAKE SURE YOU SUCCESSFULLY RAN THE INSTALLER ('python radiuid.py install')***********")
	
	##### Suck in all variables from config file (only run when program is initially started, not during while loop) #####
	
	log_writer(logfile, 
		"***********INITIAL WRITE TO THE LOG FILE: " + logfile + "...***********")

	log_writer(logfile, 
		"***********INITIALIZING VARIABLES FROM CONFIG FILE: " + configfile + "...***********")
	
	log_writer(logfile, "Initialized variable:" "\t" + "logfile" + "\t\t\t\t" + "with value:" + "\t" + color(logfile, green))
	
	radiuslogpath = parser.get('Paths_and_Files', 'radiuslogpath')
	log_writer(logfile, "Initialized variable:" "\t" + "radiuslogpath" + "\t\t\t" + "with value:" + "\t" + color(radiuslogpath, green))
	
	hostname = parser.get('Palo_Alto_Target', 'hostname')
	log_writer(logfile, "Initialized variable:" "\t" + "hostname" + "\t\t\t" + "with value:" + "\t" + color(hostname, green))
	
	panosversion = parser.get('Palo_Alto_Target', 'OS_Version')
	log_writer(logfile, "Initialized variable:" "\t" + "panosversion" + "\t\t\t" + "with value:" + "\t" + color(panosversion, green))
	
	panuser = parser.get('Palo_Alto_Target', 'username')
	log_writer(logfile, "Initialized variable:" "\t" + "panuser" + "\t\t\t\t" + "with value:" + "\t" + color(panuser, green))
	
	panpassword = parser.get('Palo_Alto_Target', 'password')
	log_writer(logfile, "Initialized variable:" "\t" + "panpassword" + "\t\t\t" + "with value:" + "\t" + color(panpassword, green))
	
	extrastuff = parser.get('URL_Stuff', 'extrastuff')
	log_writer(logfile, "Initialized variable:" "\t" + "extrastuff" + "\t\t\t" + "with value:" + "\t" + color(extrastuff, green))
	
	ipaddressterm = parser.get('Search_Terms', 'ipaddressterm')
	log_writer(logfile, "Initialized variable:" "\t" + "ipaddressterm" + "\t\t\t" + "with value:" + "\t" + color(ipaddressterm, green))
	
	usernameterm = parser.get('Search_Terms', 'usernameterm')
	log_writer(logfile, "Initialized variable:" "\t" + "usernameterm" + "\t\t\t" + "with value:" + "\t" + color(usernameterm, green))
	
	delineatorterm = parser.get('Search_Terms', 'delineatorterm')
	log_writer(logfile, "Initialized variable:" "\t" + "delineatorterm" + "\t\t\t" + "with value:" + "\t" + color(delineatorterm, green))
	
	userdomain = parser.get('UID_Settings', 'userdomain')
	log_writer(logfile, "Initialized variable:" "\t" + "userdomain" + "\t\t\t" + "with value:" + "\t" + color(userdomain, green))
	
	timeout = parser.get('UID_Settings', 'timeout')
	log_writer(logfile, "Initialized variable:" "\t" + "timeout" + "\t\t\t\t" + "with value:" + "\t" + color(timeout, green))
	
	##### Explicitly pull PAN key now and store API key in the main namespace #####
	
	log_writer(logfile, 
		"***********************************CONNECTING TO PALO ALTO FIREWALL TO EXTRACT THE API KEY...***********************************")
	log_writer(logfile, 
		"********************IF PROGRAM FREEZES/FAILS RIGHT NOW, THEN THERE IS LIKELY A COMMUNICATION PROBLEM WITH THE FIREWALL********************")
	
	pankey = pull_api_key(panuser, panpassword)
	log_writer(logfile, "Initialized variable:" "\t" + "pankey" + "\t\t\t\t" + "with value:" + "\t" + pankey)
	
	log_writer(logfile, 
		"*******************************************CONFIG FILE SETTINGS INITIALIZED*******************************************")
	
	log_writer(logfile, 
		"***********************************RADIUID SERVER STARTING WITH INITIALIZED VARIABLES...******************************")


def radiuid():
	filelist = listfiles(radiuslogpath)
	if len(filelist) > 0:
		usernames = search_to_dict(filelist, delineatorterm, usernameterm)
		ipaddresses = search_to_dict(filelist, delineatorterm, ipaddressterm)
		usernames = clean_names(usernames)
		ipaddresses = clean_ips(ipaddresses)
		ipanduserdict = merge_dicts(ipaddresses, usernames)
		push_uids(ipanduserdict, filelist)
		del filelist
		del usernames
		del ipaddresses
		del ipanduserdict


def radiuid_looper():
	configfile = find_config("noisy")
	initialize()
	while __name__ == "__main__":
		radiuid()
		time.sleep(10)




#######################ARG DECODER MAIN PROGRAM##########################
################ Recognizes arguments from program call #################
############## and run the appropriate part of the program ##############
####### if given inappropriate arg, returns list of supported args#######
#########################################################################
#########################################################################

######################### SET COMMON PATHS FOR CONFIG FILE IN GLOBAL NAMESPACE #############################
etcconfigfile = "/etc/radiuid/radiuid.conf"
localconfigfile = get_working_directory() + "radiuid.conf"



def main():
	######################### RUN #############################
	if cat_list(sys.argv[1:]) == "run":
		radiuid_looper()
	######################### INSTALL #############################
	elif cat_list(sys.argv[1:]) == "install":
		print "\n\n\n"
		packetsar()
#		configfile = find_config("noisy")
#		checkfile = file_exists(configfile)
#		if checkfile == 'no':
#			print color("ERROR: Config file (radiuid.conf) not found. Make sure the radiuid.conf file exists in same directory as radiuid.py", red)
#			quit()
#		print "Configuring File: " + color(configfile, green) + "\n"
		progress("Running RadiUID in Install/Maintenance Mode:", 3)
		installer()
		quit()
	######################### SHOW #############################
	elif cat_list(sys.argv[1:]) == "show" or cat_list(sys.argv[1:]) == "show ?":
		print "\n - show log       |     Show the RadiUID log file"
		print " - show run         |     Show the RadiUID config file"
		print " - show config      |     Show the RadiUID config file"
		print " - show status      |     Show the RadiUID and FreeRADIUS service statuses"
	elif cat_list(sys.argv[1:]) == "show log":
		configfile = find_config("quiet")
		parser = ConfigParser.SafeConfigParser()
		parser.read(configfile)
		f = open(configfile, 'r')
		config_file_data = f.read()
		f.close()
		logfile = parser.get('Paths_and_Files', 'logfile')
		header = "########################## OUTPUT FROM FILE " + logfile + " ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("more " + logfile)
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	elif cat_list(sys.argv[1:]) == "show run":
		configfile = find_config("quiet")
		header = "########################## OUTPUT FROM FILE " + configfile + " ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("more " + configfile)
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	elif cat_list(sys.argv[1:]) == "show config":
		configfile = find_config("quiet")
		header = "########################## OUTPUT FROM FILE " + configfile + " ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("more " + configfile)
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	elif cat_list(sys.argv[1:]) == "show status":
		header = "########################## OUTPUT FROM COMMAND: 'systemctl status radiuid' ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiuid")
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
		serviceinstalled = check_service_installed("radiuid")
		if serviceinstalled == "no":
			print color("\n\n********** RADIUID IS NOT INSTALLED YET **********\n\n", yellow)
		elif serviceinstalled == "yes":
			checkservice = check_service_running("radiuid")
			if checkservice == "yes":
				print color("\n\n********** RADIUID IS CURRENTLY RUNNING **********\n\n", green)
			elif checkservice == "no":
				print color("\n\n********** RADIUID IS CURRENTLY NOT RUNNING **********\n\n", yellow)


		header = "########################## OUTPUT FROM COMMAND: 'systemctl status radiusd' ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiusd")
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
		serviceinstalled = check_service_installed("radiusd")
		if serviceinstalled == "no":
			print color("\n\n********** FREERADIUS IS NOT INSTALLED YET **********\n\n", yellow)
		elif serviceinstalled == "yes":
			checkservice = check_service_running("radiusd")
			if checkservice == "yes":
				print color("\n\n********** FREERADIUS IS CURRENTLY RUNNING **********\n\n", green)
			elif checkservice == "no":
				print color("\n\n********** FREERADIUS IS CURRENTLY NOT RUNNING **********\n\n", yellow)
	######################### TAIL #############################
	elif cat_list(sys.argv[1:]) == "tail" or cat_list(sys.argv[1:]) == "tail ?":
		print "\n - tail log         |     Watch the RadiUID log file in real time\n"
	elif cat_list(sys.argv[1:]) == "tail log":
		configfile = find_config("quiet")
		parser = ConfigParser.SafeConfigParser()
		parser.read(configfile)
		f = open(configfile, 'r')
		config_file_data = f.read()
		f.close()
		logfile = parser.get('Paths_and_Files', 'logfile')
		header = "########################## OUTPUT FROM FILE " + logfile + " ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("tail -f " + logfile)
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	######################### CLEAR #############################
	elif cat_list(sys.argv[1:]) == "clear" or cat_list(sys.argv[1:]) == "clear ?":
		print "\n - clear log         |     Delete the content in the log file\n"
	elif cat_list(sys.argv[1:]) == "clear log":
		configfile = find_config("quiet")
		parser = ConfigParser.SafeConfigParser()
		parser.read(configfile)
		f = open(configfile, 'r')
		config_file_data = f.read()
		f.close()
		logfile = parser.get('Paths_and_Files', 'logfile')
		print color("********************* You are about to clear out the RadiUID log file... (" + logfile + ") ********************", yellow)
		raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
		os.system("rm -f "+ logfile)
		write_file(logfile, "***********Log cleared by RadiUID command***********\n")
		print color("********************* Cleared logfile: " + logfile + " ********************", yellow)
	######################### EDIT #############################
	elif cat_list(sys.argv[1:]) == "edit" or cat_list(sys.argv[1:]) == "edit ?":
		print "\n - edit config      |     Edit the RadiUID config file"
		print " - edit clients     |     Edit list of client IPs for FreeRADIUS\n"
	elif cat_list(sys.argv[1:]) == "edit config":
		print color("****************** You are about to edit the RadiUID config file in VI ******************", yellow)
		print color("********************* Confirm that you know how to use the VI editor ********************", yellow)
		raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
		os.system("vi /etc/radiuid/radiuid.conf")
	elif cat_list(sys.argv[1:]) == "edit clients":
		print color("****************** You are about to edit the FreeRADIUS client file in VI ******************", yellow)
		print color("*********************** Confirm that you know how to use the VI editor ********************", yellow)
		raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
		os.system("vi /etc/raddb/clients.conf")
	######################### OTHERS #############################
	elif cat_list(sys.argv[1:]) == "start":
		os.system("systemctl start radiuid")
		os.system("systemctl status radiuid")
		checkservice = check_service_running("radiuid")
		if checkservice == "yes":
			print color("\n\n********** RADIUID SUCCESSFULLY STARTED UP! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
	elif cat_list(sys.argv[1:]) == "stop":
		header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiuid")
		print color("\n\n***** ARE YOU SURE YOU WANT TO STOP IT?", yellow)
		raw_input(color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", cyan))
		os.system("systemctl stop radiuid")
		os.system("systemctl status radiuid")
		print color("\n\n********** RADIUID STOPPED **********\n\n", yellow)
	elif cat_list(sys.argv[1:]) == "restart":
		header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiuid")
		print color("\n\n***** ARE YOU SURE YOU WANT TO RESTART IT?", yellow)
		raw_input(color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", cyan))
		os.system("systemctl stop radiuid")
		os.system("systemctl status radiuid")
		print color("\n\n********** RADIUID STOPPED **********\n\n", yellow)
		progress("Preparing to Start Up:", 2)
		print "\n\n\n"
		os.system("systemctl start radiuid")
		os.system("systemctl status radiuid")
		checkservice = check_service_running("radiuid")
		if checkservice == "yes":
			print color("\n\n********** RADIUID SUCCESSFULLY RESTARTED! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
	######################### GUIDE #############################
	else:
		print color("\n\n\n************************** Below are the supported RadiUID Commands: **************************\n\n", magenta)
		print " - run              |     Run the RadiUID main program to begin pushing User-ID information"
		print "----------------------------------------------------------------------------------------------\n"
		print " - install          |     Run the RadiUID Install/Maintenance Utility"
		print "----------------------------------------------------------------------------------------------\n"
		print " - show log         |     Show the RadiUID log file"
		print " - show run         |     Show the RadiUID config file"
		print " - show config      |     Show the RadiUID config file"
		print " - show status      |     Show the RadiUID and FreeRADIUS service statuses"
		print "----------------------------------------------------------------------------------------------\n"
		print " - tail log         |     Watch the RadiUID log file in real time"
		print "----------------------------------------------------------------------------------------------\n"
		print " - clear log        |     Delete the content in the log file"
		print "----------------------------------------------------------------------------------------------\n"
		print " - edit config      |     Edit the RadiUID config file"
		print " - edit clients     |     Edit list of client IPs for FreeRADIUS"
		print "----------------------------------------------------------------------------------------------\n"
		print " - start            |     Start the RadiUID system service"
		print " - stop             |     Stop the RadiUID system service"
		print " - restart          |     Restart the RadiUID system service"
		print "----------------------------------------------------------------------------------------------\n\n\n"



if __name__ == "__main__":
	main()

#######################END OF PROGRAM###############################
