from datetime import datetime, timedelta
from tabulate import tabulate
from datetime import date

with open('./M2.B2 GEDCOM FILE.ged', 'r+') as f:
    lines = f.read().split('\n')
f.close()

validTags = ['INDI', 'NAME', 'SEX', 'BIRT', 'DEAT', 'FAMC', 'FAMS', 'FAM',
             'MARR', 'HUSB', 'WIFE', 'CHIL', 'DIV', 'DATE', 'HEAD', 'TRLR', 'NOTE']

copy = lines

for i in range(len(copy)):
    temp = copy[i].split(' ')
    if len(temp) > 2:
        if temp[2] == 'INDI' or temp[2] == 'FAM':
            t = temp[1]
            temp[1] = temp[2]
            temp[2] = t
            copy[i] = ' '.join(temp)


person = []
fams = []


class Person:
    def __init__(self, id):
        self.id = id.replace('@', '')
        self.name = None
        self.sex = None
        self.spouse_id = "NA"
        self.child_id = "NA"
        self.birth = None
        self.death = None
        self.age = None


class Fam:
    def __init__(self, f_id):
        self.f_id = f_id.replace('@', '')
        self.marriage = None
        self.divorce = None
        self.husband = None
        self.wife = None
        self.children = []


def calc_date(obj, line, dType):
    if line[1] == "DATE" and line[0] == "2":
        if isinstance(obj, Person):
            if dType == "BIRT":
                obj.birth = datetime.strptime(
                    line[2].rstrip(), '%d %b %Y').date()
            elif dType == "DEAT":
                obj.death = datetime.strptime(
                    line[2].rstrip(), '%d %b %Y').date()
        elif isinstance(obj, Fam):
            if dType == 0:
                obj.marriage = datetime.strptime(
                    line[2].rstrip(), '%d %b %Y').date()
            elif dType == 1:
                obj.divorce = datetime.strptime(
                    line[2].rstrip(), '%d %b %Y').date()

def calc_individual(copy, index, new_individual):
    details = copy[index].split(" ", 2)
    while len(copy) > index  and details[0] != "0":
        if details[0] == "1":
            if details[1] == "NAME":
                new_individual.name = details[2].strip().replace("/", "")
            elif details[1] == "SEX":
                new_individual.sex = details[2].rstrip()
            elif details[1] == "FAMS":
                new_individual.spouse_id = details[2].rstrip().replace('@', '')
            elif details[1] == "FAMC":
                new_individual.child_id = details[2].rstrip().replace('@', '')
            elif details[1].rstrip() == "BIRT" or details[1].rstrip() == "DEAT":
                calc_date(new_individual, copy[index + 1].split(" ", 2), details[1].rstrip())
        
        index = index + 1
        details = copy[index].split(" ", 2)
    new_individual.age =  int((new_individual.death - new_individual.birth).days / 365) if new_individual.death else int((date.today() - new_individual.birth).days / 365)
    person.append(new_individual)

def calc_family(lines, index, new_family):
    details = lines[index].split(" ", 2)
    
    while len(lines) > index and details[0] != "0":
        if details[0] == "1":
            if details[1] == "HUSB":
                new_family.husband = details[2].rstrip()
            elif details[1] == "WIFE":
                new_family.wife = details[2].rstrip()
            elif details[1] == "CHIL":
                new_family.children.append(details[2].rstrip())
            elif details[1].rstrip() == "MARR": 
                flag = 0
                if lines[index+2].split()[1].rstrip() == "EVEN":
                    flag = 1
                    calc_date(new_family, lines[index + 1].split(" ", 2), flag)
                calc_date(new_family, lines[index + 1].split(" ", 2), flag)
        index += 1
        details = lines[index].split(" ", 2)
    fams.append(new_family)

i = 0
while len(copy) > i:
    line = copy[i].split(" ")
    if line[1] == "INDI" and len(line) != 2:
        if line[1] == "INDI":
            calc_individual(copy, i+1, Person(line[2].rstrip()))
    elif line[1].rstrip() == "FAM":
        calc_family(copy, i+1, Fam(line[2].rstrip()))
    i += 1

person.sort(key=lambda y: int(y.id[1:]))
fams.sort(key=lambda z: int(z.f_id[1:]))

print_individuals()
print_families()
