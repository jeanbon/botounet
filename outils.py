#!/usr/bin/python
# -*- coding: utf8 -*-

import urllib
import urllib2
import os
import sys
import time
import re
import string
import subprocess
from random import randrange
from __future__ import with

def _(text, *args):
    return text % args

def erreur(message):
    sys.stderr.write(message+"\n")

class googleBlouseur(urllib.FancyURLopener):
    version = "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9b5)"\
            " Gecko/2008041514 Firefox/3.0.3"

def google(expression):
    if not expression:
        return ""
    opener = googleBlouseur()
    page = opener.open("http://www.google.fr/search?q="+\
            expression.replace(" ", "+")).read()
    occurences = re.findall('<cite>(.*?)</cite>', page)
    if len(occurences)<1:
        return ("Rien...", "Rien non plus...", "Et toujours rien.")
    else:
        liens=[]
        for oc in occurences:
            liens.append(oc.split(' ')[0].replace('<b>','').\
                    replace('</b>', ''))
        return liens

def haxor(text, lvl):
    level = str(lvl)
    haxor = {}
    haxor["1"] = ("4", "8", "C", "D", "3", "F", "6", "H", "!", "J", "K", "1",
            "M", "N", "0", "P", "Q", "R", "5", "7", "U", "V", "W", "X", "Y",
            "2")
    haxor["2"] = ("4", "8", "(", "[)", "3", "|=", "6", "[-]", "!", "_/", "|<",
            "1", "|v|", "|\\|", "0", "|*", "0,", "|2", "5", "7", "|_|", "\\/",
            "\\/\\/", "><", "*/", "2")
    haxor["3"] = (("4", "/-\\", "/\\", "@", "∂", "^"),
            ("8", "[3", "I3", "|3"),
            ("<", "(", "["),
            ("I>", "|)", "I)", "|>", "[)", "[>"),
            ("£", "3", "€", "&"),
            ("|=", "[="),
            ("(_+", "6", "9", "(_-"),
            ("[-]", "|-|", "[~]", "}{", "]-["),
            ("!", "|", "]"),
            ("_/", "_|", "_]"),
            ("|<", "|{", "]{"),
            ("1", "|_", "[_", "¬"),
            ("|v|", "[\/]", "[v]", "]v[", "/\\/\\", "(V)"),
            ("|\\|", "/\\/", "[\\]", "₪"),
            ("0", "()", "[]"),
            ("|*", "|°", "|^", "¶", "þ"),
            ("0,", "0_", "()_"),
            ("|2", "|?", "Я", "®", "ʁ"),
            ("5", "$", "z", "§"),
            ("7", "+", "†"),
            ("|_|", "(_)"),
            ("\\/", "√"),
            ("\\/\\/", "`//", "\\\\'", "\\x/", "Ш", "ɰ"),
            ("><", "}{", "Ж", "×"),
            ("*/", "Ψ", "`/", "¥"),
            ("%", "%", "2"))
    haxor["4"] = ("â", "bé", "cé", "dé", "eu", "èf", "gé", "ache", "î", "ji",
            "ka", "èl", "èm", "èn", "ô", "pé", "ku", "èr", "èss", "té", "û",
            "vé", "doublevé", "iks", "igrec", "zèd")
    haxor["5"] = ("⠁", "⠃", "⠉", "⠙", "⠑", "⠋", "⠛", "⠓", "⠊", "⠚", "⠅", "⠇",
            "⠍", "⠝", "⠕", "⠏", "⠟", "⠗", "⠎", "⠞", "⠥", "⠧", "⠽", "⠭", "⠽",
            "⠵",
        {".": "⠲", ",": "⠂", "?": "⠦", ":": "⠆", "!": "⠖", "«": "⠦", "»": "⠴",
            "-": "⠤"})
    haxor["6"] = (".- ", "-... ", "-.-. ", "-.. ", ". ", "..-. ", "--. ",
            ".... ", ".. ", ".--- ", "-.- ", ".-.. ", "-- ", "-. ", "--- ",
            ".--. ", "--.- ", ".-. ", "... ", "- ", "..-", "...- ", ".-- ",
            "-..- ", "-.-- ", "--.. ",
        {" ": " / ", ".": ".-.-.- ", ",": "--..-- ", "?": "..--.. ",
            "!": "-.-.-- ", "'": ".----. ", "/": "-..-. ", "(": "-.--. ",
            ")": "-.---. ", ":": "---... ", ";": "-.-.-. ", "=": "-...- ",
            "+": ".-.-. ", "-": "-....- ", "_": "..--.- ", "\"": ".-..-. ",
            "$": "...-..- ", "@": ".--.-. " })
    haxor["7"] = (u"\u0250", "q", u"\u0254", "p", u"\u0259", u"\u025F",
            u"\u0253", u"\u0265", u"\u0269", u"\u027E", u"\u029E", "l",
            u"\u026F", "u", "o", "d", "b", u"\u0279", "s", u"\u0287", "n",
            u"\u028C", u"\u028D", "x", u"\u028E", "z")
    if not level in haxor:
        return "Le niveau doit être compris entre 1 et %d"%len[haxor]
    out=" "
    for c in string.upper(text):
        if c in string.ascii_uppercase:
            index=ord(c)-65
            if isinstance(haxor[level][index], tuple):
                out+=haxor[level][index]\
                        [randrange(0, len(haxor[level][index])-1)]
            else:
                out+=haxor[level][index]
        elif c in string.punctuation+string.whitespace:
            if len(haxor[level])==27 and\
                    isinstance(haxor[level][26], dict) and\
                    c in haxor[level][26]:
                out+=haxor[level][26][c]
            else:
                out+=" "
        else:
            out+=c
    if level == "7":
        return out[::-1]
    return out

