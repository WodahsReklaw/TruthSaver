# -*- coding: utf-8 -*-
"""Saves all videos found on rankings.the-elite.net

This module is designed to handle the automatic downloading of all times that
have videos on rankings.the-elite.net. The behavior or this script might be
modified to select a particular player / points threshold / or any other options
that could be of importance to users of the script.

By: Daniel Coelho 2016

Some information on the datastructures encountered
The main ranks is populated from a json data structure that is as follows:
Difficulty:[
  Agent:[ 'User Name', 'User Url Suffix', 'User ID', 'Time ID', 'Time', 'Vid',
          'Next user', ... etc
  ]
  Sa:[ Same stuff
  ]
  00A[ Same stuff
  ]
]

For LTK the infromation is encoded in html in the table and not easily
obtainable through a json dump and has to be parsed seprately.

All times are stored in a dictonary with the following structure.

  Dictonary of all times {                                                       
    time_id:(time_id, player, level, diff, time (seconds), status)  
  }
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
GAMES = { "ge":"goldeneye",
          "pd":"perfectdark"
}
STAGES = {
    "ge":[
        (1, 'dam'),  (2, 'facility'), (3, 'runway'), (4, 'surface1'), 
        (5, 'bunker1'), (6, 'silo'), (7, 'frigate'), (8,'surface2'), 
        (9, 'bunker2'), (10, 'statue'), (11, 'archives'), (12, 'streets'),
        (13, 'depot'), (14, 'train'), (15, 'jungle'), (16, 'control'), 
        (17, 'caverns'), (18, 'cradle'), (19, 'aztec'), (20, 'egypt')
    ]
    "pa":[
        (21, 'defection'), (22, 'investigation'), (23, 'extraction'), 
        (24, 'villa'), (25, 'chicago'), (26, 'g5'), (27, 'infiltration'), 
        (28, 'rescue'), (29, 'escape'), (30, 'air-base'), (31, 'af1'), 
        (32, 'crash-site'), (33, 'pelagic'), (34, 'deep-sea'),(35, 'ci'),
        (36, 'attack-ship'), (37, 'skedar-ruins'), (38, 'mbr'),
        (39, 'maian-sos'), (40,'war')
    ]
}
#MODES
MODES = {
    "ge": [
        'Agent', 'SA', '00A', 'LTK', 'DLTK'
    ]
    "pa":[
        'Agent', 'SA', 'PA', 'LTK', 'DLTK'
    ]
}
class TruthSaver:
    """Downloads all videos from ranks in a nice way

  For the main ranks it downloads the JSON containing all the times for each
  level and downloads them.

  For LTK and any other functionality the level pages are scraped for that info
  """
    #Dictonary of all times
    #time_id:(time_id, player, level, diff, time (seconds), status)
    #LTK times are negative
    times_dict = dict()

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
    def ge_time_to_sec(time_str):
        t_l = time_str.split(':')
        return 60*t_l[0] + t_l[1]
    def sec_to_ge_time(time_sec):
        return str(int(time_sec / 60)) + ':' + str(time_sec%60)

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
    def timelist_to_record(self, times_list, stage_name, mode_name, status):
        ret = dict()
        for time in times_list:
            ret[time[3]] =(time[3], time[0], stage[1], mode, time[4])
        return ret

    def get_ltk_level_data(self, url, stage):
        """Parses LTK HTML for stage data similar in format to json"""
        page = requests.get(url)
        try:
            page.raise_for_status()
        except:
            print("Error loading page: " + url)
            raise
        ltk_dict = dict() 
        soup = BeautifulSoup(page.text, "html.parser")
        table_list = soup.find_all('table')
        for i, table in enumerate(table_list):
            tr_list = table.find_all('tr')
            for tr in tr_list:
                if tr.find(class_='video-link'):
                    player_name = tr.find(class_='user').text
                    time_tag = tr.find(class_='time')
                    time_id = int(time_tag["href"].split('/')[3])
                    time = ge_time_to_sec(time_tag.text)
                    ltk_list[-time_id]=( time_id, player_name, stage,
                                         diff, time, 0)
        return ltk_list
    def getTimesWithVids(level_data):
        """Gets level data, slices it by time, and keeps ones with vids"""
        ret = []
        for i in range(0, len(level_data), 6):
            if level_data[i+5] > 0:
                ret.append(level_data[i:i+6])
        return ret

    def get_check_list(self):
        """Gets download list for ge from the web"""
        check_list = []
        for key, game_name in GAMES.items():
            for stage in STAGES[key]:
                url_regular = str(BASE_URL + 'ajax/stage/' + str(stage[0]))
                #Get Regular mode data first
                stage_data_normal = get_page_json_obj(url_regular)
                for level_data in stage_data_normal:
                    check_list.extend(getTimesWithVids(level_data))
                url_ltk = str(BASE_URL + game_name
                              + '/ltk/stage/'+ str(stage[1]))

    def update_download_list(self)
        """Updates the entire times_list with new times"""
        
