#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import pickle
import shutil
import tempfile
import unittest

import truth_saver


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
            time_id='115050', player='Oscar Pleininger', mode='SA',
            stage='frigate', time=63, status=0)
        expected_path = (
            'Oscar Pleininger/Oscar Pleininger frigate SA 1:03')

        self.assertEqual(expected_path, some_time.vid_path())

    def testSaveEntries(self):
        truth = truth_saver.TruthSaver()
        entry1 = truth_saver.TimeEntry(
            url='https://rankings.the-elite.net/~Oscar+Pleininger/time/115050',
            time_id='115050', player='Oscar Pleininger', mode='SA',
            stage='frigate', time=63, status=0)
        entry2 = truth_saver.TimeEntry(
            url='https://rankings.the-elite.net/goldeneye/ltk/300',
            time_id='300', player='Lloyd Palmer', mode='DLTK',
            stage='train', time=3937, status=0)

        saved_entries = {entry1.url:entry1, entry2.url:entry2}
        truth.saved_entries = saved_entries
        pickle_path = os.path.join(self.temp_dir, 'tmp.pkl')
        truth.save_entries(pickle_path)
        self.assertTrue(os.path.exists(pickle_path))
        binfile = open(pickle_path, 'rb')
        self.assertEqual(saved_entries, pickle.load(binfile))

    def testLoadEntries(self):
        truth = truth_saver.TruthSaver('./testdata/test.pkl')

        entry1 = truth_saver.TimeEntry(
            url='https://rankings.the-elite.net/~Oscar+Pleininger/time/115050',
            time_id='115050', player='Oscar Pleininger', mode='SA',
            stage='frigate', time=63, status=0)
        entry2 = truth_saver.TimeEntry(
            url='https://rankings.the-elite.net/goldeneye/ltk/300',
            time_id='300', player='Lloyd Palmer', mode='DLTK',
            stage='train', time=3937, status=0)

        saved_entries = {entry1.url:entry1, entry2.url:entry2}

        self.assertEqual(truth.saved_entries, saved_entries)

    def testStageToTime(self):
        json_file = open('./testdata/test_data.json')
        json_data = json.loads(json_file.read())
        times = truth_saver.TruthSaver().stage_data_to_times(
            (19, 'aztec'), json_data)
        print(times)
        import pdb; pdb.set_trace()
