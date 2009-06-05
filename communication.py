#!/usr/bin/python
# -*- coding: utf8 -*-

import re
import string
from random import randint
import time

#import urllib
import irclib
from math import *

import outils

def init_mainloop(bot): #{{{
    """ Initialisation de certaines variables, avant la boucle principale. """
    # L'heure est en GMT
    bot.events_delayed.append(Event_diff(bot, "22 0 0 * *",
        bot.privmsg, 'bot.channel, "Oh my God day has changed !!§! Halleluja !"'))
    bot.events_delayed.append(Event_diff(bot, "11 37 00 * *",
        bot.privmsg,
        'bot.channel, "Leeeeeeeeeeeeeeeeeeet tiiiiiiiime !!!111 OMGWTFBBQ it\'s'\
                '1337 71|\\\\/||3 !!"'))
    bot.events_delayed.append(Event_diff(bot, "01 14 15 * *",
        bot.privmsg, 'bot.channel, "Pi time ! %f" % pi'))
    bot.events_delayed.append(Event_diff(bot, "* 42 42 * *",
        bot.privmsg, ("bot.channel, '%s:42:42, and I just lost teh game :\\'("
                      " http://www.losethegame.com/ ' % time.localtime()[3]")))
#}}}

def mainloop(bot): #{{{
    """ 
    Code exécuté à intervalles réguliers (quelques millisecondes) dans
    la boucle principale
        
    """
    if bot.getopt("MESSAGES_DIFFERES"):
        # TODO : améliorer les massages différés : système genre crontab.
        # ce sera pour *beaucoup* plus tard.
        for event in bot.events_delayed:
            event.process()
#}}}


class Event_diff: #{{{
    def __init__(self, bot, cron_str, function, args):
        """ 
        "cron_str" utilise la notation de crontab, simplifiée, et permet
        d'exécuter "function" avec les arguments "args" à un moment
        défini. Les arguments (args) doivent *impérativement* êtres
        sous forme de chaine de caractère, comme par exemple :
            Event_diff("* 42 42 * *", self.MP, "self.bot.channel, \"Hello\"")
            Event_diff("0 0 0 * *", self.MP, "self.bot.channel, i
                    time.localtime()")

        Pour ce qui est de la syntaxe de cron_str : 
        crons_str="hh mm ss dd MM" où "hh", "mm" et "ss" sont les heures,
            minutes, secondes, MM le mois, et dd le jour du mois.
        ces options (hh, mm, ss, MM, dd) peuvent prendre comme valeur
                (les nombres sont des exemples) :

            * : pour chaque unité de temps
            2-4 : les unités de temps 2,3,4
            */3 : une unité de temps sur 2 (3, 6, 9...)
            2,4,5 : les unités de temps 2,4,5
            2 : l'unité de temps 2.

        Exemple : "0 30 0 */2 *" : Tous les deux jours, à 0h30

        Remarque : Les formats exotiques comme "23-7/2,8" (tiré du man de
            crontab) ne fonctionnent pas. 

        Voir le manuel de crontab ou sa page wikipédia pour plus
        d'informations.
        
        """
        self.h, self.m, self.s, self.d, self.M = cron_str.split(" ")
        self.delay = 0
        self.bot = bot
        self.function = function
        self.args = args
        self.active = False
        self.last_time = 0

    def __match(self, unit, real_value):
        """ Return true if unit match real_value, else false """
        match_range = re.compile(r"(\d+)-(\d+)").findall(unit)
        if re.match(r"^\*$", unit):
            return True
        elif re.match(r"^\*/\d+$", unit):
            return (True if real_value % int(unit[2:]) == 0 else False)
        elif match_range:
            match_range = [int(a) for a in match_range[0]]
            match_range[1]+=1
            return (True if real_value in range(*match_range) else False)
        else:
            return (True if real_value in [int(a) for a in unit.split(",")]\
                else False)

    def __its_time(self):
        """ return true if every values match """
        t = time.gmtime()
        return (True if (self.__match(self.h, t.tm_hour) and\
                  self.__match(self.m, t.tm_min) and\
                  self.__match(self.s, t.tm_sec) and\
                  self.__match(self.M, t.tm_mon) and\
                  self.__match(self.d, t.tm_mday)) else False)

    def infos(self):
        return "%s %s %s %s %s %s %s"%(self.h, self.m, self.s, self.d, self.M,
                self.function.__name__, self.args)

    def set(self, cron_str, function, *args):
        self.h, self.m, self.s, self.d, self.M = cron_str.split(" ")
        self.function = function
        self.args = args
        self.h, self.m, self.s, self.d, self.M = cron_str.split(" ")

    def set_delay(self, delay, lenght):
        """La fonction s'exécutera toutes les "delay" secondes. "length" est
            la durée pendant laquelle elle s'exécutera.""" 
        # Fonction séparée de l'initialisation car elle encombre un peu les
        # arguments.
        self.delay = delay
        self.length = length

    def process(self):
        if (self.__its_time() or (self.delay and self.last_time and\
                time.time()>=self.last_time+self.delay)) and not self.active :
            self.active = True
            if self.delay:
                if not self.start:
                    self.start = time.time()
                    self.last_time = time.time()
            bot = self.bot # Mieux pour l'évaluation des arguments.
            args = eval(self.args)
            if isinstance(args, (tuple, list, set)):
                self.function(*args)
            else:
                self.function(args)
        if self.active and not self.__its_time():
            self.active = False
