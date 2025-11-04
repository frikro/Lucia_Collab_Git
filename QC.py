import os
import sys
import subprocess
import nibabel as nb
import numpy as np

def plotfsleyes(master_image,overlay_images=None,display_overlay=True,file_name=None,cmap=None,zoom=2500,n_images=9,image_size=None,debug=False,scale=None):
    #this function implements the fsleyes plotting suite and generates a list of images depending on the user
    # requirements

    #set standard parameters
    if cmap is None:
        cmap=['green', 'red', 'blue', 'green', 'greyscale']
    if image_size is None:
        image_size='1920 1080'
    if scale is None:
        scale = 2500

    #find the fsleyes location

    result = subprocess.run(
        "echo $FSLDIR",
        shell=True,
        capture_output=True,
        text=True
    )
    fslpath=result.stdout
    if fslpath == '/n':
        if os.path.exists('/home/frkrohn/fsl/bin/fsleyes'):
            fslpath='/home/frkrohn/fsl/bin/fsleyes'
        elif os.path.exists('Users/frkrohn/Applications/FSL/bin/fsleyes'):
            fslpath='Users/frkrohn/Applications/FSL/bin/fsleyes'
        elif os.path.exists('opt/anaconda3/bin/fsleyes'):
            fslpath='opt/anaconda3/bin/fsleyes'
        elif os.path.exists('/Users/frkrohn/anaconda3/bin/fsleyes'):
            fslpath='/Users/frkrohn/anaconda3/bin/fsleyes'
        else:
            Exception('Could not find fsleyes binary')

    #setting up the whole thing
    overlaystr=master_image+' --overlayType volume --cmap greyscale'

    # check what we should do: generate an overview_image or an ROI
    if overlay_images is None:
        #we render a plain overview image
        pass
    else:
        if len(overlay_images)>2:
            overlay_images=overlay_images[:2]
            Warning('Taking only the first two overlay images')
        #we calculate a ROI from all the images we have

        #we check the overlap and differences between the first two overlay images if desired

        #we render the main image with overlays or not depending on the requirements




def calculate_center_range(overlay_images):
    pass

def render_images(overlay_string):
    pass