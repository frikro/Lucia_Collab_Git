import os.path

import pandas as pd
import re
from QC import *
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

def preprocess_masks(files,marker,structural_img_folder,orig_ending,output_folder,qc_folder=None):
    #preprocesses Max' files in one file so they are binary images, named homogenously and have the right header
    if qc_folder == None:
        qc_folder='/DataTempVolatile/Friedrich/MATLAB-Drive/MB/Longitudinal/Lucia_Collab_Git/QC'
    #preallocate subjects and months
    unisubs=set([s[:9] for s in os.listdir(files) if not s.startswith('._')])
    months=[f"M{m:02d}" for m in range(0, 97, 12)]
    us = '_'
    for sub in unisubs:
        for month in months:
            #loop through all possible subjects and months and construct the hypothetical names
            main_name=os.path.join(structural_img_folder,sub+us+month+'.nii')#change this if necessary
            outname = os.path.join(output_folder, sub + us + month + us + marker + '.nii.gz')
            #qc_basename=
            if month == 'M00':
               maskname_left = os.path.join(files, sub + us + '0' + us + orig_ending + '.nii.gz')  # change this if necessary
               maskname_right = os.path.join(files,sub + us + '1' + us + orig_ending + '.nii.gz')  # change this if necessary.
            else:
                maskname_left  = os.path.join(files,sub + us + month + us +'0' + us + orig_ending + '.nii.gz')#change this if necessary
                maskname_right = os.path.join(files,sub + us + month + us +'1' + us + orig_ending + '.nii.gz') # change this if necessary.

            if os.path.exists(main_name) and not os.path.exists(outname) and os.path.exists(maskname_left):

                #create a clean new file from the main image header information and the binarized and merged masks
                main_img=nb.load(main_name)
                mask_left=nb.load(maskname_left)
                mask_right = nb.load(maskname_right)
                merged=(mask_left.get_fdata()+mask_right.get_fdata())>0.2
                merged=merged.astype(np.uint8)
                merged_img=nb.Nifti1Image(merged,affine=main_img.affine,header=main_img.header)
                nb.save(merged_img,outname)
                #print('processing '+sub +' at month '+month)
            if os.path.exists(outname):
                qcname=os.path.join(qc_folder,sub+us+month+us+marker)
                plotfsleyes(master_image=main_name,
                            overlay_images=outname,
                            display_overlay=True,
                            file_name=qcname,
                            )


def preprocess_wrapper():
    #create_symbolic_links()
    #import_csv_files(data_path)
    preprocess_masks(files='/DataTempVolatile/Friedrich/final/raw/Max_Masks/segmenter_output_orig_space_delcode_longitudinal',
                     orig_ending='elsi',
                     marker='LC',
                     structural_img_folder='/DataTempVolatile/Friedrich/final/all_images_link/raw/img',
                     output_folder='/DataTempVolatile/Friedrich/final/Longitudinal/Max_masks') #LC masks

    preprocess_masks(files='/DataTempVolatile/Friedrich/final/raw/Max_Masks/pons_refs_imcs_delcode_longitudinal',
                     orig_ending='ref',
                     marker='Pons',
                     structural_img_folder='/DataTempVolatile/Friedrich/final/all_images_link/raw/img',
                     output_folder='/DataTempVolatile/Friedrich/final/Longitudinal/Max_masks') #pons masks
