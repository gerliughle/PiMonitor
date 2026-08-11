import os

import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from configparser import ConfigParser
from datetime import datetime, timezone



class Database:
    APP_NAME = "pimonitor"
    __connection = None
    __temp_log = None

    @classmethod
    def connect(cls):
        if cls.__connection is None:
            home_path = os.environ['HOME']
            path = os.path.join(home_path, cls.APP_NAME)
            file = os.path.join(path, f"{cls.APP_NAME}.ini")
            if not os.path.exists(file):
                raise FileNotFoundError(f'{file} not found.')

            config_parser = ConfigParser()
            config_parser.read(file)
            username = config_parser.get("Database", "username")
            password = config_parser.get("Database", "password")
            cluster = config_parser.get("Database", "cluster")

            uri = f"mongodb+srv://{username}:{password}@{cluster}/?appName=PiMonitor"
            cls.__connection = MongoClient(uri, server_api=ServerApi('1'))
            cls.__database = cls.__connection.PiMonitor
            cls.__cpu_temp_log = cls.__database.CPUTempLog
            cls.__cpu_temp_log.create_index("timestamp", expireAfterSeconds=3600)

    @classmethod
    def upload_readings(cls, readings):
        cls.connect()
        print("Uploading readings...")

        payload = {
            "timestamp": datetime.now(timezone.utc),
            "host": "bonsai_pi_server",
            "readings": readings
        }
        insert_doc = cls.__cpu_temp_log.insert_one(payload)
        if insert_doc.acknowledged:
            print("Uploaded readings successfully.")
        else:
            print("Uploaded readings failed.")

    @classmethod
    def read_data(cls):
        cls.connect()
        return list(cls.__database.CPUTempLog.find())
