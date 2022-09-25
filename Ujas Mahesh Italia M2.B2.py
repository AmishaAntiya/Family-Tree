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


with open('./M2.B2 Output.txt', 'a') as b:
    for i in range(len(lines)):
        b.write("{}\n".format(lines[i]))
        temp = copy[i].split(' ')
        if len(temp) == 2:
            valid = 'Y' if temp[1] in validTags else 'N'
            b.write("{}|{}|{}\n".format(temp[0], temp[1], valid))
            continue
        valid = 'Y' if temp[1] in validTags else 'N'
        b.write("{}|{}|{}|{}\n".format(
            temp[0], temp[1], valid, ' '.join(temp[2:])))

    
