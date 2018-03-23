#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import pickle
import shutil
import tempfile
import unittest
from mock import patch

import truth_saver

def mock_request_get(*args, **kwargs):
  class MockResponse(object):
    def __init__(self, html_file, status):
      if html_file:
        with open('./testdata/' + html_file) as f:
          self.text = f.read()
          self.content = self.text
      else:
        self.text = ''
      self.status = status

    def raise_for_status(self):
      if self.status != 200:
        raise ValueError('Bad status')

  URL_DICT = {
      'https://rankings.the-elite.net/perfect-dark/ltk/stage/attack-ship': (
          'attack_ship_ltk.html'),
      'https://rankings.the-elite.net/goldeneye/ltk/stage/silo': (
          'silo_ltk.html'),
      'https://rankings.the-elite.net/~Big+Bossman/time/10': 'bb_dam.html',
      'https://rankings.the-elite.net/~Tara/time/113844': 'tara_dam.html',
      'https://rankings.the-elite.net/~Swompz/time/78905': 'swompz_arch.html',
      'https://rankings.the-elite.net/~Wouter+Jansen/time/54778': (
          'old_aztec.html')
  }

  if args[0] not in URL_DICT:
    return MockResponse('', 404)
  else:
    html_file = URL_DICT[args[0]]
    return MockResponse(html_file, 200)


def mock_yt(*args, **kwargs):
  pass

