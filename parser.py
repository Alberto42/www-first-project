import urllib.request
import xlrd


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


obwodas = []
gminas = {}
okragas = {}
powiatas = {}
voivodeships = {}
politicians = []
politicians_count = 12


def parse_obwody(sufix):
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

        gmina_code = row[1]
        if gmina_code not in gminas:
            gminas[gmina_code] = AdministrativeUnit(row[2])
        gminas[gmina_code].update(votes, len(obwodas) - 1)

        okrag_id = row[0]
        if okrag_id not in okragas:
            okragas[okrag_id] = AdministrativeUnit(okrag_id)
        okragas[okrag_id].update(votes, gmina_code)

        powiat = row[3]
        if powiat not in powiatas:
            powiatas[powiat] = AdministrativeUnit(powiat)
        powiatas[powiat].update(votes, okrag_id)


parse_obwody("obw01.xls")

print(gminas)
