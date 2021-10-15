#!/usr/bin/env python3

# Code to compare two STATION_XML files, specifically one from SIS
#   and one from IRIS, though is generic enough to compare any two.
#
# Alex Hutko, PNSN Feb 14, 2019

import sys
import matplotlib as mpl
mpl.use('tkagg')
import argparse
import requests
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import obspy
from obspy import read_inventory
from obspy.core import UTCDateTime

#---- set thresholds for tolerances
thresh_lat_lon_m = 10       # in meters
thresh_lat_lon = thresh_lat_lon_m / 111190
thresh_elev = 10            # in meters
thresh_dep = 10             # in meters
#thresh_freq_resp = 0.001
#thresh_sensitivity = 0.001
thresh_response_amp = 0.1   # as a percent
thresh_response_phase = 0.1 # in radians
file1alias = " (SIS)"
file2alias = "(IRIS)"

#---- verbosity = 0, just print FAILs, = 1, print all PASSs and FAILs
verbosity = 1

#-------- read input arguments and download stationXML files

parser = argparse.ArgumentParser(description="This fetches and compares SIS \
    and IRIS station XML files")
help_text = "Specify a NET.STA code, e.g.  UW.ASR"
parser.add_argument("netsta",help=help_text)
help_text = "Specify prod or test"
parser.add_argument("system",help=help_text)
args = parser.parse_args()
if ( args.netsta ):
    net = args.netsta.split(".")[0]
    sta = args.netsta.split(".")[1]
if (args.system and args.system == "test"):
    url1 = "https://files.anss-sis.scsn.org/test/FDSNStationXML1.1/" + net + "/" \
           + net + "_" + sta + ".xml"
else:
    url1 = "https://files.anss-sis.scsn.org/production/FDSNStationXML1.1/" + net \
           + "/" + net + "_" + sta + ".xml"
url2 = "https://service.iris.edu/fdsnws/station/1/query?net=" + net + "&sta=" \
    + sta + "&level=response&format=xml&includecomments=true&nodata=404"
print ()
print ("SIS file: " + url1 )
print ("IRIS file: " + url2 )
print ()
station_xml_file_1 = net + "." + sta + ".SIS.xml"
try:
    r=requests.get(url1)
    with open(station_xml_file_1,'wb') as f:
        f.write(r.content)
    f = open(station_xml_file_1)
    x1 = f.readlines()
    f.close()
except:
    print("SIS stationXML file download failed" )
    print()
    exit()

station_xml_file_2 = net + "." + sta + ".IRIS.xml"
try:
    r=requests.get(url2)
    with open(station_xml_file_2,'wb') as f:
        f.write(r.content)
    f = open(station_xml_file_2)
    x2 = f.readlines()
    f.close()
except:
    print("IRIS stationXML file download failed" )
    print()
    exit()

#-------- Functions follow.

# clean up the xml file of all "fsx:" which come from SIS XMLs
#  example:  <fsx:Longitude>-121.601640</fsx:Longitude>
def clean_up_fsx_from_xml(lines):
    newlines = []
    for line in lines:
        newlines.append(line.replace("fsx:",""))
    return newlines

# get the station code
def get_station_code_lat_lon_elev(lines):
    firstlat = True
    firstlon = True
    firstelev = True
    for line in lines:
        if ( "<Station code=" in line ):
            for word in line.split():
                print(word)
                if ( word[0:5] == "code=" ):
                    stacode = word[6:-1]
        if ( firstlat is True and "<Latitude>" in line ):
            firstlat = False
            lat = float(line.replace(">","<").split("<")[2])
        if ( firstlon is True and "<Longitude>" in line ):
            firstlon = False
            lon = float(line.replace(">","<").split("<")[2])
        if ( firstelev is True and "<Elevation>" in line ):
            firstelev = False
            elev = float(line.replace(">","<").split("<")[2])
    return stacode, lat, lon, elev


