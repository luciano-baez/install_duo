# encoding: utf-8
## #!/usr/bin/python
#
# Copyright: (c) 2020, Luciano Baez <lucianobaez@kyndryl.com>
#                                   <lucianobaez@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#  This is a module to handle /etc/sudoers file
#
# History
#   -Ver 0.1 : Nov 04 2020

import os
import filecmp
import pwd
import grp
import platform
import subprocess
import json
import shutil
import datetime

def logtofile(filename,logline):
    # open a file to append
    f = open(filename, "a")
    f.write(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+' : '+logline)
    f.write("\n")
    f.close()

def addtolog(logdic,line):
    if logdic['log']:
        logtofile(logdic['logfile'],line)

def catfile(filename):
    f = open(filename, "r")
    text = f.read()
    print(text)
    f.close()
def gettimestampstring():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")

def execute(cmdtoexecute,duologdic):
    #executable=" su - db2inst1 -c \""+cmdtoexecute+"\""
    executable=cmdtoexecute
    stdout=""
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    if duologdic['log']==True:
        logtofile(duologdic['logfile'],'Excecute cmd '+cmdtoexecute+' rc:'+str(rc)+' (execute)')
    #print (stdout)
    stdoutstr= str(stdout, "utf-8")
    #(str(hexlify(b"\x13\x37"), "utf-8"))
    return stdoutstr
    #return stdout

def executefull(cmdtoexecute,duologdic):
    executeresult={'stdout':'','stderr':'','rc':''}
    executable=cmdtoexecute
    stdout=""
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    executeresult['stdout']=stdout
    executeresult['stderr']=stderr
    executeresult['rc']=rc
    if duologdic['log']==True:
        #logtofile(duologdic['logfile'],'Excecute out '+stdout+' ')
        #logtofile(duologdic['logfile'],'Excecute err '+stderr+' ')
        logtofile(duologdic['logfile'],'Excecute cmd '+cmdtoexecute+' rc:'+str(rc)+' (executefull')
    return executeresult

def executeas(cmdtoexecute,userexe,duologdic):
    executable=" su - "+userexe.strip()+" -c \""+cmdtoexecute.strip().replace("\"","\\\"")+"\""
    if (userexe.strip() == "root"):
        # if user is "root" will remove the "su -" (swich user)
        executable=cmdtoexecute.strip()
    else:
        try:
            pwd.getpwnam(userexe.strip())
        except KeyError:
            # if user "userexe" doesen't exists will run as root
            executable=cmdtoexecute.strip()
    #executable=cmdtoexecute
    stdout=""
    #print(executable)
    #print(cmdtoexecute.strip())
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    if duologdic['log']==True:
        logtofile(duologdic['logfile'],'Excecute cmd '+cmdtoexecute+' by '+userexe+'  rc:'+str(rc)+' (executeas')
    return stdout

def getuserlist():
    resultlist=[]
    usersfile="/etc/passwd"
    if os.path.isfile(usersfile):
        with open(usersfile,"r") as sourcefh:
            line = sourcefh.readline()
            while line:
                auxline=line.replace('\n', '').strip().split(':')
                firstword=''
                if (len(auxline)>0):
                    firstword=auxline[0]
                if (firstword != ''):
                    resultlist.append(firstword)
                line = sourcefh.readline()
            sourcefh.close
    return resultlist

def getgrouplist():
    resultlist=[]
    usersfile="/etc/group"
    if os.path.isfile(usersfile):
        with open(usersfile,"r") as sourcefh:
            line = sourcefh.readline()
            while line:
                auxline=line.replace('\n', '').strip().split(':')
                firstword=''
                if (len(auxline)>0):
                    firstword=auxline[0]
                if (firstword != ''):
                    resultlist.append(firstword)
                line = sourcefh.readline()
            sourcefh.close
    return resultlist


