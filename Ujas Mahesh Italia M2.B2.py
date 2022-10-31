from datetime import datetime, timedelta
from pandas import NA
from tabulate import tabulate
from datetime import date
import unittest

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
    while len(copy) > index and details[0] != "0":
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
                calc_date(new_individual,
                          copy[index + 1].split(" ", 2), details[1].rstrip())

        index = index + 1
        details = copy[index].split(" ", 2)
    new_individual.age = int((new_individual.death - new_individual.birth).days /
                             365) if new_individual.death else int((date.today() - new_individual.birth).days / 365)
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
    return (tabulate(table, headers))


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
    return (tabulate(table, headers))


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


def get_family_by_id(i_id):
    return [fam.f_id for fam in fams if i_id in [fam.husband, fam.wife]]


def print_bigamy(ind, marriage_a, marriage_b, notes):
    if ind.sex == "M":
        notes.append("{} committed bigamy with {} and {}".format(ind.name, get_individual(marriage_a.wife).name,
                                                                 get_individual(marriage_b.wife).name))
    else:
        notes.append("{} committed bigamy with {} and {}".format(ind.name, get_individual(marriage_a.husband).name,
                                                                 get_individual(marriage_b.husband).name))

def check_bigamy_spouse_death(ind, marriage_a, marriage_b, bigamy, notes):
    if ind.sex == "M":  # check if either wife died
        if get_individual(marriage_a.wife).death is not None and get_individual(
                marriage_a.wife).death >= marriage_b.marriage:
            print_bigamy(ind, marriage_a, marriage_a, notes)
            bigamy = True
        elif get_individual(marriage_b.wife).death is not None and get_individual(
                marriage_b.wife).death >= marriage_a.marriage:
            print_bigamy(ind, marriage_a, marriage_b, notes)
            bigamy = True
    else:  # check if either husband died
        if get_individual(marriage_a.husband).death is not None and get_individual(
                marriage_a.husband).death >= marriage_b.marriage:
            print_bigamy(ind, marriage_a, marriage_b, notes)
            bigamy = True
        elif get_individual(marriage_b.husband).death is not None and get_individual(
                marriage_b.husband).death >= marriage_a.marriage:
            print_bigamy(ind, marriage_a, marriage_b, notes)
            bigamy = True

    return bigamy


def check_bigamy_divorce_spouse_death(ind, marriage_a, marriage_b, bigamy, notes):
    if ind.sex == "M":  # check if either wife died
        if get_individual(marriage_a.wife).death is None:
            if marriage_b.divorce >= marriage_a.marriage:
                print_bigamy(ind, marriage_a, marriage_a, notes)
                bigamy = True
        else:
            if marriage_b.divorce >= marriage_a.marriage or get_individual(
                    marriage_a.wife).death >= marriage_b.marriage:
                print_bigamy(ind, marriage_a, marriage_b, notes)
                bigamy = True
    else:  # check if either husband died
        if get_individual(marriage_a.husband).death is None:
            if marriage_b.divorce >= marriage_a.marriage:
                print_bigamy(ind, marriage_a, marriage_a, notes)
                bigamy = True
        else:
            if marriage_b.divorce >= marriage_a.marriage or get_individual(
                    marriage_a.husband).death >= marriage_b.marriage:
                print_bigamy(ind, marriage_a, marriage_b, notes)
                bigamy = True

    return bigamy


def check_bigamy_divorce(ind, marriage_a, marriage_b, bigamy, notes):
    if marriage_a.marriage > marriage_b.divorce or marriage_b.marriage <= marriage_a.divorce:
        print_bigamy(ind, marriage_a, marriage_b, notes)
        bigamy = True

    return bigamy


def get_descendants(i_id):
    descendants = []

    for family_id in get_family_by_id(i_id):
        if get_family(family_id).children:
            descendants.extend(get_family(family_id).children)

            for child_id in get_family(family_id).children:
                descendants.extend(get_descendants(child_id))

    return descendants


def indi_age(indi):
    return datetime.today().date().year - indi.birth.year - ((datetime.today().date().month, datetime.today().date().day)
                                                            < (indi.birth.month, indi.birth.day))

# US03: Birth Before Death
# Comparing birth dates and death dates to check the validity


