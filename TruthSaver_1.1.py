# -*- coding: utf-8 -*-
"""Saves all videos found on rankings.the-elite.net

This module is designed to handle the automatic downloading of all times that
have videos on rankings.the-elite.net. The behavior or this script might be
modified to select a particular player / points threshold / or any other options
that could be of importance to users of the script.

By: Daniel Coelho 2016
"""
import os
import re
import sys
import pickle
import requests

from printprogress import print_progress
from pytube import YouTube
from bs4 import BeautifulSoup

#Base URL for the rankings
BASE_URL = 'http://rankings.the-elite.net/'

#File which records which videos have been downloaded
DOWNLOAD_RECORD = './downloadData.pkl'

#Standard path to videos
VID_PATH = './vids/'

STAGES_GE = [
    (1, 'dam'),  (2, 'facility'), (3, 'runway'), (4, 'surface1'), 
    (5, 'bunker1'), (6, 'silo'), (7, 'frigate'), (8,'surface2'), 
    (9, 'bunker2'), (10, 'statue'), (11, 'archives'), (12, 'streets'),
    (13, 'depot'), (14, 'train'), (15, 'jungle'), (16, 'control'), 
    (17, 'caverns'), (18, 'cradle'), (19, 'aztec'), (20, 'egypt')
]
STAGES_PD= [
    (21, 'defection'), (22, 'investigation'), (23, 'extraction'), 
    (24, 'villa'), (25, 'chicago'), (26, 'g5'), (27, 'infiltration'), 
    (28, 'rescue'), (29, 'escape'), (30, 'air-base'), (31, 'af1'), 
    (32, 'crash-site'), (33, 'pelagic'), (34, 'deep-sea'),(35, 'ci'),
    (36, 'attack-ship'), (37, 'skedar-ruins'), (38, 'mbr'), (39, 'maian-sos'), 
    (40,'war')
]
#MODES
MODE_GE = {1:'Agent', 2:'SA', 3:'00A', 4:'LTK', 5:'DLTK'}
MODE_PD = {1:'Agent', 2:'SA', 3:'PA', 4:'LTK', 5:'DLTK'}


class TruthSaver:
    """Downloads all videos from ranks in a nice way

  For the main ranks it downloads the JSON containing all the times for each
  level and downloads them.

  For LTK and any other functionality the level pages are scraped for that info
  """
    #Dictonary of all times
    #Format Key: time_id Value:[time_id, player, level, diff, time (seconds), status]
    times_list = []

    def get_saved_list(self, filename):
        """Given full path return times_list saved as a pickle file"""
        try:
            binfile = open(filename, 'rb')
        except IOError:
            print('File ' + fileName + ' assuming a new download list.\n')
            return ret
        try:
            times_list = pickle.load(binfile)
        except:
            print('Failed Loading file. It might be corrupted.')
            raise
        print('File ' + fileName + ' properly loaded!\n')
        print('Fetched file is of size: ' + str(len(returnObj)))
        binfile.close()
        return ret

    def get_page_json_obj(self, url):
        """Gets the object from the json server
        
        JSON object is formatted as the following
        'player' (str), 'URL' (str), TimeID (int), Time (seconds),  status (int)
        where status = 0,1,2 where 2 == video
        """
        page = requests.get(url)
        try:
            page.raise_for_status()
        except:
            pint("Error loading page: " + url)
            raise
        return page.json()

    def get_ltk_level_data(self, url):
        """Parses LTK HTML for stage data similar in format to json"""
        page = requests.get(url)
        try:
            page.raise_for_status()
        except:
            print("Error loading page: " + url)
            raise
        soup = BeautifulSoup(page.text, "html.parser")
        table_list = soup.find_all('table')
        for table in table_list:
            tr_list = table.find_all('tr')
            for tr in tr_list:
                if tr.find(class_='video-link'):
                    player_name = tr.find(class_='user').text
                    time = tr.find(class_='time').text
                    time_page = tr.find(class_='time').get('href')

        

    def getTimesWithVids(level_data):
        """Gets level data, slices it by time, and keeps ones with vids"""
        ret = []
        for i in range(0, len(level_data), 6):
            if level_data[i+5] > 0:
                ret.append(level_data[i:i+6])
        return ret

    def get_ge_list(self):
        """Gets download list for ge from the web"""
        ge_list = []
        for stage in STAGES_GE:
            url_regular = str(BASE_URL + 'ajax/stage/' + str(stage[0]))
            #Get Regular mode data first
            stage_data_normal = get_page_json_obj(url_regular)
            for level_data in stage_data_normal:
                ge_list.extend(getTimesWithVids(level_data))
            url_ltk = str(BASE_URL + 'goldeneye/ltk' + str(stage[1]))

    def update_download_list(self)
        """Updates the entire times_list with new times"""
        
