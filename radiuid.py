#!/bin/python

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


##### Check if specific file exists #####
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


##### Writes lines to the log file and prints them to the terminal #####
def log_writer(input):
	target = open(logfile, 'a')
	target.write(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n")
	print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n"
	target.close()


##### Function to pull API key from firewall to be used for REST HTTP calls #####
def pull_api_key(username, password):
	url = 'https://' + hostname + '/api/?type=keygen&user=' + username + '&password=' + password
	response = urllib2.urlopen(url).read()
	log_writer("Pulling API key using PAN credentials: " + username + "\\" + password + "\n")
	log_writer(response + "\n")
	if 'success' in response:
		stripped1 = response.replace("<response status = 'success'><result><key>", "")
		stripped2 = stripped1.replace("</key></result></response>", "")
		return stripped2
	else:
		print 'ERROR: Username\\password failed. Please re-enter in config file...' + '\n'
		quit()


##### List all files in a directory path and subdirs #####
def listfiles(path):
	filelist = []
	for root, directories, filenames in os.walk(path):
		for filename in filenames:
			entry = os.path.join(root, filename)
			filelist.append(entry)
			log_writer("Found File: " + entry + "...   Adding to file list")
	if len(filelist) == 0:
		log_writer("No Log Files Found. Nothing to Do.")
		return filelist
	else:
		return filelist


##### Search list of files for a searchterm and use deliniator term to count instances file, then return a dictionary where key=instance and value=line where term was found #####
def search_to_dict(filelist, delineator, searchterm):
	dict = {}
	entry = 0
	for filename in filelist:
		log_writer('Searching File: ' + filename + ' for ' + searchterm)
		with open(filename, 'r') as filetext:
			for line in filetext:
				if delineator in line:
					entry = entry + 1
				if searchterm in line:
					dict[entry] = line
	return dict


##### Clean up IP addresses in dictionary #####
def clean_ips(dictionary):
	newdict = {}
	for key, value in dictionary.iteritems():
		clean1 = value.replace("\t" + ipaddressterm + " = ", "")
		cleaned = clean1.replace("\n", "")
		newdict[key] = cleaned
	log_writer("IP Address List Cleaned Up!")
	return newdict


##### Clean up user names in dictionary #####
def clean_names(dictionary):
	newdict = {}
	for key, value in dictionary.iteritems():
		clean1 = value.replace("\t" + usernameterm + " = '", "")
		cleaned = clean1.replace("'\n", "")
		newdict[key] = cleaned
	log_writer("Username List Cleaned Up!")
	return newdict


##### Merge dictionary values from two dictionaries into one dictionary and remove duplicates #####
def merge_dicts(keydict, valuedict):
	newdict = {}
	keydictkeylist = keydict.keys()
	for each in keydictkeylist:
		v = valuedict[each]
		k = keydict[each]
		newdict[k] = v
	log_writer("Dictionary values merged into one dictionary")
	return newdict


##### Delete all files in provided list #####
def remove_files(filelist):
	for filename in filelist:
		os.remove(filename)
		log_writer("Removed file: " + filename)


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
		log_writer("PAN-OS version not supported for XML push!")
		quit()


##### Use urlconverter (above) to encode the URL to acceptable format and use REST call to push UID info to PAN #####
def push_uids(ipanduserdict, filelist):
	iteration = 0
	ipaddresses = ipanduserdict.keys()
	for ip in ipaddresses:
		url = url_converter_v7(ipanduserdict[ip], ip)
		log_writer("Pushing    |    " + userdomain + "\\" + ipanduserdict[ip] + ":" + ip)
		response = urllib2.urlopen(url).read()
		log_writer(response + "\n")
		iteration = iteration + 1
	remove_files(filelist)


#######################RadiUID Installer Functions#######################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################


##### Add '/' to directory path if not included #####
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
		print "~~~ Added a '/' to the end of the path. Make sure to include it next time"
		return result
	else:
		result = directorypath
		return result


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


######################Find/Replace entries in config file##########################
def config_replace(searchfor, replacewith):
	f = open('radiuid.conf', 'r')
	filedata = f.read()
	f.close()
	newdata = filedata.replace(searchfor, replacewith)
	f = open('radiuid.conf', 'w')
	f.write(newdata)
	f.close()


######################Show progress bar##########################
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


######################Change variables to change settings##########################
def change_setting(setting, question):
	newsetting = raw_input(">>>>> " + question + " [" + setting + "]: ")
	if newsetting == '':
		print "~~~ Keeping current setting..."
		newsetting = setting
	else:
		print "~~~ Changed setting to: " + newsetting
	return newsetting


######################Apply new setting to the .conf file##########################
def apply_setting(settingname, oldsetting, newsetting):
	if oldsetting == newsetting:
		print "***** No changes to  : " + settingname
	else:
		config_replace(settingname + " = " + oldsetting, settingname + " = " + newsetting)
		print "***** Changed setting: " + settingname + "\t\t|\tfrom: " + oldsetting + "\tto: " + newsetting


######################Check if a particular systemd service is installed##########################
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


######################Check if a particular systemd service is running##########################
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


######################Install FreeRADIUS server##########################
def install_freeradius():
	os.system('yum install freeradius -y')
	print "\n\n\n\n\n\n****************Setting FreeRADIUS as a system service...****************\n"
	progress("Progress: ", 1)
	os.system('systemctl enable radiusd')
	os.system('systemctl start radiusd')


######################Copy RadiUID files##########################
def copy_radiuid(installationpath):
	os.system('mkdir -p ' + installationpath)
	os.system('cp radiuid.conf ' + installationpath + 'radiuid.conf')
	os.system('cp radiuid.py ' + installationpath + 'radiuid.py')
	progress("Copying Files: ", 2)


######################Install RadiUID SystemD service##########################
def install_radiuid(installationpath):
	##############STARTFILE DATA START##############
	startfile = "[Unit]" \
	            "\n" + "Description=RadiUID User-ID Service" \
	                   "\n" + "After=network.target" \
	                          "\n" \
	                          "\n" + "[Service]" \
	                                 "\n" + "Type=simple" \
	                                        "\n" + "User=root" \
	                                               "\n" + "ExecStart=/bin/bash -c 'cd " + installationpath + "; python radiuid.py'" \
	                                                                                                         "\n" + "Restart=on-abort" \
	                                                                                                                "\n" \
	                                                                                                                "\n" \
	                                                                                                                "\n" + "[Install]" \
	                                                                                                                       "\n" + "WantedBy=multi-user.target" \
		##############STARTFILE DATA STOP##############
	f = open('/etc/systemd/system/radiuid.service', 'w')
	f.write(startfile)
	f.close()
	progress("Installing: ", 2)
	os.system('systemctl enable radiuid')


######################Restart a particular SystemD service##########################
def restart_service(service):
	commands.getstatusoutput("systemctl start " + service)
	commands.getstatusoutput("systemctl restart " + service)
	progress("Starting/Restarting: ", 1)
	print "\n\n#########################################################################"
	os.system("systemctl status " + service)
	print "#########################################################################\n\n"


######################Ask a 'yes' or 'no' question and check answer##########################
def yesorno(question):
	answer = 'temp'
	while answer != 'yes' and answer != 'no' and answer != 'y' and answer != 'n':
		answer = raw_input("----- " + question + " [yes or no]:")
		if answer == "no":
			return answer
		elif answer == "yes":
			return answer
		elif answer == "n":
			answer = "no"
			return answer
		elif answer == "y":
			answer = "yes"
			return answer
		else:
			print "'Yes' or 'No' dude..."


######################Create dictionary with client IP and shared password entries for FreeRADIUS server##########################
def freeradius_create_changes():
	#####Set variables for use later#####
	keepchanging = "yes"
	addips = []
	#####Ask for IP address blocks and append each entry to a list. User can accept the example though#####
	while keepchanging != "no":
		addipexample = "10.0.0.0/8"
		goround = raw_input(
			'\n>>>>> Enter the IP subnet to use for recognition of RADIUS accounting sources: [' + addipexample + ']:')
		if goround == "":
			goround = addipexample
		ipcheck = cidr_checker(goround)
		if ipcheck == 'no':
			print "~~~ Nope. Give me a legit CIDR block..."
		elif ipcheck == 'yes':
			addips.append(goround)
			print "~~~ Added " + goround + " to list\n"
			keepchanging = yesorno("Do you want to add another IP block to the list of trusted sources?")
	#####List out entries#####
	print "\n\n"
	print "List of IP blocks for accounting sources:"
	for each in addips:
		print each
	print "\n\n"
	#####Have user enter shared secret to pair with all IP blocks in output dictionary#####
	radiussecret = ""
	radiussecret = raw_input(
		'>>>>> Enter a shared RADIUS secret to use with the accounting sources: [password123]:')
	if radiussecret == "":
		radiussecret = "password123"
	print "~~~ Using '" + radiussecret + "' for shared secret\n"
	#####Pair each IP entry with the shared secret and put in dictionary for output#####
	radiusclientdict = {}
	for each in addips:
		radiusclientdict[each] = radiussecret
	return radiusclientdict


######################Use dictionary of edits for FreeRADIUS and push them to the config file##########################
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
		print "\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to start back up."
		print "***** We may have made some adverse changes to the config file."
		print "***** Visit the FreeRADIUS config file at " + clientconfpath + " and remove the bad changes."
		print "***** Then try to start the FreeRADIUS service by issuing the 'systemctl start radiusd' command"
		raw_input("Hit ENTER to continue...\n")
	elif checkservice == 'yes':
		print "\n\n***** Great Success!! Looks like FreeRADIUS restarted and is back up now!"
		print "***** If you need to manually edit the FreeRADIUS config file, it is located at " + clientconfpath
		raw_input("\nHit ENTER to continue...\n\n>>>>>")

def header():
	print  "\n                        ###############################################      \n\
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
		        ###############################################      \n"


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
	print "****************First, we will configure the settings for the radiuid.conf file...****************\n"
	print "*****************The current values for each setting are [displayed in the prompt]****************\n"
	print "****************Leave the prompt empty and hit ENTER to accept the current value****************\n"
	raw_input("\n\n>>>>> Hit ENTER to continue...\n\n>>>>>")
	print "\n\n\n\n\n\n\n"

	#########################################################################
	###Read current .conf settings into interpreter
	#########################################################################
	print "****************Reading in current settings from radiuid.conf file in current directory...****************\n"

	parser = ConfigParser.SafeConfigParser()
	parser.read('radiuid.conf')

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

	installpath = "/etc/radiuid/"

	progress('Reading:', 1)
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
	apply_setting('logfile', logfile, newlogfile)
	apply_setting('radiuslogpath', radiuslogpath, newradiuslogpath)
	apply_setting('hostname', hostname, newhostname)
	apply_setting('panosversion', panosversion, newpanosversion)
	apply_setting('username', username, newusername)
	apply_setting('password', password, newpassword)
	apply_setting('userdomain', userdomain, newuserdomain)
	apply_setting('timeout', timeout, newtimeout)

	progress('Applying:', 1)

	#########################################################################
	###Check if FreeRADIUS is installed and running already
	#########################################################################
	print "\n\n\n\n\n\n****************Checking if FreeRADIUS is installed...****************\n"
	freeradiusinstalled = check_service_installed('radiusd')
	freeradiusrunning = check_service_running('radiusd')

	if freeradiusinstalled == 'yes' and freeradiusrunning == 'yes':
		print "***** Looks like the FreeRADIUS service is already installed and running...skipping the install of FreeRADIUS"

	if freeradiusinstalled == 'yes' and freeradiusrunning == 'no':
		freeradiusrestart = yesorno("----- Looks like FreeRADIUS is installed, but not running....want to start it up?")
		if freeradiusrestart == 'yes':
			restart_service('radiusd')
			freeradiusrunning = check_service_running('radiusd')
			if freeradiusrunning == 'no':
				print "***** It looks like FreeRADIUS failed to start up. You may need to change its settings and restart it manually..."
			if freeradiusrunning == 'yes':
				print "***** Very nice....Great Success!!!"
		if freeradiusrestart == 'no':
			print "~~~ OK, leaving it off..."

	if freeradiusinstalled == 'no' and freeradiusrunning == 'no':
		freeradiusinstall = yesorno(
			"Looks like FreeRADIUS is not installed. It is required by RadiUID. Is it ok to install FreeRADIUS?")
		if freeradiusinstall == 'yes':
			install_freeradius()
			checkservice = check_service_running('radiusd')
			if checkservice == 'no':
				print "\n\n***** Uh Oh... Looks like the FreeRADIUS service failed to install or start up."
				print "***** It is possible that the native package manager si not able to download the install files."
				print "***** Make sure that you have internet access and your package manager is able to download the FreeRADIUS install files"
				raw_input("Hit ENTER to quit the program...\n")
				quit()
			elif checkservice == 'yes':
				print "\n\n***** Great Success!! Looks like FreeRADIUS installed and started up successfully."
				print "***** If you need to manually edit the FreeRADIUS config file, it is located at /etc/raddb/clients.conf"
				raw_input("\n***** Hit ENTER to continue...\n\n>>>>>")
		if freeradiusinstall == 'no':
			print "***** FreeRADIUS is required by RadiUID. Quitting the installer"
			quit()

	#########################################################################
	###Check if RadiUID is installed and running already
	#########################################################################
	print "\n\n\n\n\n\n****************Checking if RadiUID is already installed...****************\n"
	radiuidinstalled = check_service_installed('radiuid')
	radiuidrunning = check_service_running('radiuid')

	if radiuidinstalled == 'yes' and radiuidrunning == 'yes':
		print "***** Looks like the RadiUID service is already installed and running...skipping the install of RadiUID\n"
		radiuidreinstall = yesorno("Do you want to re-install the RadiUID service?")
		if radiuidreinstall == 'yes':
			installpath = change_setting(installpath, "Enter a path where we should install RadiUID:")
			installpath  = directory_slash_add(installpath)
			print "\n\n****************Re-installing the RadiUID service...****************\n"
			copy_radiuid(installpath)
			install_radiuid(installpath)
			print "\n\n****************Starting the RadiUID service...****************\n"
			restart_service('radiuid')
			checkservice = check_service_running('radiuid')
			if checkservice == 'no':
				print "\n\n***** Uh Oh... Looks like the RadiUID service failed to re-install and start back up."
				print "***** It is possible that something is wrong in the SystemD startup file"
				print "***** Open up and check the RadiUID startup file at /etc/systemd/system/radiuid.service"
				raw_input("Hit ENTER to quit the program...\n")
				quit()
			elif checkservice == 'yes':
				print "\n\n***** Looks like a successful restart..."
				raw_input("Hit ENTER to continue...\n\n>>>>>")
		if radiuidreinstall == 'no':
			print "~~~ OK, leaving it alone..."

	if radiuidinstalled == 'yes' and radiuidrunning == 'yes' and radiuidreinstall == 'no':
		print "\n"
		radiuidrestart = yesorno(
			"Do you want to restart the RadiUID service to effect the changes made to the .conf file?")
		if radiuidrestart == 'yes':
			print "\n\n****************Restarting the RadiUID service to effect changes...****************\n"
			restart_service('radiuid')
			checkservice = check_service_running('radiuid')
			if checkservice == 'no':
				print "\n\n***** Uh Oh... Looks like the RadiUID service failed to restart."
				print "***** It is possible that something is wrong in the SystemD startup file"
				print "***** Open up and check the RadiUID startup file at /etc/systemd/system/radiuid.service"
				raw_input("Hit ENTER to continue...\n\n>>>>>")
			elif checkservice == 'yes':
				print "\n\n***** Looks like a successful restart..."
				raw_input("Hit ENTER to continue...\n\n>>>>>")
		if radiuidrestart == 'no':
			print "~~~ OK, leaving it alone..."

	if radiuidinstalled == 'yes' and radiuidrunning == 'no':
		print "\n"
		radiuidrestart = yesorno("Looks like RadiUID is installed, but not running....want to start it up?")
		if radiuidrestart == 'yes':
			restart_service('radiuid')
			radiuidrunning = check_service_running('radiuid')
			if radiuidrunning == "yes":
				print "***** Very nice....Great Success!!!"
			if radiuidrunning == "no":
				print "***** Looks like the startup failed..."
				radiuidreinstall = yesorno("Do you want to re-install the RadiUID service?")
				if radiuidreinstall == 'yes':
					installpath = change_setting(installpath, "Enter a path where we should install RadiUID:")
					installpath = directory_slash_add(installpath)
					print "\n\n****************Re-installing the RadiUID service...****************\n"
					copy_radiuid(installpath)
					install_radiuid(installpath)
					print "\n\n****************Starting the RadiUID service...****************\n"
					restart_service('radiuid')
		if radiuidrestart == 'no':
			print "~~~ OK, leaving it off..."

	if radiuidinstalled == 'no' and radiuidrunning == 'no':
		print "\n"
		radiuidinstall = yesorno("Looks like RadiUID is not installed. Is it ok to install RadiUID?")
		if radiuidinstall == 'yes':
			installpath = change_setting(installpath, "Enter a path where we shoud install RadiUID:")
			installpath = directory_slash_add(installpath)
			print "\n\n****************Installing the RadiUID service...****************\n"
			copy_radiuid(installpath)
			install_radiuid(installpath)
			print "\n\n****************Starting the RadiUID service...****************\n"
			restart_service('radiuid')
			radiuidrunning = check_service_running('radiuid')
			if radiuidrunning == "yes":
				print "***** RadiUID successfully installed and started up!!!"
			raw_input("Hit ENTER to continue...\n\n>>>>>")
			if radiuidrunning == "no":
				print "***** Something went wrong. Looks like the installation or startup failed... "
				print "***** Please make sure you are installing RadiUID on a support platform"
				raw_input("Hit ENTER to quit the program...\n\n>>>>>")
				quit()

		if radiuidinstall == 'no':
			print "***** The install of RadiUID is required. Quitting the installer"
			quit()

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
	raw_input(">>>>> Hit ENTER to see the tail of the RadiUID log file before you exit the utility\n\n>>>>>")
	print "\n\n############################## LAST 50 LINES FROM " + newlogfile + "##############################"
	print "########################################################################################################"
	os.system("tail -n 50 " + newlogfile)
	print "########################################################################################################"
	print "########################################################################################################"
	raw_input(
		"\n\n\n\n***** Looks like we are all done here...\n>>>>> Hit ENTER to exit the app\n\n>>>>>")
	quit()


####################Installer Runs Here If Switched######################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

#####If Install Mode is not switched on, this part is skipped and program moves on to the primary while loop

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--install", help="Run RadiUID in Installer/Management Mode", action="store_true")
args = parser.parse_args()

if args.install:
	print "\n\n\n"
	header()
	checkfile = file_exists("radiuid.conf")
	if checkfile == 'no':
		print "ERROR: Config file (radiuid.conf) not found. Make sure the radiuid.conf file exists in same directory as radiuid.py"
		quit()
	progress("Running RadiUID in Install/Maintenance Mode:", 3)
	installer()
	quit()


#######################Primary Running Function##########################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################



def main():
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


#####################Start of Main RadiUID Program#######################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + "***********RADIUID PROGRAM INITIAL START. CHECKING FOR CONFIG FILE...***********" + "\n"

##### Check if config file exists. Fail program if it doesn't #####
checkfile = file_exists("radiuid.conf")
if checkfile == 'no':
	print time.strftime(
		"%Y-%m-%d %H:%M:%S") + ":   " + "ERROR: CANNOT FIND RADIUID IN SPECIFIED PATH. QUITTING PROGRAM. RE-RUN INSTALLER" + "\n"
	quit()
if checkfile == 'yes':
	print time.strftime(
		"%Y-%m-%d %H:%M:%S") + ":   " + "***********FOUND CONFIG FILE. CONTINUING STARTUP PROCEDURE...***********" + "\n"
	print time.strftime(
		"%Y-%m-%d %H:%M:%S") + ":   " + "***********READING IN RADIUID LOGFILE INFORMATION. ALL SUBSEQUENT OUTPUT WILL BE LOGGED TO THE LOGFILE***********" + "\n"

##### Open the config file and read in the logfile location information #####

parser = ConfigParser.SafeConfigParser()
parser.read('radiuid.conf')

logfile = parser.get('Paths_and_Files', 'logfile')

##### Initial log entry and help for anybody starting the .py program without first installing it #####

log_writer(
	"***********RADIUID INITIALIZING... IF PROGRAM FAULTS NOW, MAKE SURE SUCCESSFULLY YOU RAN THE INSTALLER ('python radiuid.py -i')***********")

##### Suck in all variables from config file (only run when program is initially started, not during while loop) #####

log_writer(
	"*******************************************CONFIG FILE SETTINGS INITIALIZING...*******************************************")

log_writer("Initialized variable:" "\t" + "logfile" + "\t\t\t\t" + "with value:" + "\t" + logfile)

radiuslogpath = parser.get('Paths_and_Files', 'radiuslogpath')
log_writer("Initialized variable:" "\t" + "radiuslogpath" + "\t\t\t" + "with value:" + "\t" + radiuslogpath)

hostname = parser.get('Palo_Alto_Target', 'hostname')
log_writer("Initialized variable:" "\t" + "hostname" + "\t\t\t" + "with value:" + "\t" + hostname)

panosversion = parser.get('Palo_Alto_Target', 'OS_Version')
log_writer("Initialized variable:" "\t" + "panosversion" + "\t\t\t" + "with value:" + "\t" + panosversion)

panuser = parser.get('Palo_Alto_Target', 'username')
log_writer("Initialized variable:" "\t" + "panuser" + "\t\t\t\t" + "with value:" + "\t" + panuser)

panpassword = parser.get('Palo_Alto_Target', 'password')
log_writer("Initialized variable:" "\t" + "panpassword" + "\t\t\t" + "with value:" + "\t" + panpassword)

extrastuff = parser.get('URL_Stuff', 'extrastuff')
log_writer("Initialized variable:" "\t" + "extrastuff" + "\t\t\t" + "with value:" + "\t" + extrastuff)

ipaddressterm = parser.get('Search_Terms', 'ipaddressterm')
log_writer("Initialized variable:" "\t" + "ipaddressterm" + "\t\t\t" + "with value:" + "\t" + ipaddressterm)

usernameterm = parser.get('Search_Terms', 'usernameterm')
log_writer("Initialized variable:" "\t" + "usernameterm" + "\t\t\t" + "with value:" + "\t" + usernameterm)

delineatorterm = parser.get('Search_Terms', 'delineatorterm')
log_writer("Initialized variable:" "\t" + "delineatorterm" + "\t\t\t" + "with value:" + "\t" + delineatorterm)

userdomain = parser.get('UID_Settings', 'userdomain')
log_writer("Initialized variable:" "\t" + "userdomain" + "\t\t\t" + "with value:" + "\t" + userdomain)

timeout = parser.get('UID_Settings', 'timeout')
log_writer("Initialized variable:" "\t" + "timeout" + "\t\t\t\t" + "with value:" + "\t" + timeout)

##### Explicitly pull PAN key now and store API key in the main namespace #####

log_writer(
	"***********************************CONNECTING TO PALO ALTO FIREWALL TO EXTRACT THE API KEY...***********************************")
log_writer(
	"********************IF PROGRAM FREEZES/FAILS RIGHT NOW, THEN THERE IS LIKELY A COMMUNICATION PROBLEM WITH THE FIREWALL********************")

pankey = pull_api_key(panuser, panpassword)
log_writer("Initialized variable:" "\t" + "pankey" + "\t\t\t\t" + "with value:" + "\t" + pankey)

log_writer(
	"*******************************************CONFIG FILE SETTINGS INITIALIZED*******************************************")

log_writer(
	"***********************************RADIUID SERVER STARTING WITH INITIALIZED VARIABLES...******************************")

#######################Loop Through Main()###############################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################



while __name__ == "__main__":
	main()
	time.sleep(10)


#######################END OF PROGRAM###############################