def getduo_fact(duologdic):
    DUODIC= {'installed':False, 'platform': '','version': '','binpath': '','cfgpath': '','cfgfile': '','ikey': '','skey': '','host': '',
        'pushinfo': '','failmode': '', 'gecos_username_pos': '', 'gecos_delim': '', 'https_timeout': '', 'gecos_parsed': '', 'groups': []}
    DUODIC['platform']=getduoplatform(duologdic)
    RC=getduoinstalled(DUODIC['platform'],duologdic)

    if (RC['rc'] == 0) or (RC['rc'] == 5) or (RC['rc'] == 6):
        DUODIC['installed']=True
        DUODIC['version']=getduoversion(duologdic)
        DUODIC['binpath']="/usr/sbin"
        DUODIC['cfgpath']="/etc/duo"
        DUODIC['cfgfile']="/etc/duo/login_duo.conf"
        DUODIC['ikey']=getduo_cfgstr(DUODIC['cfgfile'],'ikey',duologdic)
        DUODIC['skey']=getduo_cfgstr(DUODIC['cfgfile'],'skey',duologdic)
        DUODIC['host']=getduo_cfgstr(DUODIC['cfgfile'],'host',duologdic)
        DUODIC['pushinfo']=getduo_cfgstr(DUODIC['cfgfile'],'pushinfo',duologdic)
        DUODIC['failmode']=getduo_cfgstr(DUODIC['cfgfile'],'failmode',duologdic)
        DUODIC['gecos_username_pos']=getduo_cfgstr(DUODIC['cfgfile'],'gecos_username_pos',duologdic)
        DUODIC['gecos_delim']=getduo_cfgstr(DUODIC['cfgfile'],'gecos_delim',duologdic)
        DUODIC['https_timeout']=getduo_cfgstr(DUODIC['cfgfile'],'https_timeout',duologdic)
        DUODIC['gecos_parsed']=getduo_cfgstr(DUODIC['cfgfile'],'gecos_parsed',duologdic)
        ALLGROUPSSTR=getduo_cfgstr(DUODIC['cfgfile'],'groups',duologdic)
        DUODIC['groups']=ALLGROUPSSTR.strip().split(',')
    return DUODIC

def getduoinstalled(platform,duologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: Duo installed (rc=0).",
            "ERR: Duo not installed (rc=1).",
            "ERR: Duo installed not configured (rc=2).",
            "ERR: Dir /etc/duo not found (rc=3).",
            "ERR: File /etc/duo/login_duo.conf not found (rc=4).",
            "ERR: File /etc/duo/pam_duo.conf not found (rc=5).",
            "WAR: File /etc/duo/login_duo.conf different from /etc/duo/pam_duo.conf (rc=6)."
            ]
    if os.path.isfile('/usr/sbin/login_duo'):
        if os.path.isdir('/etc/duo'):
            if os.path.isfile('/etc/duo/login_duo.conf'):
                if os.path.isfile('/etc/duo/pam_duo.conf'):
                    if filecmp.cmp('/etc/duo/login_duo.conf','/etc/duo/pam_duo.conf'):
                        resultcode['rc']=0
                    else:
                        # 6 File /etc/duo/login_duo.conf different from /etc/duo/pam_duo.conf
                        resultcode['rc']=6
                else:
                    # 5 File /etc/duo/pam_duo.conf not found
                    resultcode['rc']=5
            else:
                # 4 File /etc/duo/login_duo.conf not found
                resultcode['rc']=4
        else:
            # 3 Dir /etc/duo not found
            resultcode['rc']=3
    else:
        # 1 Duo not installed
        resultcode['rc']=1

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def getduo_cfgstr(duocfgfile,duocfgkey,duologdic):
    cfgstring=str('')
    KEY=str(duocfgkey).strip().upper()
    if os.path.isfile(duocfgfile):
        with open(duocfgfile,"r") as sourcefh:
            line = sourcefh.readline()
            found=False
            while line and (found==False):
                auxline=line.replace('\n', '').strip().split('=')
                firstchar=''
                firstword=''
                seccondword=''
                if (len(auxline)>0):
                    firstword=auxline[0].strip().upper()
                if (len(auxline)>1):
                    seccondword=auxline[1].strip()
                if (firstword != ''):
                    firstchar=firstword[0]
                    if firstchar != '!':
                        # Is not a comment we could process
                        if (KEY == firstword):
                            if len(seccondword.strip())>0:
                                cfgstring=seccondword
                            found=True
                line = sourcefh.readline()
            sourcefh.close
    return cfgstring
    
def getduoplatform(duologdic):
    flavor=execute("uname",duologdic)
    AUX=str(flavor).strip().split("\n")
    platform=AUX[0]
    return platform


def getduoversion(duologdic):
    duoversion=""
    duoverstr=execute("/usr/sbin/login_duo -v",duologdic)
    #print(duoVERSION)
    #AUX=duoVERSION[1].strip().split("\n")
    #print(duoVERSION)
    AUX=str(duoverstr).strip().split("\n")
    FIRSTLINE=""
    if len(AUX)>0:
        FIRSTLINE=AUX[0].strip().split()
    if len(FIRSTLINE)>0:
        duoversion=FIRSTLINE[0]
    if (duoversion == "login_duo") and (len(FIRSTLINE)>1):
        duoversion=FIRSTLINE[1]
    return duoversion

