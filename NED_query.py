import numpy as np
import pandas as pd
import wget
import time

path = '/Users/lilahskye/Desktop/Cosmology_Research/ATLAS_Project/'
filename = 'events_roundedz_001.csv' 
df = pd.read_csv(path + filename, sep = ',')

SN_name_list = df['CID']

for i in range(0,len(SN_name_list)):
    time.sleep(3)
    SN_name = SN_name_list[i]
    url = 'http://ned.ipac.caltech.edu/cgi-bin/objsearch?search_type=Near+Name+Search&objname=SN+{OBJECT_NAME}&radius=1.0&out_csys=Equatorial&out_equinox=J2000.0&obj_sort=Distance+to+search+center&of=ascii_bar'.format(OBJECT_NAME = SN_name) 
    filename = wget.download(url, out = 'NED/{OBJECT_NAME}.txt'.format(OBJECT_NAME = SN_name))
    filename