class TestTruth(unittest.TestCase):

  def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.temp_dir)

  def testTimeToSec(self):
    time_str = '1:30'
    expected_time = 90
    self.assertEqual(truth_saver.ge_time_to_sec(time_str),
                     expected_time)
    self.assertEqual(truth_saver.sec_to_ge_time(expected_time),
                     time_str)

    long_time = '2:59:13'
    long_sec = 10753

    self.assertEqual(truth_saver.ge_time_to_sec(long_time),
                     long_sec)
    self.assertEqual(truth_saver.sec_to_ge_time(long_sec),
                     long_time)

  def testTimeEntry(self):

    some_time = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Oscar+Pleininger/time/115050',
        time_id=115050, player='Oscar Pleininger', mode='SA',
        stage='frigate', time=63, status=0)
    expected_path = (
        'Oscar_Pleininger/ge.frigate.SA.0063.Oscar_Pleininger')

    self.assertEqual(expected_path, some_time.vid_path())

  def testSaveEntries(self):
    truth = truth_saver.TruthSaver()
    entry1 = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Oscar+Pleininger/time/115050',
        time_id=115050, player='Oscar Pleininger', mode='SA',
        stage='frigate', time=63, status=0)
    entry2 = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/goldeneye/ltk/300',
        time_id=300, player='Lloyd Palmer', mode='DLTK',
        stage='train', time=3937, status=0)

    saved_entries = {entry1.url:entry1, entry2.url:entry2}
    truth.saved_entries = saved_entries
    pickle_path = os.path.join(self.temp_dir, 'tmp.pkl')
    truth.save_entries(pickle_path)
    self.assertTrue(os.path.exists(pickle_path))
    with open(pickle_path, 'rb') as binfile:
      self.assertEqual(saved_entries, pickle.load(binfile))

  def testLoadEntries(self):
    truth = truth_saver.TruthSaver('./testdata/test.pkl')

    entry1 = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Oscar+Pleininger/time/115050',
        time_id=115050, player='Oscar Pleininger', mode='SA',
        stage='frigate', time=63, status=0)
    entry2 = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/goldeneye/ltk/300',
        time_id=300, player='Lloyd Palmer', mode='DLTK',
        stage='train', time=3937, status=0)

    saved_entries = {entry1.url:entry1, entry2.url:entry2}

    self.assertEqual(truth.saved_entries, saved_entries)

  def testStageToTime(self):
    with open('./testdata/test_data.json') as json_file:
      ge_data = json.loads(json_file.read())
    times = truth_saver.TruthSaver().stage_data_to_times(
        (19, 'aztec'), ge_data)

    marc_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Dark+Inkosi/time/110357',
        time_id=110357, player='Marc Rützou', mode='SA',
        stage='aztec', time=92, status=0)
    david_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~True+Faith/time/104342',
        time_id=104342, player='David Clemens', mode='00A',
        stage='aztec', time=97, status=0)

    self.assertEqual(times[marc_entry.url], marc_entry)
    self.assertEqual(times[david_entry.url], david_entry)

    with open('./testdata/test_pd.json') as pd_json_file:
      pd_data = json.loads(pd_json_file.read())
    pd_times = truth_saver.TruthSaver().stage_data_to_times(
        (21, 'defection'), pd_data)
    jezz_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~jezz/time/111493',
        time_id=111493, player='jezz', mode='PA',
        stage='defection', time=82, status=0)
    illu_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Illu/time/20761',
        time_id=20761, player='Illu', mode='Agent',
        stage='defection', time=5, status=0)
    karl_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Sim+Threat/time/98614',
        time_id=98614, player='Sim Threat', mode='SA',
        stage='defection', time=19, status=0)

    self.assertEqual(pd_times[jezz_entry.url], jezz_entry)
    self.assertEqual(pd_times[illu_entry.url], illu_entry)
    self.assertEqual(pd_times[karl_entry.url], karl_entry)

  @patch('truth_saver.requests.get', side_effect=mock_request_get)
  def testLtkToEntries(self, mock_get):
    truth = truth_saver.TruthSaver()
    attack_ship_entries = truth.get_ltk_level_data((36, 'attack-ship'))
    self.assertEqual(len(attack_ship_entries), 14)
    dltk_count = sum(v.mode == 'DLTK' for v in attack_ship_entries.values())
    ltk_count = sum(v.mode == 'LTK' for v in attack_ship_entries.values())
    self.assertEqual(dltk_count, 4)
    self.assertEqual(ltk_count, 10)

    bb_as_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/perfect-dark/ltk/3766',
        time_id=3766, player='Big Bossman', mode='LTK',
        stage='attack-ship', time=233, status=0)
    ff_as_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/perfect-dark/ltk/3649',
        time_id=3649, player='Flickerform', mode='DLTK',
        stage='attack-ship', time=990, status=0)

    self.assertEqual(attack_ship_entries[bb_as_entry.url], bb_as_entry)
    self.assertEqual(attack_ship_entries[ff_as_entry.url], ff_as_entry)

    silo_entries = truth.get_ltk_level_data((6, 'silo'))
    self.assertEqual(len(silo_entries), 23)
    dltk_count = sum(v.mode == 'DLTK' for v in silo_entries.values())
    ltk_count = sum(v.mode == 'LTK' for v in silo_entries.values())
    self.assertEqual(dltk_count, 2)
    self.assertEqual(ltk_count, 21)

    ab_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/goldeneye/ltk/74',
        time_id=74, player='Adam Bozon', mode='LTK',
        stage='silo', time=133, status=0)
    bb_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/goldeneye/ltk/3664',
        time_id=3664, player='Bryan Bosshardt', mode='DLTK',
        stage='silo', time=496, status=0)

    self.assertEqual(silo_entries[ab_entry.url], ab_entry)
    self.assertEqual(silo_entries[bb_entry.url], bb_entry)

  @patch('truth_saver.requests.get', side_effect=mock_request_get)
  def testYtLink(self, mock_request):

    bb_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Big+Bossman/time/10',
        time_id=10, player='Bryan Bosshardt', mode='Agent',
        stage='Dam', time=53, status=0)
    bb_yt_link = truth_saver.TruthSaver.get_yt_link(bb_entry)
    self.assertEqual(bb_yt_link,
                     'https://www.youtube.com/watch?v=WA4jUsCRrfs')

    tara_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Tara/time/113844',
        time_id=11384, player='Tara Kate', mode='Agent',
        stage='dam', time=53, status=0)

    try:
      truth_saver.TruthSaver.get_yt_link(tara_entry)
    except ValueError as e:
      self.assertIn('https://www.twitch.tv/videos/v/', str(e))
    else:
      self.fail('Exepected exception from tara_entry.')

    swompz_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Swompz/time/78905',
        time_id=78905, player='Brian Dupont', mode='Agent',
        stage='archives', time=16, status=0)

    sw_yt_link = truth_saver.TruthSaver.get_yt_link(swompz_entry)
    self.assertEqual(sw_yt_link, 'https://youtu.be/QtvECUNjszU')


    wouter_entry = truth_saver.TimeEntry(
        url='https://rankings.the-elite.net/~Wouter+Jansen/time/54778',
        time_id=54778, player='Wouter Jansen', mode='00A',
        stage='aztec', time=120, status=0)

    try:
      truth_saver.TruthSaver.get_yt_link(wouter_entry)
    except ValueError as e:
      self.assertIn('www.oldvideo.net/time/10', str(e))
    else:
      self.fail('Expected exception from wouter_entry.')

    bad_entry = truth_saver.TimeEntry(
        url='https://bad.com', time_id=10, player='irrel',
        mode='SPAG', stage='Nesquik', time=10, status=0)
    try:
      truth_saver.TruthSaver.get_yt_link(bad_entry)
    except ValueError as e:
      self.assertIn('Bad status', str(e))
    else:
      self.fail('Link should fail.')
