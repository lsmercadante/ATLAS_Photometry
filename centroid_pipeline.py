#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#imports

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import photutils as phot
from photutils.centroids import centroid_com, centroid_sources
from photutils.datasets import make_4gaussians_image
from photutils.utils import circular_footprint
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground
from photutils.aperture import aperture_photometry
from photutils.aperture import CircularAperture
import matplotlib.pyplot as plt
from astropy.stats import sigma_clipped_stats
from photutils.aperture import ApertureStats, CircularAperture
from photutils.datasets import make_4gaussians_image
from photutils.aperture import CircularAnnulus
import glob 
import math
import astropy
import sep
import pandas as pd


# In[ ]:


folder_path = '/Users/lilahskye/Desktop/Cosmology_Research/ATLAS_Project/CENTROID/Diff_Images/Diff_images_*'
df1 = pd.read_csv('/Users/lilahskye/Desktop/Cosmology_Research/ATLAS_Project/CENTROID/tns_info_c.csv',sep = ',')


# In[ ]:


# Defining centroid

def centroid_gauss(data, error, mask):
    return phot.centroids.centroid_2dg(data, error, mask)


# In[ ]:


def CENTROID(IMAGE_PATH, RA_TNS, DEC_TNS, SNR_CUT, OUTPUT_ARRAY_X, OUTPUT_ARRAY_Y, SNR_ARRAY, SN_NAME):
    for filename in glob.glob(IMAGE_PATH):
        obs = filename.replace('/Users/lilahskye/Desktop/Cosmology_Research/ATLAS_Project/CENTROID/Diff_Images_'+SN_NAME+'/','').replace('_diff.fits','')
        #print(obs)
        image_hdu = fits.open(filename)
        image_data = image_hdu['image'].data
        header = image_hdu[0].header
        del header['CNPIX1']
        del header['CNPIX2']
        w = WCS(header)
        sitelat = header['SITELAT']
    
        x_in, y_in = w.all_world2pix(RA_TNS,DEC_TNS,0)   # center x position (pixels)
        #RA_in, Dec_in = w.wcs_pix2world(x_in,y_in,0)

        aperture = CircularAperture((x_in, y_in), 3)
        annulus_aperture = CircularAnnulus([x_in,y_in],3,10)
        sigclip = SigmaClip(sigma=3.0, maxiters=10)
        aper_stats = ApertureStats(image_data, aperture, sigma_clip=None)
        bkg_stats = ApertureStats(image_data, annulus_aperture, sigma_clip=sigclip)

        phot_table = aperture_photometry(image_data, aperture)
        aperture_sum = phot_table['aperture_sum']
        noise_std = bkg_stats.std
        SNR = aperture_sum.value[0]/noise_std
        
        err = image_data*0 + noise_std 
        image_data = image_data - bkg_stats.mean

        mask_array = []
        for i in range(0,400):
            mask_row = []
            for j in range(0,400):
                pix_val = image_data[i,j]
                if (i >= 195 and i <= 205) and (j >= 195 and j <= 205):
                   boolian = False
                else:
                    boolian = True
                mask_row.append(boolian)
            mask_array.append(mask_row)

        if SNR < SNR_CUT:
            print('Fails SNR cut')
            continue
        else:
            output = centroid_gauss(image_data, err, mask_array)
            x_out = output[0]
            y_out = output[1]
            print(output)
            print(x_out,y_out)

        if math.isnan(x_out) or math.isnan(y_out):
            print('CENTER NOT FOUND', filename)
            continue
        else:
            RA, Dec = w.wcs_pix2world(x_out,y_out,0)
            OUTPUT_ARRAY_X.append(RA)
            OUTPUT_ARRAY_Y.append(Dec)
            SNR_ARRAY.append(SNR)
            #filename_list_o.append(filename)
            #obs_array_o.append(obs)
            #RA_diff_list_o.append(RA - RA_TNS)
            #DEC_diff_list_o.append(Dec - DEC_TNS)
            #SITE_list_o.append(sitelat)


# In[ ]:


