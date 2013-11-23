
def cmd_valid(cmd):
	if len(cmd)==1 and (cmd[0]=="LIST" or cmd[0]=="GETLIST" or cmd[0]=="LEAVE"):
		return True
	if len(cmd)==2 and (cmd[0]=="LOGIN") and cmd[1]!="":
		return True
	if len(cmd)==3 and cmd[0]=="UPDATE" and (cmd[1]=="0" or cmd[1]=="1") and cmd[2]!="":
		return True
	return False
	
def cmd_reply(cmd):
	if cmd[0]=="LOGIN" or cmd[0]=="GETLIST" or cmd[0]=="LEAVE":
		return True

	return False
