import random
import string

import easyocr
import os
import wonderwords
import faker
import csv

def main():
    if os.path.exists('test_data.csv'):
        os.remove('test_data.csv')
    makeClassifierDataset('../data/templates/CompoundPhysical.txt', 'Compound Parameters', 100,0.05)
    makeClassifierDataset('../data/templates/CouponCode.txt', 'Coupon Code', 100,0.05)
    makeClassifierDataset('../data/templates/FinalReport.txt', 'Final Report', 100,0.05)
    makeClassifierDataset('../data/templates/LobbyistReport.txt', 'Lobbyist Report', 100,0.05)
    makeClassifierDataset('../data/templates/Mutagenicity.txt', 'Mutagenicity', 100,0.05)
    makeClassifierDataset('../data/templates/SalesPromotion.txt', 'Sales Promotion', 100,0.05)
    makeClassifierDataset('../data/templates/Sample.txt', 'Sample', 100,0.05)
    makeClassifierDataset('../data/templates/TestSubstance.txt', 'TestSubstance', 100,0.05)
    makeClassifierDataset('../data/templates/Tobacco.txt', 'Tobacco', 100,0.05)
    makeClassifierDataset('../data/templates/UrbanCenter.txt', 'Urban Center', 100,0.05)
    

def makeClassifierDataset(dir, docType, num, OCRMisidentificationChance):
    rword = wonderwords.RandomWord()
    rsent = wonderwords.RandomSentence()
    fake = faker.Faker()

    template = open(dir, 'r')
    line = template.readline()
    segmants = line.split(" ")
    data = []

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

        data.append([finalString, docType])
    with open('test_data.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)

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