import io
import os
import sys
import time
import json
import pandas as pd
import requests
import subprocess

BASEURL = "https://fallingstar-data.com/forcedphot"

resp = requests.post(url=f"{BASEURL}/api-token-auth/", data={'username':" lmercadante", 'password': "Supernovas2000"})

if resp.status_code == 200:
    token = resp.json()['token']
    print(f'Your token is {token}')
    headers = {'Authorization': f'Token {token}', 'Accept': 'application/json'}
else:
    print(f'ERROR {resp.status_code}')
    print(resp.json())

name = '2022uqd_c_30'

task_url = None
while not task_url:
    with requests.Session() as s:
        resp = s.post(f"{BASEURL}/queue/", headers=headers, data={'ra': 41.650501320151335, 'dec': 4.9221715656809515, 'mjd_min': 59825., 'mjd_max': 59925., 'send_email': False})

        if resp.status_code == 201:  # successfully queued
            task_url = resp.json()['url']
            image_url = task_url + 'requestimages'
            print(f'The task URL is {task_url}')
            print(image_url)
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
        if resp.status_code == 200:  # HTTP OK
            if resp.json()['finishtimestamp']:
                result_url = resp.json()['result_url']
                print(f"Task is complete with results available at {result_url}")
                #print('TASK URL: ', task_url)
                #print('Image Result URL: ', result_image_url)
            
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
                #os.system('wget -O test/test.zip {URL}'.format(NAME = name,URL = result_image_url))
                break
            elif image_result[3]['starttimestamp']:
                print(f"Task is running (started at {image_result[3]['starttimestamp']})")
            else:
                 print("Waiting for job to start. Checking again in 10 seconds...")
                 time.sleep(10)
with requests.Session() as s:
    textdata = s.get(result_url, headers=headers).text
    os.system('source image_get.sh https://fallingstar-data.com/forcedphot/static/results/job{id}.zip'.format(id = parent_id))

        
    #time.sleep(60)
    #os.system('wget -O test/test.zip https://fallingstar-data.com/forcedphot/static/results/job{id}.zip'.format(id = parent_id)) 
    
    #print(imagedata.content)
    #fd = open('test/test.zip','wb')
    #fd.write(imagedata.content)
    #fd.close()
    # if we'll be making a lot of requests, keep the web queue from being
    # cluttered (and reduce server storage usage) by sending a delete operation
    # s.delete(task_url, headers=headers).json()
dfresult = pd.read_csv(io.StringIO(textdata.replace("###", "")), delim_whitespace=True)
print(dfresult)

#print(task_url)
#image_url = task_url+'requestimages'
#os.system('wget '+image_url)

#dfresult.to_csv('CENTROIDING/RAW_DATA/{}.csv'.format(name))
