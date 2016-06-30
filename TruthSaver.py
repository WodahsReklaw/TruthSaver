#!/usr/bin/env python
#
# TruthSaver.py
# Daniel Coelho
# June 28th 2016
#
# Webcrawler designed to download and archive videos from The-Elite.net
# 
# The majority of information is stored in a DownloadEntry
#    downloadEntry = 
#        ['Player', int_TimeID, int_Stage, int_Diff, int_Time, bool_donwloaded]
#            0          1           2          3         4            5
#
#

import errno
import os
import pickle
import re
import requests
import sys as Sys
from BeautifulSoup import BeautifulSoup
from pytube import YouTube

#some global var probs should replace or get from a config file
global_url_rankings = 'http://rankings.the-elite.net/'
global_listFile = './downloadData.pkl'
global_vidPath = './vids/'
# Stages from 1 - 40, 20 = aztec 21 = def 0 is empty The Duel is excluded
global_stage_name = ['', 'Dam', 'Facility','Runway','Surface_1','Bunker_1',
                     'Silo', 'Frigate', 'Surface_2', 'Bunker_2', 'Statue',
                     'Archives', 'Streets', 'Depot', 'Train', 'Jungle',
                     'Control', 'Caverns', 'Cradle', 'Aztec', 'Egypt',
                     'Defection', 'Investigation', 'Extraction', 'Villa', 'Chicago',
                     'G5', 'Infiltration', 'Rescue', 'Escape', 'AirBase', 
                     'AFO', 'CrashSite', 'Pelagic_II','DeepSea', 'Defense', 
                     'AttackShip', 'SkedarRuins', 'MBR','Main_SOS', 'WAR']
# PD has PA insead of 00a
global_diff_name = ['Agent', 'SA', '00A', 'Agent', 'SA', 'PA']

#initializes the data structure listToDownload

