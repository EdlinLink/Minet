#########################################################################
# Author:	Edlin (Lin Junhao)											#
# Date:		Nov.25, 2013												#
# Email:	edlinlink@qq.com											#
#########################################################################

from os.path import getsize
from random import randint
import socket


def cmd_valid(cmd):
	if len(cmd)==1 and (cmd[0]=="LIST" or cmd[0]=="GETLIST" or cmd[0]=="LEAVE"):
		return True
	if len(cmd)==2 and (cmd[0]=="LOGIN" or cmd[0]=="BEAT") and cmd[1]!="":
		return True
	if len(cmd)==3:
		if (cmd[0]=="UPDATE" and (cmd[1]=="0" or cmd[1]=="1") and cmd[2]!=""): return True
		elif (cmd[0]=="P2PFILEACCEPT") and (cmd[1]!="" and cmd[2]!=""): return True
		elif ((cmd[0]=="P2PFILE" or cmd[0]=="P2PFILESEND") and cmd[1]!="" and cmd[2]!=""):
			try:
				getsize(cmd[2])
				return True
			except:
				i=0
	if len(cmd)>=2 and cmd[0]=="MESSAGE":
		return True
	if len(cmd)>=3 and (cmd[0]=="P2PMESSAGE" and cmd[1]!="" and cmd[2]!=""):
		return True
	return False
	
def cmd_reply(cmd):
	if cmd[0]=="LOGIN" or cmd[0]=="GETLIST" or cmd[0]=="LEAVE":
		return True

	return False

def get_code():
	code = randint(00000000000000000000000000000000, 99999999999999999999999999999999)
	return str(code)


def find_idle_port():
	s = socket.socket()
	localhost = '127.0.0.1'
	for idleport in range(51000, 60000):
		try:
			s.bind((localhost, int(idleport)))
			s.close()
			return str(idleport)
		except socket.error, e:
			continue;	

def btou(filename):
	tmp = filename.split(" ")
	name = tmp[0]
	for i in tmp[1:]:
		name+=("_"+i)
	return name
