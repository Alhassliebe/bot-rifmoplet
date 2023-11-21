'''
    В данном файле производится обработка текстовых файлов и их перевод в формат баз данных
    Для каждого файла выводится список строк, которые не были обработаны
'''

import nltk
import poem_creator as pc

data = {'Harry Potter and the Prisoner of Azkaban': 'hp.db',
        'The Godfather': 'gf.db', 'Twilight': 'tw.db'}


for txt_file, db_file in data.items():
    poem = pc.DataBase(db_file, True)
    lines = []
    with open(f'Files/{txt_file}.txt', 'r', encoding="utf-8") as inf:
        for line in inf:
            lines += nltk.tokenize.sent_tokenize(line, language='english')
    unsuccessful = poem.insert_many(lines)
    print(str(len(unsuccessful)) + "/" + str(len(lines)) + " failed to parse" + '\n')