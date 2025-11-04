import os
import sys
import subprocess

import nibabel as nb
import numpy as np
import tempfile

def plotfsleyes(master_image,overlay_images=None,display_overlay=True,file_name=None,cmap=None,zoom=2500,n_images=9,
                colorbar=False,image_size=None,debug=False,scale=None):
    #this function implements the fsleyes plotting suite and generates a list of images depending on the user
    # requirements

    #set standard parameters
    if cmap is None:
        cmap=['green', 'red', 'blue', 'green', 'greyscale']
    if image_size is None:
        image_size='1920 1080'
    if scale is None:
        scale = 2500
    if file_name is None and debug is False:
        Exception('Please provide an output file name')
    if colorbar is False:
        cbarstr=''
    else:
        cbarstr= '--showColourBar --colourBarLocation right --colourBarLabelSide top-left --colourBarSize 85 '

    if isinstance(overlay_images, str):
        overlay_images = [overlay_images]
    #find the fsleyes location

    result = subprocess.run(
        "echo $FSLDIR",
        shell=True,
        capture_output=True,
        text=True
    )
    fslpath=result.stdout
    if fslpath == '\n':
        if os.path.exists('/home/frkrohn/fsl/bin'):
            fslpath='/home/frkrohn/fsl/bin'
        elif os.path.exists('Users/frkrohn/Applications/FSL/bin'):
            fslpath='Users/frkrohn/Applications/FSL/bin'
        elif os.path.exists('opt/anaconda3/bin'):
            fslpath='opt/anaconda3/bin'
        elif os.path.exists('/Users/frkrohn/anaconda3/bin'):
            fslpath='/Users/frkrohn/anaconda3/bin'
        else:
            Exception('Could not find fsleyes binary')
    if '\n' in fslpath:
        fslpath=fslpath[:fslpath.find('\n')]
    fsleyespath=os.path.join(fslpath,'bin','fsleyes')
    #setting up the whole thing
    overlaystr=master_image+' --overlayType volume --cmap greyscale '

    # check what we should do: generate an overview_image or an ROI
    if overlay_images is None:
        #we render a plain overview image
        output_name=os.path.join(file_name,'_overview.png')
        if not os.path.exists(output_name):
            cmd = (
                f"{fsleyespath} render "
                f"--scene lightbox "
                f"-of {file_name}.png "
                f"{cbarstr}"
                f"--hideCursor "
                f"--size {image_size} "
                f"--zrange 0.18 0.73 "
                f"-ss 0.08 "
                f"{overlaystr}"
            )
            run_cmd(cmd)

    else:
        if len(overlay_images)>2:
            overlay_images=overlay_images[:2]
            Warning('Taking only the first two overlay images')

        #we calculate a ROI from all the images we have
        zrange,xmean,ymean =calculate_center_range(overlay_images)

        #we check the overlap and differences between the first two overlay images if desired
        if len(overlay_images)==2:
            overlay_images = calculate_overlap(overlay_images,fslpath)
        for idx, img in enumerate(overlay_images):
            overlaystr+=(' '+img+ ' --overlayType volume '+ '--alpha 100.0  --cmap '+cmap[idx])
        #we add all info to the overlay string and render!
        zvals= np.linspace(min(zrange), max(zrange), n_images)
        if os.path.exists(file_name):
            os.makedirs(file_name)
        tmp_basename = os.path.basename(os.path.splitext(file_name)[0])
        for idx,zval in enumerate(zvals):
            tmpfname=os.path.join(file_name,tmp_basename+'_'+str(idx)+'.png')
            if os.path.exists(tmpfname):
                pass
            else:
                cmd = ("xvfb-run "
                    f"{fsleyespath} render "
                    f"--scene ortho "
                    f"-of {tmpfname}.png "
                    f"--size {image_size}"
                    f"--xzoom {zoom} --yzoom {zoom} --zzoom {zoom} "
                    f"-vl {str(xmean)} {str(ymean)} {zval}"
                    "--hideCursor "
                    f"{overlaystr}"
                )
                os.system(cmd)

def calculate_overlap(overlays,fslpath):
    tmpdir = tempfile.gettempdir()
    unique_1 = os.path.join(tmpdir,'only_1.nii.gz')
    unique_2 = os.path.join(tmpdir,'only_2.nii.gz')
    overlap = os.path.join(tmpdir,'overlap.nii.gz')

    fslmaths =os.path.join(fslpath,'fslmaths')
    run_cmd([fslmaths, overlays[0], '-sub', overlays[1], '-bin', '-thr', '0', unique_1])
    run_cmd([fslmaths, overlays[1], '-sub', overlays[0], '-bin', '-thr', '0', unique_2])
    run_cmd([fslmaths, overlays[1], '-mas', overlays[0], '-bin', '-thr', '0', overlap])

    new_overlays=[unique_1,unique_2,overlap]
    return new_overlays


def calculate_center_range(images):
    if isinstance(images, str):
        images = [images]
    mins, maxs, xmeans, ymeans = [], [], [], []

    for img in images:
        imgdata = nb.load(img).get_fdata()
        x, y, z = np.nonzero(np.squeeze(imgdata) > 0)
        mins.append(np.min(z))
        maxs.append(np.max(z))
        xmeans.append(np.mean(x))
        ymeans.append(np.mean(y))

    zrange = [float(np.min(mins)), float(np.max(maxs))]
    xmean, ymean = round(np.mean(xmeans)), round(np.mean(ymeans))
    return zrange, xmean, ymean


def run_cmd(cmd):
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()

