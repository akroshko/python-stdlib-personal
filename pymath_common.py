#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
"""A standard set of utility and system administration functions."""
# DO NOT EDIT DIRECTLY IF NOT IN cic-python-common, THIS FILE IS ORIGINALLY FROM https://github.com/akroshko/cic-python-common

# Copyright (C) 2015-2019, Andrew Kroshko, all rights reserved.
#
# Author: Andrew Kroshko
# Maintainer: Andrew Kroshko <akroshko.public+devel@gmail.com>
# Created: Wed Nov 15, 2017
# Version: 20191209
# URL: https://github.com/akroshko/cic-python-common
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

import os,sys
import compileall
import math as m
from pprint import pprint as PP
import re
import socket
import subprocess
import time
from time import time as TT
import traceback

import numpy as np
import scipy as sp

TICTOCLABELS={}

# if accessed without being set, this should raise an error
LIST_OF_FLAGS=None

NP_DOUBLE_EPS=np.finfo(sp.double).eps
SP_DOUBLE_EPS=sp.finfo(sp.double).eps

__all__ = ['All','SP_DOUBLE_EPS','NP_DOUBLE_EPS']

class All(object):
    """ Provide a decorator that add a class or method to the __all__ variable. """
    def __init__(self,global_dict):
        self.global_dict = global_dict

    def __call__(self,obj):
        if '__all__' not in self.global_dict:
            self.global_dict['__all__'] = []
        self.global_dict['__all__'].append(obj.__name__)
        return obj

def pymath_import_module(theglobals,thelocals,module_name,module_as,submodule=None):
    if submodule is None:
        themodule = __import__(module_name,theglobals,thelocals)
        theglobals[module_as] = themodule
    else:
        themodule = __import__(module_name,theglobals,thelocals,[submodule])
        theglobals[module_as] = getattr(themodule,submodule)

@All(globals())
def tic(label=None):
    global TICTOCLABELS
    if label is None:
        TICTOCLABELS['default'] = TT()
    else:
        TICTOCLABELS[label] = TT()

# TODO: use a file-local label
@All(globals())
def toc(label=None,level=0):
    if label is None:
        thetime = TT() - TICTOCLABELS['default']
        print("Timing: %.2fs" % thetime)
    else:
        thetime = TT() - TICTOCLABELS[label]
        print(''.join([' ']*level) + "---- " + label + (": %.2fs" % thetime))

@All(globals())
def filter_list_of_tuples_invalid(list_of_tuples):
    """Filter out in invalid values.  This generally for plotting, so
things that are unplottable like None are filtered out.
    TODO: raise special exception if non-scalar too?"""
    new_list_of_tuples = [t for t in list_of_tuples if t[0] is not None and t[1] is not None]
    # TODO: use m, np, or sp functions here
    new_list_of_tuples = [t for t in new_list_of_tuples if ((not isinstance(t[0],float) or not (m.isnan(t[0]) or m.isinf(t[0]))) and (not isinstance(t[1],float) or not (m.isnan(t[1]) or m.isinf(t[1]))))]
    return new_list_of_tuples

# TODO: possibily work with tuples
@All(globals())
def ax_make_symlog_y(ax,ythresh,xmin,xmax,ymin,ymax):
    if ymin < -ythresh or ymax > ythresh:
        print("Setting symlog with %s" % ythresh)
        ax.set_yscale('symlog',linthreshy=ythresh)
        if ymax > ythresh:
            print("Top symlog")
            ax.hlines(ythresh,xmin,xmax,color='r')
        if ymin < -ythresh:
            print("Bottom symlog")
            ax.hlines(-ythresh,xmin,xmax,color='r')

@All(globals())
def ax_make_nice_grid(ax):
    ""
    # TODO: do i want this here
    ax.minorticks_on()
    ax.grid(True,which='major',linestyle='dashed',linewidth=1.0)
    ax.grid(True,which='minor',linestyle='dotted',linewidth=0.4)

@All(globals())
def fig_save_fig(fig,fullpath,dpi=150):
    os_makedirs(os.path.dirname(fullpath))
    # disable transparency for efficiency
    fig.savefig(fullpath,dpi=dpi,bbox_inches='tight',transparent=False)
    print("Saved figure to: " + fullpath)
    # TODO: close fig....

