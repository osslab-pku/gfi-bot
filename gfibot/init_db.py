import json
import argparse
import pymongo
import logging

from . import BASE_DIR, CONFIG


def init_db(mongo_url: str, db_name: str, collections: list, drop: bool) -> None:
    logging.info("MongoDB URL: %s, DB Name: %s", mongo_url, db_name)
    with pymongo.MongoClient(mongo_url) as client:
        db = client[db_name]

        if drop:
            for collection in db.list_collection_names():
                count = db[collection].count_documents({})
                logging.info(
                    "Dropping collection: %s (%d documents)", collection, count
                )
                db.drop_collection(collection)

        existing_collections = db.list_collection_names()
        for c in collections:
            if c["name"] in existing_collections:
                logging.warning(
                    "Collection %s already exists (%d documents), skipping",
                    c["name"],
                    db[c["name"]].count_documents(filter={}),
                )
                logging.info(
                    "Use --drop to drop all collections before re-initializing"
                )
                continue

            logging.info("Initializing Collection: %s", c)
            # with open(BASE_DIR / "schemas" / (c["name"] + ".json"), "r") as f:
            #    schema = json.load(f)
            db.create_collection(c["name"])  # , validator={"$jsonSchema": schema})
            for index in c["indexes"]:
                db[c["name"]].create_index(
                    [(f, pymongo.ASCENDING) for f in index["fields"]],
                    unique=index["unique"],
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--drop", action="store_true")
    args = parser.parse_args()

    collections = CONFIG["mongodb"]["collections"].values()
    init_db(CONFIG["mongodb"]["url"], CONFIG["mongodb"]["db"], collections, args.drop)

    logging.info("Done!")
