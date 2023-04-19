import asyncio
import json
import pathlib

from freeletics import AsyncFreeleticsClient, FreeleticsClient


USERNAME = "INSERT YOUR USERNAME"
PASSWORD = "INSERT YOUR PASSWORD"  # noqa: S105
FILENAME = "INSERT TARGET JSON FILENAME"


async def async_main():
    async with AsyncFreeleticsClient() as client:
        await client.login(USERNAME, PASSWORD)

        # collecting activities_ids
        aids = []
        page = 1
        while True:
            r = await client.get_user_activities_by_id(page=page)
            data = r["data"]
            for i in data:
                if i["type"] == "training_completed":
                    aod = i["relationships"]["activity_object"]["data"]
                    if aod["type"] == "training":
                        aids.append(aod["id"])
            if "next" not in r["links"]:
                break
            page += 1

        # get activities from ids
        jobs = (client.get_performed_activities_by_id(i) for i in aids)
        activities = await asyncio.gather(*jobs)
        file = pathlib.Path(FILENAME)
        activities = json.dumps(activities, indent=4, default=lambda o: o.as_dict())
        file.write_text(activities)

        await client.logout()


def sync_main():
    with FreeleticsClient() as client:
        client.login(USERNAME, PASSWORD)

        # collecting activities_ids
        aids = []
        page = 1
        while True:
            r = client.get_user_activities_by_id(page=page)
            data = r["data"]
            for i in data:
                if i["type"] == "training_completed":
                    aod = i["relationships"]["activity_object"]["data"]
                    if aod["type"] == "training":
                        aids.append(aod["id"])
            if "next" not in r["links"]:
                break
            page += 1

        # get activities from ids
        activities = []
        for aid in aids:
            r = client.get_performed_activities_by_id(aid)
            activities.append(r)

        file = pathlib.Path(FILENAME)
        activities = json.dumps(activities, indent=4, default=lambda o: o.as_dict())
        file.write_text(activities)

        client.logout()


# run async
asyncio.run(async_main())

# run sync
sync_main()
