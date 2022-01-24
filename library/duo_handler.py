# encoding: utf-8
## #!/usr/bin/python
#
# Copyright: (c) 2020, Luciano Baez <lucianobaez@kyndryl>
#                                   <lucianobaez1@ibm.com>
#                                   <lucianobaez@outlook.com>
#
# Latest version at https://github.kyndryl.net/lucianobaez
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#  This is a module to handle /etc/sudoers file
#
# History
#   -Ver 0.1 : Aug 14 2020
#           - Implement the report option gets the sudo configuration as a dictionary.

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: sudo_handler

author:
    - Luciano Báez (@lucianoabez) on Kyndryl slack and on IBM slack (@lucianoabez1)
'''

EXAMPLES = '''
# Get information
- name: Get the DUO information
  duo_handler:
    state: report

# Force save both files /etc/duo/login_duo.conf and /etc/duo/pam_duo.conf using /etc/duo/login_duo.conf  as source
- name: resave files
  duo_handler:
    state: resave

# Add a group to exclude in DUO
- name: Add group to DUO
  duo_handler:
    group: staff
    state: present

# Remove a group from exclude in DUO
- name: Add group to DUO
  duo_handler:
    group: staff
    state: absent

'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the SUDO module generates
    type: str
    returned: always
'''

import os
import pwd
import grp
import platform
import subprocess
import json
import shutil
import datetime

# Importing all functions from repo lib sudo_handler_lib
from ansible.module_utils.duo_handler_lib import *

#Needed to be usable as Ansible Module
from ansible.module_utils.basic import AnsibleModule


#Module Global Variables 

duo_fact={}


def sudoershandle(options):
    SUDOHANDLERESULT={}
    return SUDOHANDLERESULT
    

def run_module():
    #------------------------------------------------------------------------------------------------------------
    # This are the arguments/parameters that a user can pass to this module
    # the action is the only one that is required

    module_args = dict(
        #action=dict(type='str', required=True),
        state=dict(type='str', default='present'),
        ikey=dict(type='str', required=False),
        skey=dict(type='str', required=False),
        host=dict(type='str', required=False),
        failmode=dict(type='str', required=False),
        gecos_username_pos=dict(type='str', required=False),
        gecos_delim=dict(type='str', required=False),
        https_timeout=dict(type='str', required=False),
        group=dict(type='str', required=False, default=""),

        pushinfo=dict(type='str', required=False),
        gecos_parsed=dict(type='str', required=False),
        
        first=dict(type='bool', required=False, default=False),
        backup=dict(type='bool', required=False, default=False),

        # Non documented option For troubleshoot
        log=dict(type='bool', required=False, default=False)
    )
    


    # Acepted values for "state" 
    #   -report                 = Provides a report without any change
    
    #------------------------------------------------------------------------------------------------------------
    # This is the dictionary to handle the module result
    result = dict(
        changed=False,
        failed=False,
        skipped=False,
        original_message='',
        message=''
    )

    # This is the dictionary to handle the logs
    logdic = dict(
        log=False,
        logfile='/tmp/duo_handler'
    )

    # The AnsibleModule object will be our abstraction working with Ansible this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module supports check mode
    
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Define Vaariables to use 
    duo_process=1
    duo_file=str('/etc/duo/login_duo.conf')
    duo_file2=str('/etc/duo/pam_duo.conf')
    duo_module_log=False
    
    duo_module_state=str('')
    duo_module_ikey=str('')
    duo_module_skey=str('')
    duo_module_host=str('')
    duo_module_failmode='safe'
    duo_module_gecos_username_pos='6'
    duo_module_gecos_delim='/'
    duo_module_https_timeout='10'

    duo_module_pushinfo=''
    duo_module_gecos_parsed=''
        
    duo_module_groups=[]
    duo_module_first= False

    duo_module_backup=False

    #

    # Dectecting arguments
    #try:
    #    sudo_module_action=str(module.params['action'])
    #except KeyError:
    #    sudo_process=0


    # Provide the the requested action as the original Message
    CR="\n"
    result['original_message'] = module.params
    #result['message'] = 'goodbye',
    ModuleExitMessage = ''
    ModuleExitChanged = False
    ModuleExitFailed= False

    # <processing parameters>
    try:
        duo_module_state=str(module.params['state'])
    except KeyError:
        duo_module_state='report'

    if duo_module_state != 'report':
        #Process when state is present or absent

        try:
            duo_module_ikey=str(module.params['ikey']).strip()
        except:
            duo_module_ikey=str('')
        if duo_module_ikey.upper() == "NONE":
            duo_module_ikey=""
        #    
        try:
            duo_module_skey=str(module.params['skey']).strip()
        except:
            duo_module_skey=str('')
        if duo_module_skey.upper() == "NONE":
            duo_module_skey=""
        #
        try:
            duo_module_host=str(module.params['host']).strip()
        except:
            duo_module_host=str('')
        if duo_module_host.upper() == "NONE":
            duo_module_host=""
        #
        try:
            duo_module_failmode=str(module.params['failmode']).strip()
        except:
            duo_module_failmode=str('')
        if duo_module_failmode.upper() == "NONE":
            duo_module_failmode=""
        #
        try:
            duo_module_gecos_username_pos=str(module.params['gecos_username_pos']).strip()
        except:
            duo_module_gecos_username_pos=str('')
        if duo_module_gecos_username_pos.upper() == "NONE":
            duo_module_gecos_username_pos=""
        #
        try:
            duo_module_gecos_delim=str(module.params['gecos_delim']).strip()
        except:
            duo_module_gecos_delim=str('')
        if duo_module_gecos_delim.upper() == "NONE":
            duo_module_gecos_delim=""
        #
        try:
            duo_module_https_timeout=str(module.params['https_timeout']).strip()
        except:
            duo_module_https_timeout=str('')
        if duo_module_https_timeout.upper() == "NONE":
            duo_module_https_timeout=""
        #
        try:
            duo_module_pushinfo=str(module.params['pushinfo']).strip()
        except:
            duo_module_pushinfo=str('')
        if duo_module_pushinfo.upper() == "NONE":
            duo_module_pushinfo=""
        #
        try:
            duo_module_gecos_parsed=str(module.params['gecos_parsed']).strip()
        except:
            duo_module_gecos_parsed=str('')
        if duo_module_gecos_parsed.upper() == "NONE":
            duo_module_gecos_parsed=""
        #
        try:
            duo_module_first=module.params['first']
        except:
            duo_module_first=False
        try:
            duo_module_backup=module.params['backup']
        except:
            duo_module_backup=False

        try:
            auxgroups=module.params['group']
            if len(auxgroups.strip())>0:
                duo_module_groups=auxgroups.split(',')
        except:
            duo_module_groups=[]

        #Detecting the include file (could be with full path or without path, adn will asume that are at /etc/sudoers.d )

        try:
            duo_module_log=module.params['log']       
        except:
            duo_module_log=False

        if duo_module_log==True:
            logdic['log']=duo_module_log
            logdic['logfile']="/var/log/duo_handler_debug"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".log"
        
        if ( os.path.isfile(duo_file) == False):
            duo_process=0
            ModuleExitMessage = ModuleExitMessage + "ERR- DUO file not present." + CR   

        if duo_module_ikey != '' or duo_module_skey != '':
            if duo_module_ikey != '' and duo_module_skey != '':
                duo_process=1
            else:
                duo_process=0
                ModuleExitMessage = ModuleExitMessage + "ERR- To configure key values, 2 values(ikey & skey), must be provided. " + CR   

    # </processing parameters>

    if duo_process==1:
        # Getting sudo fats
        duo_fact=getduo_fact(logdic)
        if duo_fact['installed']==True:
            #Processing the report
            
            if duo_module_state == 'report':
                result['changed']=False
                result['message']=duo_fact
            else:
                if duo_module_state == 'present':
                    #if len(duo_module_groups)>0:
                    #        print(duo_fact)
                    
                    # Process groups
                    if len(duo_module_groups)>0:
                        #print(duo_module_groups)
                        ModuleExitMessage = ModuleExitMessage + "INF- Adding "+str(len(duo_module_groups))+" group(s)" + CR    
                        for grp in duo_module_groups:
                            #print("Adding group: "+grp)
                            if duo_module_first==True:
                                rc=addgroupfirsttoduo(grp,duo_fact,logdic)
                            else:
                                rc=addgrouptoduo(grp,duo_fact,logdic)
                            if rc['rc'] == 0:
                                result['changed'] = True
                            else:
                                #result['changed'] = False
                                if (rc['rc']!=1 and rc['rc']!=3):                          
                                    result['failed'] = True
                            ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR    
                    
                    #if len(duo_module_groups)>0:
                    #        print(duo_fact)
                    
                    #Process keys
                    if duo_module_ikey!='' and duo_module_skey!='':
                        duo_fact['ikey']=duo_module_ikey
                        duo_fact['skey']=duo_module_skey
                        result['changed'] = True
                        Auxmsg="INF- Changing ikey to "+duo_fact['ikey']+" & skey to "+duo_fact['skey']+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 
                    
                    #if len(duo_module_groups)>0:
                    #        print( ">"+duo_fact['ikey']+" - "+duo_fact['skey']+"<"+ CR)
                    #        print(duo_fact)

                    if duo_module_host!='':
                        duo_fact['host']=duo_module_host
                        result['changed'] = True
                        Auxmsg="INF-Changing API host "+duo_module_host+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 

                    if duo_module_failmode!='':
                        # set failmode
                        duo_fact['failmode']=duo_module_failmode
                        result['changed'] = True
                        Auxmsg="INF-Changing failmode "+duo_module_failmode+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 

                    if duo_module_gecos_username_pos!='':
                        # set duo_module_gecos_username_pos
                        duo_fact['gecos_username_pos']=duo_module_gecos_username_pos
                        result['changed'] = True
                        Auxmsg="INF-Changing gecos_username_pos "+str(duo_module_gecos_username_pos)+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 

                    if duo_module_pushinfo!='':
                        # set duo_module_gecos_username_pos
                        duo_fact['pushinfo']=duo_module_pushinfo
                        result['changed'] = True
                        Auxmsg="INF-Changing pushinfo "+str(duo_module_pushinfo)+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 

                    if duo_module_gecos_delim!='':
                        # set duo_module_gecos_delim
                        duo_fact['gecos_delim']=str(duo_module_gecos_delim)
                        result['changed'] = True
                        Auxmsg="INF-Changing gecos_delim "+str(duo_module_gecos_delim)+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 

                    if duo_module_https_timeout!='':
                        # set duo_module_https_timeout
                        duo_fact['https_timeout']=duo_module_https_timeout
                        result['changed'] = True
                        Auxmsg="INF-Changing https_timeout "+str(duo_module_https_timeout)+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 

                    if duo_module_gecos_parsed!='':
                        # set duo_module_https_timeout
                        duo_fact['gecos_parsed']=duo_module_gecos_parsed
                        result['changed'] = True
                        Auxmsg="INF-Changing gecos_parsed "+str(duo_module_gecos_parsed)+". "
                        addtolog(logdic,Auxmsg)
                        ModuleExitMessage = ModuleExitMessage + Auxmsg + CR 

                if duo_module_state == 'absent':
                    if len(duo_module_groups)>0:
                        for grp in duo_module_groups:
                            rc=deletegroupfromduo(grp,duo_fact,logdic)
                            if rc['rc'] == 0:
                                result['changed'] = True
                            else:
                                result['changed'] = False
                                if (rc['rc']!=1 and rc['rc']!=3):                          
                                    result['failed'] = True
                            ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR    
                        
                if duo_module_state == 'resave' or result['changed'] == True:
                    #print(duo_fact)
                    if result['failed'] ==False:                        
                        rc=saveconfigfiles(duo_fact,duo_module_backup,logdic)
                        if rc['rc'] > 0:
                            result['failed'] = True            
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR 

        else:
            #DUO not installed
            result['changed'] = False
            result['failed'] = True
            ModuleExitMessage = ModuleExitMessage + "DUO not installed!" + CR  
        # End of declarative state parsing
        #---------------------------------------------------------------------------------------------------------------------------
    if duo_module_state != 'report':
        result['message'] = ModuleExitMessage
    # Returning the result
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()