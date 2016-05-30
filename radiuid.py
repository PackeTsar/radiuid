#!/usr/bin/python

#####        RadiUID Server v1.1.0         #####
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
import ConfigParser


##########################Main RadiUID Functions#########################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
######################################################################### 


##### Inform RadiUID version here #####
version = "v1.1.0"


##### Writes lines to the log file and prints them to the terminal #####
##### Uses the logfile variable published to the global namespace #####
def log_writer(input):
	try:
		target = open(logfile, 'a')
		target.write(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n")
		print time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + input + "\n"
		target.close()
	except IOError:
		print color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********CANNOT OPEN FILE: " + logfile + " ***********\n", red)
		print color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********PLEASE MAKE SURE YOU RAN THE INSTALLER ('python radiuid.py install')***********\n", red)
		quit()


##### Function to pull API key from firewall to be used for REST HTTP calls #####
##### Used during initialization of the RadiUID main process to generate the API key #####
def pull_api_key(username, password):
	encodedusername = urllib.quote_plus(username)
	encodedpassword = urllib.quote_plus(password)
	url = 'https://' + hostname + '/api/?type=keygen&user=' + encodedusername + '&password=' + encodedpassword
	response = urllib2.urlopen(url).read()
	log_writer("Pulling API key using PAN credentials: " + username + "\\" + password + "\n")
	if 'success' in response:
		log_writer(color(response, green) + "\n")
		stripped1 = response.replace("<response status = 'success'><result><key>", "")
		stripped2 = stripped1.replace("</key></result></response>", "")
		global pankey
		pankey = stripped2
		return pankey
	else:
		log_writer(color('ERROR: Username\\password failed. Please re-enter in config file...' + '\n', red))
		quit()


##### List all files in a directory path and subdirs #####
##### Used to enumerate files in the FreeRADIUS accounting log path #####
def listfiles(path):
	filelist = []
	for root, directories, filenames in os.walk(path):
		for filename in filenames:
			entry = os.path.join(root, filename)
			filelist.append(entry)
			log_writer("Found File: " + entry + "...   Adding to file list")
	if len(filelist) == 0:
		log_writer("No Accounting Logs Found. Nothing to Do.")
		return filelist
	else:
		return filelist


##### Search list of files for a searchterm and uses deliniator term to count instances in file, then returns a dictionary where key=instance and value=line where term was found #####
##### Used to search through FreeRADIUS log files for usernames and IP addresses, then turn them into dictionaries to be sent to the "push" function #####
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
##### Removes unwanted data from the lines with useful IP addresses in them #####
def clean_ips(dictionary):
	newdict = {}
	ipaddress_regex = "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
	for key, value in dictionary.iteritems():
		cleaned = re.findall(ipaddress_regex, value, flags=0)[0]
		newdict[key] = cleaned
	log_writer("IP Address List Cleaned Up!")
	return newdict


##### Clean up user names in dictionary #####
##### Removes unwanted data from the lines with useful usernames in them #####
def clean_names(dictionary):
	newdict = {}
	username_regex = "(\'.*\')"
	for key, value in dictionary.iteritems():
		clean1 = re.findall(username_regex, value, flags=0)[0]
		cleaned = clean1.replace("'", "")
		newdict[key] = cleaned
	log_writer("Username List Cleaned Up!")
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
	log_writer("Dictionary values merged into one dictionary")
	return newdict


##### Delete all files in provided list #####
##### Used to remove the FreeRADIUS log files so the next iteration of RadiUID doesn't pick up redundant information #####
def remove_files(filelist):
	for filename in filelist:
		os.remove(filename)
		log_writer("Removed file: " + filename)


##### Accepts a list of IP addresses (keys) and usernames (vals) in a dictionary and outputs a list of XML formatted entries as a list #####
##### This method outputs a list which is utilized by the xml_assembler_v67 method #####
def xml_formatter_v67(ipanduserdict):
	if panosversion == '7' or panosversion == '6':
		ipaddresses = ipanduserdict.keys()
		xmllist = []
		for ip in ipaddresses:
			entry = '<entry name="%s\%s" ip="%s" timeout="%s">' % (userdomain, ipanduserdict[ip], ip, timeout)
			xmllist.append(entry)
			entry = ''
		return xmllist
	else:
		log_writer(color("PAN-OS version not supported for XML push!", red))
		quit()


##### Accepts a list of XML-formatted IP-to-User mappings and produces a list of complete and encoded URLs which are used to push UID data #####
##### Each URL will contain no more than 100 UID mappings which can all be pushed at the same time by the push_uids method #####
def xml_assembler_v67(ipuserxmllist):
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
		log_writer(color("PAN-OS version not supported for XML push!", red))
		quit()


##### Accepts IP-to-User mappings as a dict in, uses the xml-formatter and xml-assembler to generate a list of URLS, then opens those URLs and logs response codes  #####
def push_uids(ipanduserdict, filelist):
	xml_list = xml_formatter_v67(ipanduserdict)
	urllist = xml_assembler_v67(xml_list)
	log_writer("Pushing the below IP : User mappings via " + str(len(urllist)) + " API calls")
	for entry in ipanduserdict:
		log_writer("IP Address: " + entry + "\t\tUsername: " + ipanduserdict[entry])
	for eachurl in urllist:
		response = urllib2.urlopen(eachurl).read()
		log_writer(response + "\n")
	remove_files(filelist)


#######################RadiUID Installer Functions#######################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
######################################################################### 


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


##### Show progress bar #####
##### The most awesome method in this program. Also the most useless #####
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
##### Used to ask questions and set new config settings in the install/maintenance utility #####
def change_setting(setting, question):
	newsetting = raw_input(color(">>>>> " + question + " [" + setting + "]: ", cyan))
	if newsetting == '':
		print color("~~~ Keeping current setting...", green)
		newsetting = setting
	else:
		print color("~~~ Changed setting to: " + newsetting, yellow)
	return newsetting
""

##### Apply new settings as veriables in the namespace #####
##### Used to write new setting values to namespace to be picked up and used by the write_file method to write to the config file #####
def apply_setting(file_data, settingname, oldsetting, newsetting):
	if oldsetting == newsetting:
		print color("***** No changes to  : " + settingname, green)
		return file_data
	else:
		new_file_data = file_data.replace(settingname + " = " + oldsetting, settingname + " = " + newsetting)
		padlen = 50 - len("***** Changed setting: " + settingname)
		pad = " " * padlen
		print color("***** Changed setting: " + settingname + pad + "|\tfrom: " + oldsetting + "\tto: " + newsetting, yellow)
		return new_file_data


##### Writes the new config data to the config file #####
##### Used at the end of the wizard when new config values have been defined and need to be written to a config file #####
def write_file(filepath, filedata):
	try:
		f = open(filepath, 'w')
		f.write(filedata)
		f.close()
	except IOError:
		print color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********CANNOT OPEN FILE: " + filepath + " ***********\n", red)
		print color(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " +"***********PLEASE MAKE SURE YOU RAN THE INSTALLER ('python radiuid.py install')***********\n", red)
		quit()


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


#### Copy RadiUID system and config files to appropriate paths for installation #####
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
##### Accept 'yes', 'no', 'y', or 'n' in any case #####
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
	print "#####About to append the below client data to the FreeRADIUS client.conf file#####"
	print "##################################################################################"
	for ip in iplist:
		newwrite = "\nclient " + ip + " {\n    secret      = " + dict_edits[
			ip] + "\n    shortname   = Created_By_RadiUID\n }\n"
		f = open(clientconfpath, 'a')
		f.write(newwrite)
		f.close()
		print newwrite
	oktowrite = yesorno("OK to write to client.conf file?")
	if oktowrite == "yes":
		print "###############Writing the above to the FreeRADIUS client.conf file###############"
		print "##################################################################################"
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
			print color("***** Then try to start the FreeRADIUS service by issuing the 'radiuid restart freeradius' command", red)
			raw_input(color("Hit ENTER to continue...\n\n>>>>>", cyan))
		elif checkservice == 'yes':
			print color("\n\n***** Great Success!! Looks like FreeRADIUS restarted and is back up now!", green)
			print color("***** If you need to manually edit the FreeRADIUS config file, it is located at " + clientconfpath, green)
			raw_input(color("\nHit ENTER to continue...\n\n>>>>>", cyan))
	elif oktowrite == "no":
		print "~~~ OK Not writing it"


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


				
				
				
				
				
				
				
				
#######################Installer/Maintenance Utility#####################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

def installer():
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
				print color("***** It is possible that the native package manager is not able to download the install files.", red)
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
			progress('Checking for Successful Startup', 3)
			os.system("systemctl status radiuid")
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
	editradiuidconf = yesorno("Do you want to edit the settings in the RadiUID .conf file (if you just installed or reinstalled RadiUID, then you need to do this)?")
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
		panosversion = parser.get('Palo_Alto_Target', 'panosversion')
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
										'Enter PAN-OS software version on target firewall (only PAN-OS 6 and 7 are currently supported)')
		print "\n"
		newusername = change_setting(username, 'Enter administrative username for Palo Alto firewall')
		print "\n"
		newpassword = change_setting(password,
									'Enter administrative password for Palo Alto firewall (entered text will be shown in the clear)')
		while newpassword.find("%") != -1:
			newpassword = change_setting(password,
									'The "%" sign is not allowed in the password. Please enter a password without it')
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






################Methods used by command interface interpreter############
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################


##### ANSI Colors for use in CLI #####
black = '\033[0m'
red = '\033[91m'
green = '\033[92m'
yellow = '\033[93m'
blue = '\033[94m'
magenta = '\033[95m'
cyan = '\033[96m'
white = '\033[97m'


##### To be used like "print 'this is ' + color('green', green) + ' is it not?'" #####
##### Easy method to write color to a str output then switch back to default black color #####
def color(input, inputcolor):
	result = inputcolor + input + black
	return result


##### Get currently logged in user #####
def currentuser():
	checkdata = commands.getstatusoutput("whoami")[1]
	return checkdata


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


##### Get the current working directory #####
##### Used when radiuid.py is run manually using the 'python radiuid.py <arg>' to get the working directory to help find the config file #####
def get_working_directory():
	listoutput = commands.getstatusoutput("pwd")
	result = listoutput[1]
	result = directory_slash_add(result)
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


##### Simple two-choice logic method to pick a preferred input over another #####
##### Used to decide whether to use the radiuid.conf file in the 'etc' location, or the one in the local working directory #####
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
		return "CHOOSERFAIL"
		quit()


##### Config file finder method with two modes, one to report on its activity, and one to operate silently #####
##### Noisy mode used for verbose logging when running or starting the primary RadiUID program #####
##### Quiet mode used for purposes like the command interface when verbose output is not desired #####
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


##### Pull logfile location from configfile #####
def get_logfile():
	global configfile
	configfile = find_config("quiet")
	parser = ConfigParser.SafeConfigParser()
	parser.read(configfile)
	f = open(configfile, 'r')
	config_file_data = f.read()
	f.close()
	global logfile
	logfile = parser.get('Paths_and_Files', 'logfile')
	return logfile


##### A 'failable' abstraction of the log_writer method which tries to pull logfile location info to write logs and displays a simple warning if it fails #####
##### Used in the command interface interpreter to write command use to the logfile for accounting #####
def cli_log_writer(message, mode):
	configfilelocal = find_config("quiet")
	if configfilelocal == "CHOOSERFAIL":
		if mode == "normal":
			print color("***** WARNING: Could not find RadiUID config file *****", yellow)
	else:
		try:
			logfile = get_logfile()
			target = open(logfile, 'a')
			target.write(time.strftime("%Y-%m-%d %H:%M:%S") + ":   " + message + "\n")
			target.close()
		except IOError:
			if mode == "normal":
				print color("***** WARNING: Could not write CLI accounting info to log file *****", yellow)


##### Create str sentence out of list seperated by spaces and lowercase everything #####
##### Used for recognizing arguments when running RadiUID from the CLI #####
def cat_list(listname):
	result = ""
	counter = 0
	#listlen = len(listname)
	for word in listname:
		result = result + listname[counter].lower() + " "
		counter = counter + 1
	result = result[:len(result) - 1:]
	return result


#################Primary Running Functions and Looper####################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
######################################################################### 


##### Initialize method used to pull all necessary RadiUID information from the config file and dump the data into variables in the global namespace #####
##### This method runs once during the initial startup of the program #####
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
	log_writer(
		"***********INITIAL WRITE TO THE LOG FILE: " + logfile + "...***********")

	log_writer(
		"***********RADIUID INITIALIZING... IF PROGRAM FAULTS NOW, MAKE SURE YOU SUCCESSFULLY RAN THE INSTALLER ('python radiuid.py install')***********")
	
	##### Suck in all variables from config file (only run when program is initially started, not during while loop) #####
	log_writer(
		"***********INITIALIZING VARIABLES FROM CONFIG FILE: " + configfile + "...***********")
	
	log_writer("Initialized variable:" "\t" + "logfile" + "\t\t\t\t" + "with value:" + "\t" + color(logfile, green))
	
	radiuslogpath = parser.get('Paths_and_Files', 'radiuslogpath')
	log_writer("Initialized variable:" "\t" + "radiuslogpath" + "\t\t\t" + "with value:" + "\t" + color(radiuslogpath, green))
	
	hostname = parser.get('Palo_Alto_Target', 'hostname')
	log_writer("Initialized variable:" "\t" + "hostname" + "\t\t\t" + "with value:" + "\t" + color(hostname, green))
	
	panosversion = parser.get('Palo_Alto_Target', 'panosversion')
	log_writer("Initialized variable:" "\t" + "panosversion" + "\t\t\t" + "with value:" + "\t" + color(panosversion, green))
	
	panuser = parser.get('Palo_Alto_Target', 'username')
	log_writer("Initialized variable:" "\t" + "panuser" + "\t\t\t\t" + "with value:" + "\t" + color(panuser, green))
	
	panpassword = parser.get('Palo_Alto_Target', 'password')
	log_writer("Initialized variable:" "\t" + "panpassword" + "\t\t\t" + "with value:" + "\t" + color(panpassword, green))
	
	extrastuff = parser.get('URL_Stuff', 'extrastuff')
	log_writer("Initialized variable:" "\t" + "extrastuff" + "\t\t\t" + "with value:" + "\t" + color(extrastuff, green))
	
	ipaddressterm = parser.get('Search_Terms', 'ipaddressterm')
	log_writer("Initialized variable:" "\t" + "ipaddressterm" + "\t\t\t" + "with value:" + "\t" + color(ipaddressterm, green))
	
	usernameterm = parser.get('Search_Terms', 'usernameterm')
	log_writer("Initialized variable:" "\t" + "usernameterm" + "\t\t\t" + "with value:" + "\t" + color(usernameterm, green))
	
	delineatorterm = parser.get('Search_Terms', 'delineatorterm')
	log_writer("Initialized variable:" "\t" + "delineatorterm" + "\t\t\t" + "with value:" + "\t" + color(delineatorterm, green))
	
	userdomain = parser.get('UID_Settings', 'userdomain')
	log_writer("Initialized variable:" "\t" + "userdomain" + "\t\t\t" + "with value:" + "\t" + color(userdomain, green))
	
	timeout = parser.get('UID_Settings', 'timeout')
	log_writer("Initialized variable:" "\t" + "timeout" + "\t\t\t\t" + "with value:" + "\t" + color(timeout, green))
	
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


##### Primary RadiUID program which is run every 10 seconds #####
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


##### RadiUID looper method which initializes the namespace with config variables and loops the main RadiUID program #####
def radiuid_looper():
	configfile = find_config("noisy")
	initialize()
	while __name__ == "__main__":
		radiuid()
		time.sleep(10)




#######################ARG DECODER MAIN PROGRAM##########################
################ Recognizes arguments from program call #################
############## and runs the appropriate part of the program #############
####### if given inappropriate arg, returns list of supported args#######
#########################################################################
#########################################################################

######################### SET COMMON PATHS FOR CONFIG FILE IN GLOBAL NAMESPACE #############################
etcconfigfile = "/etc/radiuid/radiuid.conf"
localconfigfile = get_working_directory() + "radiuid.conf"


######################### RadiUID Command Interpreter #############################
def main():
	######################### RUN #############################
	if cat_list(sys.argv[1:]) == "run":
		radiuid_looper()
	######################### INSTALL #############################
	elif cat_list(sys.argv[1:]) == "install":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "quiet")
		print "\n\n\n"
		packetsar()
		progress("Running RadiUID in Install/Maintenance Mode:", 3)
		installer()
	######################### SHOW #############################
	elif cat_list(sys.argv[1:]) == "show" or cat_list(sys.argv[1:]) == "show ?":
		print "\n - show log         |     Show the RadiUID log file"
		print " - show run         |     Show the RadiUID config file"
		print " - show config      |     Show the RadiUID config file"
		print " - show clients     |     Show the FreeRADIUS client config file"
		print " - show status      |     Show the RadiUID and FreeRADIUS service statuses"
	elif cat_list(sys.argv[1:]) == "show log":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		logfile = get_logfile()
		configfile = find_config("quiet")
		header = "########################## OUTPUT FROM FILE " + logfile + " ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("more " + logfile)
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	elif cat_list(sys.argv[1:]) == "show run":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		logfile = get_logfile()
		configfile = find_config("quiet")
		header = "########################## OUTPUT FROM FILE " + configfile + " ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("more " + configfile)
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	elif cat_list(sys.argv[1:]) == "show config":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		logfile = get_logfile()
		configfile = find_config("quiet")
		header = "########################## OUTPUT FROM FILE " + configfile + " ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("more " + configfile)
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	elif cat_list(sys.argv[1:]) == "show clients":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		logfile = get_logfile()
		configfile = find_config("quiet")
		header = "########################## OUTPUT FROM FILE /etc/raddb/clients.conf ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("more /etc/raddb/clients.conf")
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	elif cat_list(sys.argv[1:]) == "show status":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
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
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		logfile = get_logfile()
		configfile = find_config("quiet")
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
		logfile = get_logfile()
		configfile = find_config("quiet")
		print color("********************* You are about to clear out the RadiUID log file... (" + logfile + ") ********************", yellow)
		raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
		os.system("rm -f "+ logfile)
		write_file(logfile, "***********Logfile cleared via RadiUID command by " + currentuser() + "***********\n")
		print color("********************* Cleared logfile: " + logfile + " ********************", yellow)
	######################### EDIT #############################
	elif cat_list(sys.argv[1:]) == "edit" or cat_list(sys.argv[1:]) == "edit ?":
		print "\n - edit config      |     Edit the RadiUID config file"
		print " - edit clients     |     Edit list of client IPs for FreeRADIUS\n"
	elif cat_list(sys.argv[1:]) == "edit config":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		logfile = get_logfile()
		configfile = find_config("quiet")
		print color("****************** You are about to edit the RadiUID config file in VI ******************", yellow)
		print color("********************* Confirm that you know how to use the VI editor ********************", yellow)
		raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
		os.system("vi " + configfile)
	elif cat_list(sys.argv[1:]) == "edit clients":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		print color("****************** You are about to edit the FreeRADIUS client file in VI ******************", yellow)
		print color("*********************** Confirm that you know how to use the VI editor ********************", yellow)
		raw_input("Hit CTRL-C to quit. Hit ENTER to continue\n>>>>>")
		os.system("vi /etc/raddb/clients.conf")
	######################### RADIUID SERVICE CONTROL #############################
	elif cat_list(sys.argv[1:]) == "start" or cat_list(sys.argv[1:]) == "start ?":
		print "\n - start radiuid       |     Start the RadiUID system service"
		print " - start freeradius    |     Start the FreeRADIUS system service"
		print " - start all           |     Start the RadiUID and FreeRADIUS system services"
	elif cat_list(sys.argv[1:]) == "stop" or cat_list(sys.argv[1:]) == "stop ?":
		print "\n - stop radiuid        |     Stop the RadiUID system service"
		print " - stop freeradius     |     Stop the FreeRADIUS system service"
		print " - stop all            |     Stop the RadiUID and FreeRADIUS system services"
	elif cat_list(sys.argv[1:]) == "restart" or cat_list(sys.argv[1:]) == "restart ?":
		print "\n - restart radiuid     |     Restart the RadiUID system service"
		print " - restart freeradius  |     Restart the FreeRADIUS system service"
		print " - restart all         |     Restart the RadiUID and FreeRADIUS system services"
	elif cat_list(sys.argv[1:]) == "start radiuid":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		os.system("systemctl start radiuid")
		os.system("systemctl status radiuid")
		checkservice = check_service_running("radiuid")
		if checkservice == "yes":
			print color("\n\n********** RADIUID SUCCESSFULLY STARTED UP! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
	elif cat_list(sys.argv[1:]) == "stop radiuid":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiuid")
		print color("\n\n***** ARE YOU SURE YOU WANT TO STOP IT?", yellow)
		raw_input(color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", cyan))
		os.system("systemctl stop radiuid")
		os.system("systemctl status radiuid")
		print color("\n\n********** RADIUID STOPPED **********\n\n", yellow)
	elif cat_list(sys.argv[1:]) == "restart radiuid":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
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
	######################### FREERADIUS SERVICE CONTROL #############################
	elif cat_list(sys.argv[1:]) == "start freeradius":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		os.system("systemctl start radiusd")
		os.system("systemctl status radiusd")
		checkservice = check_service_running("radiusd")
		if checkservice == "yes":
			print color("\n\n********** FREERADIUS SUCCESSFULLY STARTED UP! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
	elif cat_list(sys.argv[1:]) == "stop freeradius":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiusd")
		print color("\n\n***** ARE YOU SURE YOU WANT TO STOP IT?", yellow)
		raw_input(color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", cyan))
		os.system("systemctl stop radiusd")
		os.system("systemctl status radiusd")
		print color("\n\n********** FREERADIUS STOPPED **********\n\n", yellow)
	elif cat_list(sys.argv[1:]) == "restart freeradius":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiusd")
		print color("\n\n***** ARE YOU SURE YOU WANT TO RESTART IT?", yellow)
		raw_input(color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", cyan))
		os.system("systemctl stop radiusd")
		os.system("systemctl status radiusd")
		print color("\n\n********** FREERADIUS STOPPED **********\n\n", yellow)
		progress("Preparing to Start Up:", 2)
		print "\n\n\n"
		os.system("systemctl start radiusd")
		os.system("systemctl status radiusd")
		checkservice = check_service_running("radiusd")
		if checkservice == "yes":
			print color("\n\n********** FREERADIUS SUCCESSFULLY RESTARTED! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
	######################### COMBINED SERVICE CONTROL #############################
	elif cat_list(sys.argv[1:]) == "start all":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		os.system("systemctl start radiusd")
		os.system("systemctl status radiusd")
		checkservice = check_service_running("radiusd")
		if checkservice == "yes":
			print color("\n\n********** FREERADIUS SUCCESSFULLY STARTED UP! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
		print "\n\n\n"
		os.system("systemctl start radiuid")
		os.system("systemctl status radiuid")
		checkservice = check_service_running("radiuid")
		if checkservice == "yes":
			print color("\n\n********** RADIUID SUCCESSFULLY STARTED UP! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** RADIUID STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
	elif cat_list(sys.argv[1:]) == "stop all":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiuid")
		header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiusd")
		print color("\n\n***** ARE YOU SURE YOU WANT TO ALL SERVICES?", yellow)
		raw_input(color("\n\nHit CTRL-C to quit. Hit ENTER to continue\n>>>>>", cyan))
		os.system("systemctl stop radiuid")
		os.system("systemctl status radiuid")
		print color("\n\n********** RADIUID STOPPED **********\n\n", yellow)
		print "\n\n\n"
		os.system("systemctl stop radiusd")
		os.system("systemctl status radiusd")
		print color("\n\n********** FREERADIUS STOPPED **********\n\n", yellow)
	elif cat_list(sys.argv[1:]) == "restart all":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		header = "########################## CURRENT RADIUID SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiuid")
		header = "########################## CURRENT FREERADIUS SERVICE STATUS ##########################"
		print color(header, magenta)
		print color("#" * len(header), magenta)
		os.system("systemctl status radiusd")
		print color("\n\n***** ARE YOU SURE YOU WANT TO RESTART SERVICES?", yellow)
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
		os.system("systemctl stop radiusd")
		os.system("systemctl status radiusd")
		print color("\n\n********** FREERADIUS STOPPED **********\n\n", yellow)
		progress("Preparing to Start Up:", 2)
		print "\n\n\n"
		os.system("systemctl start radiusd")
		os.system("systemctl status radiusd")
		checkservice = check_service_running("radiusd")
		if checkservice == "yes":
			print color("\n\n********** FREERADIUS SUCCESSFULLY RESTARTED! **********\n\n", green)
		elif checkservice == "no":
			print color("\n\n********** FREERADIUS STARTUP UNSUCCESSFUL. SOMETHING MUST BE WRONG... **********\n\n", red)
	######################### VERSION #############################
	elif cat_list(sys.argv[1:]) == "version":
		cli_log_writer("##### COMMAND '" + cat_list(sys.argv[1:]) + "' ISSUED FROM CLI BY USER '" + currentuser()+ "' #####", "normal")
		header = "########################## CURRENT RADIUID AND FREERADIUS VERSIONS ##########################"
		print color(header, magenta)
		print "------------------------------------------ RADIUID -------------------------------------------"
		print "***** Currently running RadiUID "+ color(version, green) + " *****"
		print "----------------------------------------------------------------------------------------------\n"
		print "----------------------------------------- FREERADIUS -----------------------------------------"
		os.system("radiusd -v | grep ersion")
		print "----------------------------------------------------------------------------------------------\n"
		print color("#" * len(header), magenta)
		print color("#" * len(header), magenta)
	######################### GUIDE #############################
	else:
		print color("\n\n\n########################## Below are the supported RadiUID Commands: ##########################", magenta)
		print color("###############################################################################################\n\n", magenta)
		print "----------------------------------------------------------------------------------------------"
		print " - run                 |     Run the RadiUID main program in shell mode begin pushing User-ID information"
		print "----------------------------------------------------------------------------------------------\n"
		print " - install             |     Run the RadiUID Install/Maintenance Utility"
		print "----------------------------------------------------------------------------------------------\n"
		print " - show log            |     Show the RadiUID log file"
		print " - show run            |     Show the RadiUID config file"
		print " - show config         |     Show the RadiUID config file"
		print " - show clients        |     Show the FreeRADIUS client config file"
		print " - show status         |     Show the RadiUID and FreeRADIUS service statuses"
		print "----------------------------------------------------------------------------------------------\n"
		print " - tail log            |     Watch the RadiUID log file in real time"
		print "----------------------------------------------------------------------------------------------\n"
		print " - clear log           |     Delete the content in the log file"
		print "----------------------------------------------------------------------------------------------\n"
		print " - edit config         |     Edit the RadiUID config file"
		print " - edit clients        |     Edit list of client IPs for FreeRADIUS"
		print "----------------------------------------------------------------------------------------------\n"
		print " - start radiuid       |     Start the RadiUID system service"
		print " - stop radiuid        |     Stop the RadiUID system service"
		print " - restart radiuid     |     Restart the RadiUID system service"
		print "----------------------------------------------------------------------------------------------\n"
		print " - start freeradius    |     Start the FreeRADIUS system service"
		print " - stop freeradius     |     Stop the FreeRADIUS system service"
		print " - restart freeradius  |     Restart the FreeRADIUS system service"
		print "----------------------------------------------------------------------------------------------\n"
		print " - start all           |     Start the RadiUID and FreeRADIUS system services"
		print " - stop all            |     Stop the RadiUID and FreeRADIUS system services"
		print " - restart all         |     Restart the RadiUID and FreeRADIUS system services"
		print "----------------------------------------------------------------------------------------------\n"
		print " - version             |     Show the current version of RadiUID and FreeRADIUS"
		print "----------------------------------------------------------------------------------------------\n\n\n"



if __name__ == "__main__":
	main()

#######################END OF PROGRAM###############################
