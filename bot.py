#!/usr/bin/env python
# -*- coding: utf8 -*-

# ATTENTION : Ce fichier va de paire avec le fichier "communication.py"
# Ils ont été séparés pour pouvoir éditer une partie du code sans devoir
# redémarer le bot.

# WARNING : This file has to be with the file "communication.py"
# They have been separated to make you able to edit a part of code without
# having to restart the bot.


__version__ = "0.1" # frozen, do not edit this !!1
# Last edition, french notation
__date__ = "04/03/09"
__hour__ = "15:45" # completely useless...
__revision__ = 13 # +~200 before I started this :-°

# Initialization {{{
import os
import time
import string
import sys
import re
import threading
import Queue # But why is this capitalized ???

import textwrap
import irclib
from urllib import urlopen
from cmd import Cmd
import readline # Is this useful ? (for the cmd module)
from getopt import GetoptError, getopt as parse_opts
import ConfigParser
from random import randint
from __future__ import with
from outils import _

communication = __import__("communication")
outils = __import__("outils")
# Rajouter les modules à recharger avec la commande /reload
# Add modules to reload with the '/reload' cmd
modules_to_reload = [communication, outils]

USAGE = """Usage :\n
$ python %s [-h] [-c channel] [-s serveur] [--ipv6] [-n nick] [-p port]
        [--filtre-grosmots]

  -a mot_de_passe ou --admin-pass=mot_de_passe : le mot de passe de
    l'administrateur
  -c channel ou --channel=channel : rejoindre le chan spécifié (laisser vide pour
    ne rien rejoindre.
  -h ou --help : Affiche l'aide. Eh oui.
  -n pseudo ou --nick=pseudo : définit le pseudo
  -p port ou --port=port : définit le port.
  -s serveur ou --server=serveur : connexion au serveur spécifié.
  --ipv6 : utiliser l'ipv6.
  --ssl : se connecter en ssl
  --nickserv-pass : le mot de passe qui sera envoyé au serveur de pseudos
  --filtre-grosmots : active le la correction des rustres.
  --messages-differes : active les messages differes.
""" % sys.argv[0]
# }}}


# TODO DELETE ALL THIS SHIT
class RechercheTitre(threading.Thread): # {{{
    """Feature pour Oxyradio. """
    def __init__(self, bot):
        self.arret = False
        self.bot = bot
        self.delai = 30
        self.adresse = "http://www.oxyradio.net/test/titreencour.php"
        threading.Thread.__init__(self)
    
    def run(self):
        old_time = time.time()
        while not self.arret and self.bot.alive:
            if time.time()>old_time+self.delai:
                contenu = urlopen(self.adresse).read().strip("\n")
                #print "> "+contenu
                if contenu.find("A suivre:")!=-1:
                    # Tant qu'on a un message "à suivre"
                    old_time = time.time()+self.delai-11
                else:
                    if not self.bot.derniers_titres:
                        # Si la liste est vide
                        self.bot.derniers_titres.append(contenu)
                    elif self.bot.derniers_titres[0]!=contenu:
                        # si le titre a ichangé
                        self.bot.derniers_titres.insert(0, contenu)
                        self.bot.action("Changement de chanson : %s" % contenu)
                    if not self.bot.derniers_titres > \
                            self.bot.getopt('LIMITE_HISTORIQUE'):
                        # Nettoyage
                        self.bot.derniers_titres = \
                                self.bot.derniers_titres[0:-1]
                    old_time = time.time()
            time.sleep(0.1)

    def stop(self):
        self.arret = True
        self.bot.alive = False
#}}}
# End of DELETE


class SendQueue(threading.Thread): #{{{
    """Envoi les messages dans la queue à intervalle réguliers."""
    def __init__(self, bot, delay = 0.5, sep = "###"):
        threading.Thread.__init__(self)
        self.arret = False
        self.bot = bot
        self.delay = delay
        self.sep = sep
        self.setName("SendQueue")
    def run(self):
        while not self.arret and self.bot.alive:
            if not self.bot.msgs_queue.empty():
                mtype, exp, dest, msg = \
                        self.bot.msgs_queue.get().split(self.sep)[:4]
                if mtype == "PM":
                    self.bot.privmsg_filtre(exp, dest, msg)
                elif mtype == "notice":
                    self.bot.notice(dest, msg)
                self.bot.msgs_queue.task_done()
            time.sleep(self.delay)
        self.bot.alive = False
    def stop(self):
        self.bot.action("Arrêt du thread %s... Cela peut prendre du temps." % \
                self.getName(), event_type="info")
        self.arret = True
        self.bot.alive = False
#}}}


