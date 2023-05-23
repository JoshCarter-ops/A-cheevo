import requests as rq
import time
import asyncio
import aiohttp
import aiofiles
from os.path import exists
import json
import glob
import os, sys
from PIL import Image
from datetime import datetime as dt
import logging
from operator import itemgetter


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


steam_url = "https://api.steampowered.com/ISteamUserStats"
config_file = resource_path("assets\\config\\steam.json")
broken_file = resource_path("assets\\images\\broken.jpg")
colour_dir = resource_path("assets\\images\\colour\\")
grey_dir = resource_path("assets\\images\\grey\\")
latest_image = resource_path("assets\\images\\achievement_icon.jpg")

col_images_cache = []
gry_images_cache = []

logging.basicConfig(
    # filename=resource_path("runtime.log"),
    # filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
log = logging.getLogger("steampy.py")


class Steam:
    def __init__(self):
        self.config = self.get_creds()

    def get_creds(self):
        if exists(config_file):
            log.info("Configuration file opened")
            with open(config_file, "r+") as openfile:
                return json.load(openfile)
        else:
            log.warn("File Doesn't Exist, creating it with default data")
            log.info("Call configure_creds(creds)")
            self.configure_creds(
                {
                    "appid": "GAME_ID",
                    "steamid": "USER_ID",
                    "key": "API_KEY",
                }
            )

    def get_completion_stats(self):
        response = rq.get(
            "{}/GetGlobalAchievementPercentagesForApp/v0002/".format(steam_url),
            params={"gameid": self.config["appid"], "format": "json"},
        )
        if response.status_code == 200:
            object = response.json()
            percentages = {}
            for i in object["achievementpercentages"]["achievements"]:
                percentages[i["name"]] = i["percent"]

            return percentages
        else:
            log.warn(
                f"Failed to Load get_completion_stats, Response code {response.status_code}"
            )
            return {"percentages": ["Failed to Load"]}

    def configure_creds(self, creds):
        data = json.dumps(creds, indent=4)
        with open(config_file, "w+") as outfile:
            outfile.write(data)
        log.info("Configuration file Updated by user")

    def get_achievements(self):
        response = rq.get(
            "{}/GetPlayerAchievements/v1/".format(steam_url),
            params=self.config,
        )
        if response.status_code == 200:
            log.info("Successful API Call for get_achievements")
            response = response.json()
            achievements = response["playerstats"]["achievements"]
            total_game_achievements = len(achievements)
            return {
                "total": total_game_achievements,
                "achievements": achievements,
                "gamename": response["playerstats"]["gameName"],
            }
        else:
            log.warn(
                f"Unsuccessful API Call for get_achievements, Response code {response.status_code}"
            )
            return {
                "total": 0,
                "achievements": ["Failed to Load"],
                "gamename": "None",
            }

    def get_details(self):
        response = rq.get(
            "{}/GetSchemaForGame/v2/".format(steam_url), params=self.config
        )
        if response.status_code == 200:
            response = response.json()
            if len(response["game"]) > 1:
                achievements = response["game"]["availableGameStats"]["achievements"]
                return {"achievement_details": achievements}
            else:
                log.warn(
                    f"Unsuccessful API Call for get_details, Response code {response.status_code}"
                )
                return {"achievement_details": ["API Failure"]}
        else:
            log.warn(
                f"Unsuccessful API Call for get_details, Response code {response.status_code}"
            )
            return {
                "achievement_details": [{"name": "API Failure", "displayName": "None"}]
            }

    def get_latest(self, achievements):
        earned = 0
        last_earned = None
        achievement_time = 0
        for achievement in achievements:
            if achievement["achieved"] == 1:
                earned += 1
                achievement_time = achievement["unlocktime"]

            if last_earned is None or achievement_time > last_earned["unlocktime"]:
                last_earned = achievement

        if earned == 0:
            log.warning("No Achievements for this Game")
            return {
                "num_earned": earned,
                "latest": {"apiname": "None Earned Yet!", "name": "None Earned Yet!", "icon": "broken.jpg"},
            }
        return {"num_earned": earned, "latest": last_earned}

    def get_latest_details(self, last_earned):
        latest_achievement_earned = None
        details = self.get_details()["achievement_details"]

        for achievement in details:
            if achievement["name"] == last_earned:
                latest_achievement_earned = achievement

        if latest_achievement_earned is None:
            file = broken_file
            latest_achievement_earned = {"displayName": last_earned}
        else:
            icon_url = latest_achievement_earned["icon"]
            icon_hash = icon_url[icon_url.rfind("/") :]
            file = "{}{}".format(colour_dir, icon_hash.replace("/", ""))

        img = Image.open(file)
        img.save(latest_image)

        log.info("Latest Achievement Image Updated")
        return latest_achievement_earned["displayName"]

    def download_images(self, urls, folder):
        start = time.time()
        asyncio.run(self.bulk_request(urls, folder))
        log.info("Got Images in {} s".format(time.time() - start))

    def clear_images(self, folder):
        files = glob.glob(folder + "\*")
        for f in files:
            if ".jpg" in f:
                os.remove(f)
        log.info(f"Images Removed from {folder}")

    async def bulk_request(self, urls, folder):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in urls:
                tasks.append(
                    self.get_store_image(session=session, url=i, folder=folder)
                )
            await asyncio.gather(*tasks)

    async def get_store_image(self, session, url, folder):
        try:
            resp = await session.request(method="GET", url=url)
        except Exception as ex:
            print(ex)
            log.error(f"Unsuccessful function for get_store_image")
            return

        if resp.status == 200:
            image_name = url[url.rfind("/") :]
            path = f"{folder}{image_name.replace('/', '')}"
            async with aiofiles.open(path, "wb") as f:
                await f.write(await resp.read())

    def get_games_list(self):
        game_response = rq.get(
            "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/",
            params={
                "key": self.config["key"],
                "steamid": self.config["steamid"],
                "format": "json",
                "include_appinfo": "true",
                "include_played_free_games": "true",
            },
        )
        achievable_list = []
        urls = []
        if game_response.status_code == 200:
            game_list = game_response.json()["response"]["games"]
            for i in game_list:
                if not (i.get("has_community_visible_stats") is None):
                    total_minutes = i["playtime_forever"]
                    time_string = "{} hours and {} minutes".format(
                        *divmod(total_minutes, 60)
                    )
                    achievable_list.append(
                        {
                            "appid": str(i["appid"]),
                            "name": i["name"],
                            "img_logo_url": i["img_icon_url"],
                            "playtime_forever": total_minutes,
                            "time_played": time_string,
                        }
                    )
                    urls.append(
                        f"http://media.steampowered.com/steamcommunity/public/images/apps/{i['appid']}/{i['img_icon_url']}.jpg"
                    )

            asyncio.run(
                self.bulk_request(
                    urls=urls, folder=resource_path("assets\\games\\icons\\")
                )
            )

        achievable_list.sort(key=itemgetter("name"), reverse=False)
        return list(achievable_list)

    def check_images(self):
        items = [f for f in os.listdir(colour_dir)]
        grey = [f for f in os.listdir(grey_dir)]

        items.extend(grey)
        return items

    def combine(self):
        color = []
        gray = []

        details = self.get_details()
        compiled_achievement_list = []
        achievements = self.get_achievements()
        percentages = self.get_completion_stats()
        latest = self.get_latest(achievements["achievements"])

        for dtl, ach in zip(
            details["achievement_details"], achievements["achievements"]
        ):
            if dtl["name"] == ach["apiname"]:
                cmbnd = dtl | ach
                cmbnd.pop("apiname")
                cmbnd["percentage"] = percentages[cmbnd["name"]]
                color.append(cmbnd["icon"])
                gray.append(cmbnd["icongray"])
                compiled_achievement_list.append(cmbnd)
            if dtl["name"] == latest["latest"]["apiname"]:
                latest["latest"]["name"] = dtl["displayName"]

        # IMAGES REFRESH
        local_imgs = self.check_images()
        for url in [s for s in color if any(xs in s for xs in local_imgs)]:
            color.remove(url)
        for url in [s for s in gray if any(xs in s for xs in local_imgs)]:
            gray.remove(url)

        if len(color) > 1:
            log.warning(
                "COLOUR: Local and Remote Image Count is different, re-downloading"
            )
            self.clear_images(colour_dir)
            self.download_images(color, colour_dir)
        elif len(gray) > 1:
            log.warning(
                "GREY: Local and Remote Image Count is different, re-downloading"
            )
            self.clear_images(grey_dir)
            self.download_images(gray, grey_dir)
        else:
            log.info("Number of images match, not touching them")

        self.get_latest_details(latest["latest"]["apiname"])

        data = {
            "total": achievements["total"],
            "gamename": achievements["gamename"],
            "achievements": compiled_achievement_list,
            "latest": latest,
            "refresh_time": dt.now().strftime("%Y-%m-%d_%H:%M:%S"),
        }

        out = json.dumps(data, indent=4)
        with open("output.json", "w+") as outfile:
            outfile.write(out)

        return data
