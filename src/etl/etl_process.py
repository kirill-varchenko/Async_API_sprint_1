import itertools
import logging
import os
from collections import defaultdict
from time import sleep
from typing import Any, Generator, Iterable

from dotenv import load_dotenv

from config import Config
from enricher import Enricher
from loader import Loader
from merger import Merger
from postgres_connection import PostgresConnection
from producer import Producer
from transform import transform_film_work, transform_genre, transform_person


def grouper_it(iterable: Iterable, n: int) -> Generator[Any, None, None]:
    """Генератор, разбивающий итерируемый iterable на чанки по n элементов."""
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)


class ETLProcess:
    def __init__(self, cfg: Config, transformers: dict):
        self.config = cfg
        self.transformers = transformers
        self.init()

    def init(self):
        self.db = PostgresConnection(self.config.dsn)
        self.loader = Loader(host=self.config.es.host)

        # Словари продьюсеров, энричеров и мёрджеров, описанных в конфиге
        self.producers = {
            sttngs.name: Producer(settings=sttngs, db=self.db)
            for sttngs in self.config.producers
        }
        self.enrichers = {
            sttngs.name: Enricher(settings=sttngs, db=self.db)
            for sttngs in self.config.enrichers
        }
        self.mergers = {
            sttngs.name: Merger(settings=sttngs, db=self.db)
            for sttngs in self.config.mergers
        }

        # Энричеры используют айди, сгенерированные продьюсерами, для
        # получения айди фильмов, которые нуждаются в обновлении.
        # Словрь producer2enricher мапит продьюсеров на испольщующих их
        # энричеров, чтобы потом знать, куда отправлять результаты продьюсеров.
        # Например, список айди персон, требующих обновления, поступает
        # одновременно на мёрджер, получающий нужную информацию для обновления
        # персон, а также на энричер, который выдаёт список айди связанных с
        # персонами фильмов, которые затем добавляются к списку фильмов на
        # обновление.
        enricher_uses = [(en.use, en.name) for en in self.config.enrichers]
        func_key = lambda x: x[0]
        enricher_uses.sort(key=func_key)
        self.producer2enricher = {
            pr_name: [b[1] for b in body]
            for pr_name, body in itertools.groupby(enricher_uses, key=func_key)
        }

    def run(self):
        """Основной цикл ETL"""
        produced = {}
        enriched = defaultdict(set)

        # Метод produce каждого продьюсера возвращает чанки айди,
        # которые сохраняются для каждого продьюсера и направляются в
        # описанные энричеры.
        for name, producer in self.producers.items():
            ids = []
            for chunk in producer.produce():
                ids.extend(chunk)
                for enricher_name in self.producer2enricher.get(name, []):
                    enriched_res = self.enrichers[enricher_name].enrich(chunk)
                    enriched[enricher_name] |= set(enriched_res)
            if ids:
                produced[name] = ids
                total = len(ids)
                logging.debug(f"{name} produced {total} ids")

        # Для каждого мёрджера объединяются айди, поступающие из продьюсеров и
        # энричеров, (без дублирования) и метод merge возвращает сырые данные
        # из БД.
        raw_data = {}
        for name, merger in self.mergers.items():
            uses = merger.settings.use
            ids = set()
            for use in uses:
                if use.endswith("_producer"):
                    ids |= set(produced.get(use, set()))
                elif use.endswith("_enricher"):
                    ids |= enriched.get(use, set())

            if not ids:
                continue

            res = merger.merge(ids)
            total = len(res)
            raw_data[name] = res
            logging.debug(f"{name} merged {total} items")

        # Лоудеры загружают полученные данные в ES. Если на предыдущем шаге для
        # лоудера получены сырые данные, они поступают в трансформер для данного
        # лоудера, а затем чанками - в метод load, загружающий данные в ES.
        for loader_settings in self.config.loaders:
            if loader_settings.use not in raw_data:
                continue

            transformed_data = self.transformers[loader_settings.name](raw_data[loader_settings.use])

            for raw_chunk in grouper_it(transformed_data, self.config.es.limit):
                self.loader.load(list(raw_chunk), index=loader_settings.index)

        for producer in self.producers.values():
            producer.save_state()


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    config = Config.parse_file("config.json")
    config.dsn.password = os.environ.get("DB_PASSWORD")

    transformers = {
        "film_work_loader": transform_film_work,
        "person_loader": transform_person,
        "genre_loader": transform_genre,
    }

    process = ETLProcess(config, transformers)
    refresh_mins = int(os.environ.get("refresh", 5))
    while True:
        process.run()
        sleep(refresh_mins * 60)