class Console(Cmd): # {{{
    """Create a console and parse the commands"""
    def __init__(self, parent):
        """Console(parent)"""
        Cmd.__init__(self)
        self.prompt = '> '
        self.doc_header = "Commandes documentées :"
        self.undoc_header = "Commandes non documentées :"
        self.nohelp = "*** Pas d'aide pour %s."
        self.ruler = "~"
        self.parent = parent
        self.bot = parent.bot

    def do_cron(self, args):
        """
        Some commands to manage the cron-like feature :
         => /cron tab : show all the programmed events
         => /cron set <num> <date> <func> [<argument1>
            [<argument2>,...]] : change the event n°num, by applying the date
            "date" (with the syntax descibed in the man) and the function
            "func" with the args.
            See man to ge more infos
         => /cron del <num> : delete the n°num event
         => /cron add <date> <func> [<argument1>, [<argument2>, ...]] :
            Add an event.
        """
        # Moche, mal foutu, impossible à utiliser, et ça ne fonctionne pas
        try:
            commande, arguments = (args.lower().split(' ')[0],
                args.split(' ')[1:])
        except IndexError:
            self.bot.erreur("Il manque des arguments à cette commande.")
        else:
            def add_event(val, n = 0):
                bot = self.bot
                found = re.compile((r"([-*0-9,/]+) ([-*0-9,/]+)"
                        " ([-*0-9,/]+) ([-*0-9,/]+) ([-*0-9,/]+)"
                        " ([_.a-zA-Z0-9]+) ?(.*)")).findall(" ".join(val))
                if not found:
                    print 'Mauvais format.'
                    return 0
                else:
                    found = found[0]
                    try:
                        thing_to_add = ["%s %s %s %s %s"\
                            % found[0:5], eval(found[5])]
                    except NameError:
                        self.bot.erreur("Fonction inconnue")
                        return 0
                    if len(found) == 7:
                        args = [eval(i) for i in found[6].split(",")]
                        thing_to_add.extend(args)
                    if n == 0:
                        self.bot.events_delayed.append(communication.Event_diff\
                                (*thing_to_add))
                    else:
                        self.bot.events_delayed[n-1].set(*thing_to_add)
                    return 1

            if commande == "tab":
                for i, event in enumerate(self.bot.events_delayed):
                    print " > %2d | %s" % (i+1, event.infos())
            elif commande == "set":
                try:
                    int(arguments[0])
                except:
                    print "Entrez un numéro d'événement (indiqué par /cron tab)"
                    return
                if len(arguments)<7:
                    print "Pas assez d'arguments."
                elif int(arguments[0])>len(self.bot.events_delayed):
                    print "Ce numéro n'existe pas. Tapez /cron tab."
                else:
                    if add_event(args.split(' ')[3:], int(arguments[0])):
                        print "Événement modifié."
            elif commande == "add":
                if len(arguments)<6:
                    print "Pas assez d'arguments."
                else:
                    if add_event(args.split(' ')[2:]):
                        print "Événement ajouté."
            elif commande == "del":
                if len(arguments)<1:
                    print "Pas assez d'arguments."
                else:
                    try:
                        self.bot.events_delayed.pop(int(arguments[0]))
                        print "Événement supprimé."
                    except TypeError:
                        print "Veuillez entrez un nombre en argument."

    def do_exit(self, args):
        """Exit from the console"""
        return -1

    def do_EOF(self, args):
        return self.do_exit(args)

    def do_eval(self, args):
        """/eval foo : try to execute a python cmd. Don't use this."""
        try:
            eval(args)
        except StandardError, err :
            print "Erreur : %s" % str(err)

    def do_freeze(self, args):
        """/freeze : Freeze the screen so you can type some long command """
        self.bot.action("Affichage des messages désactivé.",
                event_type="info")
        self.bot.freezed = True

    def do_ignore(self, args):
        """/ignore bliblu : ignore bliblu by his host """
        if args:
            self.bot.ignore(args.split(" ")[0])

    def do_join(self, args):
        """/join #channel : join a channel"""
        self.bot.join(args.split(" ")[0])

    def do_me(self, args):
        """/me action : send action. """
        self.bot.privmsg(self.bot.channel, "/me "+args)

    def do_names(self, args):
        """/names : get details about the persons in the channel """
        print "\n".join( [" > %s : %s@%s (%s)" % (nick, user, host, mode) for\
                nick, user, host, mode in self.bot.users] )

    def do_nick(self, args):
        """/nick someone : set nick to "someone" """
        self.bot.setnick(args.split(" ")[0])
    
    def do_notice(self, args):
        """/notice someone hello : notice someone."""
        try:
            dest, message = args.split(" ")[0], " ".join(args.split(" ")[1:])
        except IndexError:
            print "Pas assez d'arguments."
        else:
            self.bot.notice(dest, message)

    def do_msg(self, args):
        """/msg foo bar baz : send the message "bar baz" to user "foo" """
        try:
            dest, message = args.split(" ")[0], " ".join(args.split(" ")[1:])
        except IndexError:
            print "Pas assez d'arguments."
        else:
            self.bot.put_queue("PM", dest, dest, message)

    def do_quit(self, args):
        """/quit [msg] : leave the game."""
        self.bot.disconnect(args)
        self.do_exit(None)
        return -1

    def do_unfreeze(self, args):
        """/unfreeze : unfreeze a frozen screen with /freeze """
        self.bot.freezed = False
        self.bot.action("Affichage des messages activé.", event_type="info")

    def do_unignore(self, args):
        """/ignore bliblu : unignore bliblu """
        if args:
            self.bot.unignore(args.split(" ")[0])

    def do_reload(self, args):
        """/reload : reload the modules """
        self.bot._reload()

    def do_set(self, args):
        """/set [opt [val]] : define the value 'val' to the option 'opt'"""
        opts = args.split(" ")
        if len(opts)>1:
            self.bot.setopt(string.upper(opts[0]),
                    string.join(opts[1:]), True)
        elif len(opts) == 1:
            print string.join([string.lower(opt)+" = "+str(arg)\
                    for opt, arg in self.bot.config.items()\
                    if string.upper(opts[0]) in opt], "\n")
        else:
            print string.join([string.lower(opt)+" = "+str(arg)\
                    for opt, arg in self.bot.config.items()], \
                    "\n")

    def do_who(self, args):
        """/who georges : send a who cmd """
        self.bot.server.who(args.split(" ")[0])

    def complete(self, text, state):
        """Redefined completion"""
        #FAIL
        return "/"+Cmd.complete(self, text, state)+" "

    def emptyline(self):
        """Do nothing on empty line"""
        if not self.bot.alive or self.parent.arret:
            return -1
        return 0

    def msg(self, msg):
        """Send a message to the channel"""
        self.bot.privmsg(self.bot.channel, msg)

    def precmd(self, line):
        """Check if line is a command or not. """
        if line == "EOF":
            return line
        if not self.bot.alive or self.parent.arret:
            self.do_exit(None)
            return ""
        if line and line[0]=="/":
            return line[1:]
        else:
            self.msg(line)
            return ""
        #}}}


