import json
import logging
import os
import sys
import time

import aiohttp
import discord.ext


class Horus:

    ENDPOINT = 'https://horus-hunts.net/Timers/GetDcTimers/?DC=Crystal'

    ENDPOINTS = (
        'https://horus-hunts.net/Timers/GetDcTimers/?DC=Aether',
        'https://horus-hunts.net/Timers/GetDcTimers/?DC=Primal',
        'https://horus-hunts.net/Timers/GetDcTimers/?DC=Crystal',
        'https://horus-hunts.net/Timers/GetDcTimers/?DC=Chaos',
        'https://horus-hunts.net/Timers/GetDcTimers/?DC=Light'
    )

    def __init__(self, bot: discord.ext.commands.Bot):
        self._log = logging.getLogger(__name__)
        self._bot = bot

        with open(os.path.dirname(os.path.realpath(sys.argv[0])) + os.sep + os.path.join('data', 'marks_info.json')) as json_file:
            self.marks_info = json.load(json_file)

        self._cached_response = None
        self._cached_time = time.time()

    async def load(self, world: str):
        """
        Load Horus data on the specified world
        """
        # Currently hardcoded to the Crystal DC; we might add support for other DC's later
        if self._cached_response is not None and (time.time() <= self._cached_time + 15):
            self._log.debug('Using cached Horus response')
            response = self._cached_response
        else:
            self._log.info('Querying Horus')
            responses = []
            async with aiohttp.ClientSession() as session:
                for endpoint in self.ENDPOINTS:
                    self._log.debug(f"Querying: {endpoint}")
                    page = await self._fetch(session, endpoint)
                    responses.append(json.loads(page))

                response = {}
                for r in responses:
                    response.update(r)

            self._cached_response = response
            self._cached_time = time.time()

        if world not in response.keys():
            raise LookupError(f"""World {world} does not exist""")
        timers = response[world]['timers']

        hunts = {}
        for key, timer in timers.items():
            hunt_data = self.id_to_hunt(timer['Id'])
            hunts[hunt_data['Name'].strip().lower() + f"_{timer['ins']}"] = HorusHunt(hunt_data, timer, timer['ins'])

        return hunts

    def id_to_hunt(self, id: str):
        """
        Map Horus hunt ID's to actual hunts
        """
        id = str(id)
        if id not in self.marks_info:
            raise LookupError(f"""ID {id} does not exist""")

        return self.marks_info[id]

    async def _fetch(self, session, url):
        async with session.get(url) as response:
            return await response.text()


class HorusHunt:

    STATUS_MAXED  = 'spawn forced'
    STATUS_OPENED = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_DIED   = 'dead'

    def __init__(self, hunt_data, timer_data, instance=1):
        # Hunt data
        self.name = hunt_data['Name']
        self.instance = instance  # 0 = Not an instanced zone, 1-3 = instance number
        self.rank = hunt_data['Rank']
        self.image = hunt_data['Image']
        self.zone = hunt_data['ZoneName']
        self.region = hunt_data['RegionName']
        self.spawn_trigger = hunt_data['SpawnTrigger']
        self.tips = hunt_data['Tips']

        # Timer data
        self.world = timer_data['world']
        self.min_respawn = timer_data['minRespawn']
        self.max_respawn = timer_data['maxRespawn']
        self.last_death = timer_data['lastDeath']
        self.open_date = timer_data['openDate']
        self.max_date = timer_data['maxDate']
        self.last_alive = timer_data['lastAlive']
        self.last_try = timer_data['lastTryUnix']
        self.last_try_user = timer_data['lastTryUser']
        self.last_mark = timer_data['lastMark']

        # Parse timers
        self.status = None
        _time = time.time() * 1000
        if _time >= self.max_date:
            self.status = self.STATUS_MAXED
        elif _time >= self.open_date:
            self.status = self.STATUS_OPENED
        elif self.last_death:
            self.status = self.STATUS_DIED
        else:
            self.status = self.STATUS_CLOSED

