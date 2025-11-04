import os
import sys
import subprocess
import nibabel as nb
import numpy as np

def plotfsleyes(master_image,overlay_images=None,display_overlay=True,file_name=None,cmap=None,zoom=2500,n_images=9,colorbar=False,image_size=None,debug=False,scale=None):
    #this function implements the fsleyes plotting suite and generates a list of images depending on the user
    # requirements

    #set standard parameters
    if cmap is None:
        cmap=['green', 'red', 'blue', 'green', 'greyscale']
    if image_size is None:
        image_size=['1920',' 1080']
    if scale is None:
        scale = 2500
    if file_name is None and debug is False:
        Exception('Please provide an output file name')
    if colorbar is False:
        cbarstr=''
    else:
        cbarstr= ['--showColourBar --colourBarLocation right --colourBarLabelSide top-left --colourBarSize 85 '].split()
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
    overlaystr=master_image+' --overlayType volume --cmap greyscale '

    # check what we should do: generate an overview_image or an ROI
    if overlay_images is None:
        #we render a plain overview image
        if not file_name.exists():
            cmd = [
                      str(fsleyes_path), 'render',
                      '--scene', 'lightbox',
                      '-of', str(outputname),
                      cbarstr,
                      '--hideCursor',
                      '--size', image_size,
                      '--zrange', '0.18', '0.73',
                      '-ss', '0.08'
                  ] + overlaystr.split()
            run_cmd(cmd)
        pass
    else:
        if len(overlay_images)>2:
            overlay_images=overlay_images[:2]
            Warning('Taking only the first two overlay images')

        #we calculate a ROI from all the images we have

        zrange,xmean,ymean =calculate_center_range(overlay_images)

        #we check the overlap and differences between the first two overlay images if desired
        if len(overlay_images)==2:
            overlay_images = calculate_overlap(overlay_images)
        for img,idx in enumerate(overlay_images):
            overlaystr.append(' '+img+ ' --overlayType volume+', '--alpha 100.0  --cmap '+img+cmap[idx])
        #we add all info to the overlay string and render!



def calculate_overlap(overlays):
    tmpdir = Path(gettempdir())
    unique_1 = tmpdir / 'only_1.nii.gz'
    unique_2 = tmpdir / 'only_2.nii.gz'
    overlap = tmpdir / 'overlap.nii.gz'

    fslmaths = Path(os.getenv('FSLDIR', '/usr/local/fsl')) / 'bin' / 'fslmaths'
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
        imgdata = nib.load(img).get_fdata()
        x, y, z = np.nonzero(imgdata > 0)
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