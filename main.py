#this file contains functions for the collaboration with Lucia

########################################################################################################################
########################################################################################################################
######################################################setting up########################################################
########################################################################################################################
########################################################################################################################
import os
import pandas as pd
import re
import subprocess
import numpy as np
import nibabel as nb
########################################################################################################################
########################################################################################################################
######################################################extract/manage data###############################################
########################################################################################################################
########################################################################################################################
def create_symbolic_links():
    #here we want to create symbolic links so Max' files are all in the symbolic links folder for easier access

    #create files
    old_path = '/DataTempVolatile/Friedrich/final/Longitudinal/Max_masks_longitudinal/'
    new_path = '/DataTempVolatile/Friedrich/final/all_images_link/LC_masks_Max/'
    files = os.listdir(old_path)

    for file in files:
        if '_M' in file:
            new_filename = new_path + file.removesuffix('_vis.nii.gz') + '_LC_Max.nii.gz'
        else:
            new_filename = new_path + file.removesuffix('_vis.nii.gz') + '_M00_LC_Max.nii.gz'
        if os.path.exists(new_filename):
            pass
        else:
            old_filename = old_path + file
            os.symlink(old_filename, new_filename)
            #print("processing "+file.removesuffix('_vis.nii.gz'))


def import_csv_files(data_path):
    #here we import all csv files from the former longitudinal csv files and merge them into one big file
    file_path = '/storage/DataTempVolatile/Friedrich/MATLAB-Drive/MB/Longitudinal/'
    file_list = sorted([s for s in os.listdir(file_path) if 'long_raw' in s])
    df_all = pd.concat(
        [
            pd.read_csv(os.path.join(file_path, f)).assign(
                Timepoint=re.search(r"M\d+", f).group(0)  # extract 'M00', 'M12', etc.
            )
            for f in file_list
        ],
        ignore_index=True
    )
    df_all.to_csv("longitudinal_combined.csv", index=False)

def merge_pons_masks():


    # --- Setup ---
    basepath = "/storage/DataTempVolatile/Friedrich/final/Longitudinal/pons_refs_imcs_delcode_longitudinal/"
    file_list = [f for f in os.listdir(basepath) if f.endswith("_ref.nii.gz")]

    # --- Extract unique subject IDs (first 9 chars) ---
    rawsubs = set(f[:9] for f in file_list)

    # --- Timepoints ---
    months = ['M00'] + [f"M{str(m).zfill(2)}" for m in range(12, 97, 12)]

    # --- Main Loop ---
    for subject in rawsubs:
        for i, month in enumerate(months):
            if month == 'M00':
                left = f"{basepath}{subject}_0_ref.nii.gz"
                right = f"{basepath}{subject}_1_ref.nii.gz"
            else:
                left = f"{basepath}{subject}_0_{month}_ref.nii.gz"
                right = f"{basepath}{subject}_1_{month}_ref.nii.gz"

            outfile = f"{basepath}{subject}_{month}.nii.gz"

            # Merge if both inputs exist and output does not
            if os.path.exists(left) and os.path.exists(right) and not os.path.exists(outfile):
                cmd = ['fslmaths', left, '-add', right, outfile]
                subprocess.run(cmd, check=True)


########################################################################################################################
########################################################################################################################
#########################################statistics#####################################################################
########################################################################################################################
########################################################################################################################


def extract_contrast_volume(all_data):
    # we calculate SN volume and contrast from the processed files
    filesdir='/DataTempVolatile/Friedrich/final/all_images_link/raw/img/'
    maskdir='/DataTempVolatile/Friedrich/final/all_images_link/LC_masks_Max/'
    all_files = os.listdir(filesdir)
    lc_masks = os.listdir(maskdir)
    all_files, lc_masks = report_missing(all_files, lc_masks) # check what data we have and only select the overlapping
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

            medval=np.median(main[mask>0])
            maxval=np.max(main[mask>0])
            ponsval=np.median(main[pons>0])

            all_data[idx,'LC_volume'] = round(mask.sum())*0.75*0.75*0.75
            all_data[idx,'LC_contrast'] = (medval-ponsval)/ponsval
            all_data[idx, 'max'] = (maxval - ponsval) / ponsval

    return all_data

def report_missing(all_files, lc_masks):
    # we try to find missing data in Max's LC data and all available data and report it for QC and for our friend to know!

    # extract the raw file name from the LC and compare the two stripped lists
    raw_basenames = {f.replace('.nii', '') for f in all_files}
    lcmax_basenames = {f.replace('_LC_Max.nii.gz', '') for f in lc_masks}
    missing_in_lcmax = raw_basenames - lcmax_basenames
    missing_in_raw = lcmax_basenames - raw_basenames
    intersecting = raw_basenames & lcmax_basenames
    if len(intersecting) < len(all_files):
        # if there are missing data we want to work only with the intersection, and we record all missing data

        # Save missing raw file names to text
        if len(missing_in_lcmax) > 0:
            print(f"{str(len(missing_in_lcmax))} subjects were missing in Max' data!")
            with open("missing_LC_Max_files.txt", "w") as f:
                for name in sorted(missing_in_lcmax):
                    f.write(f"{name}_LC_Max.nii.gz\n")

        # Save missing raw file names to text
        if len(missing_in_raw) > 0:
            print(f"{str(len(missing_in_raw))} subjects were missing in raw data!")
            with open("missing_raw_files.txt", "w") as f:
                for name in sorted(missing_in_raw):
                    f.write(f"{name}.nii.gz\n")

        all_files = [f for f in all_files if f.replace('.nii', '') in intersecting]
        lc_masks = [f for f in lc_masks if f.replace('_LC_Max.nii.gz', '') in intersecting]
    return all_files, lc_masks
########################################################################################################################
########################################################################################################################
######################################################main function#####################################################
########################################################################################################################
########################################################################################################################

def main():
    #setting everything up
    all_data=pd.read_csv('data/longitudinal_combined.csv')
    create_symbolic_links()
    data_path = "/DataTempVolatile/Friedrich/MATLAB-Drive/MB/Longitudinal/Python_project_extract_LC_data/longitudinal_combined.csv"

    if os.path.exists(data_path):
        pass
    else:
        import_csv_files(data_path)



    # 1. extract LC volume and contrast
    extract_contrast_volume()

if __name__ == "__main__":
    main()
#   extract the individual data
#
#2. morph the masks to template space
#3. create a longitudinal pipeline