#}}}

def repondre(bot, message): #{{{
    """ Ouvre le fichier reponses.bot et renvoie une réponses possibles
            au message.
        Chaque ligne de ce fichier est sous la forme:
            (r"regexp entrée", temps_reflexion, ("messages sortie possible 1",
                "message sortie possible 2")) 
        La fonction message lis chaque expression régulière et si le message
        correspond, elle renvoie une réponse aléatoire de la liste
        correspondante.
        le temps_reflexion n'est pas très intéressant, mais il permet de
        rendre le bot plus "humain". Un gadget, quoi. """
    lignes=bot.read_file(bot.getopt("FICHIER_REPONSES_PRIV"))
    reponse_trouvee=False
    kaptkeudal=("Mh, je ne comprend pas ça, %n.",
            "Qu'est-ce que Ã§a signifie, %n ?",
            "Répète-moi ça un peu plus clairement, %n",
            "Pour que nous nous comprenions, il faudra vous expliquer plus"\
                    " clairement, %n.",
            "Do you speak english, %n ? Because your french is not very good.",
            "Vous devriez faire quelques efforts pour vous exprimer, %n,"\
                    " c'est incompréhensible.",
            "%n: écrivez dans un langage compréhensible !")
    i=1
    for ligne in lignes:
        try:
            regexp, temps_reflexion, reponses_possibles=eval(ligne)
        except SyntaxError, e:
            bot.erreur("reponse : SyntaxError : "+str(i)+" "+e.msg+\
                    " Origine : "+message)
            return "Mon cerveau ne fonctionne plus ! chickenzilla,"\
                    " à l'aide !", 0
        #print regexp, message
        try:
            if re.compile(regexp, re.I).match(message):
                reponse_trouvee=True
                break
        except:
            reponse_trouvee=True
            bot.erreur("reponse : RegexpError : ligne %d" % i)
            return ("Désolé, il y a une erreur dans le fichier qui me sert"\
                    " de cerveau (ligne %d)"%i, 0)
        i+=1
    if reponse_trouvee:
        #reponses_possibles=reponses_possibles[1:-1].split(",")
        return (reponses_possibles[randint(0,len(reponses_possibles)-1)],
                temps_reflexion)
    else: # Sinon, on ajoute le message à la liste des messages non compris
        bot.store(bot.getopt("FICHIER_LOG_PASCOMPRIS"), message)
        return (kaptkeudal[randint(0, len(kaptkeudal)-1)], 1)
#}}}


