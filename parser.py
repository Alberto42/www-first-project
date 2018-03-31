import urllib.request

import os

import xlrd
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape

class AdministrativeUnit:
    def __init__(self, name, id):
        name = str(name)
        self.votes = [0 for i in range(politicians_count)]
        self.subUnits = set()
        self.id = str(id)
        self.name = name

    def add_votes(self, votes):
        self.votes = [self.votes[i] + votes[i] for i in range(politicians_count)]

    def update(self, votes, subUnit):
        self.add_votes(votes)
        self.subUnits.add(subUnit)


class Obwod(AdministrativeUnit):
    def __init__(self, number, type, address, votes, id):
        AdministrativeUnit.__init__(self, number, id)
        self.type = type
        self.address = address
        self.add_votes(votes)


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
politicians_count = 12
powiatas_to_voivoderships = {}

env = Environment(
        loader=FileSystemLoader('template'),
        autoescape=select_autoescape(['html', 'xml'])
    )

def parse_voivodeships_to_powiatas():
    bk = xlrd.open_workbook("data/voivodeships_to_powiatas.xls")
    sh = bk.sheet_by_index(0)
    for row_index in range(1, sh.nrows):
        voivodeship = sh.cell_value(row_index, 1)
        powiat = sh.cell_value(row_index, 0)
        powiatas_to_voivoderships[powiat] = voivodeship


def parse_obwody(sufix):
    def update_administration_unit(set, unit_id, unit_name, sub_unit, votes):
        if unit_id not in set:
            set[unit_id] = AdministrativeUnit(unit_name, unit_id)
        set[unit_id].update(votes, sub_unit)

    filename = "data/%s" % sufix
    urllib.request.urlretrieve("http://prezydent2000.pkw.gov.pl/gminy/obwody/%s" % sufix, filename)
    bk = xlrd.open_workbook(filename)
    sh = bk.sheet_by_index(0)

    first_politician, last_politician = 12, 24

    for row_index in range(1, sh.nrows):
        votes = sh.row_values(row_index, first_politician, last_politician)
        row = sh.row_values(row_index, 0, 7)

        obwod = Obwod(row[4], row[5], row[6], votes,len(obwodas))
        obwodas.append(obwod)

        okrag = row[0]
        gmina_code = row[1]
        gmina_name = row[2]
        powiat = row[3]

        if powiat in {'Zagranica', 'Statki morskie'}:
            continue

        voivodeship_name = powiatas_to_voivoderships[powiat]

        update_administration_unit(gminas, gmina_code, gmina_name, len(obwodas) - 1, votes)
        update_administration_unit(okragas, okrag, okrag, gmina_code, votes)
        update_administration_unit(voivodeships, voivodeship_name, voivodeship_name, okrag, votes)


def parse_all_obwody():
    for i in range(1, 2):
        logger.info("parse obwod number %d" % i)
        parse_obwody("obw0%d.xls" % i)
    # for i in range(10, 69):
    #     logger.info("parse obwod number %d" % i)
    #     parse_obwody("obw%d.xls" % i)


def create_single_page_from_template(subUnitPath, targetPath, unit,subUnitSet):
    template = env.get_template(targetPath+'.html')
    subUnitSubSet = [subUnitSet[subUnit] for subUnit in unit.subUnits]
    htmlPage = template.render(subUnits=subUnitSubSet,
                               subUnitPath=subUnitPath,
                               unit=unit,
                               politicians=politicians)
    targetFileName = "result/%s/%s.html" % (targetPath, unit.id)
    # if not os.path.exists(targetFileName):
    #     os.mknod(targetFileName)

    with open(targetFileName, "w+") as targetFile:
        targetFile.write(htmlPage)
def create_pages():
    for voivodeship in voivodeships.values():
        create_single_page_from_template("okragas/","voivodeships",voivodeship, okragas)
    for okrag in okragas.values():
        create_single_page_from_template("gminas/","okragas",okrag, gminas)
    for gmina in gminas.values():
        create_single_page_from_template("obwodas/","gminas",gmina, obwodas)
    for obwod in obwodas:
        create_single_page_from_template("null", "obwodas", obwod, [])
logging.basicConfig(level=logging.INFO)
parse_voivodeships_to_powiatas()
parse_all_obwody()

create_pages()




