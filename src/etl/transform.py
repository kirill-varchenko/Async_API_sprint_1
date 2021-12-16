from itertools import groupby

from es_item import FilmItem, GenreItem, PersonItem


def transform_film_work(data: list[dict]) -> list[FilmItem]:
    key_func = lambda x: x["fw_uuid"]
    res = []
    data.sort(key=key_func)
    for fw_uuid, fw_group_iter in groupby(data, key=key_func):
        fw_group = list(fw_group_iter)

        item = FilmItem(
            uuid=fw_uuid,
            imdb_rating=fw_group[0]["rating"],
            title=fw_group[0]["title"],
            description=fw_group[0]["description"],
        )

        genres = {}
        actors = {}
        writers = {}
        directors = {}

        for elem in fw_group:
            genres[elem["genre_uuid"]] = elem["name"]
            if elem["role"] == "director":
                directors[elem["person_uuid"]] = elem["full_name"]
            if elem["role"] == "actor":
                actors[elem["person_uuid"]] = elem["full_name"]
            if elem["role"] == "writer":
                writers[elem["person_uuid"]] = elem["full_name"]

        if genres:
            item.genres_names = list(genres.values())
            item.genres = [
                GenreItem(uuid=uuid, name=name) for uuid, name in genres.items()
            ]
        for d, names, collection in [
            (actors, "actors_names", "actors"),
            (writers, "writers_names", "writers"),
            (directors, "directors_names", "directors"),
        ]:
            if d:
                setattr(item, names, list(d.values()))
                coll_value = [
                    PersonItem(uuid=uuid, full_name=full_name)
                    for uuid, full_name in d.items()
                ]
                setattr(item, collection, coll_value)

        res.append(item)

    return res


def transform_person(data: list[dict]) -> list[PersonItem]:
    res = [PersonItem(uuid=d["uuid"], full_name=d["full_name"]) for d in data]
    return res


def transform_genre(data: list[dict]) -> list[GenreItem]:
    res = [GenreItem(uuid=d["uuid"], name=d["name"]) for d in data]
    return res