# Get each channel+location epoch.  The returned "epochs" will be a 
#   list of lists... it will have Nepochs lists which will contain
#   all lines from the epoch, where each line is a list.
def get_channel_location_epochs(lines):
    channels = []
    locations = []
    startdates = []
    enddates = []
    epochs = []
    epoch_lines = []
    for line in lines:
        if ( "<Channel code=" in line ):
            epochs.append(epoch_lines)
            epoch_lines = []
            for word in line.split():
                if ( "code=" in word and len(word) == 10 ):
                    channels.append(word[6:-1])
                if ( "locationCode=" in word ):
                    locword = word.split("\"")[1]
                    locations.append(locword)
                if ( "startDate=" in word ):
                    startword = word.split("\"")[1].strip("Z")
                    try:
                        start = datetime.strptime(startword, '%Y-%m-%dT%H:%M:%S')
                    except Exception as e:
                        print(startword)
                        if "+" in startword:
                            startword = startword.rstrip("00:00")
                            startword = startword.rstrip("+")
                        if ".0000" in startword:
                            startword = startword.rstrip(".0")
                        print(startword)
                        start = datetime.strptime(startword, '%Y-%m-%dT%H:%M:%S')
                    startdates.append(start)
                if ( "endDate=" in word ):
                    endword = word.split("\"")[1].strip("Z")
                    try:
                        end = datetime.strptime(endword, '%Y-%m-%dT%H:%M:%S')
                    except Exception as e:
                        if "+" in endword:
                            endword = endword.rstrip("00:00")
                            endword = endword.rstrip("+")
                        if ".0000" in endword:
                            endword = endword.rstrip(".0")
                        end = datetime.strptime(endword, '%Y-%m-%dT%H:%M:%S')
                    if ( end.year >= 2599 ):
                        end = datetime.strptime("2599-12-31T23:59:59", \
                              '%Y-%m-%dT%H:%M:%S')
                    enddates.append(end)
            if ( "endDate=" not in line ):
                end = datetime.strptime("2599-12-31T23:59:59", \
                      '%Y-%m-%dT%H:%M:%S')
                enddates.append(end)
        epoch_lines.append(line)
    epochs.append(epoch_lines)
    del epochs[0]

    return channels, locations, startdates, enddates, epochs

# Given a keyword, e.g. "Latitude>", this returns the value between > and <
#   the first time keyword is encountered in the list of lists (lines).
def get_value(lines,keyword):
    for line in lines:
        if ( keyword in line and "Value" not in line):
            try:
                value = float(line.replace(">","<").split("<")[2])
            except Exception as e:
                value = None
            return value
    return None

# Compare two channel+location epochs for lat,lon,elev,dep,azi,samprate,clock
def compare_epochs(epoch1,epoch2,alias1,alias2):
    #thresh_lat_lon = 0.00001
    #thresh_elev = 0.01
    #thresh_dep = 0.01
    thresh_azi = 0.01
    thresh_samprate = 0.001
    thresh_clock = 0.000001
    dictionary = {"Latitude": thresh_lat_lon, "Longitude": thresh_lat_lon, \
                  "Elevation": thresh_elev, "Depth": thresh_dep, \
                  "Azimuth": thresh_azi, "SampleRate": thresh_samprate, \
                  "ClockDrift": thresh_clock }
    for key in dictionary.keys():
        value1 = get_value(epoch1,key)
        value2 = get_value(epoch2,key)
        if ( value1 is None and value2 is None ):
            print ( key + " is missing from " + alias1 + " and " + alias2 )
        elif ( value1 is not None and value2 is None ):
            print ( key + " is missing from " + alias2 + " and = " + \
                    str(value1) + " in " + alias2 )
        elif ( value1 is None and value2 is not None ):
            print ( key + " is missing from " + alias1 + " and = " + \
                    str(value2) + " in " + alias2 )
        else:
            if ( abs(value1 - value2) > dictionary[key] ):
                print( "Channel." + key + ": fail, " + str(value1) + " " + \
                       alias1 + " not within " + str(dictionary[key]) + " of " \
                       + str(value2) + " " + alias2 )
            else:
                if ( verbosity == 1 ):
                    print ( "Channel." + key + ": pass" )

#-------- Main follows.

#station_xml_file_1 = net + "." + sta + ".SIS.xml"
#try:
#    with open(station_xml_file_1,'r') as f:
#        x1 = f.readlines()
#except:
#    print("SIS stationXML file download failed" )
#    print()
#    exit()
#
#station_xml_file_2 = net + "." + sta + ".IRIS.xml"
#try:
#    with open(station_xml_file_2,'r') as f:
#        x2 = f.readlines()
#except:
#    print("IRIS stationXML file download failed" )
#    print()
#    exit()
#---- clean up the files of any "fsx:".  (present in SIS station_xml files)
x1 = clean_up_fsx_from_xml(x1)
x2 = clean_up_fsx_from_xml(x2)