# Print iterations progress Copied from stack exchange
def printProgress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : number of decimals in percent complete (Int) 
        barLength   - Optional  : character length of bar (Int) 
    """
    filledLength    = int(round(barLength * iteration / float(total)))
    percents        = round(100.00 * (iteration / float(total)), decimals)
    bar             = '#' * filledLength + '-' * (barLength - filledLength)
    Sys.stdout.write('%s [%s] %s%s %s\r' % (prefix, bar, percents, '%', suffix)),
    Sys.stdout.flush()
    if iteration == total:
        print("\n")

def get_saved_list(fileName):

    returnObj = []
    try:
        binfile = open(fileName,'rb')
    except IOError:
        print('File ' + fileName + ' assuming a new download list.\n')
        return returnObj
    try:
        returnObj = pickle.load(binfile)
        print('File ' + fileName + ' properly loaded!\n')
        print( 'Fetched file is of size: '+ str( len(returnObj)))
       # print('Printing 0th entry' + returnObj[0][0] + str(returnObj[0][1]) +
       #       str(returnObj[0][2]) + str(returnObj[0][3]) + str(returnObj[0][4]) + 
       #       str(returnObj[0][5]))
       # print('Printing 1th entry' + returnObj[1][0] + str(returnObj[1][1]) +
       #       str(returnObj[1][2]) + str(returnObj[1][3]) + str(returnObj[1][4]) + 
       #       str(returnObj[1][5]))
        return returnObj
        binfile.close()
    except:
        print('Failed loading file. Try deleting it.')
        raise
    binfile.close()

    return returnObj

#saves the list
def save_list(downloadlist, fileName):
    try:
        binfile = open(fileName,'wb')
    except IOError:
        print('Error writing download list.')
        raise
    pickle.dump(downloadlist, binfile)
    binfile.close()
    return

# Looks to see if time is in list to download
def is_in_list(listToDownload, timeID):
    if len(listToDownload) == 0:
        return False;
    for i in range(0, len(listToDownload)):
        if listToDownload[i][1] == timeID:
            return True
    return False

#updates the download list
def update_download_list(filename, url):

    # Dam = stage 1 WAR = 40
    iStageNum = 41;
    # gets list of videos to download
    listToDownload = get_saved_list(filename)
    # downloadEntry = ['Player',int_TimeID,int_Stage,int_Diff,int_Time,bool_donwloaded]
    append_count = 0
    print('Updating download list')
    for stage in range(1, iStageNum):
        
        # Get the ajax data
        page = requests.get(global_url_rankings + 'ajax/stage/' +str(stage))
        try:
            page.raise_for_status()
        except:
            print("Error loading page: " + global_url_rankings 
                  + '/ajax/stage/' + str(stage))
            raise
        # print("Page: " + global_url_rankings + 'ajax/stage/' 
        #      + str(stage) + ' loaded successfully.')
        # Parse data into diff 0 = agent, 1 = sa, 2 = 00a
        listParse = page.text.strip('[').split(']')
        listStageData = [0,0,0]
        listStageData[0] = listParse[0].split(',')
        listStageData[1] = listParse[1].split(',')
        listStageData[2] = listParse[2].split(',')

        sizeStageData = [0, 0, 0]
        sizeStageData[0] = len(listStageData[0]) / 6
        sizeStageData[1] = len(listStageData[1]) / 6
        sizeStageData[2] = len(listStageData[2]) / 6
        #print('Total of ' +  
        #      str(sizeStageData[0] + sizeStageData[1] + sizeStageData[2]) 
        #      +' times found for ' + global_stage_name[stage])
        for diff in range (0, 3):
            for i in range(0, sizeStageData[diff]):
                #print(str(int(listStageData[diff][i*6 + 5]) == 2 ) + ' & ' +
                 #     str(not is_in_list(listToDownload, listStageData[diff][i*6 + 3])))
                if (int(listStageData[diff][i*6 + 5]) == 2 
                    and not (is_in_list(listToDownload, int(listStageData[diff][i*6 + 3])))):
                    listToDownload.append(
                        [ listStageData[diff][i*6+0].strip('\"').replace(' ', '_'),
                          int(listStageData[diff][i*6+3]), stage, diff,
                          int(listStageData[diff][i*6+4]), 0 ] )
                    #print("!should be added")
                    append_count += 1
        printProgress(stage, iStageNum, prefix='Checking for new times: ',
                      suffix='Complete', barLength = 20)
    print('Update finished, added '+ str(append_count)+ ' new videos to queue.')
    save_list(listToDownload, filename)
    print('Saved updated list')
    return listToDownload
    

# Goes and fetches the YT link from the time page
def get_yt_link(levelID):
    #print('Attempting to get video for time ' + str(levelID))
    timePage = requests.get(global_url_rankings + '~/time/' + str(levelID))
    try:
        timePage.raise_for_status()
    except:
        print('Error loading page: ' + timePage.url + ' throwing exception.')
        raise
    soupTimePage = BeautifulSoup(timePage.content)
    link = soupTimePage(href=re.compile('watch?'))[0].get('href')
    return link

# Uses the YT link to download the best quality MP4, or other format
def download_video(downloadEntry):
    #check if root vid dir exists, if not make one
    try:
        os.makedirs(global_vidPath)
    except OSError:
        if not os.path.isdir(global_vidPath):
            raise

    #check if player folder exists, if not then make one
    player_path = global_vidPath + downloadEntry[0]

    try:
        os.makedirs(player_path)
    except OSError:
        if not os.path.isdir(player_path):
            raise
    diff_str = str(global_diff_name[downloadEntry[3]])
    if downloadEntry[2] > 20:
        diff_str = global_diff_name[downloadEntry[3]+2]
    videoName = (downloadEntry[0] + '-' + global_stage_name[downloadEntry[2]] 
                  + '-' + diff_str + '-'+ str(downloadEntry[4]))
    try:
        ytLink = get_yt_link(downloadEntry[1])
        yt = YouTube(ytLink)
    except Exception as ex:
        template = "Error exception of type {0} occured.\n{1}"
        print(template.format(type(ex), ex.args))
        print ('Skipping Entry for ' + str(videoName))
        return 0

    # Attempt to get a Mp4

    ytFilter = yt.filter('mp4')[-1]
    if ytFilter == []:
        ytFilter = yt.filter('webm')[-1]
        if ytFilter == []:
            print("Error no video found: " + downloadEntry[0] + ' time ' + 
                  downloadEntry[1] + 'skipped.')
            return 0

    # Cluster fuck of downloading the video
    try:
        ytFilter.filename = videoName
        ytFilter.download(player_path)
    except Exception as ex:
        template = "Error exception of type {0} occured.\n{1}"
        print(template.format(type(ex), ex.args))
        print ('Skipping Entry for ' + str(downloadEntry[0]) +
               ' time' + str(downloadEntry[1]) )
        return 0
    print('Downloaded ' + videoName + ' to ' + player_path + "\033[K")
    return 1

def main():
    print('Updating Download List')
    downloadList = update_download_list(global_listFile, global_url_rankings)
    #print(downloadList[0][0])
    print('Download List Fetched')
    print('Total Videos in list: ' + str(len(downloadList)))
    for i in range(0, len(downloadList)):
        if (downloadList[i][5] == 0):
            #Download and mark as saved in list
            downloadList[i][5] = download_video(downloadList[i]) 
            #Savelist
            save_list(downloadList, global_listFile)
        printProgress(i, len(downloadList), prefix='Downloading Videos: ',
                      suffix='Complete', barLength = 50)


    print('We finished!')

if __name__ == "__main__":
    main()

# Compare if time is saved
               
#Write Data for times to download
                   
#For all not download
#Start Open HTML Page
#Get Youtube URL
#Download Youtube Video
#Mark as Downloaded


    

