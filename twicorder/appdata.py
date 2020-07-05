#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import aiosqlite

from twicorder.config import Config


class AppData:
    """
    Class for reading and writing AppData to be used between sessions.
    """

    if not os.path.exists(Config.appdata_dir):
        os.makedirs(Config.appdata_dir)

    @classmethod
    async def _make_query_table(cls, name):
        async with aiosqlite.connect(
            Config.appdata,
            timeout=float(Config.appdata_timeout)
        ) as db:
            await db.execute(
                f'''
                CREATE TABLE IF NOT EXISTS [{name}] (
                    object_id INTEGER PRIMARY KEY,
                    timestamp INTEGER NOT NULL
                )
                '''
            )

    @classmethod
    async def _make_last_id_table(cls):
        async with aiosqlite.connect(
            Config.appdata,
            timeout=float(Config.appdata_timeout)
        ) as db:
            await db.execute(
                '''
                CREATE TABLE IF NOT EXISTS queries_last_id (
                    query_hash TEXT PRIMARY KEY,
                    object_id INTEGER NOT NULL
                )
                '''
            )
            await db.commit()

    @classmethod
    async def add_query_object(cls, query_name, object_id, timestamp):
        await cls._make_query_table(query_name)
        async with aiosqlite.connect(
            Config.appdata,
            timeout=float(Config.appdata_timeout)
        ) as db:
            await db.execute(
                f'''
                INSERT OR REPLACE INTO {query_name} VALUES (
                    ?, ?
                )
                ''',
                (object_id, timestamp)
            )
            await db.commit()

    @classmethod
    async def add_query_objects(cls, query_name, objects):
        await cls._make_query_table(query_name)
        async with aiosqlite.connect(
            Config.appdata,
            timeout=float(Config.appdata_timeout)
        ) as db:
            await db.executemany(
                f'''
                INSERT OR REPLACE INTO {query_name} VALUES (
                    ?, ?
                )
                ''',
                objects
            )
            await db.commit()

    @classmethod
    async def get_query_objects(cls, query_name):
        await cls._make_query_table(query_name)
        async with aiosqlite.connect(
            Config.appdata,
            timeout=float(Config.appdata_timeout)
        ) as db:
            cursor = await db.execute(
                f'''
                SELECT DISTINCT
                    object_id, timestamp
                FROM
                    {query_name}
                '''
            )
            return await cursor.fetchall()

    @classmethod
    async def set_last_cursor(cls, query_hash, object_id):
        await cls._make_last_id_table()
        async with aiosqlite.connect(
            Config.appdata,
            timeout=float(Config.appdata_timeout)
        ) as db:
            await db.execute(
                '''
                INSERT OR REPLACE INTO queries_last_id VALUES (
                    ?, ?
                )
                ''',
                (query_hash, object_id)
            )
            await db.commit()

    @classmethod
    async def get_last_cursor(cls, query_hash):
        await cls._make_last_id_table()
        async with aiosqlite.connect(
            Config.appdata,
            timeout=float(Config.appdata_timeout)
        ) as db:
            cursor = await db.execute(
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
            result = await cursor.fetchone()
        if not result:
            return
        return result[0]
