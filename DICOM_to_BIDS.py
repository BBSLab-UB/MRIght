############################################
##########  DICOM TO BIDS SCRIPT  ##########
##########    BBSLab Mar 2024     ##########
############################################

# import libraries
import os
import datetime
import shutil

# input paths
# remove '' from string
dicoms_path = os.path.normpath(input(r"Please, enter your DICOM source directory path (add TP folder to path if needed): ").replace("'","").replace(" ","")) # /institut directory
dicoms_list_txt = os.path.normpath(input(r"Please, enter your list of DICOMS file path: ").replace("'","").replace(" ",""))         # copy subjects folders to a .txt --> a subject folder path or ID per line
bids_path = os.path.normpath(input(r"Please, enter your BIDS destination directory path: ").replace("'","").replace(" ",""))    # recommended: local folder at /home, folder must be created before running the script
heuristic_file_path = os.path.normpath(input(r"Please, enter your heuristic file path: ").replace("'","").replace(" ",""))
ses = input(r"Please, enter your session label: ")

if ses == "NOSESSION":
    use_sessions = False
else:
    use_sessions = True

#selecting DICOMS from list
def get_dicoms_in_list(dicoms_list):
    with open(dicoms_list) as file:
        list_of_dicoms = []
        for dicom_id_path in file:
            dicom_id_path = dicom_id_path.rstrip()
            if dicom_id_path[-1] == '/':
                dicom_id_path = dicom_id_path[:-1]
            dicom_id = os.path.basename(dicom_id_path)
            list_of_dicoms.append(dicom_id)
    return list_of_dicoms
dicoms_in_list = get_dicoms_in_list(dicoms_list_txt)

# list of DICOMS in input directory
dicoms_in_dir = [s for s in os.listdir(dicoms_path)]

# is there any difference?
list_minus_dir = set(dicoms_in_list).difference(dicoms_in_dir)
if (list_minus_dir != set()) is True:                                           # Some subject not in dicoms_path
    print(f'WARNING: {str(list_minus_dir)} subject(s) not in source directory')
    with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:        # error log
        f.write(str(datetime.datetime.now()) + "\t" + str(list_minus_dir) +
                " subject(s) not in source directory\n")
    dicoms_in_list = list(set(dicoms_in_list).difference(list_minus_dir))       # missing subjects are skipped

# is there any BIDS already in the bids_path? Is there any conflict? Do you want to overwrite?
if use_sessions == True:
    ses_path ="ses-{}".format(ses)    
    bids = [s[4:] for s in os.listdir(bids_path) if ((s[:4] == 'sub-') and os.path.isdir(os.path.join(bids_path, s, ses_path)) and (os.listdir(os.path.join(bids_path, s)) != []))]

else:
    bids = [s[4:] for s in os.listdir(bids_path) if ((s[:4] == 'sub-') and (os.listdir(os.path.join(bids_path, s)) != []))]
    
intersection_bids_list = set(dicoms_in_list).intersection(bids)

if intersection_bids_list == set():                                             # If there isn't any subject in both list and bids_path
    todo_dicoms = dicoms_in_list

while (intersection_bids_list != set()) is True:                                # Some subject is both in list and bids_path
    overwrite_bids = input(str(intersection_bids_list) +
                           " already in BIDS directory, do you want to overwrite? (Y/N) ").upper()
    if overwrite_bids == "N":                                                   # No overwriting: todo_dicoms = dicoms in list not in bids_path
        todo_dicoms = list(set(dicoms_in_list).difference(bids))
        intersection_bids_list = set()
        print('Overwriting of ' + str(intersection_bids_list) + 'was skipped.')
    elif overwrite_bids == "Y":                                                # Overwriting: delete BIDS in conflict, convert the entire list
        if use_sessions == True:
            for dicom_id in dicoms_in_list:
                if os.path.exists(os.path.join(bids_path, 'sub-{}'.format(dicom_id), ses_path)):
                    shutil.rmtree(os.path.join(bids_path, 'sub-{}'.format(dicom_id), ses_path))
                    print('INFO: ' + os.path.join(bids_path, 'sub-{}'.format(dicom_id), ses_path) + ' will be overwritten.')
                if os.path.exists(os.path.join(bids_path, '.heudiconv', dicom_id, ses_path)):
                    shutil.rmtree(os.path.join(bids_path, '.heudiconv', dicom_id, ses_path))
                    print('INFO: ' + os.path.join(bids_path, '.heudiconv', dicom_id, ses_path) + ' will be overwritten.')
        else:            
            for dicom_id in dicoms_in_list:
                if os.path.exists(os.path.join(bids_path, 'sub-{}'.format(dicom_id))):
                    shutil.rmtree(os.path.join(bids_path, 'sub-{}'.format(dicom_id)))
                    print('INFO: ' + os.path.join(bids_path, 'sub-{}'.format(dicom_id)) + ' will be overwritten.')
                if os.path.exists(os.path.join(bids_path, '.heudiconv', dicom_id)):
                    shutil.rmtree(os.path.join(bids_path, '.heudiconv', dicom_id))
                    print('INFO: ' + os.path.join(bids_path, '.heudiconv', dicom_id) + ' will be overwritten.')                    
        todo_dicoms = dicoms_in_list
        intersection_bids_list = set()
    else:
        print("Please, enter a valid response.\n")                              # can't exit loop if Y/N is not entered


