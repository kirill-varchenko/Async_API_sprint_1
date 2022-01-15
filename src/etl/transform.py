from itertools import groupby

from es_item import FilmItem, GenreItem, PersonItem


def transform_film_work(data: list[dict]) -> list[FilmItem]:
    key_func = lambda x: x["fw_uuid"]
    res = []
    data.sort(key=key_func)
    for fw_uuid, fw_group_iter in groupby(data, key=key_func):
        # Группируем данные по uuid фильма, в каждой группе затем формируются
        # списки уникальных персон и жанров.
        fw_group = list(fw_group_iter)

        item = FilmItem(
            uuid=fw_uuid,
            imdb_rating=fw_group[0]["rating"],
            title=fw_group[0]["title"],
            description=fw_group[0]["description"],
        )

        genres = {}
        persons = {'director': {},
                   'actor': {},
                   'writer': {}}

        for elem in fw_group:
            if elem["genre_uuid"]:
                genres[elem["genre_uuid"]] = elem["name"]
            if elem['role'] and elem['person_uuid']:
                persons[elem['role']][elem['person_uuid']] = elem['full_name']

        if genres:
            item.genres_names = list(genres.values())
            item.genre = [GenreItem(uuid=uuid, name=name) for uuid, name in genres.items()]
        for role, names, collection in [('actor', 'actors_names', 'actors'),
                                        ('writer', 'writers_names', 'writers'),
                                        ('director', 'directors_names', 'directors')]:
            setattr(item, names, list(persons[role].values()))
            setattr(item, collection, [PersonItem(uuid=uuid, full_name=full_name)
                                       for uuid, full_name in persons[role].items()])

        res.append(item)

    return res


def transform_person(data: list[dict]) -> list[PersonItem]:
    res = [PersonItem(uuid=d["uuid"], full_name=d["full_name"]) for d in data]
    return res


def transform_genre(data: list[dict]) -> list[GenreItem]:
    res = [GenreItem(uuid=d["uuid"], name=d["name"]) for d in data]
    return res
