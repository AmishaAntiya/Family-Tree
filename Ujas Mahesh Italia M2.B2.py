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

def print_individuals():
    headers = ["Id", "Name", "Sex", "Birthday", "Age",
               "Alive", "Death", "Child Id", "Spouse Id"]
    table = []
    for ind in person:
        table.append([ind.id, ind.name, ind.sex, format_date(ind.birth), ind.age, True if ind.death is None else False,
                      format_date(ind.death) if ind.death is not None else "NA", ind.child_id, ind.spouse_id])
    print(tabulate(table, headers, tablefmt="fancy_grid"))


def print_families():
    headers = ["Id", "Married", "Divorced", "Husband Id",
               "Husband Name", "Wife Id", "Wife Name", "Children Ids"]
    table = []
    for fam in fams:
        table.append([fam.f_id, format_date(fam.marriage) if fam.marriage is not None else "NA",
                      format_date(
                          fam.divorce) if fam.divorce is not None else "NA", fam.husband.replace('@', ''),
                      get_individual(fam.husband).name, fam.wife.replace(
                          '@', ''), get_individual(fam.wife).name,
                      ", ".join(fam.children).replace('@', '')])
    print(tabulate(table, headers, tablefmt="fancy_grid"))


def format_date(input_date):
    return datetime.strftime(input_date, '%d %b %Y')


def get_husband_id(ind):
    return fams[int(ind.child_id[1:]) - 1].husband


def get_wife_id(ind):
    return fams[int(ind.child_id[1:]) - 1].wife


def get_individual(ind_id):
    return person[int(ind_id[2]) - 1]


def get_family(fam_id):
    return fams[int(fam_id[1:]) - 1]

# US03: Birth Before Death
# Comparing birth dates and death dates to check the validity
def birth_before_death(table):  
    born_before_death = True
    arr1 = []
    for per in person:
        if per.death is not None and per.birth > per.death:
            arr1.append("{} has a birthdate after their deathdate.".format(per.name))
            arr1.append("Birthdate: {} and Deathdate: {}".format(format_date(per.birth), format_date(per.death)))
            born_before_death = False

    if born_before_death:
        result = "Birth and death dates are valid."
    else:
        result = "One or more people has a death date before their birth."

    table.append(
        ["US03", "Birth Before Death", "\n".join(arr1), born_before_death, result])
    return table

# US28: Order Siblings By Age
# Sorted all the children in the fams array according to their D.O.B in descending order
def order_siblings_by_age(arr):  
    for fam in fams:
        if fam.children:
            fam.children.sort(key=lambda child: get_individual(child).birth)

        arr.append(
            ["US28", "Order Siblings By Age", "", True, "\n{}\n".format(fam.children).replace("@","")])
    return tabulate(arr)

# US29: List Deceased
# Finding all the deaceased people and appending it to a list
def list_deceased(arr2):  
    detail = "\n".join([per.name for per in person if per.death is not None])
    if detail:
        arr2.append(["US29", "List Deceased", "", True, detail])
    else:
        arr2.append(["US29", "List Deceased", "", True, "No death"])
    return arr2

# US30: List Living Married
# Finding all the living people who are married
def list_living_married(arr3):  
    list_of_living_married = []
    for per in person:
        if (per.spouse_id is not None and per.spouse_id != "NA") and per.death is None:
            list_of_living_married.append(per.name)
    if list_of_living_married:
        arr3.append(["US30", "List Living Married", "", True, "\n".join(list_of_living_married)])
    else:
        arr3.append(["US30", "List Living Married", "", True, "No living married person"])
    return arr3

# US35: List Recent Births
# All the recent births found in last year
def list_recent_births(arr4):  
    list_of_recent_births = []
    for per in person:
        if per.birth is not None and datetime.now().date() - timedelta(days=365) <= per.birth <= datetime.now().date():
            list_of_recent_births.append(per.name)
    if list_of_recent_births:
        arr4.append(["US35", "List Recent Births", "", True, "\n".join(list_of_recent_births)])
    else:
        arr4.append(["US36", "List Recent Births", "", True, "No recent Birth"]) 
    return arr4

# US36: List Recent Deaths
# All the recent death found in last year
def list_recent_deaths(arr5):  
    list_of_recent_deaths = []

    for per in person:
        if per.death is not None and datetime.now().date() - timedelta(days=365) <= per.death <= datetime.now().date():
            list_of_recent_deaths.append(per.name)
    if list_of_recent_deaths:
        arr5.append(["US36", "List Recent Deaths", "", True, "\n".join(list_of_recent_deaths)]) 
    else:
        arr5.append(["US36", "List Recent Deaths", "", True, "No recent death"]) 
    return arr5



def user_Stories():
    headers = ["User Story", "Description", "Error Message", "Pass", "Result"]
    table = []
    birth_before_death(table)
    order_siblings_by_age(table)
    list_deceased(table)
    list_living_married(table)
    list_recent_births(table)
    list_recent_deaths(table)
    print(tabulate(table, headers, tablefmt="fancy_grid"))

i = 0
count_Indi=0
count_fams=0
while len(copy) > i:
    line = copy[i].split(" ")
    if line[1] == "INDI" and len(line) != 2:
        if line[1] == "INDI" and count_Indi < 5000:
            calc_individual(copy, i+1, Person(line[2].rstrip()))
            count_Indi+=1
    elif line[1].rstrip() == "FAM" and count_fams < 1000:
        calc_family(copy, i+1, Fam(line[2].rstrip()))
        count_fams+=1
    i += 1

person.sort(key=lambda y: int(y.id[1:]))
fams.sort(key=lambda z: int(z.f_id[1:]))

print_individuals()
print_families()
user_Stories()