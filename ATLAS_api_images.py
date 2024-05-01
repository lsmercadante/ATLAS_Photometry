import io
import os
import sys
import time
import numpy as np
import pandas as pd
import requests
import csv

#reading in data frame
df1 = pd.read_csv('events_post_cuts_012224.csv')
RA_list = df1['RA']   # list of RA values in deg
DEC_list = df1['DEC'] # list of DEC values in deg
dates_list = df1['PKMJD']   # dates in mjd
names = df1['CID']   # names of supernova
z_list = df1['zHEL']
list_length = np.arange(0,len(names),1)
#print(len(names))
BASEURL = "https://fallingstar-data.com/forcedphot"

ATLAS_files_list = []
names_pass = []
RA_pass = []
DEC_pass = []
MJD_pass = []
z_pass = []



resp = requests.post(url=f"{BASEURL}/api-token-auth/", data={'username':" lmercadante", 'password': "Supernovas2000"})
if resp.status_code == 200:
    token = resp.json()['token']
    print(f'Your token is {token}')
    headers = {'Authorization': f'Token {token}', 'Accept': 'application/json'}
else:
    print(f'ERROR {resp.status_code}')
    print(resp.json())

done_list = open('ATLAS_done.txt','r').readlines()
done_list = np.array([dl.rstrip() for dl in done_list])
print(done_list)


#output_list = open("ATLAS_API_OUTPUT/RAW_DATA/file_list.csv", 'a')
#header = ['File_Name', 'SN_Name']
#csvwriter = csv.writer(output_list)
#csvwriter.writerow(header)

#no_z_list = open('ATLAS_API_OUTPUT/SNIA_no_z.txt','r').readlines()
#no_z_list = np.array([dl.rstrip() for dl in no_z_list])

for i in range(0,200,1):
    event_RA = RA_list[i]
    event_DEC = DEC_list[i]
    event_name = names[i]
    event_MJD = dates_list[i]
    event_z = z_list[i]
