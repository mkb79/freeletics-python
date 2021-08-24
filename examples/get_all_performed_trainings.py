import asyncio
import json
import pathlib

from freeletics import FreeleticsClient, AsyncFreeleticsClient


USERNAME = 'INSERT YOUR USERNAME'
PASSWORD = 'INSERT YOUR PASSWORD'
FILENAME = 'INSERT TARGET JSON FILENAME'


async def async_main():
    async with AsyncFreeleticsClient() as client:
        client.login(USERNAME, PASSWORD)

        # collecting activities_ids
        aids = []
        page = 1
        while True:
            r, _ = await client.user_activities(page=page)
            data = r['data']
            for i in data:
                if i['type'] == 'training_completed':
                    aod = i['relationships']['activity_object']['data']
                    if aod['type'] == 'training':
                        aids.append(aod['id'])
            if not 'next' in r['links']:
                break
            page += 1

        # get activities from ids
        jobs = (
            client.performed_activities(i) for i in aids
        )
        r = await asyncio.gather(*jobs)
        activities = []
        for i in r:
            activities.append(i[0])  # we dont need the headers
        file = pathlib.Path(FILENAME)
        activities = json.dumps(activities, indent=4)
        file.write_text(activities)

        client.logout()


def sync_main():
    with FreeleticsClient() as client:
        client.login(USERNAME, PASSWORD)


        # collecting activities_ids
        aids = []
        page = 1
        while True:
            r, _ = client.user_activities(page=page)
            data = r['data']
            for i in data:
                if i['type'] == 'training_completed':
                    aod = i['relationships']['activity_object']['data']
                    if aod['type'] == 'training':
                        aids.append(aod['id'])
            if not 'next' in r['links']:
                break
            page += 1

        # get activities from ids
        activities = []
        for aid in aids:
            r, _ = client.performed_activities(aid)
            activities.append(r)

        file = pathlib.Path(FILENAME)
        activities = json.dumps(activities, indent=4)
        file.write_text(activities)

        client.logout()


# run async
loop = asyncio.get_event_loop()
loop.run_until_complete(async_main())

# run sync
sync_main()
