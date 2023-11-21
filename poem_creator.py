import nltk
nltk.download('cmudict')

import sqlite3, re, random
from nltk.corpus import cmudict
from functools import reduce

class ResourceError(Exception):
    pass

# Ниже работаем с исходными строками и их транскрипциями

class Line(object):

    regex = re.compile("[a-z]+(?:'[a-z]+)?")
    pdict = cmudict.dict()

    @staticmethod
    def verify_and_parse(line):
        '''
            Функция verify_and_parse проверяет каждое слово в строке на его наличие в CMUDICT,
            возвращает значение True/False
            Входные данные:
                line: строка <string>
        '''
        # find all words in content
        words = Line.regex.findall(line.lower())
        if (len(words) == 0):
            return (False, [], None, "No words found")
        for word in words:
            if not (word in Line.pdict):
                return (False, words, None, "No pronunciation found for word '" + word + "'")
        return (True, words, [Line.pdict[word][0] for word in words], "Valid")

    @staticmethod
    def extract_rhyme_phoneme(pron):
        '''
            Функция extract_rhyme_phoneme возвращает уникальный ключ, отсылающий ко всем транскрипциям,
            ривмующимся с данным.
            Входные данные:
                pron: произношение <string>
        '''
        # ищем все гласные в слове, а если их нет, берем всю транскрипцию
        vowels = [(i, vow) for (i, vow) in enumerate(pron) if vow[-1].isnumeric()]
        if (len(vowels) == 0):
            return reduce(lambda x, y: x + y, pron)
        # нам нужна последняя гласная без индекса ударения, а также все следующие за ней согласные
        (i, _) = max(vowels, key=lambda x: x[0])
        return reduce(lambda x, y: x + " " + y, [pron[i][:-1]] + pron[i + 1:])

    def __init__(self, content):
        self.content = content.strip().replace('\n', ' ')
        (self.is_valid, self.words, self.parsed, self.diagnostics) = Line.verify_and_parse(self.content)
        if (self.is_valid):
            self.syllable_count = sum([len([syl for syl in pron if syl[-1].isnumeric()]) for pron in self.parsed])
            last_pron = self.parsed[-1]
            self.rhyme = Line.extract_rhyme_phoneme(last_pron)

    def to_sql_params(self):
        return (self.content, self.syllable_count, self.rhyme,)

# Ниже работаем с базами данных

class DataBase(object):

    def __init__(self, database_path, new=False):
        self.conn = sqlite3.connect(database_path)
        if (new):
            self.reset_database()

    def reset_database(self):
        '''
            Функция reset_database производит сброс настоящей базы данных
        '''
        c = self.conn.cursor()
        c.execute('''DROP TABLE IF EXISTS line;''')
        c.execute('''CREATE TABLE line (id INTEGER PRIMARY KEY,
                                        raw_text TEXT NOT NULL,
                                        syllable_count INTEGER NOT NULL,
                                        rhyme TEXT);''')
        self.conn.commit()

    def insert_many(self, resources):
        '''
            Функция insert_many дополняет настоящую базу данными и возвращет количество строк,
            которые не смогла обработать
            Входные данные:
                resources: данные <string>
        '''
        n = 0
        new_lines = []
        unsuccessful_lines = []
        for resource in resources:
            line = Line(resource)
            if not (line.is_valid):
                unsuccessful_lines.append(line)
            else:
                new_lines.append(line)
        # insert many into our database
        c = self.conn.cursor()
        c.executemany('''INSERT INTO line (raw_text, syllable_count, rhyme) VALUES (?,?,?)''',
                      [line.to_sql_params() for line in new_lines])
        self.conn.commit()
        return unsuccessful_lines

# Ниже работаем над созданием стихотворения

def get_rhyme(word):
    '''
        Функция get_rhyme определяет в слове кластер "последняя гласная + последующие согласные"
        Входные данные:
            word: слово <string>
    '''
    pdict = cmudict.dict()
    pron = pdict[word][0]
    vowels = [(i, vow) for (i, vow) in enumerate(pron) if vow[-1].isnumeric()]
    if (len(vowels) == 0):
        return reduce(lambda x, y: x + y, pron)
    (i, _) = max(vowels, key=lambda x: x[0])
    return reduce(lambda x, y: x + " " + y, [pron[i][:-1]] + pron[i + 1:])

