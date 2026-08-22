from datetime import datetime, timedelta, timezone
import requests
from configparser import ConfigParser
import os

from database.Database import Database


class CloudFlareTraffic:
    home_path = os.environ['HOME']
    path = os.path.join(home_path, Database.APP_NAME)
    file = os.path.join(path, f"{Database.APP_NAME}.ini")
    if not os.path.exists(file):
        raise FileNotFoundError(f'{file} not found.')

    config_parser = ConfigParser()
    config_parser.read(file)
    API_TOKEN = config_parser.get("API", "api_token")
    ZONE_ID = config_parser.get("API", "zone_id")

    @classmethod
    def get_cloudflare_analytics(cls, days):
        url = "https://api.cloudflare.com/client/v4/graphql"

        headers = {
            "Authorization": f"Bearer {cls.API_TOKEN}",
            "Content-Type": "application/json",
        }

        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
        query GetSiteAnalytics($zoneTag: string!, $startDate: Date!, $endDate: Date!) {
            viewer {
                zones(filter: {zoneTag: $zoneTag}) {
                    httpRequests1dGroups(
                        limit: 30, 
                        filter: {date_geq: $startDate, date_leq: $endDate}
                    ) {
                        dimensions { date }
                        uniq { uniques }
                        sum { requests }
                    }
                }
            }
        }
        """

        variables = {
            "zoneTag": cls.ZONE_ID,
            "startDate": start_date,
            "endDate": end_date,
        }

        response = requests.post(
            url, headers=headers, json={"query": query, "variables": variables}
        )
        data = response.json()
        # Safe checking before indexing
        if data.get("errors"):
            print("Cloudflare API Errors:", data["errors"])
            return []
        try:
            raw_days = data["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]
            daily_stats = [
                {
                    "date": day["dimensions"]["date"],
                    "unique_visitors": day["uniq"]["uniques"],
                    "total_requests": day["sum"]["requests"],
                }
                for day in raw_days
            ]
            Database.upload_cloudflare_logs(daily_stats)
        except (KeyError, TypeError) as e:
            print(f"Failed to parse Cloudflare response: {e}")
            return []
