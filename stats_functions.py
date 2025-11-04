import os
import numpy as np
import nibabel as nb

def extract_contrast_volume(all_data):
    # we calculate SN volume and contrast from the processed files
    filesdir='/DataTempVolatile/Friedrich/final/all_images_link/raw/img/'
    maskdir='/DataTempVolatile/Friedrich/final/all_images_link/LC_masks_Max/'
    all_files = os.listdir(filesdir)
    lc_masks = os.listdir(maskdir)
   # all_files, lc_masks = report_missing(all_files, lc_masks) # check what data we have and only select the overlapping
    # we need to extract the relevant names and time points and loop over the subjects and time points to calculate SN
    # volume and contrast
    all_data['LC_contrast']=np.nan
    all_data['LC_volume'] = np.nan
    all_data['LC_max']=np.nan


    for idx in all_data.index:

        #identifying the subject
        subject=all_data[idx,'Subject']
        month=all_data[idx,'visnam']

        #preallocating the different names
        main_name=filesdir+subject+'_'+month+'.nii'
        maskname = maskdir + subject + '_' + month + '_LC.nii'
        if os.path.exists(main_name)&os.path.exists(maskname):
            ponsname=maskdir+subject+'_'+month+'Pons.nii'

            #loading and preparing all relevant data
            main_img=nb.load(main_name).get_fdata()
            mask=nb.load(maskname).get_fdata()
            pons=nb.load(ponsname).get_fdata()

            mask[mask < 0.2] = 0
            pons[pons < 0.2] = 0

            medval=np.median(main_img[mask>0])
            maxval=np.max(main_img[mask>0])
            ponsval=np.median(main_img[pons>0])

            all_data[idx,'LC_volume'] = round(mask.sum())*0.75*0.75*0.75
            all_data[idx,'LC_contrast'] = (medval-ponsval)/ponsval
            all_data[idx, 'max'] = (maxval - ponsval) / ponsval

    return all_data