def func1(db, rhyme, x1, x2):
    '''
        Функция func1 создает список строк, имеющих нужный размер и рифмующихся с исходным словом
        Входные данные:
            db: название файла с базой данных <string>
            rhyme: рифма слова word <string>
            x1: минимальный размер строки (по слогам) <int>
            x2: максимальный размер строки (по слогам) <int>
    '''
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    query = """
    SELECT raw_text, syllable_count, rhyme
    FROM line 
    WHERE rhyme = ? AND syllable_count BETWEEN ? AND ?
    ORDER BY RANDOM()
    """
    cur.execute(query, (rhyme, x1, x2))
    data = cur.fetchall()
    return data


def func2(db, rhyme, x1, x2):
    '''
        Функция func2 создает список строк, имеющих нужный размер и НЕ рифмующихся с исходным словом
        Входные данные:
            db: название файла с базой данных <string>
            rhyme: рифма слова word <string>
            x1: минимальный размер строки (по слогам) <int>
            x2: максимальный размер строки (по слогам) <int>
    '''
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    query = """
    WITH DuplicateValue AS (
        SELECT rhyme, COUNT(*) AS CNT
        FROM line
        GROUP BY rhyme
        HAVING COUNT(*) > 1
    )
    SELECT raw_text, syllable_count, rhyme
    FROM line
    WHERE rhyme IN (SELECT rhyme FROM DuplicateValue) AND rhyme != ? AND syllable_count BETWEEN ? AND ?
    ORDER BY rhyme
    """
    cur.execute(query, (rhyme, x1, x2))
    data = cur.fetchall()
    return data


def init(db, word, rhyme_scheme, rhyme, sel_ab, notsel_ab, syllable_count):
    '''
        Функция init создает словарь с готовыми строками стихотворения
        Входные данные:
            db: название файла с базой данных <string>
            word: слово, по которому строится стихотворение <string>
            rhyme_scheme: схема рифмы стиха <string>
            rhyme: рифма слова word <string>
            sel_ab: буква, которой в rhyme_scheme обозначена строка с word <string>
            notsel_ab: отличная от sel_ab буква <string>
            syllable_count: размер строки (по слогам) от n по k <list>
    '''
    print(db, rhyme, syllable_count[0], syllable_count[1])
    data1 = func1(db, rhyme, syllable_count[0], syllable_count[1])
    sample1 = random.sample(data1, k=rhyme_scheme.count(sel_ab))

    data2 = func2(db, rhyme, syllable_count[0], syllable_count[1])
    n = rhyme_scheme.count(notsel_ab)
    j = 0
    while j != n:
        sample = random.sample(data2, k=1)
        s = data2[data2.index(sample[0])]
        indices = [x for i, x in enumerate(data2) if x[2] == s[2]]
        j = len(indices)
    sample2 = random.sample(indices, k=n)

    dic = {}
    line = " ".join(sample1[0][0].split(' ')[:-1] + [word])
    dic[sel_ab] = [line]
    dic[sel_ab] += [sample1[i][0] for i in range(1, len(sample1))]
    dic[notsel_ab] = [sample2[i][0] for i in range(len(sample1))]

    return dic


def poem_creation(db, word, rhyme_scheme, sel_ab, notsel_ab, syllable_count):
    '''
        Функция poem_creation создает итоговый вариант стихотворения
        Входные данные:
            db: название файла с базой данных <string>
            word: слово, по которому строится стихотворение <string>
            rhyme_scheme: схема рифмы стиха <string>
            sel_ab: буква, которой в rhyme_scheme обозначена строка с word <string>
            notsel_ab: отличная от sel_ab буква <string>
            syllable_count: размер строки (по слогам) от n по k <list>
    '''
    rhyme = get_rhyme(word)
    dic = init(db, word, rhyme_scheme, rhyme, sel_ab, notsel_ab, syllable_count)
    poem = ''
    for r in rhyme_scheme:
        poem += dic[r][0][0].upper() + dic[r][0][1:] + '\n'
        dic[r].pop(0)

    return poem