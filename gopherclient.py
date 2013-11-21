#!/usr/bin/env python
# Simple Gopher Client - Chapter 1

import socket, sys
from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid, cmd_reply

def update_NameList(list_body):
	global NameList
	NameList = {}
	allline = list_body.split("\n")
	for item in allline:
		if item=="":
			break
		recd = item.split(" ")
		NameList[recd[0]] = (True, recd[1], recd[2])

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

def handle(sheet_str, status):
	global Username

	allsheet = sheet_str.split("CS1.0")
	sheet_count = len(allsheet)

	for sheet_str in allsheet[1:]:	# because the sheet[0]=""
		sheet = sheet_toForm(sheet_str)
		if sheet.Cmd=="STATUS":
			if sheet.Arg=="1":
				print "@@@ Login Successful!"
				status["login"] = True
			else:
				print sheet.Body
				status["login"] = False
		if sheet.Cmd=="LIST":
			update_NameList(sheet.Body)
		if sheet.Cmd=="LEAVE":
			if Username==sheet.Arg:
				status["login"] = False
		
	return status

port = 51423
host = "127.0.0.1"
Status={}
Status["login"]= False

myport = "11270"
NameList = {}
Username = ""



s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

#--------------------------- handshake ------------------------------
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
		print "$",
		cmd_input = raw_input()
		#cmd_input = "LOGIN Client02"
		cmd = cmd_input.split(" ")
		if cmd_valid(cmd):
			sheet = make_sheet(cmd)
			s.send(sheet.toStr())

			if cmd_reply(cmd):
				reply_str = s.recv(1024)
				Status = handle(reply_str, Status)

			if Status["login"]==False:
				print "# leave program."
				break

		else:
			print "@@@ command ERROR!"

	s.close()
