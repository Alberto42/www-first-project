import urllib.request

import os

import xlrd
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape


class AdministrativeUnit:
    def __init__(self, name, id):
        name = str(name)
        self.votes = [0 for i in range(vote_columns_count)]
        self.subUnits = set()
        self.id = str(id)
        self.name = name
        self.votes_percentage = []

    def add_votes(self, votes):
        self.votes = [self.votes[i] + votes[i] for i in range(vote_columns_count)]

    def update(self, votes, subUnit):
        self.add_votes(votes)
        self.subUnits.add(subUnit)
    def get_votes(self):
        return self.votes[5:]
    def get_additional_information(self):
        return [int(i) for i in self.votes[:4] ]


class Obwod(AdministrativeUnit):
    def __init__(self, number, type, address, votes, id, gmina):
        AdministrativeUnit.__init__(self, number, id)
        self.type = type
        self.address = address
        self.add_votes(votes)
        self.gmina = gmina


logger = logging.getLogger('parser')

obwodas = []
gminas = {}
okragas = {}
voivodeships = {}

politicians = [
    'Dariusz Maciej Grabowski',
    'Piotr Ikonowicz',
    'Jarosław Kalinowski',
    'Janusz Korwin-Mikke',
    'Marian Krzaklewski',
    'Aleksander Kwaśniewski',
    'Andrzej Lepper',
    'Jan Łopuszański',
    'Andrzej Marian Olechowski',
    'Bogdan Pawłowski',
    'Lech Wałęsa',
    'Tadeusz Adam Wilecki',
]
additional_information_names = [
    'Uprawnieni',
    'Wydane karty',
    'Głosy oddane',
    'Głosy nieważne',
    'Głosy ważne',
]

vote_columns_count = 17
okragas_to_voivodeships = []

env = Environment(
    loader=FileSystemLoader('html'),
    autoescape=select_autoescape(['html', 'xml'])
)


def parse_relations_between_voivodeships_and_okragas():
    bk = xlrd.open_workbook("resources/zal2.xls")
    sh = bk.sheet_by_index(0)
    voivodeship = "null"
    okragas_to_voivodeships.append('null')
    for row_index in range(7, sh.nrows):
        potential_voivodeship = sh.cell_value(row_index, 1)
        okrag = sh.cell_value(row_index, 0)
        if okrag == 'województwo':
            voivodeship = potential_voivodeship
        else:
            okragas_to_voivodeships.append(voivodeship.lower())


def parse_single_file(sufix):
    def update_administration_unit(set, unit_id, unit_name, sub_unit, votes):
        if unit_id not in set:
            set[unit_id] = AdministrativeUnit(unit_name, unit_id)
        set[unit_id].update(votes, sub_unit)

    filename = "data/%s" % sufix
    urllib.request.urlretrieve("http://prezydent2000.pkw.gov.pl/gminy/obwody/%s" % sufix, filename)
    bk = xlrd.open_workbook(filename)
    sh = bk.sheet_by_index(0)

    first_vote_column, last_politician = 7, 24

    for row_index in range(1, sh.nrows):
        votes = sh.row_values(row_index, first_vote_column, last_politician)
        row = sh.row_values(row_index, 0, 7)

        okrag = int(row[0])
        gmina_code = row[1]
        gmina_name = row[2]
        powiat = row[3]

        obwod = Obwod(int(row[4]), row[5], row[6], votes, len(obwodas), gmina_name)
        obwodas.append(obwod)

        voivodeship_name = okragas_to_voivodeships[okrag]

        update_administration_unit(gminas, gmina_code, gmina_name, len(obwodas) - 1, votes)
        update_administration_unit(okragas, okrag, okrag, gmina_code, votes)
        update_administration_unit(voivodeships, voivodeship_name, voivodeship_name, okrag, votes)


def download_and_parse_all_data():
    for i in range(1, 10):
        logger.info("parse obwod number %d" % i)
        parse_single_file("obw0%d.xls" % i)
    for i in range(10, 69):
        logger.info("parse obwod number %d" % i)
        parse_single_file("obw%d.xls" % i)


def create_single_page_from_template(subUnitPath, targetPath, unit, subUnitSet):
    template = env.get_template(targetPath + '.html')

    subUnitSubSet = [subUnitSet[subUnit] for subUnit in unit.subUnits]
    subUnitSubSet.sort(key=lambda x: int(x.name) if x.name.isdigit() else x.name)

    htmlPage = template.render(subUnits=subUnitSubSet,
                               subUnitPath=subUnitPath,
                               unit=unit,
                               politicians=politicians,
                               additional_information=zip(unit.get_additional_information(), additional_information_names))

    targetFileName = "result/%s/%s.html" % (targetPath, unit.id)

    with open(targetFileName, "w+") as targetFile:
        targetFile.write(htmlPage)


def create_pages():
    logger.info("create pages")
    for voivodeship in voivodeships.values():
        create_single_page_from_template("okragas/", "voivodeships", voivodeship, okragas)
    for okrag in okragas.values():
        create_single_page_from_template("gminas/", "okragas", okrag, gminas)
    for gmina in gminas.values():
        create_single_page_from_template("obwodas/", "gminas", gmina, obwodas)
    for obwod in obwodas:
        create_single_page_from_template("null", "obwodas", obwod, [])


def calc_percentage_votes_for_all_units():
    logger.info("calc percentage votes")
    all_units = set.union(set(gminas.values()), set(okragas.values()), set(voivodeships.values()), set(obwodas))
    for unit in all_units:
        sum_of_votes = sum(unit.get_votes())
        for vote in unit.get_votes():
            unit.votes_percentage.append((vote / sum_of_votes if sum_of_votes != 0 else 0) * 100)


def copy_resources():
    os.system('cp resources/js/* result/js')
    os.system('cp resources/* result')
    os.system('cp html/poland.html result')


logging.basicConfig(level=logging.INFO)

parse_relations_between_voivodeships_and_okragas()
download_and_parse_all_data()

calc_percentage_votes_for_all_units()

create_pages()
copy_resources()

logger.info("Done !")
