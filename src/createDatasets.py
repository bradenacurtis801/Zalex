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
    
    templates = {
        'Compound Parameters': '../data/templates/CompoundPhysical.txt',
        'Coupon Code': '../data/templates/CouponCode.txt',
        'Final Report': '../data/templates/FinalReport.txt',
        'Lobbyist Report': '../data/templates/LobbyistReport.txt',
        'Mutagenicity': '../data/templates/Mutagenicity.txt',
        'Sales Promotion': '../data/templates/SalesPromotion.txt',
        'Sample': '../data/templates/Sample.txt',
        'TestSubstance': '../data/templates/TestSubstance.txt',
        'Tobacco': '../data/templates/Tobacco.txt',
        'Urban Center': '../data/templates/UrbanCenter.txt',
    }

    for label, path in templates.items():
        makeClassifierDataset(path, label, 100, 0.05, list(templates.values()))
    
def get_sentence_fragment(template, min_length=5, max_length=20):
    tokens = template.split(" ")
    if len(tokens) < min_length:
        return template
    framgent_range = random.randint(min_length, min(max_length, len(tokens)))
    start_index = random.randint(0, len(tokens) - framgent_range)
    fragment = tokens[start_index:start_index + framgent_range]
    return " ".join(fragment)

def makeClassifierDataset(dir, docType, num, OCRMisidentificationChance, all_templates):
    rword = wonderwords.RandomWord()
    rsent = wonderwords.RandomSentence()
    fake = faker.Faker()

    template = open(dir, 'r')
    line = template.readline()
    segmants = line.split(" ")
    data = []

    for i in range(num):
        genCopy = ""
        if random.random() < 0.1:
            other_template_path = random.choice(all_templates)
            if other_template_path != dir:
                with open(other_template_path, 'r') as other_file:
                    other_text = other_file.readline()
                    other_fragment = get_sentence_fragment(other_text)
                    genCopy += other_fragment
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
    
    file_exists = os.path.exists('test_data.csv')

    with open('test_data.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['text', 'label'])
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