class PublicCommand: #{{{
    """ Parse a public command """
    def __init__(self, bot, command, expediteur):
        self.bot = bot
        self.expediteur = expediteur
        try:
            self.command, self.args = command.split(" ", 1)
        except:
            self.command, self.args = command, None

        # Command, pattern, syntax
        self.commands = (("help", "!help", "%n"),
                ("calc", "!calc(uler|ulate)?", "%n 1+1"),
                ("google", "!google", "%n <thing to search>"),
                ("haxor", "!h[4a]x[0o]r", "%n <level> <thing to haxorize>"),
                ("kikoo", "!kikoo(lol)?", "%n <phrase kikoololisée (ou pas)>"),
                ("version", "!version", "%n"),
                ("spell", "!spell", "%n <some bad word>"),
                ("snif", "!snif", "%n <adresse à suivre>"),
                ("cass_toi_pov_con", "!cass_toi_pov_con", "%n"),
                ("kick", "!kick$", "%n <pseudo>"),
                ("mute", "!mute$", "%n <pseudo>"),
                ("unmute", "!verbose$", "%n <pseudo>"),
                ("ban", "!ban$", "%n <nick>"),
                ("kickban", "!(kickban|kb)", "%n <nick>"),
                ("banuser", "!banuser", "%n <nick>"),
                ("banmask", "!banmask", "%n <nick>"),
                ("banhost", "!banhost", "%n <nick>"))

    def proceed(self):
        """Evaluate the expression given at the initialization"""
        for c, pattern, usage in self.commands:
            if re.compile(pattern, re.I).match(self.command) and\
                    hasattr(self, "do_"+c):
                func = getattr(self, "do_"+c)
                ret = func(self.args)
                if not ret:
                    return "Mauvaise syntaxe : %s." % usage.replace("%n",\
                            pattern.strip('$'))
                return ret
        ret = self.retrieve_from_file(self.command+" "+self.args if\
                self.args else self.command)
        return ret
        # Même si ret == None, osef.

    def retrieve_from_file(self, args):
        if not args:
            return None
        lignes = self.bot.read_file(self.bot.getopt("FICHIER_REPONSES_PUB"))
        # Récupère les réponses préformatées 
        for i, ligne in enumerate(lignes):
            try:
                regexp, reponse=eval(ligne)
            except SyntaxError, err:
                self.bot.erreur(("reponse_message_pub : SyntaxError : %s ligne"
                        " %d. Origine : %s") % (err.msg, i, args))
                # TODO Rajouter un message à l'admin ?
                return None
            try:
                if re.compile(regexp, re.I).match(args):
                    exp = self.expediteur
                    dest=""
                    stripped=args.split(" ")
                    # genre ("!commande", "dest")
                    if len(stripped)>1 and args[0]=="!":
                        # si il y a un pseudo en plus, on remplace le
                        # pseudo de l'expéditeur par celui-là
                        dest=stripped[1]
                        if not re.match(".*%d", reponse):
                            exp=stripped[1]
                    return reponse.replace('%n', exp).replace('%d', dest)
            except re.error, err:
                self.bot.erreur("réponse_messages_pub : RegexpError : %s ligne"\
                        " %d" % (self.bot.getopt("FICHIER_REPONSES_PUB"), i))
                return None

    def do_calc(self, args):
        if not args:
            return None
        try:
            strings = re.finditer(r".*?([a-z]+)", args)
            for m in strings:
                if not m.group(1) in __import__("math").__dict__:
                    # Si ce n'est pas un élément du module math :
                    # On tente de rendre impossible les exploits...
                    return "Bien essayé :p"
            return args+" = "+str(eval(args))
        except:
            return None

    def do_google(self, args):
        if not args:
            return None
        # Recherche sur google et renvoie les GOOGLE_MAX_RESULTS
        # premiers résultats.
        liste=outils.google(args)
        i=0
        resultats = []
        while i<self.bot.getopt("GOOGLE_MAX_RESULTS"):
            resultats.append("- http://%s" % liste[i])
            i+=1
        return resultats

    def do_haxor(self, args):
        if not args:
            return None
        try:
            level, thing = args.split(" ", 1)
            return outils.haxor(thing, int(level))
        except ValueError:
            return None

    def do_help(self, args):
        commands = zip(*self.commands)[1]
                # On remplace les '[4a]' par '4' et on supprime les "(uler)?"
        return "Commandes disponibles : %s" %\
                " ".join( [re.sub(r"\[(\w)\w*\]", r"\1", s.split("(")[:1][0])\
                for s in commands] )
    
    def do_version(self, args):
        return self.bot.version

    def do_snif(self, args):
        if not args:
            return None
        rep = outils.snif(args.split(' ')[0])
        return rep

    def do_spell(self, args):
        if not args :
            return None
        rep = self.bot.spellcheck.spell(args)
        if rep:
            return "L'orthographe est fausse, voici"\
                    " quelques proposition : "+", ".join(rep)
        else:
            return "L'orthographe est correcte."

    def do_kikoo(self, args):
        """ En test : un filtre à kikoolol..."""
        if not args:
            return None
        result = outils.check_junk(args)
        if result == 1:
            return "C'est bon."
        elif result == 0:
            return "Beaurgl, quelle horreur"
        else:
            return "Hum, je ne sais pas."

    def do_kick(self, args):
        if self.bot.is_admin(self.expediteur):
            self.bot.kick(args.split(' ')[0], "foo")
        return "nothing"

    def do_mute(self, args):
        if self.bot.is_admin(self.expediteur):
            if not args:
                return None
            self.bot.mode(self.bot.channel, "-v %s" % args.split(' ')[0])
            self.bot.ban(nick=args.split(' ')[0], mode="nick")
        return "nothing"

    def do_unmute(self, args):
        if self.bot.is_admin(self.expediteur):
            if not args:
                return None
            self.bot.mode(self.bot.channel, "+v %s" % args.split(' ')[0])
            self.bot.mode(self.bot.channel, "-b %s!*@*" % args.split(" ")[0])
        return "nothing"

    def do_ban(self, args):
        if self.bot.is_admin(self.expediteur):
            if not args:
                return None
            self.bot.ban(nick=args.split(' ')[0], mode="nick")
        return "nothing"

    def do_banuser(self, args):
        if self.bot.is_admin(self.expediteur):
            if not args:
                return None
            self.bot.ban(nick=args.split(' ')[0], mode="user")
        return "nothing"

    def do_banhost(self, args):
        if self.bot.is_admin(self.expediteur):
            if not args:
                return None
            self.bot.ban(nick=args.split(' ')[0], mode="host")
        return "nothing"

    def do_banmask(self, args):
        if self.bot.is_admin(self.expediteur):
            if not args:
                return none
            self.bot.ban(mask=args.split(' ')[0])
        return "nothing"

    def do_kickban(self, args):
        if self.bot.is_admin(self.expediteur):
            if not args:
                return none
            self.bot.ban(nick=args.split(' ')[0], mode="nick")
            self.bot.kick(args.split(' ')[0])
        return "nothing"

    def do_cass_toi_pov_con(self, args):
        if self.bot.is_admin(self.expediteur):
           self.bot.disconnect()
        return "nothing"