# heudiconv run

for subj in todo_dicoms:
    
    try:
        subj_path = os.path.join(bids_path, "sub-{}".format(subj))
        if os.path.exists(subj_path) == False: os.mkdir(subj_path) # create  sub- path 
        subdir_list = [subdir for subdir in os.listdir(subj_path) if os.path.isdir(os.path.join(subj_path , subdir))]
        
        # for longitudinal studies
        # heuristic must have keys like t1w=create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_T1w')
        if use_sessions == True:
                    
        # ses- check: Subj folder must be empty or contain ONLY ses- subfolders
            if subdir_list:
                subdir_check = [ses_subdir for ses_subdir in subdir_list if 'ses-' in ses_subdir[:4]]
                if subdir_check != subdir_list:
                    with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:
                        print("WARNING: Subject {} has been skipped because it lacks session hierarchy, despite a session was inputed. Issue logged in error_heudiconv.txt".format(subj))
                        f.write(str(datetime.datetime.now()) + "\t" + subj + " session inputed, but there is no previous session hierarchy\n")
                    continue
            if not ses_path in os.listdir(subj_path):
                print("Starting subject {} conversion".format(subj))
                command = 'heudiconv -d '+ os.path.join(dicoms_path,'{subject}','*','*.IMA') + ' -o '+ bids_path +' -f '+ heuristic_file_path +' -s '+ subj + ' -ss '+ ses +' -c dcm2niix -b --minmeta --overwrite'
                os.system(command)
            else:                                                                   # this should not happen, todo_dicoms subjects are never in bids_path previously
                with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:
                    print("WARNING: Subject {} has been processed before and you chose to not overwrite. Subject will be skipped. Issue logged in error_heudiconv.txt".format(subj))
                    f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
       
        # for NON-longitudinal studies
        # heuristic must have keys like t1w=create_key('sub-{subject}/anat/sub-{subject}_run-{item:02d}_T1w')        
        else:
            
            # ses- check: Subj folder must be empty or contain ONLY ses- subfolders
            if subdir_list:
                subdir_check = [ses_subdir for ses_subdir in subdir_list if 'ses-' not in ses_subdir[:4]]
                if subdir_check != subdir_list:
                    with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:
                        print("WARNING: Subject {} has been skipped because it has session hierarchy, despite no session was inputed. Issue logged in error_heudiconv.txt".format(subj))
                        f.write(str(datetime.datetime.now()) + "\t" +subj + " session not inputed, but there is previous session hierarchy\n")
                    continue
            if ("sub-{}".format(subj) not in os.listdir(bids_path)) or (subdir_list == []):
                print("Starting subject {} conversion".format(subj))
                command = 'heudiconv -d '+ os.path.join(dicoms_path,'{subject}','*','*.IMA') + ' -o '+ bids_path +' -f '+ heuristic_file_path +' -s '+ subj +' -c dcm2niix -b --minmeta --overwrite'
                os.system(command)
            else:                                                                   # this should not happen, todo_dicoms subjects are never in bids_path previously
                with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:
                    print("WARNING: Subject {} has been processed before and you chose to not overwrite. Subject will be skipped. Issue logged in error_heudiconv.txt".format(subj))
                    f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
    
    except:                                                                     # this could happen, especially if the script is run on Windows
        with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:
            print("WARNING: Unable to process subject {}. Subject will be skipped. Issue logged in error_heudiconv.txt".format(subj))
            f.write(str(datetime.datetime.now()) + "\t" + subj + " error\n")
        continue

# .bidsignore file in case error_heudiconv.txt is created

if os.path.exists(os.path.join(bids_path, "error_heudiconv.txt")) == True:
    if os.path.exists(os.path.join(bids_path, ".bidsignore")) == False:
        with open(os.path.join(bids_path, ".bidsignore"), 'a') as f:
                    f.write('error_heudiconv.txt\n')
    else:
        with open(os.path.join(bids_path, ".bidsignore"), 'r+') as f:
            lines = {line.rstrip() for line in f}
            if "error_heudiconv.txt" not in lines:
                f.write('error_heudiconv.txt\n')          
