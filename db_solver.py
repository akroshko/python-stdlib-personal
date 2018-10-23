#!/usr/local/bin/sage -python
# -*- coding: iso-8859-15 -*-
"""."""
# DO NOT EDIT DIRECTLY IF NOT IN python-stdlib-personal, THIS FILE IS ORIGINALLY FROM https://github.com/akroshko/python-stdlib-personal

# Copyright (C) 2018, Andrew Kroshko, all rights reserved.
#
# Author: Andrew Kroshko
# Maintainer: Andrew Kroshko <akroshko.public+devel@gmail.com>
# Created: Thu Aug 09, 2018
# Version: 20181022
# URL: https://github.com/akroshko/python-stdlib-personal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

# python standard libraries
import os,sys
# TODO: this stuff needs to be put somewhere else, add arguments for this
# if os.environ['PYTHODE_ROOT'] not in sys.path: sys.path.append(os.environ['PYTHODE_ROOT'])
from pymath_common import *
sys.path.append(sys.argv[1])
pymath_default_imports(globals(),locals())
exec('from ' + sys.argv[2] + ' import *')

import Queue

from defaults import *
try:
    from defaults_local import *
except ImportError:
    pass

TMPPATH=os.getenv('PYMATHDBTMP')

# pythode imports
# TODO: replace with something programatic

# from experiment_common import *

# TODO: add a --curent-host-only option
if '--serial' in sys.argv:
    PROCESSES=1
else:
    PROCESSES=4
# MAXTASKSPERCHILD=None
MAXTASKSPERCHILD=512

THEHOSTNAME=socket.gethostname()

# XXXX: set this extremely large, if there are wierd problems, delete this
sys.setcheckinterval(10000)

def timestamp_now():
    ts = TIME_TIME()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y%m%dT%H%M%S')

if __name__ == '__main__':
    # TODO: add an else with help message and exit
    if len(sys.argv) > 3:
        # TODO: do a bit nicer
        LOGDIR=os.path.expanduser(TMPPATH+'/db_solver_capture_output')
        if not os.path.exists(LOGDIR):
            os_makedirs(LOGDIR)
        SPECIFIC_LOGDIR=os.path.join(LOGDIR,'db_solver_'+timestamp_now()+'_'+sys.argv[3])
        if not os.path.exists(SPECIFIC_LOGDIR):
            os_makedirs(SPECIFIC_LOGDIR)
    else:
        # TODO: don't exit with 1.... in order to make things easy to parse
        sys.exit(1)

def db_solver_worker(q,solve_number,selected_solver,incoming_properties_dict,redirect_stdout_path=None):
    # DBSOLVERTIMESTAMP should clear out as soon as things are reset
    # TODO: add milliseconds or microseconds to timestamp
    # TODO: do not check verbose flag every time
    worker_time=TIME_TIME()
    verbose_flag='--verbose' in sys.argv
    if redirect_stdout_path:
        stdout_old=sys.stdout
        if verbose_flag:
            # I like to remove buffering during verbose so i can catch the last possible thing if something is locked up over ssh
            fh=open(os.path.join(redirect_stdout_path,str(os.getpid())+'.out'),"a", buffering=0)
        else:
            # https://stackoverflow.com/questions/6735917/redirecting-stdout-to-nothing-in-python
            fh=open(os.devnull,"a")
        sys.stdout = fh
    try:
        if not selected_solver[0][0].startswith('<<') or not selected_solver[0][0].endswith('>>'):
            raise RuntimeError("solver_object string not valid!!!")
        if not selected_solver[0][1].startswith('<<') or not selected_solver[0][1].endswith('>>'):
            raise RuntimeError("method_properties string not valid!!!")
        if not selected_solver[0][2].startswith('<<') or not selected_solver[0][2].endswith('>>'):
            raise RuntimeError("ode_properties string not valid!!!")
        # pprint(globals())
        solver_object              = globals()[selected_solver[0][0].strip('<>')]
        method_properties          = globals()[selected_solver[0][1].strip('<>')]
        ode_properties             = globals()[selected_solver[0][2].strip('<>')]
        incoming_properties_keys   = selected_solver[0][3]
        outgoing_properties_keys   = selected_solver[0][4]
        if verbose_flag:
            print "--------------------"
            pprint(ode_properties)
            pprint(method_properties)
            pprint(incoming_properties_dict)
        outgoing_properties = solver_object(method_default_properties=method_properties,
                                            ode_default_properties=ode_properties,
                                            incoming_properties=incoming_properties_dict).run(globals())
        # TODO: need a loop to handle errors
        # outgoing_properties_dict={k:outgoing_properties[k] for k in outgoing_properties_keys}
        new_dict={}
        for k in outgoing_properties_keys:
            if outgoing_properties.has_key(k):
                new_dict[k]=outgoing_properties[k]
            else:
                new_dict[k]=None
        outgoing_properties_dict=new_dict
        # TODO: make sure nothing bad goes into the queue
        if verbose_flag:
            pprint(outgoing_properties_dict)
        # throw outgoing into the queue, block until there is space
        # TODO: wish I was not blocking here, or I knew time spent blocking
        outgoing_properties_dict['worker time']=TIME_TIME()-worker_time
        q.put((solve_number,outgoing_properties_dict),block=True)
    except Exception,e:
        # TODO: to stderr and/or log
        # TODO: optionally send poison pill back to kill things
        print str(e)
        # TODO: does this go to appropriate place?  print differentialy
        traceback.print_exc()
        # send email/text/warning on a secondary channel
        # TODO: replace, make better
        # send_error_happened()
        # os.system('pkill -f db_solver')
    if redirect_stdout_path:
        if verbose_flag:
            sys.stdout.flush()
        sys.stdout.close()
        sys.stdout=stdout_old

