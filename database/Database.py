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
    __cloudflare_log = None

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
            # cls.__cpu_temp_log.drop_index("timestamp_1")
            # cls.__cpu_temp_log.create_index("timestamp", expireAfterSeconds=86400)
            cls.__cloudflare_log = cls.__database.CloudFlareLog
            # cls.__cloudflare_log.create_index("date", unique=True)

    @classmethod
    def read_system_stats(cls):
        cls.connect()
        return list(cls.__database.CPUTempLog.find())

    @classmethod
    def read_site_stats(cls):
        cls.connect()
        return list(cls.__database.CloudFlareLog.find())

    @classmethod
    def upload_cpu_readings(cls, readings):
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
    def upload_cloudflare_logs(cls, daily_stats):
        """ Takes daily stats from Cloudflare, upserts new daily data to MongoDB """
        cls.connect()

        if not daily_stats:
            print("Error, no stats provided.")
            return

        updated_count = 0
        for day in daily_stats:
            date_str = day["date"]

            filter_query = {"date": date_str}
            update_data = {
                "$set": {
                    "date": date_str,
                    "unique_visitors": day["unique_visitors"],
                    "total_requests": day["total_requests"],
                    "last_update": datetime.now(timezone.utc)
                }
            }

            result = cls.__cloudflare_log.update_one(filter_query, update_data, upsert=True)
            if result.acknowledged:
                updated_count += 1
        print(f"Successfully uploaded {updated_count} days of CloudFlare logs to database.")