#}}}

def repondre_messages_pub(bot, message, exp): #{{{
    # Début définition commandes
    # TODO : refaire ça avec une classe et des fonctions do_*, proprement, quoi
    if re.match("!", message):
        # Gestion du flood :
        # - Un délai de DELAI_COMMANDES entre deux appels
        # - Pas plus de LIMITE_COMMANDES fois la même commande
        # - Une ignorelist des boulays de service.
        if bot.date_derniere_commande+bot.getopt("DELAI_COMMANDES") >\
                time.time():
            # si la dernière commande date de moins de DELAI_COMMANDES
            if bot.prevention == False:
                bot.prevention = True
            #return (bot.channel, "Flood.")
            return ('', '')
        else:
            bot.prevention=False
            bot.date_derniere_commande=time.time()
        commande=message.split(" ")[0]
        if bot.derniere_commande==commande:
            bot.repetitions+=1
        else:
            bot.repetitions=0
            bot.derniere_commande=commande
        if bot.repetitions==bot.getopt("LIMITE_COMMANDES"):
            return (bot.channel, "Hey les gens, faut varier les commandes,"\
                    " un peu. Stop flood nubs.")
        elif bot.repetitions>bot.getopt("LIMITE_COMMANDES"):
            # Si on a dépassé la limite
            return ("", "")
    pubcommand = PublicCommand(bot, message, exp)
    resp = pubcommand.proceed()
    if resp == "nothing":
        return ("", "")
    if resp:
        return (bot.channel, resp)
        # Features pour oxyradio. Deprecated
        # delete all ? Breaks my heart.
        # Fuck, I really don't wanna erase this.
        # Oh, please, help me.
        # PLIZ HELP BIG BADABOUM MULTIPASS
        #
        #if re.match("!(chanson|titre|whatthehellisthatbeautifulsong)",
        #        message) and 0: # désactivé, obsolète :'(
        #    chanson=urllib.urlopen("http://www.oxyradio.net/test"\
        #            "/titreencour.php").read().strip("\n")
        #    if chanson.find("A suivre")!=-1 or not chanson:
        #        if len(bot.derniers_titres)>0:
        #            chanson=bot.derniers_titres[0]
        #        else:
        #            return (bot.chan, "Laissez-moi le temps !")
        #    else:
        #        if len(bot.derniers_titres)==0 or\
        #                chanson!=bot.derniers_titres[0]:
        #            bot.derniers_titres.insert(0, chanson)
        #            if len(bot.derniers_titres) >\
        #                    bot.getopt("LIMITE_HISTORIQUE"):
        #                bot.derniers_titres=bot.derniers_titres[0:-1]
        #    return (bot.channel, "En cours : %s" % chanson)
        #elif re.match("!historique", message) and 0:
        #    ## Fucking flood -> NOTICE ??? FIXME
        #    i=0
        #    for titre in bot.derniers_titres:
        #        if i==0:
        #            (exp, "En cours : %s" % titre)
        #        else:
        #            (exp, "%d > %s" % (i, titre))
        #        i+=1
        #elif re.match("!(back(tothefutur)?|whatthehellwasthatbeautifulsong)",
        #            message):
        #    try:
        #        num=int(message.split(' ')[1])
        #    except:
        #        return (bot.channel, "Il me faut un nombre en argument.")
        #    if len(bot.derniers_titres)-1<num or num<0:
        #        return (bot.channel, "Hum, désolé, je n'ai pas encore enregistré"\
        #                " ce titre dans ma mémoire :).")
        #    else:
        #        return (bot.channel, "%d : %s" %(num, bot.derniers_titres[num]))
    if 0 and check_junk(message)==0 and bot.getopt("TEST_FEATURES"):
        return (bot.channel, "%s : kikoolol spotted." % exp)
    if 0 and not outils.punctuation(message) and not bot.is_admin(exp):
        return (bot.channel, "%s, go apprendre à écrire des phrases, newfag."% exp)
    if re.match('.*:[a-zA-Z_-]+:', message):
        return (bot.channel, "%s, va t'acheter des vrais smileys." % exp)

    if message==bot.last_message:
        bot.combo+=1
    elif bot.combo>1:
        cmb=bot.combo
        bot.combo=1
        awesomeness = ("Double Kill ", "Multi Kill ", "Ultra Kill ",
                "Monster Kill ", "Killing Spree ", "Rampage ",
                "Dominating !", "Unstopable !!", "GODLIKE !!!")
        return (bot.channel, "Combo ! +%d%% ! %s!!"%((cmb-1)*10,
            (awesomeness[cmb-2] if cmb-2<len(awesomeness) else\
                    "BUFFER OVERFLOW !")))
    regexp=re.compile(r"(?P<avant>.*)c'est (?P<entre>(?!(dans|pour|\W) ))"\
            "?(?P<sujet>des|les|tes|mes|ses|leurs)", re.I)
    if regexp.match(message):# and CHAN=="#oxyradio":
        def sub(g):
            avant=g.group('avant')
            entre=g.group('entre')
            sujet=g.group('sujet').upper()
            if not entre:
                entre=""
            elif entre in ("que ", "pas "):
                return avant+"CE NE SONT "+entre+sujet
            return avant+"CE SONT "+entre+sujet
        return (bot.channel, "Correction : "+regexp.sub(sub, message)+", "+\
                exp+" (Sinon Nazou te fouettera avec une hachette)")
    if re.compile(r".*(croivent|croyent)").match(message):
        def sub(g):
            avant=g.group('avant')
            return avant+"CROIENT"
        regexp=re.compile(r"(?P<avant>.*)(croyent|croivent)", re.I)
        return (bot.channel, "Correction : %s, %s (Sinon MrFreeze^ va te"\
                " faire du mal)" % (regexp.sub(sub, message), exp))
    return ("", "")
#}}}

def admin(bot, exp, message): #{{{
    cmd, args = message.split(' ')[0], message.split(' ')[1:]
    if re.match("(deco(nnexion)?|d[eé]gage)", cmd):
        bot.disconnect(bot.getopt("QUIT_MESSAGE"))
    elif re.match("(reload|recharger)", cmd):
        bot._reload()
        bot.privmsg(exp, "Fichiers rechargés")
    elif re.match(".*(tg|chut|tais-toi|verb)", cmd):
        if 'on' in args:
            bot.speak(True)
        else:
            bot.speak(False)
    elif cmd =='unignore':
        bot.unignore(args[0])
    elif cmd =='ignorelist':
        bot.print_ignorelist(exp)
    elif cmd =='ignore':
        bot.ignore(args[0])
    else:
        bot.privmsg(exp, "Commande inconnue")
#}}}