@All(globals())
def mpl_print_rc():
    from matplotlib import rcParams
    PP(rcParams)

@All(globals())
def os_makedirs(path):
    if not os.path.exists(path):
        # hack to make this function thread-safe, because the path might already exist, because that's been an issue before...
        try:
            os.makedirs(path)
        except OSError,e:
            print(e)

@All(globals())
def pymath_default_imports(theglobals,thelocals):
    """Import commonly used libraries into global namespace.  Especially
    useful for quick little scripts.

    After 'from pythode.pymathdb.pymath_common import *' use the line:
    'pymath_default_imports(globals(),locals())'

    """
    # standard library
    pymath_import_module(theglobals,thelocals,'copy','copy')
    pymath_import_module(theglobals,thelocals,'copy','COPY',submodule='copy')
    pymath_import_module(theglobals,thelocals,'copy','DEEPCOPY',submodule='deepcopy')
    pymath_import_module(theglobals,thelocals,'datetime','datetime')
    pymath_import_module(theglobals,thelocals,'itertools','itertools')
    # TODO: lxml.html
    pymath_import_module(theglobals,thelocals,'lxml','lxml')
    pymath_import_module(theglobals,thelocals,'json','json')
    pymath_import_module(theglobals,thelocals,'multiprocessing','multiprocessing')
    pymath_import_module(theglobals,thelocals,'multiprocessing','Pool',submodule='Pool')
    pymath_import_module(theglobals,thelocals,'pprint','pprint',submodule='pprint')
    pymath_import_module(theglobals,thelocals,'pprint','pp',submodule='pprint')
    pymath_import_module(theglobals,thelocals,'pprint','PP',submodule='pprint')
    pymath_import_module(theglobals,thelocals,'pycurl','pycurl')
    pymath_import_module(theglobals,thelocals,'signal','signal')
    pymath_import_module(theglobals,thelocals,'Queue','Queue')
    pymath_import_module(theglobals,thelocals,'random','random')
    # TODO: import a nice re matcher
    pymath_import_module(theglobals,thelocals,'re','re')
    pymath_import_module(theglobals,thelocals,'subprocess','subprocess')
    pymath_import_module(theglobals,thelocals,'socket','socket')
    pymath_import_module(theglobals,thelocals,'time','time')
    pymath_import_module(theglobals,thelocals,'time','TT',submodule='time')
    pymath_import_module(theglobals,thelocals,'time','TIME_TIME',submodule='time')
    pymath_import_module(theglobals,thelocals,'traceback','traceback')
    pymath_import_module(theglobals,thelocals,'urllib','urllib')
    ########################################
    # math
    pymath_import_module(theglobals,thelocals,'math','m')
    pymath_import_module(theglobals,thelocals,'math','M_COS', submodule='cos')
    pymath_import_module(theglobals,thelocals,'math','M_PI',  submodule='pi')
    pymath_import_module(theglobals,thelocals,'math','M_SIN', submodule='sin')
    pymath_import_module(theglobals,thelocals,'math','M_SQRT',submodule='sqrt')
    ########################################
    # not standard library
    pymath_import_module(theglobals,thelocals,'matplotlib','mpl')
    # XXXX: this allows things to be done with no graphics
    # TODO: have a nicer configuration that accomodates headless servers, but still allows graphics to pop up
    theglobals['mpl'].use('Agg')
    # TODO: change back for Sage 8.3
    # if os.name == 'posix' and not os.getenv("DISPLAY"):
    #     theglobals['mpl'].use('Agg')
    # else:
    #     theglobals['mpl'].use('TkAgg')
    pymath_import_module(theglobals,thelocals,'matplotlib','plt',submodule='pyplot')

    # TODO: psycopg2.extras
    pymath_import_module(theglobals,thelocals,'psycopg2','psycopg2')

    # from matplotlib.backends.backend_pdf import PdfPages
    # these are things that I commonly use in inner loops (do not want to do the dot operator), or for convienience
    # scipy
    pymath_import_module(theglobals,thelocals,'numpy','np')
    pymath_import_module(theglobals,thelocals,'numpy','NP_ABSOLUTE',   submodule='absolute')
    pymath_import_module(theglobals,thelocals,'numpy','NP_ARRAY',      submodule='array')
    pymath_import_module(theglobals,thelocals,'numpy','NP_CONCATENATE',submodule='concatenate')
    pymath_import_module(theglobals,thelocals,'numpy','NP_DIVIDE',     submodule='divide')
    pymath_import_module(theglobals,thelocals,'numpy','NP_DOT',        submodule='dot')
    pymath_import_module(theglobals,thelocals,'numpy','NP_EMPTY',      submodule='empty')
    pymath_import_module(theglobals,thelocals,'numpy','NP_FLOAT64',    submodule='float64')
    pymath_import_module(theglobals,thelocals,'numpy','NP_INF',        submodule='inf')
    pymath_import_module(theglobals,thelocals,'numpy','NP_ISINF',      submodule='isinf')
    pymath_import_module(theglobals,thelocals,'numpy','NP_ISFINITE',   submodule='isfinite')
    pymath_import_module(theglobals,thelocals,'numpy','NP_MAXIMUM',    submodule='maximum')
    pymath_import_module(theglobals,thelocals,'numpy','NP_MESHGRID',   submodule='meshgrid')
    pymath_import_module(theglobals,thelocals,'numpy','NP_MULTIPLY',   submodule='multiply')
    pymath_import_module(theglobals,thelocals,'numpy','NP_MA',         submodule='ma')
    pymath_import_module(theglobals,thelocals,'numpy','NP_MEAN',       submodule='mean')
    pymath_import_module(theglobals,thelocals,'numpy','NP_NAN',        submodule='nan')
    pymath_import_module(theglobals,thelocals,'numpy','NP_NEWAXIS',    submodule='newaxis')
    pymath_import_module(theglobals,thelocals,'numpy','NP_ONES',       submodule='ones')
    pymath_import_module(theglobals,thelocals,'numpy','NP_REPEAT',     submodule='repeat')
    pymath_import_module(theglobals,thelocals,'numpy','NP_SQUARE',     submodule='square')
    pymath_import_module(theglobals,thelocals,'numpy','NP_SUM',        submodule='sum')
    pymath_import_module(theglobals,thelocals,'numpy','NP_TILE',       submodule='tile')
    pymath_import_module(theglobals,thelocals,'numpy','NP_SWAPAXES',   submodule='swapaxes')
    pymath_import_module(theglobals,thelocals,'numpy','NP_WARNINGS',   submodule='warnings')
    pymath_import_module(theglobals,thelocals,'numpy','NP_ZEROS',      submodule='zeros')
    pymath_import_module(theglobals,thelocals,'numpy','NP_ZEROS_LIKE', submodule='zeros_like')
    pymath_import_module(theglobals,thelocals,'scipy','sp')
    pymath_import_module(theglobals,thelocals,'scipy','linalg',submodule='linalg')
    pymath_import_module(theglobals,thelocals,'scipy','sparse',submodule='sparse')
    pymath_import_module(theglobals,thelocals,'scipy','SP_ABSOLUTE',   submodule='absolute')
    pymath_import_module(theglobals,thelocals,'scipy','SP_ARRAY',      submodule='array')
    pymath_import_module(theglobals,thelocals,'scipy','SP_CONCATENATE',submodule='concatenate')
    pymath_import_module(theglobals,thelocals,'scipy','SP_DIVIDE',     submodule='divide')
    pymath_import_module(theglobals,thelocals,'scipy','SP_DOT',        submodule='dot')
    pymath_import_module(theglobals,thelocals,'scipy','SP_EMPTY',      submodule='empty')
    pymath_import_module(theglobals,thelocals,'scipy','SP_INF',        submodule='inf')
    pymath_import_module(theglobals,thelocals,'scipy','SP_ISINF',      submodule='isinf')
    pymath_import_module(theglobals,thelocals,'scipy','SP_ISFINITE',   submodule='isfinite')
    pymath_import_module(theglobals,thelocals,'scipy','SP_LINSPACE',   submodule='linspace')
    pymath_import_module(theglobals,thelocals,'scipy','SP_MA',         submodule='ma')
    pymath_import_module(theglobals,thelocals,'scipy','SP_NAN',        submodule='nan')
    pymath_import_module(theglobals,thelocals,'scipy','SP_MAXIMUM',    submodule='maximum')
    pymath_import_module(theglobals,thelocals,'scipy','SP_MEAN',       submodule='mean')
    pymath_import_module(theglobals,thelocals,'scipy','SP_MULTIPLY',   submodule='multiply')
    pymath_import_module(theglobals,thelocals,'scipy','SP_NEWAXIS',    submodule='newaxis')
    pymath_import_module(theglobals,thelocals,'scipy','SP_ONES',       submodule='ones')
    pymath_import_module(theglobals,thelocals,'scipy','SP_REPEAT',     submodule='repeat')
    pymath_import_module(theglobals,thelocals,'scipy','SP_SQUARE',     submodule='square')
    pymath_import_module(theglobals,thelocals,'scipy','SP_SUM',        submodule='sum')
    pymath_import_module(theglobals,thelocals,'scipy','SP_SWAPAXES',   submodule='swapaxes')
    pymath_import_module(theglobals,thelocals,'scipy','SP_TILE',       submodule='tile')
    pymath_import_module(theglobals,thelocals,'scipy','SP_ZEROS',      submodule='zeros')
    pymath_import_module(theglobals,thelocals,'scipy','SP_ZEROS_LIKE', submodule='zeros_like')