#    if event_z =='None':
        
    if event_name in done_list:
        print(event_name,'ALREADY DONE')
        continue
    
 #   if event_name in no_z_list:
 #       print(event_name, 'ALREADY DONE')
 #       continue 

    if event_z=='None':
        print('WARNING: SKIPPING ',event_name,' BECAUSE NO Z')
        no_z_file = open('ATLAS_API_OUTPUT/SNIA_no_z.txt','a')
        no_z_file.write(str(event_name+"\n"))
        no_z_file.close()
        continue
    #done_file=open('ATLAS_done.txt','a')
    print('STARTING ',event_name)
    task_url = None
    while not task_url:
        with requests.Session() as s:
            resp = s.post(f"{BASEURL}/queue/", headers=headers, data={'ra': RA_list[i], 'dec': DEC_list[i], 'mjd_min': dates_list[i]-50.0, 'mjd_max':dates_list[i]+210.0,'send_email': False})

            if resp.status_code == 201:  # successfully queued
                task_url = resp.json()['url']
                image_url = task_url + 'requestimages'
                print(f'The task URL is {task_url}')
            elif resp.status_code == 429:  # throttled
                message = resp.json()["detail"]
                print(f'{resp.status_code} {message}')
                t_sec = re.findall(r'available in (\d+) seconds', message)
                t_min = re.findall(r'available in (\d+) minutes', message)
                if t_sec:
                    waittime = int(t_sec[0])
                elif t_min:
                    waittime = int(t_min[0]) * 60
                else:
                    waittime = 10
                print(f'Waiting {waittime} seconds')
                time.sleep(waittime)
            else:
                print(f'ERROR {resp.status_code}')
                print(resp.json())
                sys.exit()
    result_url = None
    while not result_url:
        with requests.Session() as s:
            resp = s.get(task_url, headers=headers)
            resp2 = s.get(image_url, headers=headers)

            if resp.status_code == 200:  # HTTP OK
                if resp.json()['finishtimestamp']:
                    result_url = resp.json()['result_url']
                    print(f"Task is complete with results available at {result_url}")
                    break
                elif resp.json()['starttimestamp']:
                    print(f"Task is running (started at {resp.json()['starttimestamp']})")
                else:
                    print("Waiting for job to start. Checking again in 10 seconds...")
                time.sleep(10)
            else:
                print(f'ERROR {resp.status_code}')
                print(resp.json())
                sys.exit()
    result_image_url = None
    while not result_image_url:
        with requests.Session() as s:
            image_url = task_url + 'requestimages'
            print("TASK URL IM:",task_url)
            print("IMAGE URL:",image_url)
            resp2 = s.get(image_url, headers=headers)

            if resp2.status_code == 200:  # HTTP OK
                image_result = resp2.json()['results']
                print(image_result)
                if image_result[3]['finishtimestamp']:
                    print(image_result[3]['finishtimestamp'])
                    parent_id = image_result[0]['parent_task_id']
                    result_image_url = 'https://fallingstar-data.com/forcedphot/static/results/job{id}.zip'.format(id = parent_id)
                    print('Result Image URL:',result_image_url)
                    print(f"Task is complete with results available at {result_image_url}")
                    break
                elif image_result[3]['starttimestamp']:
                    print(f"Task is running (started at {image_result[3]['starttimestamp']})")
                else:
                    print("Waiting for job to start. Checking again in 10 seconds...")
                    time.sleep(10)
    if result_url ==None:
        print('NO DATA')
        done_file=open('ATLAS_done.txt','a')
        done_file.write(str(event_name)+"\n")
        done_file.close()
        continue
                                            
    with requests.Session() as s:
        textdata = s.get(result_url, headers=headers).text
        os.system('source image_get.sh CENTROID/Diff_Images2/Diff_Images_{NAME}.zip  https://fallingstar-data.com/forcedphot/static/results/job{id}.zip'.format(NAME = event_name, id = parent_id))


    with requests.Session() as s:
        textdata = s.get(result_url, headers=headers).text


    # if we'll be making a lot of requests, keep the web queue from being
    # cluttered (and reduce server storage usage) by sending a delete operation
    # s.delete(task_url, headers=headers).json()
    dfresult = pd.read_csv(io.StringIO(textdata.replace("###", "")), delim_whitespace=True)
    print(type(dfresult))
    dfresult.to_csv('CENTROID/RAW_DATA/RAW_DATA_3/{}.csv'.format(names[i]))
    print(dfresult)
    
    names_pass.append(event_name)
    RA_pass.append(event_RA)
    DEC_pass.append(event_DEC)
    MJD_pass.append(event_MJD)
    z_pass.append(event_z)
    
    output_list = open("CENTROID/RAW_DATA/RAW_DATA_3/file_list.csv", 'a')
    csvwriter = csv.writer(output_list)
    filename = '{}.csv'.format(event_name)
    row = [filename,event_name]
    csvwriter.writerow(row)

    with open("CENTROID/RAW_DATA/RAW_DATA_3/TNS_raw.csv", 'a') as csvfile2:
        csvwriter = csv.writer(csvfile2)
        row = [str(event_name),event_RA,event_DEC,event_MJD,event_z]
        csvwriter.writerow(row)
    
    done_file=open('ATLAS_done.txt','a')
    done_file.write(str(event_name)+"\n")
    done_file.close()

#with open("ATLAS_API_OUTPUT/RAW_DATA/TNS_raw.csv", 'a') as csvfile:
    #header = ['Name','RA(deg)','DEC(deg)','MJD','SN_Redshift']
#    csvwriter = csv.writer(csvfile)
    #csvwriter.writerow(header)
#    for i in range(0,len(names_pass),1):
#        row = [str(names_pass[i]),RA_pass[i],DEC_pass[i],MJD_pass[i],z_pass[i]]
#        csvwriter.writerow(row)


    #ATLAS_files_list.append(filename)
    #names_pass.append(names[i])

#with open("ATLAS_API_OUTPUT/RAW_DATA/file_list.csv", 'w') as csvfile:
#    header = ['File_Name', 'SN_Name']
#    csvwriter = csv.writer(csvfile)
#    csvwriter.writerow(header)
#    for i in range(0,len(ATLAS_files_list)):
#        row = [ATLAS_files_list[i],names_pass[i]]
#        csvwriter.writerow(row)