class WaitInput(threading.Thread): #{{{
    """Attend une entrée de la part de l'utilisateur"""
    def __init__(self, bot):
        threading.Thread.__init__(self)
        self.arret = False
        self.bot = bot
        self.console = Console(self)
        self.setName("WaitInput")

    def run(self):
        if self.bot.gtkwin:
            self.bot.win = self.bot.gtkwin.InputW(self.console)
            self.bot.win.mainloop()
        else:
            self.console.cmdloop()
        self.bot.alive = False
        # En théorie totalement inutile, mais je tiens à éviter un kill -9

    def stop(self):
        self.bot.action(("Arrêt du thread %s... Appuyez sur un touche pour"
                " l'arrêter.") % self.getName(), event_type="info")
        self.console.do_exit(None)
        self.arret = True
        self.bot.alive = False
#}}}


class BotConfig(ConfigParser.SafeConfigParser): #{{{
    def __init__(self):
        dossier_courant = os.getcwd()
        self.config_skel = (
                ("irc", "server", "kornbluth.freenode.net", ("Le serveur "
                        "auquel le bot doit se connecter")),
                ("irc", "port", 6667, "Le port correspondant"),
                ("irc", "ssl", False, "Activer SSL ? "),
                ("irc", "ipv6", False, "Utiliser l'ipv6 ? "),
                ("irc", "channel", "", "Le canal où le bot doit aller"),
                ("irc", "nick", "botounet", "Le pseudo du bot"),
                ("irc", "nickserv_pwd", "", ("Le mot de passe à fournir au bot"
                        " « nickserv » (si le pseudo est enregistré)")),
                ("bot", "admin_pwd", "", ("Le mot de passe administrateur "
                        "(pour commander le bot à distance)")),
                ("bot", "admin_retention", 2592000, ("En secondes, le temps "
                        "durant lequel le host d'un admin est conservé. passé"
                        " ce délai, il devra s'identifier à nouveau. Défaut : "
                        "30 jours.")),
                ("irc", "nomreel", "R2D2", ("Le nom réel. Ne sert pas à grand "
                        "chose sinon en cas de whois.")),
                ("irc", "quit_message", "Mon maître m'a tuer", ("Le message "
                        "qui sera affiché lorsque le bot quitte le canal.")),
                ("bot", "filtre_grosmots", False, ("Le bot devra-t-il "
                        "s'offusquer à chaque gros mot ? ")),
                ("bot", "reponse_publique", True, ("Le bot soit-il répondre "
                        "lorsqu'on s'adresse à lui dans un canal ? ")),
                ("bot", "google_max_results", 3, ("Le nombre maximal de résultats"
                        " pour la commande !google")),
                ("files", "fichier_log_erreurs", dossier_courant+"/error.log",
                    "Le fichier utilisé pour recenser les erreurs"),
                ("files", "dossier_log_msgs", dossier_courant+"/log_messages",
                    "Le dossier où seront enregistrées les conversations"),
                ("files", "fichier_log_privmsgs", dossier_courant+"/privmsgs.log",
                    ("Le fichier où sont enregistrés les messages privés"
                            " reçus.")),
                ("files", "fichier_log", dossier_courant+"/infos.log",
                    ("Le fichier où sont enregistrées les informations"
                            " relatives au fonctionnement")),
                ("files", "fichier_log_pascompris", dossier_courant+"/wtf.log",
                    ("Le fichier où sont enregistrées toutes les répliques"
                    " auquelles le bot n'a pas su répondre.")),
                ("files", "fichier_reponses_priv", dossier_courant+"/reponses.bot",
                    "Les réponses possibles aux différentes répliques"),
                ("files", "fichier_reponses_pub", dossier_courant+"/reponses_pub.bot",
                    "La liste des commandes basiques"),
                ("files", "fichier_grosmots", dossier_courant+"/grosmots.bot",
                    "Un liste de gros mots."),
                ("files", "fichier_ignore", dossier_courant+"/ignorelist.bot",
                    "La liste des gens ignorés"),
                ("files", "fichier_admins", dossier_courant+"/adminlist.bot",
                    "La liste des administrateurs"),
                ("ui", "color_text", True, (" Le affiché localement sera"
                        " coloré ou non ?")),
                ("irc", "msglen_limit", 305, ("The messages are cut in "
                        "submessages if they exceed this limit")),
                ("oxyradio", "limite_historique", 10,
                    ("Spécifique au module de notification de chanson, définit"
                        " le nombre de chansons à garder en mémoire.")),
                ("bot", "limite_commandes", 5, ("Le nombre de commandes "
                        "identiques maximal. Après, le bot est bloqué")),
                ("bot", "messages_differes", True, ("Le bot devra-t-il "
                        "annoncer certains messages à une heure précise ?")),
                ("bot", "delai_commandes", 5, ("Le délai, en secondes, entre "
                        "chaque commande. Avant ce délai, le bot ne répondra "
                        "pas.")),
                ("ui", "use_gtk", True, ("Utiliser une, hum, «interface "
                        "graphique.»")),
                ("bot", "test_features", True, ("Utiliser les fonctions encore"
                        "en test. ATTENTION : cela peut faire planter"
                        " l'application et provoquer une faille dans le"
                        " continuum espace-temps. À vos risques et périls,"
                        " donc."))
                )
        ConfigParser.SafeConfigParser.__init__(self, {'curdir':
            dossier_courant})
        [self.add_section(section) for (section, opt, val, info) in\
                self.config_skel if not self.has_section(section)]
        [ConfigParser.SafeConfigParser.set(self, sect, opt, str(val)) for\
                (sect, opt, val, info) in self.config_skel]

    def items(self, raw=False, vars=None):
        return [(opt, val) for sect, opt, val, _help in self.config_skel]

    def read(self, filenames):
        ConfigParser.SafeConfigParser.read(self, filenames)
        self.set('channel', '#'+self.get('channel'))

    def write(self, fp):
        self.set('channel', self.get('channel')[1:])
        ConfigParser.SafeConfigParser.write(self, fp)
        self.set('channel', '#'+self.get('channel'))

    def get(self, option, raw=False, vars=None):
        if option in zip(*self.config_skel)[1]:
            section = [sect  for sect, opt, val, _help in self.config_skel\
                     if opt == option][0]
            return ConfigParser.SafeConfigParser.get(self, section, option, raw, vars)
        else:
            return None

    def set(self, option, value):
        if option in zip(*self.config_skel)[1]:
            section = [sect for sect, opt, val, _help in self.config_skel\
                     if opt == option][0]
            ConfigParser.SafeConfigParser.set(self, section, option, value)
        else:
            ConfigParser.SafeConfigParser.set(self, ConfigParser.DEFAULTSECT,
                    option, value)

    def help(self, option):
        if option in zip(*self.config_skel)[1]:
            return [usage for sect, opt, val, usage in self.config_skel\
                    if opt == option][0]
        else:
            return None
