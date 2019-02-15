# compare_station_xml
This script will download the stationXML files from IRIS and SIS-production and compares all of the parameters (latitude, longitdue, starttime...) for each channel+location epoch.  The responses are also compared using ObsPy's evalresp.

Python libraries needed: numpy, obspy.


Config parameters are at the top of the file, change them if you like.
```
thresh_lat_lon_m = 0.1       # in meters
thresh_elev = 0.1            # in meters
thresh_dep = 0.1             # in meters
thresh_response_amp = 0.01   # as a percent
thresh_response_phase = 0.01 # in radians
verbosity = 0
```

Example of failed request because station isn't in SIS or IRIS:
```
ahutko@namazu:~/STATION_XML_COMPARE$ 
ahutko@namazu:~/STATION_XML_COMPARE$ ./compare_station_xml.py UW.ALKI

SIS file: https://files.anss-sis.scsn.org/production/FDSNstationXML/UW/UW_ALKI.xml
IRIS file: https://service.iris.edu/fdsnws/station/1/query?net=UW&sta=ALKI&level=response&format=xml&includecomments=true&nodata=404

SIS stationXML file download failed

ahutko@namazu:~/STATION_XML_COMPARE$ 
```

To show what execution and output looks like, this example used a fudged IRIS stationXML file with verbosity = 0 (only ouput parameters that failed the check):
```
ahutko@namazu:~/STATION_XML_COMPARE$ 
ahutko@namazu:~/STATION_XML_COMPARE$ 
ahutko@namazu:~/STATION_XML_COMPARE$ ./compare_station_xml.py UW.ASR

SIS file: https://files.anss-sis.scsn.org/production/FDSNstationXML/UW/UW_ASR.xml
IRIS file: https://service.iris.edu/fdsnws/station/1/query?net=UW&sta=ASR&level=response&format=xml&includecomments=true&nodata=404

/home/ahutko/anaconda3/lib/python3.6/site-packages/obspy/io/stationxml/core.py:84: UserWarning: The StationXML file has version 2.2, ObsPy can deal with version 1.0. Proceed with caution.
  root.attrib["schemaVersion"], SCHEMA_VERSION))


Comparing  (SIS): ASR..EHZ 1982-09-01 00:00:00 to 1982-09-30 00:00:00
          (IRIS): ASR..EHZ 1982-09-02 00:00:00 to 1982-09-30 00:00:00
WARNING: ASR..EHZ starttimes not matching  (SIS): 1982-09-01 00:00:00  (IRIS): 1982-09-02 00:00:00
Channel.Latitude: fail, 46.152592  (SIS) not within 1e-05 of 6.152592 (IRIS)
Channel.Longitude: fail, -121.601639  (SIS) not within 1e-05 of -21.601639 (IRIS)
Channel.Elevation: fail, 1357.0  (SIS) not within 0.01 of 357.0 (IRIS)
Channel.Depth: fail, 0.0  (SIS) not within 0.01 of 9.0 (IRIS)
Channel.Azimuth: fail, 0.0  (SIS) not within 0.01 of 9.0 (IRIS)
Channel.SampleRate: fail, 100.0  (SIS) not within 0.001 of 500.0 (IRIS)
ClockDrift is missing from  (SIS) and = 0.0001 in (IRIS)
Channel.response.amp: fail, max(diff_in_amp) of 59.8746203166 % not within 0.01
Channel.response.phase: fail, max(diff_in_phase) of 65.9138034161 radians not within 0.01


Comparing  (SIS): ASR..EHZ 1982-09-30 00:00:00 to 1982-10-10 00:00:00
          (IRIS): ASR..EHZ 1982-09-30 00:00:00 to 1982-10-10 00:00:00
ClockDrift is missing from  (SIS) and = 0.0001 in (IRIS)
Number of response stages don't match: 4 in  (SIS), 5 in (IRIS)


Comparing  (SIS): ASR..EHZ 1982-10-10 00:00:00 to 1983-10-23 00:00:00
          (IRIS): ASR..EHZ 1982-10-10 00:00:00 to 1983-10-23 00:00:00
ClockDrift is missing from  (SIS) and = 0.0001 in (IRIS)
...
```
To show what output looks like, this example used a fudged IRIS stationXML file with verbosity = 1 (ouput all parameters checked):
```
ahutko@namazu:~/STATION_XML_COMPARE$ 
ahutko@namazu:~/STATION_XML_COMPARE$ 
ahutko@namazu:~/STATION_XML_COMPARE$ ./compare_station_xml.py UW.ASR

SIS file: https://files.anss-sis.scsn.org/production/FDSNstationXML/UW/UW_ASR.xml
IRIS file: https://service.iris.edu/fdsnws/station/1/query?net=UW&sta=ASR&level=response&format=xml&includecomments=true&nodata=404

/home/ahutko/anaconda3/lib/python3.6/site-packages/obspy/io/stationxml/core.py:84: UserWarning: The StationXML file has version 2.2, ObsPy can deal with version 1.0. Proceed with caution.
  root.attrib["schemaVersion"], SCHEMA_VERSION))


Comparing  (SIS): ASR..EHZ 1982-09-01 00:00:00 to 1982-09-30 00:00:00
          (IRIS): ASR..EHZ 1982-09-02 00:00:00 to 1982-09-30 00:00:00
WARNING: ASR..EHZ starttimes not matching  (SIS): 1982-09-01 00:00:00  (IRIS): 1982-09-02 00:00:00
Channel.Latitude: fail, 46.152592  (SIS) not within 1e-05 of 6.152592 (IRIS)
Channel.Longitude: fail, -121.601639  (SIS) not within 1e-05 of -21.601639 (IRIS)
Channel.Elevation: fail, 1357.0  (SIS) not within 0.01 of 357.0 (IRIS)
Channel.Depth: fail, 0.0  (SIS) not within 0.01 of 9.0 (IRIS)
Channel.Azimuth: fail, 0.0  (SIS) not within 0.01 of 9.0 (IRIS)
Channel.SampleRate: fail, 100.0  (SIS) not within 0.001 of 500.0 (IRIS)
ClockDrift is missing from  (SIS) and = 0.0001 in (IRIS)
Channel.response.amp: fail, max(diff_in_amp) of 59.8746203166 % not within 0.01
Channel.response.phase: fail, max(diff_in_phase) of 65.9138034161 radians not within 0.01
Channel.response.amp: maximum diff in amp is 59.8746203166 %
Channel.response.phase: maximum diff in phase is 65.9138034161 radians


Comparing  (SIS): ASR..EHZ 1982-09-30 00:00:00 to 1982-10-10 00:00:00
          (IRIS): ASR..EHZ 1982-09-30 00:00:00 to 1982-10-10 00:00:00
Channel.Latitude: pass
Channel.Longitude: pass
Channel.Elevation: pass
Channel.Depth: pass
Channel.Azimuth: pass
Channel.SampleRate: pass
ClockDrift is missing from  (SIS) and = 0.0001 in (IRIS)
Number of response stages don't match: 4 in  (SIS), 5 in (IRIS)


Comparing  (SIS): ASR..EHZ 1982-10-10 00:00:00 to 1983-10-23 00:00:00
          (IRIS): ASR..EHZ 1982-10-10 00:00:00 to 1983-10-23 00:00:00
Channel.Latitude: pass
Channel.Longitude: pass
Channel.Elevation: pass
Channel.Depth: pass
Channel.Azimuth: pass
Channel.SampleRate: pass
ClockDrift is missing from  (SIS) and = 0.0001 in (IRIS)
Channel.response.amp: maximum diff in amp is 0.00792423036261 %
Channel.response.phase: maximum diff in phase is 1.7763568394e-13 radians

...
```