################################################################################
## deal with argv, functions that look like simple expression
@All(globals())
def argv_in(thearg):
    """Make sure a flag is valid and check if in sys.argv."""
    global LIST_OF_FLAGS
    if thearg not in LIST_OF_FLAGS:
        raise RuntimeError("Improper flag check!")
    return thearg in sys.argv

@All(globals())
def argv_not_in(thearg):
    """Make sure a flag is valid and check if not in sys.argv."""
    global LIST_OF_FLAGS
    if thearg not in LIST_OF_FLAGS:
        raise RuntimeError("Improper flag check!")
    return thearg not in sys.argv

################################################################################
## some program utilities
## TODO: rename this to have argv in it
@All(globals())
def check_valid_flags(argv,list_of_flags=[],mutually_exclusive_flags=[]):
    """This is a sanity check for simple flags.  Generally so long
experiments do not fail because of minor mispellings.  For more
sophisticated use argparse is recommended."""
    global LIST_OF_FLAGS
    LIST_OF_FLAGS=list_of_flags
    # TODO: maybe I want to just use sys.argv?
    # TODO: mutually exclusive flags should be tuples
    # TODO: should this actually call argparse?
    for a in argv[1:]:
        if a.startswith('--') and a not in list_of_flags:
            raise RuntimeError("Improper arguments or flags given!!! Specifically: ",a)