def db_more_work(batch_table,CURSOR):
    if PROCESSES == 1:
        # ignore all hostname designations if only one process
        selected_batch_string="SELECT table_name,solve_number FROM " + batch_table + " WHERE done=FALSE;"
        CURSOR.execute(selected_batch_string)
        selected=CURSOR.fetchall()
    else:
        # is there work for this hostname
        selected_batch_string="SELECT table_name,solve_number FROM " + batch_table + " WHERE hostname='" + THEHOSTNAME + "' AND done=FALSE;"
        CURSOR.execute(selected_batch_string)
        selected=CURSOR.fetchall()
        if selected == []:
            # check if there is unassigned work
            selected_unassigned_string="SELECT table_name,solve_number FROM " + batch_table + " WHERE hostname IS NULL AND done=FALSE;"
            CURSOR.execute(selected_unassigned_string)
            unassigned=CURSOR.fetchall()
            if unassigned != []:
                # TODO: I'd like to get this into one select that does everything
                # keep waiting 5-10s until some work is assigned or no more work is available
                while selected == [] and unassigned != []:
                    time.sleep(WORKWAIT)
                    # selected unassigned and hostname stuff together distinguish here rather than doing 2 selects
                    CURSOR.execute(selected_batch_string)
                    selected=CURSOR.fetchall()
                    if selected == []:
                        CURSOR.execute(selected_unassigned_string)
                        unassigned=CURSOR.fetchall()
                    else:
                        unassigned == None
                if selected == [] and unassigned == []:
                    return False
            else:
                # no unassigned work and no work for me, return false
                return False
    # return true if we make it here
    return (selected != [])

# POOL must be before main but after workers
if __name__ == '__main__':
    if len(sys.argv) > 3:
        POOL = multiprocessing.Pool(processes=PROCESSES,maxtasksperchild=MAXTASKSPERCHILD)