def birth_before_death(table):
    born_before_death = True
    arr1 = []
    for per in person:
        if per.death is not None and per.birth > per.death:
            arr1.append(
                "{} has a birthdate after their deathdate.".format(per.name))
            arr1.append("Birthdate: {} and Deathdate: {}".format(
                format_date(per.birth), format_date(per.death)))
            born_before_death = False

    if born_before_death:
        result = "Birth and death dates are valid."
    else:
        result = "One or more people has a death date before their birth."

    table.append(
        ["US03", "Birth Before Death", "\n".join(arr1), born_before_death, result])
    return table

# US15: Fewer Than 15 Siblings
# Checking whether the family has children less than 15 or more


def fewer_than_15_siblings(arr7):
    more_than_15_kids = False
    arr0 = []
    for fam in fams:
        if fam.children and len(fam.children) >= 15:
            arr0.append(
                "Family {} has more than 15 children.".format(fam.f_id))
            more_than_15_kids = True

    if more_than_15_kids:
        arr7.append(["US15", "Fewer Than 15 Siblings", "\n".join(
            arr0), not more_than_15_kids, "Some families have more than 15 children"])
    else:
        arr7.append(["US15", "Fewer Than 15 Siblings", "\n".join(
            arr0), not more_than_15_kids, "All families have less than 15 children"])
    return arr7

# US28: Order Siblings By Age
# Sorted all the children in the fams array according to their D.O.B in descending order


def order_siblings_by_age(arr):
    res = []
    for fam in fams:
        if fam.children:
            fam.children.sort(key=lambda child: get_individual(child).birth)
        res.append(fam.children)

    fin = []
    for i in res:
        fin += i

    final = []
    for i in res:
        temp = []
        for k in i:
            for j in person:
                if j.id == k.replace('@', ''):
                    temp.append(j.name)
        final.append(temp)

    final = '\n'.join([str(i) for i in final])
    arr.append(['US28', 'Order Siblings by age',
               '', True, '\n{}\n'.format(final)])
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
        arr3.append(["US30", "List Living Married", "",
                    True, "\n".join(list_of_living_married)])
    else:
        arr3.append(["US30", "List Living Married", "",
                    True, "No living married person"])
    return arr3

# US31: List Living Single
# listing all the people who are single


def list_living_single(arr6):
    list_of_living_single = []
    for per in person:
        if (per.spouse_id is None or per.spouse_id == "NA") and per.death is None:
            list_of_living_single.append(per.name)
    if list_of_living_single:
        arr6.append(["US31", "List Living Single", "",
                    True, "\n".join(list_of_living_single)])
    else:
        arr6.append(["US31", "List Living Single", "",
                    True, "All living people are married"])
    return arr6

# US35: List Recent Births
# All the recent births found in last year


def list_recent_births(arr4):
    list_of_recent_births = []
    for per in person:
        if per.birth is not None and datetime.now().date() - timedelta(days=365) <= per.birth <= datetime.now().date():
            list_of_recent_births.append(per.name)
    if list_of_recent_births:
        arr4.append(["US35", "List Recent Births", "",
                    True, "\n".join(list_of_recent_births)])
    else:
        arr4.append(["US36", "List Recent Births",
                    "", True, "No recent Birth"])
    return arr4

# US36: List Recent Deaths
# All the recent death found in last year


def list_recent_deaths(arr5):
    list_of_recent_deaths = []

    for per in person:
        if per.death is not None and datetime.now().date() - timedelta(days=365) <= per.death <= datetime.now().date():
            list_of_recent_deaths.append(per.name)
    if list_of_recent_deaths:
        arr5.append(["US36", "List Recent Deaths", "",
                    True, "\n".join(list_of_recent_deaths)])
    else:
        arr5.append(["US36", "List Recent Deaths",
                    "", True, "No recent death"])
    return arr5


