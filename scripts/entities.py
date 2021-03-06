import re
from scripts.tags import tag
from pyquery import PyQuery as pq
from datetime import datetime

def process_xml(par):
    text = ''
    for run in pq(par)('w|r'):
        text += run.text
    return text

def clean_xml(xml):
    return re.sub(r"\s\&\s", " &amp; ", xml)

class Parties:
    def _format(self, tagger, raw_str):
        return re.sub(r"([A-Z][A-Z\s+.]+)", lambda entity: tagger(entity.group().title().rstrip()), raw_str)

    def format_for_xml(self, raw_str):
        return tag.parties(self._format(tag.party, raw_str))

    def format_for_html(self, raw_str):
        return tag.h1(self._format(tag.em, raw_str))

    def __init__(self, raw_str):
        self.xml = self.format_for_xml(clean_xml(raw_str))
        self.html = self.format_for_html(raw_str)

class Casename:
    def format_for_db(self, raw_str, name_abbreviation):
        name = re.sub(r"<footnotemark>\d+<\/footnotemark>", "", raw_str)
        return re.sub(r"[A-Z][A-Z]+", lambda entity: entity.group().title(), name), name_abbreviation

    def format_for_xml(self, raw_str, name_abbr_str):
        name = re.sub(r"<footnotemark>\d+<\/footnotemark>", "", raw_str)
        title = re.sub(r"[A-Z][A-Z]+", lambda entity: entity.group().title(), name)
        name_xml = tag.name(title)
        name_parts = name_xml.split('<name')
        name_xml = '<name' + name_parts[0] + " abbreviation='" + name_abbr_str + "'" + name_parts[1]
        return tag.name(title)

    def format_for_html(self, raw_str):
        name = re.sub(r"<footnotemark>\d+<\/footnotemark>", lambda footnote: tag.sup(Footnote.get_footnote_num(footnote.group())), raw_str)
        title = re.sub(r"[A-Z][A-Z\s+.]+", lambda entity: tag.em(entity.group().title()), name)
        return tag.h1(title)

    def __init__(self, raw_str, name_abbr_str):
        clean_xml_str = clean_xml(raw_str)
        clean_xml_abbr = clean_xml(name_abbr_str)
        self.xml = self.format_for_xml(clean_xml_str, clean_xml_abbr)
        self.db_name, self.db_name_abbreviation = self.format_for_db(raw_str, name_abbr_str)
        self.html = self.format_for_html(raw_str)

class Footnote:
    number = None

    @classmethod
    def get_footnote_num(self, footnote_str):
        return re.search(r"\d+", footnote_str).group()

    def format_for_xml(self):
        return "<footnotemark>%s</footnotemark>" % self.number

    def __init__(self, xml):
        footnote_id = re.search(r'footnoteReference\s+w\:id\=\"(\d+)\"', xml)
        self.number=int(footnote_id.groups()[0])

class FootnoteContent:
    number = None

    def format_for_xml(self, raw_str):
        return "<footnote label=\"" + str(self.number) + "\">" + tag.p(raw_str)  + "</footnote>"

    def add_to_xml(self, raw_str):
        footnote_parts = self.xml.split("</p></footnote>")
        self.xml = footnote_parts[0] + "</p>" + tag.p(raw_str) + "</footnote>"

    def __init__(self, raw_str, num):
        self.number = num
        clean_xml_str = clean_xml(raw_str)
        self.xml = self.format_for_xml(clean_xml_str)

class Footnotes:
    def format_for_xml(self, raw_list):
        footnotes = ""
        for footnote in raw_list:
            footnotes += clean_xml(footnote.xml + "\n")
        return footnotes

    def __init__(self, raw_list):
        self.xml = self.format_for_xml(raw_list)

