#!/usr/bin/env python
#########################################################################
# Author:   Edlin (Lin Junhao)                                          #
# Date:     Nov.25, 2013                                                #
# Email:    edlinlink@qq.com                                            #   
#########################################################################

import socket, thread, time
from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid

myhost = "127.0.0.1"
host = ''
port = 51423
NameList = {}
AllSocket = {}
cur_time = time.time()
BEAT_TIME = 10
EPSILON = 2


def start():

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((host, port))
	s.listen(10)

	t_beat = thread.start_new_thread(check_beat, ())
	while 1:
		clientsock, clientaddr = s.accept()
		t = thread.start_new_thread(main, (clientsock, clientaddr,))
	s.close()


def check_beat():

	global NameList
	cur_time = time.time()

	while 1:
		if time.time() - cur_time > BEAT_TIME:
			cur_time = time.time()

			for client in NameList:
				if NameList[client][0]:
					if time.time() - NameList[client][3] > BEAT_TIME + EPSILON:
						NameList[client][0] = False
						update_handle(client, "0")
						del AllSocket[client]

		else:
			time.sleep(1)


def main(clientsock, clientaddr):

	#-------------------------- handshake --------------------------------	
	handshake_str = clientsock.recv(1024)			# get handshake
	print "[60]",handshake_str
	handshake = handshake_toForm(handshake_str)

	if handshake.Type != "MINET" :
		clientsock.close()
		print "@@@ connection NOT come from Minet!"
	else:
		handshake = HANDSHAKE()
		handshake.Type = "MIRO"
		handshake.Hostname = myhost
		clientsock.send(handshake.toStr())			# send handshake_reply

	#============================ login ==================================
#		try:
		login_tag = False
		while 1:
			cmd_str = clientsock.recv(1024)			# get login 
			login_tag, username = login_handle(cmd_str, clientsock, clientaddr)
			if login_tag: break

		#-------------------- command --------------------------------
		while NameList[username][0]:
			cmd_str = clientsock.recv(1024)			# get login 
			if not cmd_str: break
			handle(cmd_str, username, clientsock)
		#-------------------------------------------------------------
#		except:
		if login_tag:
			print "# normal EXIT."
		else:
			print "# someone LOGIN FAIL(2)."
	#=====================================================================
	print "@@@ Finish connection!"
	clientsock.close()


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
	global AllSocket
	sheet = sheet_toForm(sheet_str)
	# LOGIN ----------------------------------------
	if sheet.Cmd=="LOGIN":
		print "# recv LOGIN request."
		if sheet.Arg!="" and is_off(sheet.Arg):
			NameList[sheet.Arg] = [True, clientaddr[0], sheet.Headline["Port"], time.time()]
			print "# ONLINE. [" + sheet.Arg + "]"
			status = SHEET()
			status.fill("STATUS", "1")

		else:
			status = SHEET()
			status.fill("STATUS", "0")
			if not is_off(sheet.Arg):
				status.fill_body("@@@ username is online!\n")
			
		status.headAdd("Content-Length", str(len(status.Body)))
		if status.Arg == "1":
			clientsock.send(status.toStr())							#send status
			print "# send STATUS reply. [status=" + status.Arg + "]"

			time.sleep(0.01)
			getlist_handle(clientsock)
			update_handle(sheet.Arg, "1")
			AllSocket[sheet.Arg] = clientsock
			return True, sheet.Arg
		else:
			clientsock.send(status.toStr())							
			print "# send STATUS reply. [status=" + status.Arg + "]"
	
	print "# someone LOGIN FAIL(1)."
	return False, ""
	# LOGIN end ====================================

# the definition of UPDATE is not clear
def update_handle(username, status):
	
	global NameList, AllSocket
	
	sheet = SHEET()
	sheet.fill("UPDATE", username, status)

	for name in AllSocket:
		if NameList.has_key(name) and NameList[name][0] == True:
			s = AllSocket[name]
			try:
				s.send(sheet.toStr())
			except:
				continue
	
	print "# send UPDATE to everyone. [" + username +"="+ status + "]"

# handle the GETLIST command from client	
def getlist_handle(clientsock):
	print "# recv GETLIST request."
	list_body = listname()
	list = SHEET()
	list.fill("LIST")
	list.fill_body(list_body)
	list.headAdd("Content-Length", str(len(list.Body)))
	clientsock.send(list.toStr())
	print "# send LIST reply."
	print "# current LIST: "
	print_NameList()


def message_handle(clientsock, username, content_str):
	
	global NameList, AllSocket
	
	sheet = SHEET()
	sheet.fill("CSMESSAGE", username)
	sheet.fill_body(content_str)

	for name in AllSocket:
		if NameList.has_key(name) and NameList[name][0] == True:
			s = AllSocket[name]
			s.send(sheet.toStr())

	print "# send CSMESSAGE to everyone."	

def beat_handle(username):
	global NameList
	NameList[username][3] = time.time()
	

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
			print "# OFFLINE. [" + sheet.Arg + "]"
			clientsock.send(sheet.toStr())
			print "# send LEAVE reply."

			update_handle(username, "0")
			del AllSocket[username]

		# MESSAGE --------------------------------------------------------
		if sheet.Cmd=="MESSAGE":
			print "# recv MESSAGE request."
			print "# MESSAGE: '" + sheet.Body + "'"
			message_handle(clientsock, sheet.Arg, sheet.Body)

		# BEAT -----------------------------------------------------------
		if sheet.Cmd=="BEAT":
			print "# recv BEAT request. [" + username + "]"
			beat_handle(username)
			print "[233]", NameList



# return the list of the online users
def listname():
	global NameList
	list_str = ""
	for item in NameList:
		if NameList[item][0] == True:
			list_str = list_str + item + " " + NameList[item][1] + " " + NameList[item][2] + "\n"
	list_str = list_str + "\n"
	return list_str



print "Server is running on port %d; press Ctrl-C to terminiate." % port


start()