#---- Compare station level information
try:
    station_code1, station_lat1, station_lon1, station_elev1 = \
        get_station_code_lat_lon_elev(x1)
except Exception as e:
    print("Problem getting station_code and location from XML file {}, could it be empty?".format(station_xml_file_1))
    print(e)
    sys.exit(1)
try:
    station_code2, station_lat2, station_lon2, station_elev2 = \
        get_station_code_lat_lon_elev(x2)
except Exception as e:
    print("Problem getting station_code and location from XML file {}, could it be empty?".format(station_xml_file_2))
    print(e)
    sys.exit(1)

if ( station_code1 != station_code2 ):
    print ("FAIL: station.code  1: " + station_code1 + \
    "  2: " + station_code2 )
if ( abs(station_lat1 - station_lat2) > thresh_lat_lon ):
    print ("Fail: station.latitude  1: " + str(station_lat1) + \
    "  2: " + str(station_lat2) )
if ( abs(station_lon1 - station_lon2) > thresh_lat_lon ):
    print ("Fail: station.latitude  1: " + str(station_lon1) + \
    "  2: " + str(station_lon2) )
if ( abs(station_elev1 - station_elev2) > thresh_elev ):
    print ("Fail: station.elevation  1: " + str(station_elev1) + \
    "  2: " + str(station_elev2) )

#---- get all channel+location epochs
chan1,loc1,start1,end1,epoch1 = get_channel_location_epochs(x1)
chan2,loc2,start2,end2,epoch2 = get_channel_location_epochs(x2)

#---- compare channel+location epochs

if ( len(chan1) != len(chan2) ):
    print ("FAIL: number of channel+location epochs  1: " + str(len(chan1)) \
           + "  2: " + str(len(chan2)))

inv1 = read_inventory(station_xml_file_1)
inv2 = read_inventory(station_xml_file_2)
ninv1 = int(str(inv1[0][0]).split("Channel Count")[1].split()[1].split("/")[1])
ninv2 = int(str(inv2[0][0]).split("Channel Count")[1].split()[1].split("/")[1])
if ( ninv1 != ninv2 ):
    print ("WARNING: numer of channel+location epochs don't match " + \
           str(ninv1) + " " + file1alias + " vs " + str(ninv2) + " " + \
           file2alias )