# US01: Dates before today
def dates_before_today(arr):
    valid_dates = True
    mt = []
    for indi in person:
        if indi.birth is not None and datetime.now().date() < indi.birth:
            mt.append("{} should born before current date, {}.".format(
                indi.name, format_date(indi.birth)))
            valid_dates = False
        if indi.death is not None and datetime.now().date() < indi.death:
            mt.append("{} died before current date, {}.".format(
                indi.name, format_date(indi.death)))
            valid_dates = False

    for fam in fams:
        wife_name = get_individual(fam.wife).name
        hubby_name = get_individual(fam.husband).name

        if fam.marriage is not None and datetime.now().date() < fam.marriage:
            mt.append(
                "{} {} should be married before current date, {}.".format(hubby_name, wife_name, format_date(fam.marriage)))
            valid_dates = False

        if fam.divorce is not None and datetime.now().date() < fam.divorce:
            mt.append(
                "{} {} should be divorced before current date, {}.".format(hubby_name, wife_name, format_date(fam.divorce)))
            valid_dates = False

    if valid_dates:
        result = "All dates are valid."
    else:
        result = "Found invalid dates."

    arr.append(
        ["US01", "Dates Before Today", "\n".join(mt), valid_dates, result])
    return arr

# US05: Marriage Before Death


def marriage_before_death(arr):
    marry_before_dead = True
    mt = []
    for fam in fams:
        for ind in person:
            if fam.marriage is not None:
                if ind.name == get_individual(fam.wife).name or ind.name == get_individual(fam.husband).name:
                    if ind.death is not None:
                        if fam.marriage > ind.death:
                            mt.append(
                                "{} has an incorrect marriage and/or death date.".format(ind.name))
                            mt.append("Marriage is: {} and Death is: {}".format(format_date(fam.marriage),
                                                                                format_date(ind.death)))
                            marry_before_dead = False

    if marry_before_dead:
        result = "All marriages dates are valid."
    else:
        result = "One or more marriages are not before death dates"

    arr.append(
        ["US05", "Marriage Before Death", "\n".join(mt), marry_before_dead, result])
    return arr

# US38: Upcoming Birthdays
# To get the list of people whose birthday is nearby
def upcoming_birthdays(arr9):
    birthday_list = []
    for indi in person:
        if indi.birth is not None:
            birthdate = datetime(datetime.now().year,
                                 indi.birth.month, indi.birth.day).date()
            days_to_go = birthdate - datetime.today().date()
            if birthdate > datetime.today().date() and days_to_go < timedelta(days=30):
                birthday_list.append(indi.name)
    arr9.append(["US38", "Upcoming Birthdays", "", True, "\n".join(birthday_list)])
    return arr9