class Date:
    def get_enddate_str(self, raw_str):
        return raw_str.split(' - ')[1]

    def get_startdate_str(self, raw_str):
        return re.sub(r'^\w+\.\s+', '', raw_str.split(' - ')[0])

    def format_for_xml(self, raw_str):
        """
        Examples:
        <decisiondate>1997-05-19</decisiondate>
        in <casebody>:
        <decisiondate id="AML" pgmap="66">May 19, 1997.</decisiondate>
        <otherdate id="A6q" pgmap="66">January 9, 1997. -</otherdate>
        """

        enddate = self.get_enddate_str(raw_str)
        decisiondate_casebody = tag.decisiondate(enddate)

        datetime_obj = datetime.strptime(enddate, "%B %d, %Y.")
        decisiondate = tag.decisiondate(datetime.strftime(datetime_obj, "%Y-%d-%m"))

        otherdate = tag.otherdate(self.get_startdate_str(raw_str))
        return decisiondate, decisiondate_casebody, otherdate

    def format_for_html(self, raw_str):
        enddate = self.get_enddate_str(raw_str)
        startdate = self.get_startdate_str(raw_str)
        dates = startdate + " - " + enddate
        return tag.h3(dates)

    def format_for_db(self, raw_str):
        return datetime.strptime(self.get_enddate_str(raw_str), "%B %d, %Y.")

    def __init__(self, raw_str):
        self.xml = self.format_for_xml(raw_str)
        self.db_obj = self.format_for_db(raw_str)
        self.html = self.format_for_html(raw_str)

class Categories:
    def format_for_html(self, raw_str):
        return tag.p(raw_str)

    def format_for_xml(self, raw_str):
        return tag.categories(raw_str)

    def __init__(self, raw_str):
        clean_xml_str = clean_xml(raw_str)
        self.xml = self.format_for_xml(clean_xml_str)
        self.html = self.format_for_html(raw_str)

class Judges:
    def format_for_db(self, raw_str):
        judges = re.sub(r'Present:|C.J.,|JJ.|&|\s{1}', '', raw_str).split(',')
        judges.pop()
        return judges

    def format_for_html(self, raw_str):
        return tag.h4(raw_str)

    def format_for_xml(self, raw_str):
        return tag.judges(raw_str)

    def __init__(self, raw_str):
        clean_xml_str = clean_xml(raw_str)
        self.xml = self.format_for_xml(clean_xml_str)
        self.db_list = self.format_for_db(raw_str)
        self.html = self.format_for_html(raw_str)

class Author:
    def format_for_html(self, raw_str):
        return tag.bold(raw_str)

    def format_for_xml(self, raw_str):
        return tag.author(raw_str)

    def __init__(self, raw_str):
        raw_str = re.sub(r'\t', '', raw_str)
        clean_xml_str = clean_xml(raw_str)
        self.xml = self.format_for_xml(clean_xml_str)
        self.html = self.format_for_html(raw_str)

class Appearance:
    def format_for_xml(self, alist):
        appearance_string = ""
        for p in alist:
            appearance_string += clean_xml(tag.attorneys(p) + "\n")
        return appearance_string

    def format_for_html(self, plist):
        appearance_string = ""
        for p in plist:
            if 'footnotemark' in p:
                p = re.sub(r"<footnotemark>\d+<\/footnotemark>", lambda footnote: tag.sup(Footnote.get_footnote_num(footnote.group())), p)
            appearance_string += clean_xml(tag.p(p) + "\n")
        return appearance_string

    def __init__(self, plist):
        self.html = self.format_for_html(plist)
        self.xml = self.format_for_xml(plist)

class CaseText:
    def format_for_html(self, plist):
        casetext_string = ""
        for p in plist:
            if 'footnotemark' in p:
                p = re.sub(r"<footnotemark>\d+<\/footnotemark>", lambda footnote: tag.sup(Footnote.get_footnote_num(footnote.group())), p)
            casetext_string += clean_xml(tag.p(p) + "\n")
        return casetext_string

    def format_for_xml(self, plist):
        casetext_string = ""
        for p in plist:
            casetext_string += clean_xml(tag.p(p) + "\n")
        return casetext_string

    def __init__(self, plist):
        self.html = self.format_for_html(plist)
        self.xml = self.format_for_xml(plist)

class Headnotes:
    def format_for_xml(self, hlist):
        headnotes_string = ""
        for h in hlist:
            headnotes_string += clean_xml(tag.p(process_xml(h)) + "\n")
        return headnotes_string

    def __init__(self, plist):
        self.xml = self.format_for_xml(plist)
        self.html = self.format_for_xml(plist)

class Court:
    def set_lower_court(self, date_string):
        self.lower_court = re.match(r'\w+', date_string).group()
        self.xml.append(tag.court(self.lower_court))

    def __init__(self):
        self.xml = []
        pass

class Citation:
    def format_for_xml(self, raw_str):
        return tag.citation(raw_str)

    def __init__(self, raw_str):
        clean_xml_str = clean_xml(raw_str)
        self.xml = self.format_for_xml(clean_xml_str)