def color(thing, t):
    colors={"msg":32, "notice":33, "info":36, "privmsg":31, "event":35}
    if t in colors:
        return "\033[%dm%s\033[0m"%(colors[t], thing)
    else:
        return thing

def heure():
    return time.strftime("%T")

def date_log():
    return time.strftime("%d/%m/%y %T ")

def test_ecriture(fichier):
    try:
        open(fichier, "w").close()
        return 0
    except IOError, e:
        erreur(_("Impossible d'écrire dans le fichier %s : %d - %s" %\
                (e.filename, e.errno, e.strerror)))
        return 1
def dir_exists(directory):
    try:
        if os.path.isdir(directory):
            return 1
        else:
            print "Le dossier %s n'existe pas. Tentative de création..." %\
                    directory
            os.mkdir(directory)
            print "Réussie !"
            return 1
    except IOError:
        print "Impossible..."
        return 0

class Spellcheck:
    def __init__(self, cmd="aspell -a"):
        self.cmd=cmd
        self.p = subprocess.Popen([cmd], shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)
        self.p.stdout.readline()
    def spell(self, word):
        self.p.stdin.write(word+"\n")
        self.p.stdin.flush()
        resp = self.p.stdout.readline().strip()
        self.p.stdout.readline()
        return self.__traitement(resp)
    def __traitement(self, reponse):
        if "ispell" in self.cmd:
            if "word: ok" in reponse:
                return None
            return reponse[17:-1].split(", ")
        elif "aspell" in self.cmd:
            if reponse[:1]=="#":
                return [""]
            m = reponse.split(": ")
            if len(m)>1:
                return m[1].split(", ")
            else:
                return None
        else:
            return reponse

def triviallogger(connexion, event):
    # Juste un truc que j'ai utilisé pour récupérer un maximum de phrases
    # au hasard, pour le filtre bayesien
    return 1
    with open("trivialog", "a") as fichier:
        fichier.write(event.arguments()[0]+"\n")

def check_junk(phrase):
    try:
        from reverend.thomas import Bayes
        g = Bayes()
        g.load("config/kikoo.bot")
        result = g.guess(phrase)
        print result
        if result:
            return int(result[0][0])
        else:
            return -1
    except:
        return -1

def snif(address):
    from htmlentitydefs import entitydefs
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(),
            urllib2.HTTPDefaultErrorHandler)
    opener.addheaders = [('User-agent', ("Mozilla/5.0 (X11; U; Linux i686; fr; "
            "rv:1.9b5) Gecko/2008041514 Firefox/3.0.3"))]
    urllib2.install_opener(opener)
    pattern = re.compile(r"<title.*?>(.*)</title>")
    if not address.startswith("http://"):
        address = "http://"+address
    try:
        page = urllib2.urlopen(address)
    except urllib2.HTTPError, err:
        return "Erreur %s #@$!" % err.getcode()

    real_addr = (lambda s:"/".join(s[:3])+"/.../"+"/".join(s[-1:])
            if len(s)>4 else "/".join(s))(page.geturl().split('/'))
    content_type = page.info().gettype()
    match = pattern.findall(page.read())
    titre = match[0] if match else "None"
    if not titre:
        return "Rien trouvé :'("
    for entity in entitydefs:
        titre = titre.replace("&"+entity+";", entitydefs[entity])
    return 'Titre : "%s" ; Type de contenu : %s ; Véritable adresse : "%s"'\
            % (titre, content_type, real_addr)

def punctuation(line):
    if re.match(r'^.*([].;»"…:!?%+§),]|:/|:P|:p|T_T|^^|:D+|-_-|><|:-°|:-\'+|:x|:s|é_è|è_é)$',
            line.strip('\n').rstrip()):
        return True
    return False

if __name__ == "__main__":
    print punctuation('Foo.')
    print punctuation('foo.')
    print punctuation('Foo]')
    print punctuation('Foo')
