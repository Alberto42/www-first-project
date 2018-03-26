import urllib.request
import xlrd
import logging


class AdministrativeUnit:
    def __init__(self, name):
        self.votes = [0 for i in range(politicians_count)]
        self.subUnits = set()
        self.name = name

    def add_votes(self, votes):
        self.votes = [self.votes[i] + votes[i] for i in range(politicians_count)]

    def update(self, votes, subUnit):
        self.add_votes(votes)
        self.subUnits.add(subUnit)


class Obwod(AdministrativeUnit):
    def __init__(self, number, type, address, votes):
        AdministrativeUnit.__init__(self, number)
        self.type = type
        self.address = address
        self.add_votes(votes)


logger = logging.getLogger('parser')
obwodas = []
gminas = {}
okragas = {}
voivodeships = {}
politicians = []
politicians_count = 12
powiatas_to_voivoderships = {}


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
            set[unit_id] = AdministrativeUnit(unit_name)
        set[unit_id].update(votes, sub_unit)

    filename = "data/%s" % sufix
    urllib.request.urlretrieve("http://prezydent2000.pkw.gov.pl/gminy/obwody/%s" % sufix, filename)
    bk = xlrd.open_workbook(filename)
    sh = bk.sheet_by_index(0)

    first_politician, last_politician = 12, 24
    global politicians
    politicians = sh.row_values(0, first_politician, last_politician)

    for row_index in range(1, sh.nrows):
        votes = sh.row_values(row_index, first_politician, last_politician)
        row = sh.row_values(row_index, 0, 7)

        obwod = Obwod(row[4], row[5], row[6], votes)
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
    for i in range(1, 10):
        logger.info("parse obwod number %d" % i)
        parse_obwody("obw0%d.xls" % i)
    for i in range(10, 69):
        logger.info("parse obwod number %d" % i)
        parse_obwody("obw%d.xls" % i)


logging.basicConfig(level=logging.INFO)
parse_voivodeships_to_powiatas()
parse_all_obwody()
print("koniec")
