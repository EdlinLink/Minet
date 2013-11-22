#!/usr/bin/env python
# Simple Gopher Client - Chapter 1

import socket, sys, thread, time
from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid, cmd_reply

PROCESSING = True

def update_NameList(list_body):
	global NameList
	NameList = {}
	allline = list_body.split("\n")
	for item in allline:
		if item=="":
			break
		recd = item.split(" ")
		NameList[recd[0]] = (True, recd[1], recd[2])

def print_NameList():
	global NameList
	print "[",	  
	for i in NameList:
		if NameList[i][0]==True:
			print i + ".",
	print "]\n"


def make_sheet(cmd):
	global Username
	sheet = SHEET()
	if cmd[0]=="LOGIN":
		Username = cmd[1]
		sheet.fill(cmd[0], cmd[1])
		sheet.headAdd("Port", "11270")
	if cmd[0]=="GETLIST":
		sheet.fill(cmd[0])
	if cmd[0]=="LEAVE":
		sheet.fill(cmd[0], Username)
		
	return sheet

def login_handle(clientsock):
	global Statue

	sheet_str = clientsock.recv(1024)
	allsheet = sheet_str.split("CS1.0")
	sheet_count = len(allsheet)

	for sheet_str in allsheet[1:]:	# because the sheet[0]=""
		sheet = sheet_toForm(sheet_str)
		
		if sheet.Cmd=="STATUS":
			if sheet.Arg=="1":
				print "# LOGIN SUCCEED!"
				Status["login"] = True
			else:
				print sheet.Body
				Status["login"] = False




def handle(clientsock):
	global Statue, Username, PROCESSING

	while 1:
#		try:
		sheet_str = clientsock.recv(1024)
		allsheet = sheet_str.split("CS1.0")
		sheet_count = len(allsheet)

		for sheet_str in allsheet[1:]:	# because the sheet[0]=""
			sheet = sheet_toForm(sheet_str)
			
			# STATUS ------------------------------------------------
			if sheet.Cmd=="STATUS":
				if sheet.Arg=="1":
					print "# LOGIN SUCCEED!"
					Status["login"] = True
				else:
					print sheet.Body
					Status["login"] = False

			# LIST --------------------------------------------------
			if sheet.Cmd=="LIST":
				update_NameList(sheet.Body)
				print "# current LIST:"
				print_NameList()

			# LEAVE -------------------------------------------------
			if sheet.Cmd=="LEAVE":
				if Username==sheet.Arg:
					Status["login"] = False

		PROCESSING = False
#		except:

port = 51423
host = "127.0.0.1"
Status={}
Status["login"]= False

myport = "11270"
NameList = {}
Username = ""

def main():
	global Username, NameList, PROCESSING
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))

#--------------------------- handshake -----------------------------
	handshake = HANDSHAKE()
	handshake.Type = "MINET"
	handshake.Hostname = host
	s.send(handshake.toStr())						# send handshake
	handshake_str = s.recv(1024)					# get handshake_reply
	handshake = handshake_toForm(handshake_str)
#===================================================================	


	if handshake.Type != "MIRO" or handshake.Hostname != host:
		s.close()
		print "@@@ connection NOT from Miro!"
	else:
		print "# please enter 'LOGIN Username':"

		while 1:
			print "~",
			cmd_input = raw_input()
		
			if cmd_input=="LEAVE":
				break

			cmd = cmd_input.split(" ")

			# try to login ================================================
			if cmd_valid(cmd) and cmd[0]=="LOGIN":
				sheet = make_sheet(cmd)
				s.send(sheet.toStr())

				login_handle(s)

				if Status["login"]:
					t = thread.start_new_thread(handle, (s,))

				while Status["login"]:
					if not PROCESSING:
						print Username+"$",
						cmd_input = raw_input()
						cmd = cmd_input.split(" ")
						if cmd_valid(cmd):
							sheet = make_sheet(cmd)
							PROCESSING = True
							s.send(sheet.toStr())
						else:
							print "# command ERROR!"

					else:
						time.sleep(0.1)

					#if cmd_reply(cmd):
						#reply_str = s.recv(1024)
						#handle(reply_str)

				# end login ---------------------------------
				break

			else:
				print "# command ERROR!"
			# out of login ===============================================
		
		s.close()

#=========================================

main()