# TODO: try and cut down on amount of data structures
# TODO: ???
def main(argv):
    batch_table=argv[3]
    global POOL
    global SPECIFIC_LOGDIR
    # connect to the database
    CONNECTION,CURSOR=open_database(None,None)
    # create the Queue
    m = multiprocessing.Manager()
    q = m.Queue()
    # if only one process, ignore hostname
    # find next batch of work, this gets work if possible
    solve_number_list=[]
    limitpersegement_str=str(LIMITPERSEGMENT)
    while db_more_work(batch_table,CURSOR) or solve_number_list != []:
        selected_solver_dict={}
        if PROCESSES == 1:
            selected_batch_string="SELECT table_name,solve_number FROM " + batch_table + " WHERE done=FALSE LIMIT " + limitpersegement_str + ";"
        else:
            selected_batch_string="SELECT table_name,solve_number FROM " + batch_table + " WHERE hostname='" + THEHOSTNAME + "' AND done=FALSE LIMIT " + limitpersegement_str + ";"
        CURSOR.execute(selected_batch_string)
        selected=CURSOR.fetchall()
        CONNECTION.commit()
        # build the select strings first
        print "==== "  + THEHOSTNAME + ": Building select strings and incoming properties ===="
        sys.stdout.flush()
        ##########
        dbtable_dict={}
        # XXXX: this part was one of the biggest bottlenecks for large numbers of easy problems
        # indexing by solve_number solves this issue for now, otherwise, it scales quadratically
        # or much worse once the number of problems climbed above 100000
        selectstring_list=[]
        for dbtable,solve_number in selected:
            dbtable_dict[solve_number]=dbtable
            # TODO: do these selects seperately
            # TODO: trim selected_solver to ensure solve_number is not used
            solve_number_str=str(solve_number)
            selectstring = "SELECT solver_object,method_properties,ode_properties,incoming_properties_keys,outgoing_properties_keys FROM " + dbtable + " WHERE solve_number=" + solve_number_str + ';'
            CURSOR.execute(selectstring)
            selected_solver=CURSOR.fetchall()
            # print selectstring
            # print selected_solver
            # select the standard things
            # TODO: looop here
            incoming_properties_keys   = selected_solver[0][3]
            # select incoming
            # TODO: only do this once....
            incoming_properties_keys_quoted = ['"' + k + '"' for k in incoming_properties_keys]
            selecting_incoming_string="SELECT " + ','.join(incoming_properties_keys_quoted) + " FROM " + dbtable +  " WHERE solve_number=" + solve_number_str + ";"
            CURSOR.execute(selecting_incoming_string)
            incoming_properties_values=CURSOR.fetchall()[0]
            incoming_properties_dict=dict(zip(incoming_properties_keys,incoming_properties_values))
            selected_solver_dict[solve_number]=(selected_solver,incoming_properties_dict)
        CONNECTION.commit()
        print "==== " + THEHOSTNAME + ": Starting solution =========="
        sys.stdout.flush()
        for solve_number in selected_solver_dict:
            if solve_number in solve_number_list:
                continue
            if PROCESSES==1:
                POOL.apply_async(db_solver_worker,(q,solve_number,selected_solver_dict[solve_number][0],selected_solver_dict[solve_number][1]))
            else:
                #
                POOL.apply_async(db_solver_worker,(q,solve_number,selected_solver_dict[solve_number][0],selected_solver_dict[solve_number][1],SPECIFIC_LOGDIR))
            solve_number_list.append(solve_number)
        ##########
        print "==== "  + THEHOSTNAME + ": Processing solutions ===="
        # TODO: add some text to explain this
        print len(solve_number_list)
        sys.stdout.flush()
        update_strings=[]
        # TODO: this is many statements pasted as one right now, could be made faster into fewer statements
        # TODO: best way will be bulk update using temp table for each dbtable from https://dba.stackexchange.com/questions/41059/optimizing-bulk-update-performance-in-postgresql
        # TODO: http://tapoueh.org/blog/2013/03/15-batch-update.html
        while solve_number_list != []:
            # XXXX: I think this should be good, this blocks, but won't run unless there are things left
            # TODO: this blocks... hence the machinery above
            try:
                outgoing=q.get(timeout=5)
                solve_number=outgoing[0]
                outgoing_properties_dict=outgoing[1]
                outgoing_properties_keys=outgoing_properties_dict.keys()
                dbtable=dbtable_dict[solve_number]
                solve_number_list.remove(solve_number)
                #
                # TODO: want to copy to table...
                outgoing_properties_strings = ['\"' + k + '\"=%(' + k + ')s' for k in outgoing_properties_keys]
                solve_number_str=str(solve_number)
                outgoing_properties_update_string="UPDATE " + dbtable + " SET " + ', '.join(outgoing_properties_strings) + " WHERE solve_number=" + solve_number_str + ";"
                outgoing_properties_update_string=CURSOR.mogrify(outgoing_properties_update_string,outgoing_properties_dict)
                update_strings.append(outgoing_properties_update_string)
                # CURSOR.execute(outgoing_properties_update_string,outgoing_properties_dict)
                # update the work table
                update_batch_table_string="UPDATE " + batch_table + " SET done=TRUE WHERE solve_number=" + solve_number_str + ";"
                update_strings.append(update_batch_table_string)
            except Queue.Empty:
                print "Queue empty..."
                sys.stdout.flush()
                # if queue times out and processors not all working, try and get more work
                if len(solve_number_list) <= PROCESSES and '--serial' not in sys.argv:
                    # this should not take too long... but maybe add timeout...
                    # update before breaking
                    if update_strings != []:
                        print "Updating..."
                        sys.stdout.flush()
                        CURSOR.execute(''.join(update_strings))
                        print "Committing..."
                        sys.stdout.flush()
                        CONNECTION.commit()
                        print "Done committing."
                        sys.stdout.flush()
                        update_strings=[]
                    break
            # TODO: make sure commit occurs frequently, change based on batch size and such
            #       should know size of segment too, change to segment_size - 4
            #       a timout of 20-30s might be nice
            print THEHOSTNAME, "Solve number list: ", len(solve_number_list)
            # XXXX: divided by two because it confusing not to have these two numbers match
            #       spaces added for readability
            print THEHOSTNAME, "Queued for update:    ", len(update_strings)/2
            sys.stdout.flush()
            if len(update_strings) > MAXUPDATESTRINGS:
                print "Updating..."
                sys.stdout.flush()
                CURSOR.execute(''.join(update_strings))
                print "Committing..."
                sys.stdout.flush()
                CONNECTION.commit()
                print "Done committing."
                sys.stdout.flush()
                update_strings=[]
            # TODO: I think a bare minimum sleep is needed avoid spin locking
            #       threading would be far better
            time.sleep(0.01)
        if update_strings != []:
            CURSOR.execute(''.join(update_strings))
            CONNECTION.commit()
            update_strings=[]
    CONNECTION.commit()
    CONNECTION.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print "PROCESSES: "        + str(PROCESSES)
        print "MAXTASKSPERCHILD: " + str(MAXTASKSPERCHILD)
        main(sys.argv)
        POOL.close()
        POOL.join()
