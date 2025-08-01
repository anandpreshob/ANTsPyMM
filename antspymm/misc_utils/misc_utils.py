"""
Misc_Utils functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

# Standard library imports
import os
import numpy as np
import pandas as pd

# Conditional imports
try:
    import ants
except ImportError:
    ants = None

# is_bst_region
    def is_bst_region(filename):
        return filename[-4:] == '.bst'

    # Read the statistical file
    zz = statistical_df 
    
    # Read the data dictionary from a CSV file
    mydict = data_dictionary
    mydict = mydict[~mydict['Measurement'].str.contains("tractography-based connectivity", na=False)]
    mydict2=mydict.copy()
    mydict2['tidynames']=mydict2['tidynames'].str.replace(".left","")
    mydict2['tidynames']=mydict2['tidynames'].str.replace(".right","")

    statistical_df['anat'] = statistical_df['anat'].str.replace("_", ".", regex=True)

    # Load image and process it
    edgeimg = ants.iMath(brain_image,"Normalize")
    if edge_image_dilation > 0:
        edgeimg = ants.iMath( edgeimg, "MD", edge_image_dilation)

    # Define lists and data frames
    postfix = ['bf', 'cit168lab', 'mtl', 'cerebellum', 'dkt_cortex','brainstem','JHU_wm','yeo']
    atlas = ['BF', 'CIT168', 'MTL', 'TustisonCobra', 'desikan-killiany-tourville','brainstem','JHU_wm','yeo']
    postdesc = ['nbm3CH13', 'CIT168_Reinf_Learn_v1_label_descriptions_pad', 'mtl_description', 'cerebellum', 'dkt','CIT168_T1w_700um_pad_adni_brainstem','FA_JHU_labels_edited','ppmi_template_500Parcels_Yeo2011_17Networks_2023_homotopic']
    templateprefix = '~/.antspymm/PPMI_template0_'
    # Iterate through columns and create figures
    col2viz = 'values'
    if True:
        anattoshow = zz['anat'].unique()
        if verbose > 0:
            print(col2viz)
            print(anattoshow)
        # Rest of your code for figure creation goes here...
        addem = edgeimg * 0
        for k in range(len(anattoshow)):
            if verbose > 0 :
                print(str(k) +  " " + anattoshow[k]  )
            mysub = zz[zz['anat'].str.contains(anattoshow[k])]
            anatsear=shorten_pymm_names( anattoshow[k] )
            anatsear=re.sub(r'[()]', '.', anatsear )
            anatsear=re.sub(r'\.\.', '.', anatsear )
            anatsear=re.sub("dti.mean.md.snc","md.snc",anatsear)
            anatsear=re.sub("dti.mean.fa.snc","fa.snc",anatsear)
            anatsear=re.sub("dti.mean.md.snr","md.snr",anatsear)
            anatsear=re.sub("dti.mean.fa.snr","fa.snr",anatsear)
            anatsear=re.sub("dti.mean.md.","",anatsear)
            anatsear=re.sub("dti.mean.fa.","",anatsear)
            anatsear=re.sub("dti.md.","",anatsear)
            anatsear=re.sub("dti.fa.","",anatsear)
            anatsear=re.sub("dti.md","",anatsear)
            anatsear=re.sub("dti.fa","",anatsear)
            anatsear=re.sub("cbf.","",anatsear)
            anatsear=re.sub("rsfmri.fcnxpro122.","",anatsear)
            anatsear=re.sub("rsfmri.fcnxpro129.","",anatsear)
            anatsear=re.sub("rsfmri.fcnxpro134.","",anatsear)
            anatsear=re.sub("t1hier.vollravg","",anatsear)
            anatsear=re.sub("t1hier.volasym","",anatsear)
            anatsear=re.sub("t1hier.thkasym","",anatsear)
            anatsear=re.sub("t1hier.areaasym","",anatsear)
            anatsear=re.sub("t1hier.vol.","",anatsear)
            anatsear=re.sub("t1hier.thk.","",anatsear)
            anatsear=re.sub("t1hier.area.","",anatsear)
            anatsear=re.sub("t1.volasym","",anatsear)
            anatsear=re.sub("t1.thkasym","",anatsear)
            anatsear=re.sub("t1.areaasym","",anatsear)
            anatsear=re.sub("t1.vol.","",anatsear)
            anatsear=re.sub("t1.thk.","",anatsear)
            anatsear=re.sub("t1.area.","",anatsear)
            anatsear=re.sub("asymdp.","",anatsear)
            anatsear=re.sub("asym.","",anatsear)
            anatsear=re.sub("asym","",anatsear)
            anatsear=re.sub("lravg.","",anatsear)
            anatsear=re.sub("lravg","",anatsear)
            anatsear=re.sub("dktcortex","",anatsear)
            anatsear=re.sub("dktregions","",anatsear)
            anatsear=re.sub("_",".",anatsear)
            anatsear=re.sub("superior","sup",anatsear)
            anatsear=re.sub("cerebellum","",anatsear)
            anatsear=re.sub("brainstem","",anatsear)
            anatsear=re.sub("t.limb.int","t.int",anatsear)
            anatsear=re.sub("paracentral","paracent",anatsear)
            anatsear=re.sub("precentral","precent",anatsear)
            anatsear=re.sub("postcentral","postcent",anatsear)
            anatsear=re.sub("sup.cerebellar.peduncle","sup.cereb.ped",anatsear)
            anatsear=re.sub("inferior.cerebellar.peduncle","inf.cereb.ped",anatsear)
            anatsear=re.sub(".crossing.tract.a.part.of.mcp.","",anatsear)
            anatsear=re.sub(".crossing.tract.a.part.of.","",anatsear)
            anatsear=re.sub(".column.and.body.of.fornix.","",anatsear)
            anatsear=re.sub("fronto.occipital.fasciculus.could.be.a.part.of.ant.internal.capsule","frnt.occ",anatsear)
            anatsear=re.sub("inferior.fronto.occipital.fasciculus.could.be.a.part.of.anterior.internal.capsule","inf.frnt.occ",anatsear)
            anatsear=re.sub("fornix.cres.stria.terminalis.can.not.be.resolved.with.current.resolution","fornix.column.and.body.of.fornix",anatsear)
            anatsear=re.sub("external.capsule","ext.cap",anatsear)
            anatsear=re.sub(".jhu.icbm.labels.1mm","",anatsear)
            anatsear=re.sub("dp.",".",anatsear)
            anatsear=re.sub(".mtg.sn.snc.",".snc.",anatsear)
            anatsear=re.sub(".mtg.sn.snr.",".snr.",anatsear)
            anatsear=re.sub("mtg.sn.snc.",".snc.",anatsear)
            anatsear=re.sub("mtg.sn.snr.",".snr.",anatsear)
            anatsear=re.sub("mtg.sn.snc",".snc.",anatsear)
            anatsear=re.sub("mtg.sn.snr",".snr.",anatsear)
            anatsear=re.sub("anterior.","ant.",anatsear)
            anatsear=re.sub("rsf.","",anatsear)
            anatsear=re.sub("fcnxpro122.","",anatsear)
            anatsear=re.sub("fcnxpro129.","",anatsear)
            anatsear=re.sub("fcnxpro134.","",anatsear)
            anatsear=re.sub("ant.corona.radiata","ant.cor.rad",anatsear)
            anatsear=re.sub("sup.corona.radiata","sup.cor.rad",anatsear)
            anatsear=re.sub("posterior.thalamic.radiation.include.optic.radiation","post.thalamic.radiation",anatsear)
            anatsear=re.sub("retrolenticular.part.of.internal.capsule","rent.int.cap",anatsear)
            anatsear=re.sub("post.limb.of.internal.capsule","post.int.cap",anatsear)
            anatsear=re.sub("ant.limb.of.internal.capsule","ant.int.cap",anatsear)
            anatsear=re.sub("sagittal.stratum.include.inferior.longitidinal.fasciculus.and.inferior.fronto.occipital.fasciculus","ilf.and.ifo",anatsear)
            anatsear=re.sub("post.thalamic.radiation.optic.rad","post.thalamic.radiation",anatsear)
            atlassearch = mydict['tidynames'].str.contains(anatsear)
            if atlassearch.sum() == 0:
                atlassearch = mydict2['tidynames'].str.contains(anatsear)
            if verbose > 0 :
                print( " anatsear " + anatsear + " atlassearch " )
            if atlassearch.sum() > 0:
                whichatlas = mydict[atlassearch]['Atlas'].iloc[0]
                oglabelname = mydict[atlassearch]['Label'].iloc[0]
                oglabelname=re.sub("_",".",oglabelname)
                oglabelname=re.sub(r'\.\.','.',oglabelname)
            else:
                print(anatsear)
                oglabelname='unknown'
                whichatlas=None
            if verbose > 0:
                print("oglabelname " + oglabelname + " whichatlas " + str(whichatlas) )
            vals2viz = mysub[col2viz].agg(['min', 'max'])
            vals2viz = vals2viz[abs(vals2viz).idxmax()]
            myext = None
            if anatsear == 'cingulum.hippocampus':
                myext = 'JHU_wm'
            elif 'dktcortex' in anattoshow[k] or whichatlas == 'desikan-killiany-tourville' or 'dtkregions' in anattoshow[k]  :
                myext = 'dkt_cortex'
            elif ('cit168' in anattoshow[k] or whichatlas == 'CIT168') and not 'brainstem' in anattoshow[k] and not is_bst_region(anatsear):
                myext = 'cit168lab'
            elif 'mtl' in anattoshow[k]:
                myext = 'mtl'
                oglabelname=re.sub('mtl', '',anatsear)
            elif 'cerebellum' in anattoshow[k]:
                myext = 'cerebellum'
                oglabelname=re.sub('cerebellum', '',anatsear)
                oglabelname=re.sub('t1.vo','',oglabelname)
                # oglabelname=oglabelname[2:]
            elif 'brainstem' in anattoshow[k] or is_bst_region(anatsear):
                myext = 'brainstem'
            elif any(item in anattoshow[k] for item in ['nbm', 'bf']):
                myext = 'bf'
                oglabelname=re.sub('bf', '',oglabelname)
#                oglabelname=re.sub(r'\.', '_',anatsear)
            elif whichatlas == 'johns hopkins white matter':
                myext = 'JHU_wm'
            elif whichatlas == 'desikan-killiany-tourville':
                myext = 'dkt_cortex'
            elif whichatlas == 'CIT168':
                myext = 'cit168lab'
            elif whichatlas == 'BF':
                myext = 'bf'
                oglabelname=re.sub('bf', '',oglabelname)
            elif whichatlas == 'yeo_homotopic':
                myext = 'yeo'
            if myext is None and verbose > 0 :
                if whichatlas is None:
                    whichatlas='None'
                if anattoshow[k] is None:
                    anattoshow[k]='None'
                print( "MYEXT " + anattoshow[k] + ' unfound ' + whichatlas )
            else:
                if verbose > 0 :
                    print( "MYEXT " + myext )

            if myext == 'cit168lab':
                oglabelname=re.sub("cit168","",oglabelname)
            
            for j in postfix:
                if j == "dkt_cortex":
                    j = 'dktcortex'
                if j == "deep_cit168lab":
                    j = 'deep_cit168'
                anattoshow[k] = anattoshow[k].replace(j, "")
            if verbose > 0:
                print( anattoshow[k] + " " + str( vals2viz ) )
            correctdescript = postdesc[postfix.index(myext)]
            locfilename =  templateprefix + myext + '.nii.gz'
            if verbose > 0:
                print( locfilename )
            if myext == 'yeo':
                oglabelname=oglabelname.lower()
                oglabelname=re.sub("rsfmri_fcnxpro122_","",oglabelname)
                oglabelname=re.sub("rsfmri_fcnxpro129_","",oglabelname)
                oglabelname=re.sub("rsfmri_fcnxpro134_","",oglabelname)
                oglabelname=re.sub("rsfmri.fcnxpro122.","",oglabelname)
                oglabelname=re.sub("rsfmri.fcnxpro129.","",oglabelname)
                oglabelname=re.sub("rsfmri.fcnxpro134.","",oglabelname)
                oglabelname=re.sub("_",".",oglabelname)
                locfilename = "~/.antspymm/ppmi_template_500Parcels_Yeo2011_17Networks_2023_homotopic.nii.gz"
                atlasDescript = pd.read_csv(f"~/.antspymm/{correctdescript}.csv")
                atlasDescript.rename(columns={'SystemName': 'Description'}, inplace=True)
                atlasDescript.rename(columns={'ROI': 'Label'}, inplace=True)
                atlasDescript['Description'] = atlasDescript['Description'].str.lower()
            else:
                atlasDescript = pd.read_csv(f"~/.antspyt1w/{correctdescript}.csv")
                atlasDescript['Description'] = atlasDescript['Description'].str.lower()
                atlasDescript['Description'] = atlasDescript['Description'].str.replace(" ", "_")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("_left_", "_")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("_right_", "_")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("_left", "")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("_right", "")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("left_", "")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("right_", "")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("/",".")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace("_",".")
                atlasDescript['Description'] = atlasDescript['Description'].str.replace(r'[()]', '', regex=True)
                atlasDescript['Description'] = atlasDescript['Description'].str.replace(r'\.\.', '.')
                if myext == 'JHU_wm':
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("-", ".")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("jhu.icbm.labels.1mm", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("fronto-occipital", "frnt.occ")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("superior", "sup")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("fa-", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("-left-", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("-right-", "")
                if myext == 'cerebellum':
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("l_", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("r_", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("l.", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("r.", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("_",".")

            if verbose > 0:
                print( atlasDescript )
            oglabelname = oglabelname.lower()
            oglabelname = re.sub(" ", "_",oglabelname)
            oglabelname = re.sub("_left_", "_",oglabelname)
            oglabelname = re.sub("_right_", "_",oglabelname)
            oglabelname = re.sub("_left", "",oglabelname)
            oglabelname = re.sub("_right", "",oglabelname)
            oglabelname = re.sub("t1hier_vol_", "",oglabelname)
            oglabelname = re.sub("t1hier_area_", "",oglabelname)
            oglabelname = re.sub("t1hier_thk_", "",oglabelname)
            oglabelname = re.sub("dktregions", "",oglabelname)
            oglabelname = re.sub("dktcortex", "",oglabelname)

            oglabelname = re.sub(" ", ".",oglabelname)
            oglabelname = re.sub(".left.", ".",oglabelname)
            oglabelname = re.sub(".right.", ".",oglabelname)
            oglabelname = re.sub(".left", "",oglabelname)
            oglabelname = re.sub(".right", "",oglabelname)
            oglabelname = re.sub("t1hier.vol.", "",oglabelname)
            oglabelname = re.sub("t1hier.area.", "",oglabelname)
            oglabelname = re.sub("t1hier.thk.", "",oglabelname)
            oglabelname = re.sub("dktregions", "",oglabelname)
            oglabelname = re.sub("dktcortex", "",oglabelname)
            oglabelname=re.sub("brainstem","",oglabelname)
            if myext == 'JHU_wm':
                oglabelname = re.sub("dti_mean_fa.", "",oglabelname)
                oglabelname = re.sub("dti_mean_md.", "",oglabelname)
                oglabelname = re.sub("dti.mean.fa.", "",oglabelname)
                oglabelname = re.sub("dti.mean.md.", "",oglabelname)
                oglabelname = re.sub(".left.", "",oglabelname)
                oglabelname = re.sub(".right.", "",oglabelname)
                oglabelname = re.sub(".lravg.", "",oglabelname)
                oglabelname = re.sub(".asym.", "",oglabelname)
                oglabelname = re.sub(".jhu.icbm.labels.1mm", "",oglabelname)
                oglabelname = re.sub("superior", "sup",oglabelname)

            if verbose > 0:
                print("oglabelname " + oglabelname )

            if myext == 'cerebellum':
                if not atlasDescript.empty and 'Description' in atlasDescript.columns:
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("l_", "")
                    atlasDescript['Description'] = atlasDescript['Description'].str.replace("r_", "")
                    oglabelname=re.sub("ravg","",oglabelname)
                    oglabelname=re.sub("lavg","",oglabelname)
                    whichindex = atlasDescript.index[atlasDescript['Description'] == oglabelname].values
                else:
                    if atlasDescript.empty:
                        print("The DataFrame 'atlasDescript' is empty.")
                    if 'Description' not in atlasDescript.columns:
                        print("The column 'Description' does not exist in 'atlasDescript'.")
            else:
                whichindex = atlasDescript.index[atlasDescript['Description'].str.contains(oglabelname)]

            if type(whichindex) is np.int64:
                labelnums = atlasDescript.loc[whichindex, 'Label']
            else:
                labelnums = list(atlasDescript.loc[whichindex, 'Label'])

            if myext == 'yeo':
                parts = re.findall(r'\D+', oglabelname)
                oglabelname = [part.replace('_', '') for part in parts if part.replace('_', '')]
                oglabelname = [part.replace('.', '') for part in parts if part.replace('.', '')]
                filtered_df = atlasDescript[atlasDescript['Description'].isin(oglabelname)]
                labelnums = filtered_df['Label'].tolist()

            if not isinstance(labelnums, list):
                labelnums=[labelnums]
            addemiszero = ants.threshold_image(addem, 0, 0)
            temp = ants.image_read(locfilename)
            temp = ants.mask_image(temp, temp, level=labelnums, binarize=True)
            if verbose > 0:
                print("DEBUG")
                print(  temp.sum() ) 
                print( labelnums )
            temp[temp == 1] = (vals2viz)
            temp[addemiszero == 0] = 0
            addem = addem + temp

        if verbose > 0:
            print('Done Adding')
        for axx in axes:
            figfn=output_prefix+f"fig{col2viz}ax{axx}_py.jpg"
            if crop > 0:
                cmask = ants.threshold_image( addem,1e-5, 1e9 ).iMath("MD",crop) + ants.threshold_image( addem,-1e9, -1e-5 ).iMath("MD",crop)
                addemC = ants.crop_image( addem, cmask )
                edgeimgC = ants.crop_image( edgeimg, cmask )
            else:
                addemC = addem
                edgeimgC = edgeimg
            if fixed_overlay_range is not None:
                addemC[0:3,0:3,0:3]=fixed_overlay_range[0]
                addemC[4:7,4:7,4:7]=fixed_overlay_range[1]
                addemC[ addemC <= fixed_overlay_range[0] ] = 0 # fixed_overlay_range[0]
                addemC[ addemC >= fixed_overlay_range[1] ] = fixed_overlay_range[1]
            ants.plot(edgeimgC, addemC, axis=axx, nslices=nslices, ncol=ncol,       
                overlay_cmap=overlay_cmap, resample=False, overlay_alpha=1.0,
                filename=figfn, cbar=axx==axes[0], crop=True, black_bg=black_bg )
        if verbose > 0:
            print(f"{col2viz} done")
    if verbose:
        print("DONE brain map figures")
    return addem



# docsamson
def docsamson(locmod, studycsv, outputdir, projid, sid, dtid, mysep, t1iid=None, verbose=True):
    """
    Processes image file names based on the specified imaging modality and other parameters.

    The function selects file names from the provided dictionary `studycsv` based on the imaging modality.
    It supports various modalities like T1w, T2Flair, perf, NM2DMT, rsfMRI, DTI, and configures the filenames accordingly.
    The function can optionally print verbose output during processing.

    Parameters:
    locmod (str): The imaging modality. Options include 'T1w', 'T2Flair', 'perf', 'NM2DMT', 'rsfMRI', 'DTI'.
    studycsv (dict): A dictionary with keys corresponding to imaging modalities and values as file names.
    outputdir (str): Base directory for output files.
    projid (str): Project identifier.
    sid (str): Subject identifier.
    dtid (str): Data acquisition time identifier.
    mysep (str): Separator used in file naming.
    t1iid (str, optional): Identifier related to T1-weighted images, used in naming output files when locmod is not 'T1w'.
    verbose (bool, optional): If True, prints detailed information during execution.

    Returns:
    dict: A dictionary with keys 'modality', 'outprefix', and 'images'.
        - 'modality' (str): The imaging modality used.
        - 'outprefix' (str): The prefix for output file paths.
        - 'images' (list): A list of processed image file names.

    Notes:
    - The function is designed to work within a specific workflow and might require adaptation for general use.

    Examples:
    >>> result = docsamson('T1w', studycsv, outputdir, projid, sid, dtid, mysep)
    >>> print(result['modality'])
    'T1w'
    >>> print(result['outprefix'])
    '/path/to/output/directory/T1w/some_identifier'
    >>> print(result['images'])
    ['image1.nii', 'image2.nii']
    """

    import os
    import re

    myimgsInput = []
    myoutputPrefix = None
    imfns = ['filename', 'rsfid1', 'rsfid2', 'dtid1', 'dtid2', 'flairid']
    
    # Define image file names based on the modality
    if locmod == 'T1w':
        imfns=['filename']
    elif locmod == 'T2Flair':
        imfns=['flairid']
    elif locmod == 'perf':
        imfns=['perfid']
    elif locmod == 'pet3d':
        imfns=['pet3did']
    elif locmod == 'NM2DMT':
        imfns=[]
        for i in range(11):
            imfns.append('nmid' + str(i))
    elif locmod == 'rsfMRI':
        imfns=[]
        for i in range(4):
            imfns.append('rsfid' + str(i))
    elif locmod == 'DTI':
        imfns=[]
        for i in range(4):
            imfns.append('dtid' + str(i))
    else:
        raise ValueError("docsamson: no match of modality to filename id " + locmod )

    # Process each file name
    for i in imfns:
        if verbose:
            print(i + " " + locmod)
        if i in studycsv.keys():
            fni = str(studycsv[i].iloc[0])
            if verbose:
                print(i + " " + fni + ' exists ' + str(os.path.exists(fni)))
            if os.path.exists(fni):
                myimgsInput.append(fni)
                temp = os.path.basename(fni)
                mysplit = temp.split(mysep)
                iid = re.sub(".nii.gz", "", mysplit[-1])
                iid = re.sub(".mha", "", iid)
                iid = re.sub(".nii", "", iid)
                iid2 = iid
                if locmod != 'T1w' and t1iid is not None:
                    iid2 = iid + "_" + t1iid
                else:
                    iid2 = t1iid
                myoutputPrefix = os.path.join(outputdir, projid, sid, dtid, locmod, iid, projid + mysep + sid + mysep + dtid + mysep + locmod + mysep + iid2)
    
    if verbose:
        print(locmod)
        print(myimgsInput)
        print(myoutputPrefix)
    
    return {
        'modality': locmod,
        'outprefix': myoutputPrefix,
        'images': myimgsInput
    }




# best_mmm
def best_mmm( mmdf, wmod, mysep='-', outlier_column='ol_loop', verbose=False):
    """
    Selects the best repeats per modality.

    Args:
    wmod (str): the modality of the image ( 'T1w', 'T2Flair', 'NM2DMT' 'rsfMRI', 'DTI')

    mysep (str, optional): the separator used in the image file names. Defaults to '-'.

    outlier_name : column name for outlier score

    verbose (bool, optional): default True

    Returns:

    list: a list containing two metadata dataframes - raw and filt. raw contains all the metadata for the selected modality and filt contains the metadata filtered for highest quality repeats.

    """
#    mmdf = mmdf.astype(str)
    mmdf[outlier_column]=mmdf[outlier_column].astype(float)
    msel = mmdf['modality'] == wmod
    if wmod == 'rsfMRI':
        msel1 = mmdf['modality'] == 'rsfMRI'
        msel2 = mmdf['modality'] == 'rsfMRI_LR'
        msel3 = mmdf['modality'] == 'rsfMRI_RL'
        msel = msel1 | msel2
        msel = msel | msel3
    if wmod == 'DTI':
        msel1 = mmdf['modality'] == 'DTI'
        msel2 = mmdf['modality'] == 'DTI_LR'
        msel3 = mmdf['modality'] == 'DTI_RL'
        msel4 = mmdf['modality'] == 'DTIdwi'
        msel5 = mmdf['modality'] == 'DTIb0'
        msel = msel1 | msel2 | msel3 | msel4 | msel5
    if sum(msel) == 0:
        return {'raw': None, 'filt': None}
    metasub = mmdf[msel].copy()

    if verbose:
        print(f"{wmod} {(metasub.shape[0])} pre")

    metasub['subjectID']=None
    metasub['date']=None
    metasub['subjectIDdate']=None
    metasub['imageID']=None
    metasub['negol']=math.nan
    for k in metasub.index:
        temp = metasub.loc[k, 'filename'].split( mysep )
        metasub.loc[k,'subjectID'] = str( temp[1] )
        metasub.loc[k,'date'] = str( temp[2] )
        metasub.loc[k,'subjectIDdate'] = str( temp[1] + mysep + temp[2] )
        metasub.loc[k,'imageID'] = str( temp[4])


    if 'ol_' in outlier_column:
        metasub['negol'] = metasub[outlier_column].max() - metasub[outlier_column]
    else:
        metasub['negol'] = metasub[outlier_column]
    if 'date' not in metasub.keys():
        metasub['date']=None
    metasubq = add_repeat_column( metasub, 'subjectIDdate' )
    metasubq = highest_quality_repeat(metasubq, 'filename', 'date', 'negol')

    if verbose:
        print(f"{wmod} {metasubq.shape[0]} post")

#    metasub = metasub.astype(str)
#    metasubq = metasubq.astype(str)
    metasub[outlier_column]=metasub[outlier_column].astype(float)
    metasubq[outlier_column]=metasubq[outlier_column].astype(float)
    return {'raw': metasub, 'filt': metasubq}



# get_hemisphere_and_base
    def get_hemisphere_and_base(description):
        desc = str(description).strip()

        # Pattern 1: FreeSurfer-like (e.g., "left caudal anterior cingulate")
        match_fs = re.match(r"^(left|right)\s(.+)$", desc, re.IGNORECASE)
        if match_fs:
            return match_fs.group(1).capitalize(), match_fs.group(2).strip()

        # Pattern 2: BN_STR-like (e.g., "BN_STR_Pu_Left")
        match_bn = re.match(r"(.+)_(Left|Right)$", desc, re.IGNORECASE)
        if match_bn:
            return match_bn.group(2).capitalize(), match_bn.group(1).strip()

        # No clear hemisphere identified (e.g., 'corpus callosum')
        return 'Unknown', desc

    processed_idp_df[['Hemisphere', 'BaseRegion']] = processed_idp_df['Description'].apply(
        lambda x: pd.Series(get_hemisphere_and_base(x))
    )

    # Dictionary to store the final computed value for each ROI Label
    label_value_map = {}

    # --- 4. Process Values based on map_type ---
    if map_type == 'raw':
        logging.info("Mapping raw IDP values to ROIs.")
        # Directly map values where available
        for _, row in processed_idp_df.dropna(subset=['Value']).iterrows():
            label_value_map[row['Label']] = row['Value']

    else: # 'average' or 'asymmetry' types which require pairing logic
        # Group by the 'BaseRegion' to find potential left/right pairs
        grouped = processed_idp_df.groupby('BaseRegion')

        for base_region, group_df in grouped:
            left_roi_data = group_df[group_df['Hemisphere'] == 'Left'].dropna(subset=['Value'])
            right_roi_data = group_df[group_df['Hemisphere'] == 'Right'].dropna(subset=['Value'])

            # Handle ROIs that are not clearly left/right (e.g., 'Bilateral' or 'Unknown')
            # For these, we include their raw value regardless of map_type.
            other_rois = group_df[ (group_df['Hemisphere'] != 'Left') & (group_df['Hemisphere'] != 'Right') ].dropna(subset=['Value'])
            for _, row in other_rois.iterrows():
                label_value_map[row['Label']] = row['Value']
                logging.debug(f"ROI: '{base_region}' (Label: {row['Label']}) - Not a pair, mapped raw value: {row['Value']:.2f}")

            # Process paired regions if both left and right data are available
            if not left_roi_data.empty and not right_roi_data.empty:
                l_label = left_roi_data['Label'].iloc[0]
                l_value = left_roi_data['Value'].iloc[0]
                r_label = right_roi_data['Label'].iloc[0]
                r_value = right_roi_data['Value'].iloc[0]

                if map_type == 'average':
                    avg_val = (l_value + r_value) / 2
                    label_value_map[l_label] = avg_val
                    label_value_map[r_label] = avg_val
                    logging.debug(f"ROI: '{base_region}' - Paired AVG: {avg_val:.2f} (L:{l_value:.2f}, R:{r_value:.2f})")
                elif map_type == 'asymmetry':
                    asym_val = l_value - r_value
                    label_value_map[l_label] = asym_val
                    # Right ROI is not assigned a value based on asymmetry, so it retains 0
                    logging.debug(f"ROI: '{base_region}' - Paired ASYM (L-R): {asym_val:.2f} (L:{l_value:.2f}, R:{r_value:.2f})")
            else:
                # If only one side of a pair (or neither) is found with a valid value
                if map_type == 'average':
                    if not left_roi_data.empty:
                        label_value_map[left_roi_data['Label'].iloc[0]] = left_roi_data['Value'].iloc[0]
                        logging.debug(f"ROI: '{base_region}' - L-only AVG (raw): {left_roi_data['Value'].iloc[0]:.2f}")
                    if not right_roi_data.empty:
                        label_value_map[right_roi_data['Label'].iloc[0]] = right_roi_data['Value'].iloc[0]
                        logging.debug(f"ROI: '{base_region}' - R-only AVG (raw): {right_roi_data['Value'].iloc[0]:.2f}")
                elif map_type == 'asymmetry':
                    # If only one hemisphere's data is available, asymmetry cannot be computed.
                    # For asymmetry map_type, any unpaired ROI (including left) gets 0.
                    if not left_roi_data.empty:
                        label_value_map[left_roi_data['Label'].iloc[0]] = 0.0
                        logging.debug(f"ROI: '{base_region}' - L-only ASYM: Set to 0.0 (no pair for computation).")
                    if not right_roi_data.empty:
                        logging.debug(f"ROI: '{base_region}' - R-only ASYM: Not assigned (relevant for left hemisphere only).")

    # --- 5. Populate Output Image Array ---
    # Initialize the output NumPy array with zeros, using the robust float32 type
    output_numpy = np.zeros(roi_image.shape, dtype=np.float32)
    # Get the input ROI image's data as a NumPy array for fast lookups
    roi_image_numpy = roi_image.numpy()

    total_voxels_mapped = 0
    unique_labels_mapped_in_image = set() # Track unique labels actually processed in the image

    # Iterate through the `label_value_map` to assign values to the output image
    for label_id, value in label_value_map.items():
        # Only map if the value is not NaN (means it had data from IDP, valid conversion, etc.)
        if not np.isnan(value):
            # Find all voxels in `roi_image_numpy` that match the current `label_id`
            matching_indices = np.where(roi_image_numpy == int(label_id))

            if matching_indices[0].size > 0: # Check if this label actually exists in roi_image
                output_numpy[matching_indices] = value
                total_voxels_mapped += matching_indices[0].size
                unique_labels_mapped_in_image.add(label_id)

    logging.info(f"Mapped values for {len(unique_labels_mapped_in_image)} unique ROI labels found in `roi_image`, affecting {total_voxels_mapped} voxels.")
    logging.info("Unmapped ROIs in `roi_image` (not present in `idp_data_frame` or outside processing scope) retain value of 0.")

    # --- 6. Create ANTsImage Output ---
    # Construct the final ANTsImage from the populated NumPy array,
    # preserving the spatial header information from the original `roi_image`.
    output_image = ants.from_numpy(
        output_numpy,
        origin=roi_image.origin,
        spacing=roi_image.spacing,
        direction=roi_image.direction
    )

    logging.info("map_idps_to_rois completed successfully.")
    return output_image



# map_idps_to_rois
def map_idps_to_rois(
    idp_data_frame: pd.DataFrame,
    roi_image: ants.ANTsImage,
    idp_column: str,
    map_type: str = 'average'
) -> ants.ANTsImage:
    """
    Produces a new ANTsImage where each ROI is assigned a value based on IDP data
    from a DataFrame. ROIs are identified by integer labels in `roi_image`
    and values are linked via `idp_data_frame`.

    Assumes `idp_data_frame` contains both 'Label' (integer ROI ID) and
    'Description' (string description for the ROI, e.g., 'left caudal anterior cingulate')
    columns, in addition to the specified `idp_column`.

    Parameters:
    - idp_data_frame (pd.DataFrame): DataFrame containing IDP measurements.
      Must have 'Label', 'Description' (for hemisphere parsing), and `idp_column`.
    - roi_image (ants.ANTsImage): An ANTsImage where each voxel contains an integer
      label identifying an ROI.
    - idp_column (str): The name of the column in `idp_data_frame` whose values
      are to be mapped to the ROIs (e.g., 'VolumeInMillimeters').
    - map_type (str): Type of mapping to perform.
      - 'average': For identified paired left/right ROIs, their `idp_column` values are
                   averaged and this average is assigned to both the left and right
                   hemisphere ROIs in the output image. If only one side of a pair
                   is found, its raw value is used.
      - 'asymmetry': For identified paired left/right ROIs, the (Left - Right)
                     difference for `idp_column` is calculated and assigned only
                     to the left hemisphere ROI. Right hemisphere ROIs that are
                     part of a pair, and any unpaired ROIs, will be set to 0 in
                     the output image.
      - 'raw': Each ROI's original value from `idp_column` is mapped directly to
               its corresponding ROI in the output image.
      Default is 'average'.

    Returns:
    - ants.ANTsImage: A new ANTsImage with the same header (origin, spacing,
                      direction, etc.) as `roi_image`, where ROI voxels are filled
                      with the mapped IDP values. Voxels not part of any described
                      ROI, or unmatched based on `map_type`, will be 0.

    Raises:
    - ValueError: If required columns (`Label`, `Description`, `idp_column`) are missing
                  from `idp_data_frame`, `roi_image` is not an ANTsImage,
                  or `map_type` is invalid.
    """
    import logging

    logging.info(f"Starting map_idps_to_rois (map_type='{map_type}', IDP column='{idp_column}')")

    # --- 1. Input Validation ---
    required_idp_cols = ['Label', 'Description', idp_column]
    if not all(col in idp_data_frame.columns for col in required_idp_cols):
        raise ValueError(f"idp_data_frame must contain columns: {', '.join(required_idp_cols)}")

    if not isinstance(roi_image, ants.ANTsImage):
        raise ValueError("roi_image must be an ants.ANTsImage object.")

    valid_map_types = ['average', 'asymmetry', 'raw']
    if map_type not in valid_map_types:
        raise ValueError(f"Invalid map_type: '{map_type}'. Must be one of {valid_map_types}.")

    # --- 2. Prepare Data (use idp_data_frame directly) ---
    # Select only the necessary columns from the input idp_data_frame
    processed_idp_df = idp_data_frame[['Label', 'Description', idp_column]].copy()
    processed_idp_df.rename(columns={idp_column: 'Value'}, inplace=True)

    # Ensure 'Label' column is numeric and drop rows where conversion fails
    processed_idp_df['Label'] = pd.to_numeric(processed_idp_df['Label'], errors='coerce')
    processed_idp_df = processed_idp_df.dropna(subset=['Label']) # Drop rows where Label is NaN after coercion
    processed_idp_df['Label'] = processed_idp_df['Label'].astype(int) # Convert to integer labels

    logging.info(f"Processed IDP data contains {len(processed_idp_df)} entries. "
                 f"{processed_idp_df['Value'].isnull().sum()} entries have no valid IDP value (NaN).")

    # --- 3. Identify Hemispheres and Base Regions ---
    # This helper function parses the ROI description to determine its hemisphere
    # and a common base name for pairing (e.g., 'caudal anterior cingulate').
    def get_hemisphere_and_base(description):
        desc = str(description).strip()

        # Pattern 1: FreeSurfer-like (e.g., "left caudal anterior cingulate")
        match_fs = re.match(r"^(left|right)\s(.+)$", desc, re.IGNORECASE)
        if match_fs:
            return match_fs.group(1).capitalize(), match_fs.group(2).strip()

        # Pattern 2: BN_STR-like (e.g., "BN_STR_Pu_Left")
        match_bn = re.match(r"(.+)_(Left|Right)$", desc, re.IGNORECASE)
        if match_bn:
            return match_bn.group(2).capitalize(), match_bn.group(1).strip()

        # No clear hemisphere identified (e.g., 'corpus callosum')
        return 'Unknown', desc

    processed_idp_df[['Hemisphere', 'BaseRegion']] = processed_idp_df['Description'].apply(
        lambda x: pd.Series(get_hemisphere_and_base(x))
    )

    # Dictionary to store the final computed value for each ROI Label
    label_value_map = {}

    # --- 4. Process Values based on map_type ---
    if map_type == 'raw':
        logging.info("Mapping raw IDP values to ROIs.")
        # Directly map values where available
        for _, row in processed_idp_df.dropna(subset=['Value']).iterrows():
            label_value_map[row['Label']] = row['Value']

    else: # 'average' or 'asymmetry' types which require pairing logic
        # Group by the 'BaseRegion' to find potential left/right pairs
        grouped = processed_idp_df.groupby('BaseRegion')

        for base_region, group_df in grouped:
            left_roi_data = group_df[group_df['Hemisphere'] == 'Left'].dropna(subset=['Value'])
            right_roi_data = group_df[group_df['Hemisphere'] == 'Right'].dropna(subset=['Value'])

            # Handle ROIs that are not clearly left/right (e.g., 'Bilateral' or 'Unknown')
            # For these, we include their raw value regardless of map_type.
            other_rois = group_df[ (group_df['Hemisphere'] != 'Left') & (group_df['Hemisphere'] != 'Right') ].dropna(subset=['Value'])
            for _, row in other_rois.iterrows():
                label_value_map[row['Label']] = row['Value']
                logging.debug(f"ROI: '{base_region}' (Label: {row['Label']}) - Not a pair, mapped raw value: {row['Value']:.2f}")

            # Process paired regions if both left and right data are available
            if not left_roi_data.empty and not right_roi_data.empty:
                l_label = left_roi_data['Label'].iloc[0]
                l_value = left_roi_data['Value'].iloc[0]
                r_label = right_roi_data['Label'].iloc[0]
                r_value = right_roi_data['Value'].iloc[0]

                if map_type == 'average':
                    avg_val = (l_value + r_value) / 2
                    label_value_map[l_label] = avg_val
                    label_value_map[r_label] = avg_val
                    logging.debug(f"ROI: '{base_region}' - Paired AVG: {avg_val:.2f} (L:{l_value:.2f}, R:{r_value:.2f})")
                elif map_type == 'asymmetry':
                    asym_val = l_value - r_value
                    label_value_map[l_label] = asym_val
                    # Right ROI is not assigned a value based on asymmetry, so it retains 0
                    logging.debug(f"ROI: '{base_region}' - Paired ASYM (L-R): {asym_val:.2f} (L:{l_value:.2f}, R:{r_value:.2f})")
            else:
                # If only one side of a pair (or neither) is found with a valid value
                if map_type == 'average':
                    if not left_roi_data.empty:
                        label_value_map[left_roi_data['Label'].iloc[0]] = left_roi_data['Value'].iloc[0]
                        logging.debug(f"ROI: '{base_region}' - L-only AVG (raw): {left_roi_data['Value'].iloc[0]:.2f}")
                    if not right_roi_data.empty:
                        label_value_map[right_roi_data['Label'].iloc[0]] = right_roi_data['Value'].iloc[0]
                        logging.debug(f"ROI: '{base_region}' - R-only AVG (raw): {right_roi_data['Value'].iloc[0]:.2f}")
                elif map_type == 'asymmetry':
                    # If only one hemisphere's data is available, asymmetry cannot be computed.
                    # For asymmetry map_type, any unpaired ROI (including left) gets 0.
                    if not left_roi_data.empty:
                        label_value_map[left_roi_data['Label'].iloc[0]] = 0.0
                        logging.debug(f"ROI: '{base_region}' - L-only ASYM: Set to 0.0 (no pair for computation).")
                    if not right_roi_data.empty:
                        logging.debug(f"ROI: '{base_region}' - R-only ASYM: Not assigned (relevant for left hemisphere only).")

    # --- 5. Populate Output Image Array ---
    # Initialize the output NumPy array with zeros, using the robust float32 type
    output_numpy = np.zeros(roi_image.shape, dtype=np.float32)
    # Get the input ROI image's data as a NumPy array for fast lookups
    roi_image_numpy = roi_image.numpy()

    total_voxels_mapped = 0
    unique_labels_mapped_in_image = set() # Track unique labels actually processed in the image

    # Iterate through the `label_value_map` to assign values to the output image
    for label_id, value in label_value_map.items():
        # Only map if the value is not NaN (means it had data from IDP, valid conversion, etc.)
        if not np.isnan(value):
            # Find all voxels in `roi_image_numpy` that match the current `label_id`
            matching_indices = np.where(roi_image_numpy == int(label_id))

            if matching_indices[0].size > 0: # Check if this label actually exists in roi_image
                output_numpy[matching_indices] = value
                total_voxels_mapped += matching_indices[0].size
                unique_labels_mapped_in_image.add(label_id)

    logging.info(f"Mapped values for {len(unique_labels_mapped_in_image)} unique ROI labels found in `roi_image`, affecting {total_voxels_mapped} voxels.")
    logging.info("Unmapped ROIs in `roi_image` (not present in `idp_data_frame` or outside processing scope) retain value of 0.")

    # --- 6. Create ANTsImage Output ---
    # Construct the final ANTsImage from the populated NumPy array,
    # preserving the spatial header information from the original `roi_image`.
    output_image = ants.from_numpy(
        output_numpy,
        origin=roi_image.origin,
        spacing=roi_image.spacing,
        direction=roi_image.direction
    )

    logging.info("map_idps_to_rois completed successfully.")
    return output_image