def saveconfigfiles(duofact,backup,duologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    timestamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filecfg1='/etc/duo/login_duo.conf'
    filecfg2='/etc/duo/pam_duo.conf'
    filecfg1bkp=filecfg1+'-'+timestamp+'.bkp'
    filecfg2bkp=filecfg2+'-'+timestamp+'.bkp'
    duotmpfile='/tmp/duo_handler_conf'+'-'+timestamp+'.tmp'
    
    if duofact['installed']==True:
        if backup==True:
            # Perform backups 
            addtolog(duologdic,"Backing up file: "+filecfg1)
            if os.path.isfile(filecfg1):
                shutil.copy2(filecfg1, filecfg1bkp)
                os.chmod(filecfg1bkp, 0o600)
            else:
                resultcode['rc']=3
            addtolog(duologdic,"Backing up file: "+filecfg2)
            if os.path.isfile(filecfg2):
                shutil.copy2(filecfg2, filecfg2bkp)
                os.chmod(filecfg2bkp, 0o600)
            else:
                resultcode['rc']=4

        # Save the file
        if resultcode['rc']==0:
            addtolog(duologdic,"Generating DUO config file")
            # determine DUO version in order to determine cfg format
            AUXVERSION=duofact['version'].strip().split(".")
            VERMAJOR=''
            VERMINOR=''
            if len(AUXVERSION)>0:
                VERMAJOR=AUXVERSION[0]
            if len(AUXVERSION)>1:
                VERMINOR=AUXVERSION[1]
            cfgformat=2
            if (int(VERMAJOR)<=1):
                if (int(VERMINOR)<=10):
                    cfgformat=1
            
            with open(duotmpfile,"w") as duotargetfh:
                duotargetfh.write("; Configuration file created by duo_handler (by lucianobaez@kyndryl.com) for DUO "+duofact['version']+"\n")
                duotargetfh.write("[duo]\n")
                duotargetfh.write("; Duo integration key\n")
                #AUXSTRING=duofact['ikey'].strip()
                duotargetfh.write("ikey = "+str(duofact['ikey'])+"\n")
                duotargetfh.write("; Duo secret key\n")
                duotargetfh.write("skey = "+str(duofact['skey'])+"\n")
                duotargetfh.write("; Duo API host\n")
                duotargetfh.write("host = "+str(duofact['host'])+"\n")
                duotargetfh.write("; Send command for Duo Push authentication"+"\n")
                duotargetfh.write(";pushinfo = yes"+"\n")
                duotargetfh.write("; "+"\n")
                if (cfgformat==1):
                    duotargetfh.write("; OLD version so these features disabled"+"\n")
                    duotargetfh.write(";failmode = "+str(duofact['failmode'])+"\n")
                    duotargetfh.write(";gecos_username_pos="+str(duofact['gecos_username_pos'])+"\n")
                    duotargetfh.write(";gecos_delim="+str(duofact['gecos_delim'])+"\n")
                    duotargetfh.write(";https_timeout = "+str(duofact['https_timeout'])+"\n")
                
                if (cfgformat==2):
                    duotargetfh.write("; New version format "+"\n")
                    duotargetfh.write("failmode = "+str(duofact['failmode'])+"\n")
                    duotargetfh.write("gecos_username_pos="+str(duofact['gecos_username_pos'])+"\n")
                    duotargetfh.write("gecos_delim="+str(duofact['gecos_delim'])+"\n")
                    duotargetfh.write("https_timeout = "+str(duofact['https_timeout'])+"\n")
                duotargetfh.write("; "+"\n")
                if (cfgformat==1):
                    duotargetfh.write("gecos_parsed = "+str(duofact['gecos_parsed'])+"\n")
                if (cfgformat==2):
                    duotargetfh.write(";gecos_parsed = yes"+"\n")
                duotargetfh.write("; "+"\n")

                duotargetfh.write("; gecos_parsed = "+str(duofact['gecos_parsed'])+"\n")
                GROUPLINE=""
                for grp in duofact['groups']:
                    if grp != "":
                        if GROUPLINE=="":
                            GROUPLINE=grp
                        else:
                            GROUPLINE=GROUPLINE+","+grp
                duotargetfh.write("groups = "+GROUPLINE+"\n")
                duotargetfh.close
            addtolog(duologdic,"Saving DUO config file: "+filecfg1)
            shutil.copy2(duotmpfile,filecfg1)
            os.chmod(filecfg1, 0o600)
            addtolog(duologdic,"Saving DUO config file: "+filecfg2)
            shutil.copy2(duotmpfile,filecfg2)
            os.chmod(filecfg2, 0o600)
            os.remove(duotmpfile)

    else:
        # No tinstalled or installed wiht errors
        resultcode['rc']=1

    rcstdout=["INF: Config files generated succesfully (rc=0).",
            "ERR: Duo No tinstalled or installed wiht errors (rc=1).",
            "ERR: Config files generation error (rc=2).",
            "ERR: Duo "+filecfg1+" error (rc=3).",
            "ERR: Duo "+filecfg2+" error (rc=4)."
            ]

    resultcode['stdout']=rcstdout[resultcode['rc']]
    addtolog(duologdic,resultcode['stdout'])
    return resultcode

def getgroupcfglist(duofact,duologdic):
    grpresultlist=[]
    grplist=[]
    grplist=duofact['groups'].copy()
    firstchar=""

    while grplist:
        grp=grplist.pop()
        grouptoadd=grp.strip()
        firstchar=""
        if len(grouptoadd)>0:
            firstchar=grouptoadd[0]
        if firstchar == "!":
            grouptoadd=grouptoadd[1:(len(grouptoadd))]
        grpresultlist.append(grouptoadd)
        
    return grpresultlist

def addgrouptoduoat(position,group,duofact,duologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    grouptoadd=group.strip()
    groupupper=group.upper().strip() 
    firstchar=""
    if len(grouptoadd)>0:
        firstchar=grouptoadd[0]
    if firstchar == "!":
        grouptoadd=grouptoadd[1:(len(grouptoadd))]

    addtolog(duologdic,"Adding group "+group+" at "+str(position))
    rcstdout=["INF: Group "+grouptoadd+"("+group+") added succesfully (rc=0).",
            "WAR: Group "+grouptoadd+"("+group+") already there (rc=1).",
            "ERR: Group "+grouptoadd+"("+group+") doesn't exists on server(rc=2).",
            "WAR: Group "+grouptoadd+"("+group+") already on config (rc=3)."
            ]
    grpfound=0
    grplist=[]
    grplist=duofact['groups'].copy()
    resultcode['rc']=0
    
    #check if group exists or is a wildcard
    if (grouptoadd in getgrouplist()) or grouptoadd=="*" or grouptoadd=="!*":

        if (grouptoadd in  duofact['groups']) or (grouptoadd in getgroupcfglist(duofact,duologdic) ):
            # Group is already in the config
            resultcode['rc']=3
        else:
            while (grplist and grpfound==0):
                grp=grplist.pop()
                grpupper=grp.upper().strip()
                if groupupper==grpupper:
                    grpfound=1
                    # Group is already in the list
                    resultcode['rc']=1
            if grpfound==0:
                #duofact['groups'].append(group)
                duofact['groups'].insert(position,group)
    else:
        resultcode['rc']=2
    resultcode['stdout']=rcstdout[resultcode['rc']]
    addtolog(duologdic,resultcode['stdout'])
    return resultcode

def addgrouptoduo(group,duofact,duologdic):
    resultcode={}
    groupcount=len(duofact['groups'])
    addtolog(duologdic,"Adding group at the end of the list")
    resultcode=addgrouptoduoat(groupcount,group,duofact,duologdic)
    return resultcode

def addgroupfirsttoduo(group,duofact,duologdic):
    resultcode={}
    addtolog(duologdic,"Adding group at the begining of the list")
    resultcode=addgrouptoduoat(0,group,duofact,duologdic)
    return resultcode

def deletegroupfromduo(group,duofact,duologdic):
    grouptodelete=group.strip()
    firstchar=""
    if len(grouptodelete)>0:
        firstchar=grouptodelete[0]
    if firstchar == "!":
        grouptodelete=grouptodelete[1:(len(grouptodelete))]

    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: Group "+grouptodelete+"("+group+") deleted succesfully (rc=0).",
            "ERR: Group "+grouptodelete+"("+group+") isn't there (rc=1)."
            ]
    groupupper=group.upper()
    grpfound=0
    grplist=[]
    grplist=duofact['groups'].copy()
    resultcode['rc']=1
    poslist=-1
    while (grplist and grpfound==0):
        poslist=poslist+1
        grp=grplist.pop(0)
        grpupper=grp.upper().strip()
        grpupperonlygrp=grpupper
        if len(grpupperonlygrp)>0:
            if (grpupperonlygrp[0]=="!"):
                grpupperonlygrp=grpupperonlygrp[1:(len(grpupperonlygrp))]
        
        if (groupupper==grpupper or groupupper==grpupperonlygrp):
            grpfound=1
            resultcode['rc']=0

    if grpfound==1:
        duofact['groups'].pop(poslist)

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode
