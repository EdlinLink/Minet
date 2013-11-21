#!/usr/bin/env python
# simple server - Chapter 1

import socket, threading
from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid

def is_valid(sheet):
	if sheet.Version=="CS1.0":
		if sheet.Cmd=="LOGIN" and is_off(sheet.Arg):
			return True

def is_off(name):
	global NameList
	if name!="" and (not NameList.has_key(name) or (NameList[name]==False)):
		return True


def handle(sheet_str):
	global NameList, clientaddr, CONNECTION

	allsheet = sheet_str.split("CS1.0")
	sheet_count = len(allsheet)-1

	for sheet_str in allsheet[1:]:
		sheet = sheet_toForm(sheet_str)
		# LOGIN ----------------------------------------
		if sheet.Cmd=="LOGIN":
			print "# recv LOGIN request!"
			if sheet.Arg!="" and is_off(sheet.Arg):
				NameList[sheet.Arg] = (True, clientaddr[0], sheet.Headline["Port"])
				print "# client [" + sheet.Arg + "] online!"
				status = SHEET()
				status.fill("STATUS", "1")

			else:
				status = SHEET()
				status.fill("STATUS", "0")
				if not is_off(cmd.Arg):
					status.fill_body("@@@ user is online!")

			if status.Arg == "1":
				list_body = listname()
				list = SHEET()
				list.fill("LIST")
				list.fill_body(list_body)
				clientsock.send(status.toStr()+list.toStr())			#send status
				print "# send STATUS reply! [status=" + status.Arg + "]"
				print "# send LIST reply!"
				print "# current LIST: "
				print NameList.keys()
			else:
				clientsock.send(status.toStr())							
				print "# send STATUS to clinet! [status=" + status.Arg + "]"
		# LOGIN end ====================================
		
		# GETLIST --------------------------------------------------------
		if sheet.Cmd=="GETLIST":
			print "# recv GETLIST request."
			list_body = listname()
			list = SHEET()
			list.fill("LIST")
			list.fill_body(list_body)
			clientsock.send(list.toStr())
			print "# send LIST reply."
			print "# current LIST: "
			print NameList.keys()
		# GETLIST end ====================================================

		# LEAVE ----------------------------------------------------------
		if sheet.Cmd=="LEAVE":
			print "# recv LEAVE request."
			del NameList[sheet.Arg]
			print "# client [" + sheet.Arg + "] offline,"
			clientsock.send(sheet.toStr())
			CONNECTION = False
			print "# send LEAVE reply."

		# LEAVE end ======================================================



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
CONNECTION = False

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
s.listen(1)

print "Server is running on port %d; press Ctrl-C to terminiate." % port


while 1:
	clientsock, clientaddr = s.accept()
	CONNECTION = True
	
	#-------------------------- handshake --------------------------------	
	handshake_str = clientsock.recv(1024)			# get handshake
	handshake = handshake_toForm(handshake_str)

	if handshake.Type != "MINET" or handshake.Hostname != myhost:
		clientsock.close()
		print "@@@ connection NOT come from Minet!"
	else:
		handshake = HANDSHAKE()
		handshake.Type = "MIRO"
		handshake.Hostname = myhost
		clientsock.send(handshake.toStr())			# send handshake_reply
	#=====================================================================	

	
		while 1:
			cmd_str = clientsock.recv(1024)			# get login 
			handle(cmd_str)

			if not CONNECTION:
				break

	print "@@@ Finish connection!"
	clientsock.close()