@All(globals())
def extract_flags_selecting_dictionary_key(argv,thedict):
    select_key=None
    for thearg in argv:
        if thearg.startswith('--'):
            for k in thedict:
                if thearg[2:] == k:
                    if select_key is None:
                        select_key=thearg[2:]
                    else:
                        raise Exception("Duplicate matching select keys!!!")
    return select_key

@All(globals())
def print_full_exception(message=None):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # TODO: can I print my e automatically?
    if message:
        print(message)
    traceback.print_exc()

@All(globals())
def timestamp_now():
    import time
    import datetime
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y%m%dT%H%M%S')

check_orphaned_compiled_patterns=[('.pyc',    '.py'),
                                  ('.sage.py','.sage'),
                                  ('.sage.pyc','.sage')]

################################################################################
## some project utilties

# TODO: this can take a long time
@All(globals())
def check_python_sage_project_sanity(project_path):
    "Helpful function to check sanity of python and sage project."
    # TODO: want my proper expand_all
    project_path=os.path.expanduser(project_path)
    for path,subdirs,files in os.walk(project_path):
        for filename in files:
            # check that there are no orphaned compiled functions
            # TODO: does not work if pyc or pyx or distributed seperately
            for compiled_pattern,base_pattern in check_orphaned_compiled_patterns:
                if filename.endswith(compiled_pattern):
                    if not os.path.exists(os.path.join(path,filename[:-len(compiled_pattern)]+base_pattern)):
                        # TODO: ask to delete
                        print("Orphaned compiled file: %s" % os.path.join(path,filename))
                        return 1
    # check all python scripts
    # TODO: make sure regex works, still listing these directories...
    rc = compileall.compile_dir(project_path,rx=re.compile('.*/(\.git|\.svn|\.hg|\.ropeproject)/.*'))
    if rc != 1:
        print("Python compile return code: %s" % rc)
        return 1
    print("==================== 2")
    # looping twice because orphaned is faster and should be fixed first
    # this is special for sage, might want to double compile python because that is fast
    for path,subdirs,files in os.walk(project_path):
        for filename in files:
            # if filename.endswith('.sage'):
            #     # should be fairly lightweight
            #     from sage.repl.preparse import preparse_file_named
            #     print "Preparsing: ", os.path.join(path,filename)
            #     preparse_file_named(os.path.join(path,filename))
            # check for things compiling
            if filename.endswith('.sage'):
                command_list=['sage','-preparse',os.path.join(path,filename)]
                if (not (os.path.exists(os.path.join(path,filename)+'.py'))) or (os.path.getmtime(os.path.join(path,filename)) > os.path.getmtime(os.path.join(path,filename)+'.py')):
                    # TODO: check timestamps for sage preparser
                    print(command_list)
                    p = subprocess.Popen(command_list)
                    p.communicate()
                    if p.returncode != 0:
                        print("Failed to compile: %s" % os.path.join(path,filename))
                        return 1
            # TODO: handle python 3 etc
    return 0

