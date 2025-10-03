import random
import string

import easyocr
import os
import wonderwords
import faker

def main():
    set = makeClassifierDataset('../data/templates/CompoundPhysical.txt', 100,0.05)
    print(set)

def makeClassifierDataset(dir,num, OCRMisidentificationChance):
    rword = wonderwords.RandomWord()
    rsent = wonderwords.RandomSentence()
    fake = faker.Faker()

    template = open(dir, 'r')
    line = template.readline()
    segmants = line.split(" ")
    copies = []

    for i in range(num):
        genCopy = ""
        for segment in segmants:
            if segment == "{ID}":
                genCopy += str(random.randrange(0,9999))
            elif segment == "{Name}":
                genCopy += fake.name()
            elif segment == "{Sentence}":
                genCopy += rsent.sentence()
            elif segment == "{Paragraph}":
                genCopy += rsent.sentence()+rsent.sentence()+rsent.sentence()
            elif segment == "{Word}":
                genCopy += rword.word()
            elif segment == "{Phone}":
                genCopy += fake.phone_number()
            elif segment == "{Address}":
                genCopy += fake.address()
            elif segment == "{Date}":
                genCopy += fake.date()
            else:
                genCopy += segment
            genCopy += " "

        finalString = ""

        for char in genCopy:
            if random.random() < OCRMisidentificationChance:
                s1 = ['8','S','5','s','B']
                s2 = ['0','O','o','Q']
                s3 = ['i','I','l','/']
                if char in s1:
                    finalString += random.choice(s1)
                elif char in s2:
                    finalString += random.choice(s2)
                elif char in s3:
                    finalString += random.choice(s3)
                else:
                    finalString += random.choice(string.ascii_letters)
            else:
                finalString += char

        copies.append(finalString)

    return copies

def extractText(dir):
    reader = easyocr.Reader(['en'], gpu=False)
    rawData = reader.readtext(dir)
    newPath = "../data/OCRProcessed/{}.txt".format(os.path.splitext(os.path.basename(dir))[0])
    f = open(newPath,'w+')
    justText = ""
    for line in rawData:
        justText += line[1]
        justText += " "
    f.write(justText)
    f.close()

main()