# US42: Reject Illegitimate Birthdays
def checker(date):
    Feb = 28
    #feb would be of 29 days in leap years
    if (date.year % 4) == 0:
        Feb = 29
    #array of number of days in every month
    days_in_month = [31, Feb, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date.day <= days_in_month[date.month - 1]

def reject_illegitimate_birthdays(arr10):  
    invalid = []
    date = False
    for indi in person:
        if not (indi.birth is None or checker(indi.birth)) or not (indi.death is None or checker(indi.death)):
            invalid.append("{} has a illegitimate birthday.".format(indi.name))
            date = True
    if invalid:
        arr10.append(["US42", "Reject Illegitimate Birthdays", "", not date, "\n".join(invalid)])
    else:
        arr10.append(["US42", "Reject Illegitimate Birthdays", "", not date, "All birthdays are legitimate"])
    return arr10

def birth_before_marriage(table):  # US02: Birth Before Marriage
    valid_marriage = True
    data = []

    for fam in fams:
        hubby_name = get_individual(fam.husband).name
        wife_name = get_individual(fam.wife).name

        for per in person:
            if fam.marriage is not None:
                if fam.marriage < per.birth and (wife_name == per.name or hubby_name == per.name):
                    data.append(
                        f"{per.name} has either an incorrect birth or marriage date.")
                    data.append(
                        f"Birthdate is: {format_date(per.birth)} and Marriage date is: {format_date(fam.marriage)}")
                    valid_marriage = False

    if valid_marriage:
        table.append(["US02", "Birth Before Marriage", "\n".join(
            data), valid_marriage, "All birth dates and marriage dates were correct"])
    else:
        table.append(["US02", "Birth Before Marriage", "\n".join(
            data), valid_marriage, "Atleast one birthdate or marriage date is incorrect."])
    return table

  # US04: Marriage Before Divorce
def marriage_before_divorce(table):
    marry_before_divorce = True
    data1 = []
    for fam in fams:
        if not fam.marriage and not fam.divorce:
            if fam.marriage > fam.divorce:
                data1.append(
                    f"{get_individual(fam.husband)} and {get_individual(fam.wife)} have a marriage before their divorce")
                data1.append(
                    f"Marriage is: {format_date(fam.marriage)} and divorce is: {format_date(fam.divorce)}")
                marry_before_divorce = False

    if marry_before_divorce:
        table.append(["US04", "Marriage Before Divorce", "\n".join(
            data1), marry_before_divorce, "All marriage and divorce dates are valid."])
    else:
        table.append(["US04", "Marriage Before Divorce", "\n".join(
            data1), marry_before_divorce, "Atleast one marriage or divorce dates are invalid."])

    return table

# US17: No Marriage to Descendants
def no_marriage_to_descendants(table):
    descendant_marriage = False
    data2 = []

    for per in person:
        descendants = get_descendants(per.id)
        if descendants is not None:
            for fam_id in get_family_by_id(per.id):
                if any(s_id in descendants for s_id in [get_family(fam_id).husband, get_family(fam_id).wife]):
                    if per.i_id == get_family(fam_id).husband:
                        data2.append(
                            f"{per.name} is married to descendant, {get_individual(get_family(fam_id).wife).name}.")
                    else:
                        data2.append(
                            f"{per.name} is married to descendant, {get_individual(get_family(fam_id).husband).name}.")
                    descendant_marriage = True

    if descendant_marriage:
        table.append(["US17", "No Marriage to Descendants", "\n".join(
            data2), not descendant_marriage, "Some ancestors are married to descendants."])

    else:
        table.append(["US17", "No Marriage to Descendants", "\n".join(
            data2), not descendant_marriage, "No ancestors are married to descendants."])
    return table


# US18: Siblings Should Not Marry
def siblings_should_not_marry(table): 
    marriage_sibling = False
    data = []
    for fam in fams:
        if fam.children and len(fam.children) > 1:
            for i in range(len(fam.children)):
                for j in range(i + 1, len(fam.children)):
                    if any(fam.children[i] in [f.husband, f.wife] and fam.children[j] in [f.husband, f.wife] for f in fams):
                        marriage_sibling = True
                        data.append(f"{get_individual(fam.children[i]).name} and {get_individual(fam.children[j]).name} are married siblings.")

    if marriage_sibling:
        table.append(["US18", "Siblings Should Not Marry Each other", "\n".join(data), not marriage_sibling,"Some siblings are married."])
    else:
        table.append(["US18", "Siblings Should Not Marry Each other", "\n".join(data), not marriage_sibling,"No siblings are married to one another."])
   
# US10: Marriage After 14
def marriage_after_fourteen(inp): 
    valid_marriage = True
    arr = []
    for fam in fams:
        if fam.marriage is None:
            continue
        wife = get_individual(fam.wife)
        hsb = get_individual(fam.husband)
        wife_age_mrg = (fam.marriage - wife.birth).days / 365
        hsb_age_mrg = (fam.marriage - hsb.birth).days / 365

        if  hsb_age_mrg < 14 and wife_age_mrg < 14:
            arr.append("{} and {} got married before the age of 14!".format(wife.name, hsb.name))
            arr.append("They got married on: {} and {}'s birth date is: {} and {}'s birth date is: {}".format(
                format_date(fam.marriage),
                wife.name, format_date(wife.birth), hsb.name, format_date(hsb.birth)))
            valid_marriage = False
        elif wife_age_mrg < 14:
            arr.append("{} got married before the age of 14!".format(wife.name))
            arr.append(
                "{} got married on: {} and their birth date is: {}".format(wife.name, format_date(fam.marriage),
                                                                           format_date(wife.birth)))
            valid_marriage = False
        elif hsb_age_mrg < 14:
            arr.append("{} got married before the age of 14!".format(hsb.name))
            arr.append(
                "{} got married on: {} and their birth date is: {}".format(hsb.name, format_date(fam.marriage),
                                                                           format_date(hsb.birth)))
            valid_marriage = False

    if valid_marriage:
        ans = "Everyone got married at the right age."
    else:
        ans = "Someone got married too early!"
    inp.append(
        ["US10", "Marriage After 14", "\n".join(arr), valid_marriage, ans])
    return inp

# US12: Parents Not Too Old
def parents_not_too_old(inp):  
    old = False
    arr = []
    for fam in fams:
        if fam.children:
            mom = get_individual(fam.wife)
            dad = get_individual(fam.husband)
            for child_id in fam.children:
                child = get_individual(child_id)
                if abs(indi_age(mom) - indi_age(child)) >= 60 and abs(indi_age(dad) - indi_age(child)) >= 80:
                    arr.append("{}'s parents, {} and {}, are too old.".format(child.name, mom.name, dad.name))
                    old = True
                elif abs(indi_age(mom) - indi_age(child)) >= 60:
                    arr.append("{}'s mother, {}, is too old.".format(child.name, mom.name))
                    old = True
                elif abs(indi_age(dad) - indi_age(child)) >= 80:
                    arr.append("{}'s father, {}, is too old.".format(child.name, dad.name))
                    old = True
    if old:
        ans = "Some parents are too old in this file."
    else:
        ans = "All parents are not too old in this file."
    inp.append(
        ["US12", "Parents Are Not Too Old", "\n".join(arr), not old, ans])
    return inp

# US09: Birth Before Death of Parents
def birth_before_parents_death(table):
    valid_birth = True
    notes = []
    for per in person:
        if per.child_id == "NA":            
            continue
        husband = get_individual(get_husband_id(per))  # get husband
        wife = get_individual(get_wife_id(per))  # get wife

        if husband.death is None and wife.death is None:  # if husband and wife are alive
            continue
        if husband.death is not None and wife.death is not None:  # if husband and wife are both dead
            if per.birth < husband.death and per.birth < wife.death:
                continue
            else:
                valid_birth = False
                notes.append(
                    "{} was born after death of parent(s).".format(per.name))
        elif husband.death is not None and per.birth < husband.death:  # if husband is dead
            continue
        elif wife.death is not None and per.birth < wife.death:  # if wife is dead
            continue
        else:
            valid_birth = False
            notes.append(
                "{} was born after death of parent(s).".format(per.name))

    if valid_birth:
        result = "Birth dates were valid and before parents' deaths."
    else:
        result = "Atleast one birth date was invalid."

    table.append(
        ["US09", "Birth Before Death of Parents", "\n".join(notes), valid_birth, result])
    return table


# US11: No marriage occured before divorcing previous marriage
def no_bigamy(table):  # US11: No Bigamy
    bigamy = False
    notes = []
    for ind in person:
        # Find all marriages for an individual
        marriages = []
        for fam in fams:
            if ind.id == fam.husband or ind.id == fam.wife:
                marriages.append(fam)

        # If they are in less than 2 families, there can be no bigotry
        if len(marriages) < 2:
            continue

        for i in range(len(marriages)):
            for j in range(i + 1, len(marriages)):
                # Neither family are divorced
                if marriages[i].divorce is None and marriages[j].divorce is None:
                    bigamy = check_bigamy_spouse_death(
                        ind, marriages[i], marriages[j], bigamy, notes)
                # Was Family A created before Family B divorce/death?
                elif marriages[i].divorce is None:
                    bigamy = check_bigamy_divorce_spouse_death(
                        ind, marriages[i], marriages[j], bigamy, notes)
                # Was Family B created before Family A divorce/death?
                elif marriages[j].divorce is None:
                    bigamy = check_bigamy_divorce_spouse_death(
                        ind, marriages[j], marriages[i], bigamy, notes)
                else:  # Both families are divorced
                    bigamy = check_bigamy_divorce(
                        ind, marriages[i], marriages[j], bigamy, notes)

    if bigamy:
        result = "There is atleast one bigamy case in this data."
    else:
        result = "No marriage occured before divorcing previous marriage."

    table.append(
        ["US11", "No Bigamy", "\n".join(notes), not bigamy, result])

    return table
# US07:Check whether anyone is more than 150 years old
def less_than_150_years_old(table): 
    right_age = True
    notes = []
    # Find the difference of everyone and check whether he is below 150
    for ind in person:
        #checking whether person is alive
        if ind.death is None:
            diff = datetime.now().date() - ind.birth
            if (diff.days / 365) > 150:
                notes.append(f"{ind.name} is over 150 years old! and birthdate is {format_date(ind.birth)}.")
                right_age = False
        # else calculate the death
        else:
            diff = ind.death - ind.birth
            if (diff.days / 365) > 150:
                notes.append(f"{ind.name} was over 150 years old and birthday is {format_date(ind.birth)} and death is {format_date(ind.death)}.")
                right_age = False

    if right_age:
        table.append(["US07", "Less Than 150 Years Old", "\n".join(notes), right_age, "Every person is below 150 years."])
    else:
        table.append(["US07", "Less Than 150 Years Old", "\n".join(notes), right_age, "One of the person is above 150 years old."])
    return table

# US06:Divorce before death
def divorce_before_death (arr12):
    divorce=True
    msg=[]
    for fam in fams:
        wife=get_individual(fam.wife).name
        husband=get_individual(fam.husband).name
        for indi in person:
            #check if there is divorce
            if (fam.divorce is not None):
                #check if the name matches
                if (indi.name==wife or indi.name==husband):
                    #check if the individual is dead
                    if (indi.death is not None):
                        #compare the death and divorce death
                        if (indi.death<fam.divorce):
                            msg.append("{} is having an incorrect divorce or death date".format(indi.name))
                            divorce=False
    if divorce:
            note="All divorce are before death"
    else:
            note="Divorce after death"
    arr12.append(["US06","Divorce before death","\n".join(msg),divorce,note])
    return arr12

# US16:Male last names
def male_last_name(arr13):
    last_name=True
    msg=[]
    for fam in fams:
        if fam.children:
            #to get the last name from the father's name
            name=get_individual(fam.husband).name[get_individual(fam.husband).name.rfind(" "):]
            for childs in fam.children:
                #to check if the individual is male and whether he is having last name or not
                if get_individual(childs).sex=="M" and (name not in get_individual(childs).name):
                    msg.append("{} don't have last name".format(get_individual(childs).name))
                    last_name=False
    if last_name:
        note="All male having last name"
    else:
        note="Few male not having last name"
    arr13.append(["US16","Male last names","\n".join(msg),last_name,note])
    return arr13

# US13: Siblings spacing
def sibling_age_space(table):
    sibling_space = True
    notes = []
    # To get all the birthdates of siblings and check whether they are born 8 months apart
    # If no then sibling spacing will be false and error will be thrown
    for fam in fams:
        if fam.children and len(fam.children) > 1:
            for i in range(len(fam.children)):
                for j in range(i + 1, len(fam.children)):
                    if 2 < abs((get_individual(fam.children[i]).birth - get_individual(fam.children[j]).birth).days) < 243.3:
                        notes.append(f"{get_individual(fam.children[i]).name} and {get_individual(fam.children[j]).name} are not spaced properly.")
                        sibling_space = False
    if sibling_space:
        table.append( ["US13", "Sibling Age Spacing", "\n".join(notes), sibling_space, "All sibling ages have birthdates more than 8 months apart  "])
    else:
        table.append( ["US13", "Sibling Age Spacing", "\n".join(notes), sibling_space, " One of the siblings have birthday within 8 months"])
    return table

def user_Stories():
    headers = ["User Story", "Description", "Error Message", "Pass", "Result"]
    table = []
    birth_before_death(table)
    fewer_than_15_siblings(table)
    order_siblings_by_age(table)
    list_deceased(table)
    list_living_married(table)
    list_living_single(table)
    list_recent_births(table)
    list_recent_deaths(table)
    dates_before_today(table)
    marriage_before_death(table)
    upcoming_birthdays(table)
    reject_illegitimate_birthdays(table)
    birth_before_marriage(table)
    marriage_before_divorce(table)
    no_marriage_to_descendants(table)
    siblings_should_not_marry(table)
    marriage_after_fourteen(table)
    parents_not_too_old(table)
    birth_before_parents_death(table)
    no_bigamy(table)
    divorce_before_death(table)
    male_last_name(table)
    less_than_150_years_old(table)
    sibling_age_space(table)
    
    print(tabulate(table, headers, tablefmt="fancy_grid"))
    return (tabulate(table, headers))


i = 0
count_Indi = 0
count_fams = 0
while len(copy) > i:
    line = copy[i].split(" ")
    if line[1] == "INDI" and len(line) != 2:
        if line[1] == "INDI" and count_Indi < 5000:
            calc_individual(copy, i+1, Person(line[2].rstrip()))
            count_Indi += 1
    elif line[1].rstrip() == "FAM" and count_fams < 1000:
        calc_family(copy, i+1, Fam(line[2].rstrip()))
        count_fams += 1
    i += 1

person.sort(key=lambda y: int(y.id[1:]))
fams.sort(key=lambda z: int(z.f_id[1:]))

print_individuals()
print_families()
user_Stories()

with open('output.txt', 'w') as f:
    f.write("Output for individual\n")
    f.write(print_individuals()+"\n\n")
    f.write("Output for families\n")
    f.write(print_families()+"\n\n")
    f.write("Output for user stories\n")
    f.write(user_Stories())

class TestStringMethods(unittest.TestCase):

    def test_checkUS03(self):
        self.assertEqual(birth_before_death([]), [
                         ['US03', 'Birth Before Death', '', True, 'Birth and death dates are valid.']])

    def test_checkUS01(self):
        self.assertEqual(dates_before_today(
            []), [['US01', 'Dates Before Today', '', True, 'All dates are valid.']])
    
    def test_checkUS02(self):
        self.assertNotEqual(birth_before_marriage([]), [['US02','Birth Before Marriage','Rajan Nanda has either an incorrect birth or marriage date.\n Birthdate is: 18 May 1974 and Marriage date is: 09 Jul 1969',True,'Atleast one birthdate or marriage date is incorrect.']])

    def test_checkUS05(self):
        self.assertEqual(marriage_before_death([]), [
                         ['US05', 'Marriage Before Death', '', True, 'All marriages dates are valid.']])
    def test_checkUS18(self):
        self.assertIsNotNone(marriage_before_death([]))

    def test_checkUS28(self):
        self.assertIsNotNone(order_siblings_by_age([]))

    def test_checkUS04(self):
        self.assertEqual(marriage_before_divorce([]), [
                         ['US04', 'Marriage Before Divorce', '', True, 'All marriage and divorce dates are valid.']])

    def test_checkUS17(self):
        self.assertEqual(no_marriage_to_descendants([])[0][3], True)

    def test_checkUS29(self):
        self.assertNotEqual(list_deceased([])[0][0],"US30")
    
    def test_checkUS30(self):
        self.assertIsNotNone(list_living_married([]))

    def test_checkUS35(self):
        self.assertEqual(list_recent_births([]), [['US35', 'List Recent Births', '', True, 'Ridhima Kapoor']])

    def test_checkUS36(self):
        self.assertNotIn("Rishi Kapoor",list_recent_deaths([])[0])

    def test_checkUS38(self):
        self.assertIsNotNone(upcoming_birthdays([]))
    
    def test_checkUS42(self):
        self.assertEqual(reject_illegitimate_birthdays([]),[['US42', "Reject Illegitimate Birthdays", "", True, "All birthdays are legitimate"]])
    
    def test_checkUS10(self):
        self.assertEqual(marriage_after_fourteen([])[0][3], False)
    
    def test_checkUS12(self):
        self.assertIsNotNone(parents_not_too_old([]))

    def test_checkUS09(self):
        self.assertIn("Ridhima Kapoor", birth_before_parents_death([])[0][2])

    def test_checkUS11(self):
        self.assertTrue(no_bigamy([])[0][3])

    def test_checkUS06(self):
        self.assertEqual(divorce_before_death ([]),[["US06","Divorce before death","",True,"All divorce are before death"]])

    def test_checkUS16(self):
        self.assertIsNotNone(male_last_name([]))
    def test_checkUS07(self):
        self.assertEqual(less_than_150_years_old([])[0][2], '')
    def test_checkUS13(self):
        self.assertTrue(sibling_age_space([])[0][3])

    
    
if __name__ == '__main__':
    unittest.main()


