#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3

from threading import Lock

from twicorder.config import Config


class AppData:
    """
    Class for reading and writing AppData to be used between sessions.
    """

    if not os.path.exists(Config.appdata_dir):
        os.makedirs(Config.appdata_dir)
    _con = sqlite3.connect(
        Config.appdata,
        check_same_thread=False,
        timeout=float(Config.appdata_timeout)
    )
    _lock = Lock()

    def __del__(self):
        self._con.close()

    @classmethod
    def _make_query_table(cls, name):
        with cls._lock, cls._con as con:
            con.execute(
                f'''
                CREATE TABLE IF NOT EXISTS [{name}] (
                    object_id INTEGER PRIMARY KEY,
                    timestamp INTEGER NOT NULL
                )
                '''
            )

    @classmethod
    def _make_last_id_table(cls):
        with cls._lock, cls._con as con:
            con.execute(
                '''
                CREATE TABLE IF NOT EXISTS queries_last_id (
                    query_hash TEXT PRIMARY KEY,
                    object_id INTEGER NOT NULL
                )
                '''
            )

    @classmethod
    def add_query_object(cls, query_name, object_id, timestamp):
        cls._make_query_table(query_name)
        with cls._lock, cls._con as con:
            con.execute(
                f'''
                INSERT OR REPLACE INTO {query_name} VALUES (
                    ?, ?
                )
                ''',
                (object_id, timestamp)
            )

    @classmethod
    def add_query_objects(cls, query_name, objects):
        cls._make_query_table(query_name)
        with cls._lock, cls._con as con:
            con.executemany(
                f'''
                INSERT OR REPLACE INTO {query_name} VALUES (
                    ?, ?
                )
                ''',
                objects
            )

    @classmethod
    def get_query_objects(cls, query_name):
        cls._make_query_table(query_name)
        with cls._lock, cls._con as con:
            cursor = con.cursor()
            cursor.execute(
                f'''
                SELECT DISTINCT
                    object_id, timestamp
                FROM
                    {query_name}
                '''
            )
            return cursor.fetchall()

    @classmethod
    def set_last_cursor(cls, query_hash, object_id):
        cls._make_last_id_table()
        with cls._lock, cls._con as con:
            con.execute(
                '''
                INSERT OR REPLACE INTO queries_last_id VALUES (
                    ?, ?
                )
                ''',
                (query_hash, object_id)
            )

    @classmethod
    def get_last_cursor(cls, query_hash):
        cls._make_last_id_table()
        with cls._lock, cls._con as con:
            cursor = con.cursor()
            cursor.execute(
                '''
                SELECT
                DISTINCT
                    object_id
                FROM
                    queries_last_id
                WHERE
                    query_hash=?
                ''',
                (query_hash,)
            )
            result = cursor.fetchone()
        if not result:
            return
        return result[0]