for i in range(0,len(chan1)):
    found_matching_epoch = 0
    for j in range(0,len(chan2)):
        if ( chan1[i] == chan2[j] and loc1[i] == loc2[j] ):
            if ( ( start1[i] == start2[j] ) or ( end1[i] == end2[j] ) or \
                 ( start1[i] >= start2[j] and end1[i] <= end2[j] ) ):
                 #( (start1[i]-start2[j]).days < 2 or (end1[i]-end2[j]).days < 2 )):
                found_matching_epoch = 1
                print ()
                print ()
                print ("Comparing " + file1alias + ": " + station_code1 + \
                       "." + loc1[i] + "." + chan1[i] + " " + str(start1[i]) + \
                       " to " + str(end1[i]) )
                print ("          " + file2alias + ": " + station_code2 + \
                       "." + loc2[j] + "." + chan2[j] + " " + str(start2[j]) + \
                       " to " + str(end2[j]) )
                if ( start1[i] != start2[j] ):
                    print("WARNING: " + station_code1 + "." + loc1[i] + "." + \
                          chan1[i] + " starttimes not matching " + file1alias + \
                          ": " + str(start1[i]) + "  " + file2alias + ": " + \
                          str(start2[j]) )
                if ( end1[i] != end2[j] ):
                    print("WARNING: " + station_code1 + "." + loc1[i] + "."  + \
                          chan1[i] + " endtime not matching " + file1alias + \
                          ": " + str(end1[i]) + "  " + file2alias + ": " \
                          + str(end2[j]) )
                #---- compare the channel+location epochs, everything except response.
                compare_epochs(epoch1[i],epoch2[j],file1alias,file2alias)

                #---- compare the response info
                Nstages1 = sum(line.count("Stage number=") for line in epoch1[i])
                Nstages2 = sum(line.count("Stage number=") for line in epoch2[j])
                if ( Nstages1 != Nstages2 ):
                    print ("Warning: Number of response stages don't match: " + \
                           str(Nstages1) + " in " + file1alias + ", " + \
                           str(Nstages2) + " in " + file2alias )
                #else: RH: always do this, even when number of stages doesn't match.
                inv1_cha = inv1[0][0][i]
                inv2_cha = inv2[0][0][j]
                #print ("A: " + inv1_cha.code + " " + str(inv1_cha.start_date) )
                #print ("B: " + inv2_cha.code + " " + str(inv2_cha.start_date) )
                if ( (UTCDateTime(start1[i]) - inv1_cha.start_date) > 1 ):
                    print ("WARNING, I'm using the wrong start date.  " + \
                           "start1[i] = " + str(start1[i]) + \
                           " inv1_cha.start_date = " + str(inv_cha1.start_date) )
                try:
                    print("Calculating response for inv1 (SIS)")
                    response1, freqs1 = inv1_cha.response.get_evalresp_response(\
                                    0.01, 16384, output="VEL")
                except Exception as e:
                    print("Warning for xml 1, cannot calculate response: {}".format(e))
                    response1 = []
                try:
                    print("Calculating response for inv2 (DMC)")
                    response2, freqs2 = inv2_cha.response.get_evalresp_response(\
                                    0.01, 16384, output="VEL")
                except Exception as e:
                    print("Warning for xml 2, cannot calculate response: {}".format(e))
                    response2 = []
                # RH: found response a bit unstable near the nyquist frequency, stop before
                # response is calculated from 0 to fnyquist, with steps of  fnyquist/(16384/2)
                # i.e. fnyquist/8192, 90% of fnyquist = 0.90 * 8192, or 7373
                MAXN = 7373
                #MAXN = 1000
                if len(response1) > 0 and len(response2) > 0:
                    amp1 = abs(response1[1:MAXN])
                    amp2 = abs(response2[1:MAXN])
                    ampdiff = 100*(abs(amp1 - amp2)/abs(amp2))
                    phase1 = 2 * np.pi + np.unwrap(np.angle(response1[1:MAXN]))
                    phase2 = 2 * np.pi + np.unwrap(np.angle(response2[1:MAXN]))
                    phasediff = 100*abs(phase1-phase2)
                    if ( max(ampdiff) > thresh_response_amp ):
                        title = "Channel.response.amp: fail, max(diff_in_amp) of " \
                              + str(max(ampdiff)) + " % not within " + \
                              str(thresh_response_amp)
                        print(title)
                        #plt.plot(freqs1[1:MAXN],amp1,'k.',label=("SIS: " + inv1_cha.code + " " + str(inv1_cha.start_date)))
                        #plt.plot(freqs2[1:MAXN],amp2,'r.',label=("DMC: " + inv2_cha.code + " " + str(inv2_cha.start_date)))
                        #plt.title(title)
                        #plt.legend()
                        #plt.show()
                    if ( max(phasediff) > thresh_response_phase ):
                        title = "Channel.response.phase: fail, max(diff_in_phase) of " \
                              + str(max(phasediff)) + " radians not within " + \
                              str(thresh_response_phase)
                        print(title)
                        #plt.plot(freqs1[1:MAXN],phase1,'k.',label=(inv1_cha.code + " " + str(inv1_cha.start_date) + "-" + str(inv1_cha.end_date)))
                        #plt.plot(freqs2[1:MAXN],phase2,'r.',label=(inv2_cha.code + " " + str(inv2_cha.start_date) + "-" + str(inv2_cha.end_date)))
                        #plt.title(title)
                        #plt.legend()
                        #plt.show()
                    if ( verbosity == 1 ):
                        print ("Channel.response.amp: maximum diff in amp is " \
                               + str(max(ampdiff)) + " %"  )
                        print ("Channel.response.phase: maximum diff in phase is " \
                               + str(max(phasediff)) + " radians"  )
    if ( found_matching_epoch == 0 ):
        print ("No corresponding epoch to: " + file1alias + ": " + station_code1 + "." \
            + loc1[i] + "." + chan1[i] + " " + str(start1[i]) + " to " + str(end1[i]) )