################################################################################
## some array utilities

@All(globals())
def compact_array_print(arr,threshold=0.5,levels=np.array([])):
    # TODO: string are immutable, this is not efficient...
    # TODO: this is mostly for debugging right now
    # TODO: implement levels....
    thestring = u''
    # TODO: do not use a for loop, make something that works well with various boolean things
    # TODO: have something that gives relative magnitude (logarithmic too)
    for i in xrange(arr.shape[1]):
        for j in xrange(arr.shape[0]):
            if arr[i,j] > threshold:
                thestring += '##'
                # thestring += u'\u2588\u2588'
                # thestring += u'\u2591\u2591'
            else:
                thestring += '  '
        thestring += '\n'
    return thestring

@All(globals())
def compact_integer_array_print(arr):
    thestring = ''
    charstart=ord('A')
    for i in xrange(arr.shape[1]):
        for j in xrange(arr.shape[0]):
            if arr[i,j] == -1:
                thestring += '  '
            else:
                thechar = chr(charstart+arr[i,j])
                thestring += thechar
                thestring += thechar
        thestring += '\n'
    return thestring

@All(globals())
def open_database(connection,cursor):
    import psycopg2
    # TODO: do not open database if connection and cursor still work
    # always localhost, but as a variable just in case
    dbhostname='localhost'
    # TODO: can socket.gethostname()
    if (os.getenv('PYMATHDBMAIN') and socket.gethostname() == os.getenv('PYMATHDBMAIN')) or not os.getenv('PYMATHDBMAIN'):
        # PostgreSQL database is local
        port='5432'
    else:
        # TODO: make configurable
        port='5433'
    if connection == None:
        try:
            # TODO: password in args?
            conn_string = "dbname='pymathdb' user=" + os.getenv('PYMATHDBUSER') + " port='" + port + "' host='" + dbhostname + "' password='" + os.getenv('PYMATHDBPASSWORD') + "'"
            # print the connection string we will use to connect
            print("Connecting to database:\n  --> %s" % (conn_string))
            # get a connection, if a connect cannot be made an exception will be raised here
            connection = psycopg2.connect(conn_string)
            # should also be disabled in database config
            # TODO: put back on once I understand!!!
            # TODO: change for interactive use?
            connection.autocommit=False
            # conn.cursor will return a cursor object, you can use this cursor to perform queries
            cursor = connection.cursor()
        except Exception, e:
            print("Unable to connect to the database")
            print(e)
            # TODO: do I really want to bail on failed connection?
            sys.exit(1)
    return connection,cursor

@All(globals())
def pymath_db_setup(theglobals,thelocals):
    # TODO: open database and add things to globals
    # TODO: how does this go?
    dbhostname = "localhost"
    connection = None
    cursor = None
    # TODO: need a better function for this that does not comprimise privacy
    connection,cursor=open_database(connection,cursor)
    theglobals['CONNECTION'] = connection
    theglobals['CURSOR'] = cursor
    # TODO: an all decorator and other utilities
    # TODO: need some nice functions for stuff....

@All(globals())
def pymath_default_imports_and_db_setup(theglobals,thelocals):
    from pythode.pymathdb.pymath_common import pymath_default_imports
    pymath_default_imports(theglobals,thelocals)
    pymath_db_setup(theglobals,thelocals)
