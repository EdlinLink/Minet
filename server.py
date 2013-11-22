#!/usr/bin/env python
# simple server - Chapter 1

import socket, thread, time
from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid

def is_valid(sheet):
	if sheet.Version=="CS1.0":
		if sheet.Cmd=="LOGIN" and is_off(sheet.Arg):
			return True

def is_off(name):
	global NameList
	if name!="" and (not NameList.has_key(name) or (NameList[name][0]==False)):
		return True

def print_NameList():
	global NameList
	print "[",
	for i in NameList:
		if NameList[i][0]==True:
			print i + ".",
	print "]"

def login_handle(sheet_str, clientsock, clientaddr):

	sheet = sheet_toForm(sheet_str)
	# LOGIN ----------------------------------------
	if sheet.Cmd=="LOGIN":
		print "# recv LOGIN request!"
		if sheet.Arg!="" and is_off(sheet.Arg):
			NameList[sheet.Arg] = [True, clientaddr[0], sheet.Headline["Port"]]
			print "# client [" + sheet.Arg + "] online!"
			status = SHEET()
			status.fill("STATUS", "1")

		else:
			status = SHEET()
			status.fill("STATUS", "0")
			if not is_off(sheet.Arg):
				status.fill_body("@@@ username is online!\n")

		if status.Arg == "1":
			clientsock.send(status.toStr())							#send status
			print "# send STATUS reply! [status=" + status.Arg + "]"

			time.sleep(0.01)
			getlist_handle(clientsock)
			return True, sheet.Arg
		else:
			clientsock.send(status.toStr())							
			print "# send STATUS to clinet! [status=" + status.Arg + "]"
	
	print "# someone LOGIN FAIL(1)."
	return False, ""
	# LOGIN end ====================================

# handle the GETLIST command from client	
def getlist_handle(clientsock):
	print "# recv GETLIST request."
	list_body = listname()
	list = SHEET()
	list.fill("LIST")
	list.fill_body(list_body)
	clientsock.send(list.toStr())
	print "# send LIST reply."
	print "# current LIST: "
	print_NameList()


def handle(sheet_str, username, clientsock):
	global NameList

	allsheet = sheet_str.split("CS1.0")
	sheet_count = len(allsheet)-1

	for sheet_str in allsheet[1:]:
		sheet = sheet_toForm(sheet_str)

		# GETLIST --------------------------------------------------------
		if sheet.Cmd=="GETLIST":
			getlist_handle(clientsock)

		# LEAVE ----------------------------------------------------------
		if sheet.Cmd=="LEAVE":
			print "# recv LEAVE request."

			NameList[username][0] = False
			print "# client [" + sheet.Arg + "] offline,"
			clientsock.send(sheet.toStr())
			print "# send LEAVE reply."

		# LEAVE end ======================================================

		#return False , ""



# return the list of the online users
def listname():
	global NameList
	list_str = ""
	for item in NameList:
		if NameList[item][0] == True:
			list_str = list_str + item + " " + NameList[item][1] + " " + NameList[item][2] + "\n"
	list_str = list_str + "\n"
	return list_str

myhost = "127.0.0.1"
host = ''
port = 51423
NameList = {}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
s.listen(10)

print "Server is running on port %d; press Ctrl-C to terminiate." % port

def main(clientsock, clientaddr):

	#-------------------------- handshake --------------------------------	
	handshake_str = clientsock.recv(1024)			# get handshake
	handshake = handshake_toForm(handshake_str)

	if handshake.Type != "MINET" :
		clientsock.close()
		print "@@@ connection NOT come from Minet!"
	else:
		handshake = HANDSHAKE()
		handshake.Type = "MIRO"
		handshake.Hostname = myhost
		clientsock.send(handshake.toStr())			# send handshake_reply
	#=====================================================================	

	#============================ login ==================================
		try:
			cmd_str = clientsock.recv(1024)			# get login 
			login_tag, username = login_handle(cmd_str, clientsock, clientaddr)
	
			#-------------------- command --------------------------------
			while login_tag and NameList[username][0]:
				cmd_str = clientsock.recv(1024)			# get login 
				handle(cmd_str, username, clientsock)
			#-------------------------------------------------------------
		except:
			print "# someone LOGIN FAIL(2)."
	#=====================================================================
	print "@@@ Finish connection!"
	clientsock.close()


def start():

	all_threads = []
	while 1:
		clientsock, clientaddr = s.accept()
		t = thread.start_new_thread(main, (clientsock, clientaddr,))
		all_threads.append(t)
	s.close()


start()