def PIXEL_CUT(OBS_ARRAY,X_ARRAY,Y_ARRAY,OUTPUT_ARRAY_X,OUTPUT_ARRAY_Y):
    for obs in OBS_ARRAY:
        x_val = float(DF_TNS['x'][DF_TNS.Obs == obs])
        y_val = float(DF_TNS['y'][DF_TNS.Obs == obs])
        if x_val < 1000 or x_val > 9500 or y_val < 1000 or y_val > 9500:
            continue
        else:
            index = OBS_ARRAY.index(obs)
            OUTPUT_ARRAY_X.append(X_ARRAY[index])
            OUTPUT_ARRAY_Y.append(Y_ARRAY[index])


# In[ ]:


def SIGMA_CUT(ARRAY, OUTPUT_ARRAY):
    for i in range(0,len(ARRAY)):
        val = ARRAY[i]
        std = np.std(ARRAY)
        std_lim = 3*std
        mean = np.mean(ARRAY)
    if val < (mean + std_lim) or val > (mean - std_lim):
        OUTPUT_ARRAY.APPEND(val)
        #print('Passing x in O:', x_val, SNR, filename)


# In[ ]:


def SIGNIFICANCE(ARRAY, VAL_TNS, VAL_FINAL):
    uncert = np.std(ARRAY)/np.sqrt(len(ARRAY))
    
    if VAL_TNS < (VAL_FINAL - uncert) or VAL_TNS > (VAL_FINAL + uncert):
        print("SIGNIFIGANT POSITION CHANGE")
        out = open(test_out.txt,'w')
        out.write(VAL_FINAL)
        out.close()
    else: 
        print('INSIGNIFICANT POSITION CHANGE')
        out = open(test_out.txt,'w')
        out.write(VAL_TNS)
        out.close()


# In[ ]:


for folder in glob.glob(folder_path):
    SN_name = folder.replace('/Users/lilahskye/Desktop/Cosmology_Research/ATLAS_Project/CENTROID/Diff_Images/Diff_images_','')
    ra_tns = df1['RA(deg)'][df1['Name']== SN_name]
    dec_tns = df1['DEC(deg)'][df1['Name']== SN_name]
    snr_cut = 30

    x_array_o = []
    y_array_o = []
    x_array_c = []
    y_array_c = []
    SNR_array_o = []
    SNR_array_c = []
    o_images = folder + '/*o_diff.fits'
    c_images = folder + '/*c_diff.fits'

    x_array_o2 = []
    y_array_o2 = []
    x_array_c2 = []
    y_array_c2 = []

    x_pass_o = []
    y_pass_o = []
    x_pass_c = []
    y_pass_c = []

    #Centroiding orange images
    CENTROID(o_images,ra_tns,dec_tns,snr_cut,x_array_o,y_array_o, SNR_array_o, SN_name)
    
    #Centroiding cyan images
    CENTROID(c_images,ra_tns,dec_tns, snr_cut, x_array_c, y_array_c, SNR_array_c,SN_name)
    
    #Pixel cut for orange images
    PIXEL_CUT(OBS_ARRAY,x_array_o,y_array_o,x_array_o2,y_array_o2)
    
    #Pixel cut for cyan images
    PIXEL_CUT(OBS_ARRAY,x_array_c,y_array_c,x_array_c2,y_array_c2)

    #Sigma cut for orange images
    SIGMA_CUT(x_array_o2, x_pass_o)
    SIGMA_CUT(y_array_o2,y_pass_o)

    #Sigma cut for cyan images
    SIGMA_CUT(x_array_c2, x_pass_c)
    SIGMA_CUT(y_array_c2,y_pass_c)

    #Final Centroid Values
    x_final_o = np.mean(x_pass_o)
    y_final_o = np.mean(y_pass_o)
    x_final_c = np.mean(x_pass_c)
    y_final_c = np.mean(y_pass_c)

    #Significance check: orange
    SIGNIFICANCE(x_pass_o, ra_tns, x_final_o)
    SIGNIFICANCE(y_pass_o, dec_tns, y_final_o)

    #Significance check: cyan
    SIGNIFICANCE(x_pass_c, ra_tns, x_final_c)
    SIGNIFICANCE(y_pass_c, dec_tns, y_final_c)

    print("Done Centroiding")