#}}}


class Bot: #{{{
    """
    Permet de créer et de gérer un bot IRC.

    bot = bot.Bot(handlers = {})
    # des handlers personnalisés peuvent être ajoutés grâce au dictionnaire
    #   handlers :
    # bot = bot.Bot({"whois": log_whois, "welcome": direbonjour}) voir irclib
    #   pour plus d'informations.
    bot.parse_config()
    bot.parse_cmd(sys.argv[1:])
    bot.connexion()
    bot.join("channel")
    bot.mainloop()
    """
    def __init__(self, config_file, handlers={}):
        self.irc = irclib.IRC()
        self.irc.add_global_handler("ctcp", self.gestion_ctcp, -5)
        self.irc.add_global_handler("join", self.user_join, -10)
        self.irc.add_global_handler("kick", self.user_kick, -10)
        self.irc.add_global_handler("namreply", self.namreply, 0)
        self.irc.add_global_handler("none", self.fooevent, 10)
        self.irc.add_global_handler("nosuchnick", self.nosuchnick, 0)
        self.irc.add_global_handler("mode", self.do_mode, -10)
        self.irc.add_global_handler("part", self.user_quit, -10)
        self.irc.add_global_handler("privnotice", self.gestion_notice, -20)
        self.irc.add_global_handler("privmsg", self.do_priv_msg, -15)
        self.irc.add_global_handler("pubmsg", self.gestion_message, -20)
        self.irc.add_global_handler("pubnotice", self.fooevent, -20)
        self.irc.add_global_handler("quit", self.user_quit, -10)
        self.irc.add_global_handler("userhost", self.store_userhost, 0)
        self.irc.add_global_handler("welcome", self.welcomemsg, 0)
        self.irc.add_global_handler("whoisuser", self.store_whois, -5)
        self.irc.add_global_handler("whoreply", self.store_who, -5)
        #self.irc.add_global_handler("yourhost", self.fooevent)
        for handler in handlers: # ajoute les handlers passés en argument/
            self.irc.add_global_handler(handler, handlers[handler], 0)
        self.nombre_repetitions = 0 # Pour l'antiflood
        self.derniere_commande = ""
        self.date_derniere_commande = 0
        self.derniers_titres = list()
        self.freezed = False
        self.print_buf = list()
        self.alive = True
        self.verb = True
        self.last_userhost = ""
        self.last_whois = ""
        self.last_who = ""
        # Users : (nick, user, host, mode)
        self.users = set()
        self.modes = {"admin":"2", "user":"1"}
        self.timeout = 5 #seconds
        # On vérifie la première fois, puis on stocke le pseudo dans la
        # liste pour éviter de devoir refaire un `who', à chaque fois
        self.ignoring = set()

        # Read the configuration
        dossier_courant = os.getcwd()
        self.config = BotConfig()
        self.config.read(config_file)

        # Un vérificateur orthographique.
        self.spellcheck = outils.Spellcheck()
        # La queue contenant les messages
        self.msgs_queue = Queue.Queue(0)
        # Le thread qui la gère
        self.send_queue = SendQueue(self)
        #self.send_queue.setDaemon(True)
        self.send_queue.start()
        self.events_delayed = list()
        self.last_message = ""
        self.combo = 1 # useless feature...
        self.version = __version__

    def __get_type(self, option):
        """Renvoie le type de l'option spécifiée. """
        for opt, defarg, desc in self.config_skel:
            if opt == option:
                return type(defarg)
        return None

    def __is_admin(self, host):
        """ Check if the host is authorized """
        lines = self.read_file(self.getopt("fichier_admins"))
        for line in lines:
            if line.split(' ')[1].strip('\n') == host:
                return True
        return False
        
    def __clean_admins(self):
        """ Clean the admin list """
        lines = self.read_file(self.getopt("fichier_admins"))
        lines = [ line for line in lines if int(line.split(' ')[0]) +
                self.getopt("admin_retention") < time.time() ]
        with open(self.getopt("fichier_admins")) as f:
            f.writelines(lines)

    def _reload(self):
        for module in modules_to_reload:
            try:
                reload(module)
                self.action(_("Le module « %s » a été rechargé.", str(module)),
                        event_type="info")
            except StandardError, e:
                self.erreur("Impossible de recharger le module : %s"% `e.arg`)

    def action(self, text = "", log = True, event_type=""):
        """ Print a message and write in a log file """
        if log:
            self.store(self.getopt("FICHIER_LOG"), outils.date_log()+" "+text)
        if self.getopt("COLOR_TEXT"):
            text = outils.color(text, event_type)
        line = outils.heure()+" "+text
        if self.freezed:
            self.print_buf.append(line)
        else:
            if self.print_buf:
                print "\n".join(self.print_buf)
                self.print_buf = list()
            else:
                print line

    def ban(self, mask="", nick="", mode="nick"):
        """
        There's two way to ban:
            - ban a mask (like *!*@foo.bar)
            - ban the user 'nick' with mode:
                - nick : nick!*@*
                - user : *!user@*
                - host : *!*@host
        """
        if (not mask and not nick) or (nick and not mode):
            return
        if mask:
            self.mode(self.channel, "+b %s" % mask)
        else:
            nick, user, host, m = self.get_user_info(nick)
            if not nick:
                return
            if mode == "user":
                cmd = "+b *!*%s@*" % user
            elif mode == "host":
                cmd = "+b *!*@%s" % host
            else:
                cmd = "+b %s!*@*" % nick
            self.mode(self.channel, cmd)
            

    def connexion(self, server_name = "", port = None, nickname = "", pwd = None,
            username = None, ircname = None, localaddress = "", localport = 0,
            ssl = None, ipv6 = None):
        try:
            self.gtkwin
        except NameError:
            self.start_window()
        if not server_name:
            server_name = self.getopt("server")
        if not port:
            port = int(self.getopt("PORT"))
        if not nickname:
            nickname = self.getopt("NICK")
        if ssl == None:
            ssl = self.getopt("SSL")
        if ipv6 == None:
            ipv6 = self.getopt("IPV6")
        self.server = self.irc.server()
        self.server_name = server_name
        self.nick = nickname
        self.action("Connexion au serveur %s par le port %d avec le pseudo %s"\
                % (server_name, port, nickname), event_type="info")
        self.server.connect(server_name, port, nickname, pwd, username, ircname,
                localaddress, localport, ssl, ipv6)
        if self.getopt("NICKSERV_PWD"):
            self.privmsg("nickserv", "identify "+self.getopt("NICKSERV_PWD"))
        outils.dir_exists(self.getopt("DOSSIER_LOG_MSGS"))
        # Créé le dossier s'il n'existe pas.

    def disconnect(self, quit_message = "noquitmsg"):
        if quit_message == "noquitmsg":
            quit_message = self.getopt("QUIT_MESSAGE")
        self.action("Deconnexion du serveur...", event_type="info")
        self.msgs_queue.join()
        self.send_queue.stop()
        self.server.disconnect(quit_message)
        self.server.close()
        self.alive = False
        self.irc.disconnect_all()

    def do_mode(self, connexion, events):
        self.action("~ %s sets '%s' on %s" % (irclib.nm_to_n(events.source()),
            " ".join(events.arguments()), events.target()), event_type="info")

    def erreur(self, text):
        sys.stderr.write(outils.heure()+" ! "+text+"\n")
        sys.stdout.flush()
        self.store(self.getopt("FICHIER_LOG_ERREURS"),
                outils.date_log()+" "+text)

    def fooevent(self, connexion, evenement):
        print ("> %s Événement :\n>  Type : %s\n>  Source : %s\n>  Dest : %s\n"
                "> Arguments : %s") % (outils.heure(), evenement.eventtype(),
                        evenement.source(), evenement.target(),
                        evenement.arguments())

    def gestion_ctcp(self, connexion, evenement):
        commande = evenement.arguments()[0].upper()
        dest = evenement.source().split('!')[0]
        if commande == "CLIENTINFO":
            connexion.ctcp_reply(dest, 'CLIENTINFO USERINFO VERSION TIME PING')
        elif commande == "PING":
            connexion.ctcp_reply(dest, 'PONG '+evenement.arguments()[1])
        elif commande == "TIME":
            connexion.ctcp_reply(dest,
                    'TIME '+time.strftime("%A %d %B %G, %T %Z"))
        elif commande == "USERINFO":
            connexion.ctcp_reply(dest, 'USERINFO botounet v0.1')
        elif commande == "VERSION":
            connexion.ctcp_reply(dest, 'VERSION botounet v0.1')
        elif commande == "ACTION": # /me
            evenement1 = irclib.Event(evenement.eventtype(),
                    evenement.source(), evenement.target(),
                    evenement.arguments()[1:])
            self.gestion_message(connexion, evenement1, action = True)

    def gestion_message(self, connexion, evenement, action = False):
        if evenement.source():
            exp = irclib.nm_to_n(evenement.source()) # On conserve le nom
            message = evenement.arguments()[0]
            if action:
                self.action("* "+exp+" "+message, log=False, event_type="msg")
            else:
                self.action(exp+" > "+message, log=False, event_type="msg")
            if message.find(self.nick) >= 0 and self.getopt("REPONSE_PUBLIQUE"):
                #Si le message est adressé au bot
                reponse, temps_reflexion = communication.repondre(self,
                        message.replace(self.nick,"").strip(":!,."))
                reponse = reponse.replace("%n", exp)
                temps_reponse = len(reponse)*60/800+temps_reflexion
                # Calcul approximatif du temps qu'il faut pour écrire la répons
                # if temps_reflexion != 0:
                #   time.sleep(temps_reponse)
                self.put_queue("PM", exp, self.channel, reponse)
            else:
                self.do_pub_msg(connexion, evenement, action)
        else:
            action(evenement.arguments()[0], event_type="msg")
        date = time.localtime()
        def date_format():
            date = time.localtime()
            return "%02d%02d%02d" % (date[0], date[1], date[2])
        fichier_log = "%s/%s/%s.log" % (self.getopt('DOSSIER_LOG_MSGS'),
                self.channel, date_format())
        # s'il s'agit d'une action (/me), on rajoute un préfixe devant
        #   le message
        prefix = (action and ["* "+irclib.nm_to_n(evenement.source())] or\
                [""])[0]
        if outils.dir_exists(self.getopt('DOSSIER_LOG_MSGS')+"/"+self.channel):
            # Créer le dossier #channel si il n'existe pas
            self.store(fichier_log, "%s ;; %s ;; %s" % (outils.heure(),
                    irclib.nm_to_n(evenement.source()),
                    prefix+evenement.arguments()[0]))
        self.last_message = message

    def do_priv_msg(self, connexion, evenement):
        # On conserve le nom de l'expéditeur
        exp = irclib.nm_to_n(evenement.source())
        message = evenement.arguments()[0]
        if self.get_user_info(exp)[3] == self.modes['admin']:
            communication.admin(self, exp, message)
        else:
            if message.split(' ')[0:2] == ["auth", self.getopt('admin_pwd')]:
                self.store(self.getopt('fichier_admins'),
                        "%s %s" % (time.time(), self.get_user_info(exp)[2]))
                return
            print "%s + %s > %s" % (outils.heure(), exp, message)
            reponse, temps_reflexion = communication.repondre(self,
                    message.replace(self.nick,"").strip(":!,."))
            reponse = reponse.replace("%n", exp)
            if reponse:
                # Calcul approximatif du temps qu'il faut pour écrire la répons
                #temps_reponse = len(reponse)*60/1000+temps_reflexion
                temps_reponse = 0
                if temps_reflexion != 0:
                    time.sleep(temps_reponse)
                self.put_queue("PM", exp, exp, reponse)
            self.store(self.getopt('FICHIER_LOG_PRIVMSGS'),
                    "%s %s => %s"%(evenement.source(), evenement.arguments(),
                    reponse))

    def do_pub_msg(self, connexion, evenement, action=False):
        exp = irclib.nm_to_n(evenement.source()) # On conserve le nom
        message = evenement.arguments()[0]
        reply = communication.repondre_messages_pub(self, message, exp)
        # Traitement des réponses séparées pour pouvoir recharger le module
        # "communication" sans redémarrer
        if isinstance(reply, (list, set, tuple)):
            dest, reponse = reply
            if isinstance(reponse, (list, tuple, set)):
                for rep in reponse:
                    if rep:
                        self.put_queue("PM", exp, self.channel, rep)
            elif reponse:
                self.put_queue("PM", exp, dest, reponse)
        if self.getopt("FILTRE_GROSMOTS"):
            # Fait plus caguer qu'autre chose : le réseau IRC est rempli
            # de charretiers.
            grosmots = self.read_file(self.getopt('FICHIER_GROSMOTS'))
            for grosmot in grosmots:
                if re.compile(r".*%s" % grosmot.strip("\n"), re.I).\
                        match(message):
                    reponses = ("Restons poli, %n.",
                            ("Nous sommes entre gentlemen, %n, n'use pas de ce"
                                    " genre de langage."),
                            ("Je te conseille de garder ce langage pour tes"
                                    " soirées foot autours d'un bière, %n."),
                            ("Ce n'est pas un langage adapté aux conversations"
                                    " publiques, %n."),
                            "%n: surveille ton langage !",
                            "Roooh, %n !",
                            "Ton langage est décevant, %n.",
                            ("Exprime toi autrement qu'avec ce genre"
                                    " d'expressions, %n."),
                            ("Entre gens bien éduqués, on ne prononce pas ce"
                                    " genre de chose, %n"))
                    self.put_queue("PM", exp, self.channel,
                            reponses[randint(0, len(reponses)-1)].\
                            replace("%n", exp))

    def gestion_notice(self, connexion, evenement):
        exp = evenement.source()
        if exp:
            self.action("[%s] %s" % (irclib.nm_to_n(exp),
                evenement.arguments()[0]), event_type="notice")
        else:
            self.action("[Serveur] %s" % (evenement.arguments()[0]),
                    event_type="notice")

    def getopt(self, option):
        """Récupère la valeur d'une option et renvoie le bon type."""
        option = string.lower(option)
        defval = [val for sect, opt, val, help in self.config.config_skel\
                if opt==option]
        if defval:
            type_val = type(defval[0])
            if type_val == bool:
                return self.config.get(option)[0].lower() == "t"
            else:
                return type(defval[0])(self.config.get(option))
        else:
            return self.config.get(option)

    def get_user_info(self, nick):
        """Return a tuple with the user's informations, or None"""
        for info in self.users:
            if info[0] == nick:
                return info
        return (None, None, None, None)

    def ignore(self, pseudo):
        """Ignore une personne"""
        t = [n for n in self.users if n[0] == pseudo]
        if t:
            pseudo, user, host, mode = t[0]
        else:
            return
        self.ignoring.add(pseudo) # On ajoute le pseudo chez les sales.
        self.store(self.getopt('FICHIER_IGNORE'), host)
        self.action("Ignore : %s (%s@%s)" % (pseudo, user, host),
                event_type="info")
        self.privmsg(self.channel, "/me ignore %s, désormais." % pseudo)

    def is_admin(self, nick):
        """True if nick has the rights"""
        for n, u, h, m in self.users:
            if nick == n:
                if m == self.modes['admin']:
                    return True
                else:
                    return False
        return False

    def join(self, channel = ""):
        """
        Rejoint le canal spécifié, et si aucun n'est spécifié, rejoint
        celui défini dans la configuration.
        """
        if not channel:
            channel = self.getopt("channel")
        self.action("Je rejoins le canal %s." % channel, event_type="info")
        self.server.join(channel)
        self.server.who("*") # Bah oui, ça parait très moche, mais c'est la
            # seule solution que j'ai trouvé pour l'instant :
            # La première requète "who" renvoie "". TODO voir RFC1459 si normal
            # ou si je est juste mauvais.
        self.channel = channel

    def kick(self, nick, comment=":/"):
        self.server.kick(self.channel, nick, comment)

    def read_file(self, fichier):
        """ Retourne un tuple contenant les lignes du fichier."""
        if os.path.exists(fichier):
            with open(fichier, "r") as file:
                lignes = file.readlines()
            return lignes
        else:
            self.erreur(_("Le fichier %s n'existe pas !", fichier))
            return ""

    def names(self, channels = None):
        if channels == None:
            channels = self.channel
        self.server.names(channels)

    def mainloop(self):
        communication.init_mainloop(self)
        try:
            while self.alive:
                communication.mainloop(self)
                self.irc.process_once()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.action("Demande de déconnexion...", event_type="info")
            self.disconnect()
        if self.win:
            self.win.quit()
        if self.alive:
            self.disconnect()

    def mode(self, target, command):
        self.server.mode(target, command)

    def privmsg(self, who, msg):
        if self.verb:
            try:
                if re.match("/me", msg):
                    self.server.action(who, string.join(msg.split(" ")[1:]))
                else:
                    self.server.privmsg(who, msg)
            except irclib.ServerNotConnectedError:
                pass
        else:
            pass

    def privmsg_filtre(self, exp, who, msg):
        if not exp in self.ignoring:
            self.privmsg(who, msg)

    def nosuchnick(self, connexion, argument):
        print "Nick inexistant !"

    def notice(self, who, msg):
        self.server.notice(who, msg)

    def parse_cmd(self, arguments):
        """
        Parse la ligne de commande et renvoie une erreur si un agument
        n'est pas reconnu
        """
        try:
            opts, args = parse_opts(arguments, "a:hc:n:s:p:g",
                    ['admin-pass=', 'channel=', 'help', 'nick=', 'server=',
                    'port=', 'nickserv-pass=', 'filtre-grosmots',
                    'messages-differes', 'ipv6', 'ssl', 'graphic',
                    'no-graphic'])
        except GetoptError, e:
            print "ParseError : Argument « %s » inconnu." % e.opt
            print USAGE
            sys.exit(1)
        for option, value in opts:
            if option in ('-h', '--help'):
                print USAGE
                sys.exit(0)
            elif option in ('-n', '--nick'):
                self.setopt("NICK", value)
            elif option in ('-c', '--channel'):
                self.setopt("channel", value)
            elif option in ('-s', '--server'):
                self.setopt("server", value)
            elif option in ('-p', '--port'):
                try:
                    self.setopt("PORT", int(value))
                except:
                    print "ParseError : Le port doit être un nombre !"
                    sys.exit(1)
            elif option in ('--ipv6'):
                self.setopt("IPV6", True)
            elif option in ('--ssl'):
                self.setopt("ssl", True)
            elif option in ('--filtre-grosmots'):
                self.setopt("FILTRE_GROSMOTS", True)
            elif option in ('--messages-differes'):
                self.setopt("MESSAGES_DIFFERES", True)
            elif option in ('-g', '--graphic'):
                self.setopt('use_gtk', True)
            elif option in ('--no-graphic'):
                self.setopt('use_gtk', False)
            elif option in ('--nickserv-pass'):
                self.setopt("NICKSERV_PWD", value)
            elif option in ('--admin-pass', '-a'):
                self.setopt("ADMIN_PWD", value)

    def print_ignorelist(self, exp):
        self.put_queue("PM", exp, exp, "Ignorés : "+", ".join(self.ignoring))
        # TODO : liste ignore

    def put_queue(self, type, exp, dest, msg):
        """Rajoute le message à la suite de la queue."""
        msgs = textwrap.wrap(msg, self.getopt("MSGLEN_LIMIT"))
        sep = "###"
        for message in msgs:
            print message
            self.msgs_queue.put(sep.join( (type, exp, dest, message) ))

    def setopt(self, option, value = "", affichage = False):
        option = string.lower(option)
        self.config.set(option, str(value))
        if affichage:
            self.action("%s = %s" % (option, str(value)), event_type="info")

    def setnick(self, newnick):
        self.action("Changement du pseudo de %s à %s." %\
                (self.server.get_nickname(), newnick), event_type="info")
        self.server.nick(newnick)

    def speak(self, verb):
        if verb:
            self.action("Activation de la parole.", event_type="info")
        else:
            self.action("Désactivation de la parole.", event_type="info")
        self.verb = verb

    def start_window(self):
        self.gtkwin = None
        if self.getopt("use_gtk"):
            try:
                self.gtkwin = __import__('gtkwin')
            except Warning:
                print "Impossible d'utilser l'interface graphique."
        self.win = None

    def store(self, fichier, message):
        """Ajoute le message à la fin du fichier."""
        try:
            dirs = os.path.dirname(fichier).split(os.sep)
            try: dirs.remove('')
            except: pass
            if len(dirs)>1:
                # Tente de créer les dossiers manquants.
                prefix = "/" if os.name == "posix" else ""
                [outils.dir_exists(prefix+os.sep.join(dirs[:i])) for i in\
                        xrange(0, len(dirs)+1)]
            if os.path.exists(fichier):
                flag = "a"
            else:
                flag = "w"
            with open(fichier, flag) as f:
                f.write(message+"\n")
        except IOError, e:
            outils.erreur(_("Impossible d'écrire dans le fichier %s ! %s" %\
                    (e.filename, e.strerror)))
            return 1
        return 0

    def store_userhost(self, connexion, evenement): # Ne fonctionne pas
        print ("userhost > ", evenement.eventtype(), evenement.source(),
                evenement.arguments()) # XXX
        pass

    def store_users(self, nick, user="", host="", mode="", remove = False):
        """Stocke les informations dans le tableau 'names' """
        if remove:
            self.users = set( [u for u in self.users if u[0] != nick] )
        else:
            if self.users and nick in zip(*self.users)[0]:
                # Si le nick est déjà dedans, on modifie juste.
                self.users = set( [u if u[0] != nick else (nick, user, host,
                    mode) for u in self.users] )
            else:
                self.users.add( (nick, user, host, mode) )
        lignes = self.read_file(self.getopt('FICHIER_IGNORE'))
        if host in lignes or user in lignes:
            self.ignoring.append(nick)

    def store_whois(self, connexion, evenement): # ne fonctionne pas non plus 
        print "whois > "+evenement.arguments() # XXX
        pass

    def store_who(self, connexion, evenement):
        self.last_who = evenement.arguments()
        nick, user, host = self.last_who[4], self.last_who[1], self.last_who[2]
        if self.__is_admin(host):
            mode = self.modes['admin']
        else:
            mode = self.modes['user']
        self.store_users(nick, user, host, mode)

    def unignore(self, pseudo):
        self.ignoring = [p for p in self.ignoring if p != pseudo]
        try:
            pseudo, user, host, mode = [n for n in self.users if n[0] == pseudo][0]
        except:
            return

        lignes = self.read_file(self.getopt('FICHIER_IGNORE'))
        deleted = False
        for i, ligne in enumerate(lignes):
            if host in ligne and ligne.strip("\n\r")!="":
                lignes.pop(i)
                deleted = True
        if deleted:
            try:
                with open(self.getopt('FICHIER_IGNORE'), "w") as f:
                    f.writelines(lignes)
                self.action("Unignore : %s" % host, event_type="info")
                self.privmsg(self.channel, "/me n'ignore plus %s !" % pseudo)
            except IOError:
                self.erreur("unignore : Impossible d'écrire dans le fichier"
                        " %s !" % self.getopt('FICHIER_IGNORE'))

    def user_join(self, connexion, event):
        nick, user_host = event.source().split("!")
        self.action("+ Join : %s [%s]" % (nick, user_host), event_type="event")
        user, host = user_host.split("@")
        if self.__is_admin(host):
            mode = self.modes['admin']
            self.notice(nick, "Vous êtes authentifié en tant qu'administrateur")
        else:
            mode = self.modes['user']
        self.store_users(nick, user, host, mode)

    def user_kick(self, connexion, event):
        nick, user_host = event.source().split("!")
        self.action("! Kick : %s [%s] motif : %s" % (nick, user_host,
                event.arguments()[0]), event_type="event")
        self.store_users(nick, remove = True)

    def user_quit(self, connexion, event):
        nick, user_host = event.source().split("!")
        self.action("- Part : %s [%s] : %s" % (nick, user_host,
                event.arguments()[0]), event_type="event")
        self.store_users(nick, remove = True)

    def welcomemsg(self, connexion, event):
        self.action("Connecté.", event_type="info")

    def namreply(self, connexion, event):
        self.action("Quidams présents : %s" % event.arguments()[2],
                event_type="info")

    def who(self, pseudo):
    #   self.last_userhost = ""
        self.server.who(pseudo)
#}}}

def main(): # {{{
    fichier_config = os.getcwd()+"/botrc"
    try:
        opts, args = parse_opts(sys.argv[1:], "")
        if args:
            fichier_config = args[0]
    except GetoptError:
        pass
    botounet = Bot(fichier_config, {"pubmsg": outils.triviallogger})
    botounet.parse_cmd(sys.argv[1:])
    botounet.start_window()
    botounet.connexion()
    if botounet.getopt("channel"): botounet.join()
    botounet.notice("jeanbon", "Je suis en ligne :)")
    #botounet.mode(botounet.channel, "+m")

    #recup_titre = RechercheTitre(botounet)
    #recup_titre.start()

    attente_entree = WaitInput(botounet)
    attente_entree.start()

    botounet.mainloop()

    #recup_titre.stop()
    #recup_titre.join()

    attente_entree.stop()
    botounet.action("Veuillez appuyer sur entrée...", log=False,
            event_type="info")
    attente_entree.join()

if __name__ == "__main__":
    main()
#}}}

