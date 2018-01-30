#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import logging
import os
import glob
import subprocess
import sys
import time
import urllib.request
from uuid import uuid4

from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, InlineQueryHandler
from telegram.ext.dispatcher import run_async

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('bot.ini')

updater = Updater(token=config['KEYS']['bot_api'])
path = config['DATA']['path']
link = config['DATA']['url']
sudo_users = config['ADMIN']['sudo']
sudo_usernames = config['ADMIN']['usernames']
dispatcher = updater.dispatcher

def get_latest_build(build_type):
    files = glob.glob(path + build_type + "/*.zip")
    if len(files) == 0:
        return ""
    latest_file = max(files, key=os.path.getctime)
    latest_file = latest_file.replace(path + build_type + '/', '')
    latest_changelog = latest_file.replace(".zip", "_changelog.txt")
    return {'file_name': latest_file, 'changelog_file': latest_changelog}


def publishbeta(bot, update):
    if not isAuthorized(update):
        sendNotAuthorizedMessage(bot, update)
        return
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=ChatAction.TYPING)
    newest_build = get_latest_build("beta")
    latest_file = newest_build['file_name']
    latest_changelog = newest_build['changelog_file']
    os.rename(path + "beta/" + latest_file, path + "stable/" + latest_file)
    os.rename(path + "beta/" + latest_changelog, path + "stable/" + latest_changelog)
    base_url = link + "stable/"
    build_link = "*Latest beta build promoted to stable*\n\n*Link* : [ZIP]({})\n\n*Changelog* : [Changelog]({})" \
        .format(base_url + latest_file,
                base_url + latest_changelog)
    update.message.reply_text(build_link, parse_mode="Markdown")


def publishalpha(bot, update):
    if not isAuthorized(update):
        sendNotAuthorizedMessage(bot, update)
        return
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=ChatAction.TYPING)
    newest_build = get_latest_build("alpha")
    latest_file = newest_build['file_name']
    latest_changelog = newest_build['changelog_file']
    os.rename(path + "alpha/" + latest_file, path + "beta/" + latest_file)
    os.rename(path + "alpha/" + latest_changelog, path + "beta/" + latest_changelog)
    base_url = link + "beta/"
    build_link = "*Latest alpha build promoted to beta*\n\n*Link* : [ZIP]({})\n\n*Changelog* : [Changelog]({})" \
        .format(base_url + latest_file,
                base_url + latest_changelog)
    update.message.reply_text(build_link, parse_mode="Markdown")


def _latest_test_build():
    build_type = "test"
    newest_build = get_latest_build(build_type)
    if newest_build == "":
        return "There are no current {} builds".format(build_type)
    latest_file = newest_build['file_name']
    latest_changelog = newest_build['changelog_file']
    base_url = link + build_type + '/'
    build_link = "*Latest {} build*\n\n*Link* : [ZIP]({})\n\n*Changelog* : [Changelog]({})"\
        .format(build_type,
                base_url + latest_file,
                base_url + latest_changelog)
    return build_link


def latest_test_build(bot, update):
    build_link = _latest_test_build()
    update.message.reply_text(build_link, parse_mode="Markdown")


def _latest_beta_build():
    build_type = "beta"
    newest_build = get_latest_build(build_type)
    if newest_build == "":
        return "There are no current {} builds".format(build_type)
    latest_file = newest_build['file_name']
    latest_changelog = newest_build['changelog_file']
    base_url = link + build_type + '/'
    build_link = "*Latest {} build*\n\n*Link* : [ZIP]({})\n\n*Changelog* : [Changelog]({})"\
        .format(build_type,
                base_url + latest_file,
                base_url + latest_changelog)
    return build_link


def latest_beta_build(bot, update):
    build_link = _latest_beta_build()
    update.message.reply_text(build_link, parse_mode="Markdown")


def _latest_alpha_build():
    build_type = "alpha"
    newest_build = get_latest_build(build_type)
    if newest_build == "":
        return "There are no current {} builds".format(build_type)
    latest_file = newest_build['file_name']
    latest_changelog = newest_build['changelog_file']
    base_url = link + build_type + '/'
    build_link = "*Latest {} build*\n\n*Link* : [ZIP]({})\n\n*Changelog* : [Changelog]({})"\
        .format(build_type,
                base_url + latest_file,
                base_url + latest_changelog)
    return build_link


def latest_alpha_build(bot, update):
    build_link = _latest_alpha_build()
    update.message.reply_text(build_link, parse_mode="Markdown")


def _latest_stable_build():
    build_type = "stable"
    newest_build = get_latest_build(build_type)
    if newest_build == "":
        return "There are no current {} builds".format(build_type)
    latest_file = newest_build['file_name']
    latest_changelog = newest_build['changelog_file']
    base_url = link + build_type + '/'
    build_link = "*Latest {} build*\n\n*Link* : [ZIP]({})\n\n*Changelog* : [Changelog]({})"\
        .format(build_type,
                base_url + latest_file,
                base_url + latest_changelog)
    return build_link


def latest_stable_build(bot, update):
    build_link = _latest_stable_build()
    update.message.reply_text(build_link, parse_mode="Markdown")


def id(bot, update):
    update.message.reply_text(str(update.message.chat_id))


def restart(bot, update):
    if isAuthorized(update):
        bot.sendMessage(update.message.chat_id, "Bot is restarting...")
        time.sleep(0.2)
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        sendNotAuthorizedMessage(bot, update)


def ip(bot, update):
    with urllib.request.urlopen("https://icanhazip.com/") as response:
        bot.sendMessage(update.message.chat_id, response.read().decode('utf8'))


def update(bot, update):
    if isAuthorized(update):
        subprocess.Popen('bash update.sh', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        restart(bot, update)


def execute(bot, update, direct=True):
    try:
        user_id = update.message.from_user.id
        command = update.message.text
        inline = False
    except AttributeError:
        # Using inline
        user_id = update.inline_query.from_user.id
        command = update.inline_query.query
        inline = True

    if command.split(' ')[0] in ['beta', 'alpha', 'stable']:
        build_link = ""
        build_type = command.split(' ')[0]
        if build_type == "beta": build_link = _latest_beta_build()
        elif build_type == "alpha": build_link = _latest_alpha_build()
        elif build_type == "stable": build_link = _latest_stable_build()
        elif build_type == "test": build_link = _latest_test_build()
        if not inline:
            bot.sendMessage(chat_id=update.message.chat_id,
                text=build_link, parse_mode="Markdown")
            return False
        else:
            return build_link

    if isAuthorizedID(user_id, update.inline_query.from_user.name):
        if not inline:
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = output.stdout.read().decode('utf-8')
        output = '`{0}`'.format(output)

        if not inline:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=output, parse_mode="Markdown")
            return False

        if inline:
            return output
    else:
        return "Die " + update.inline_query.from_user.name


@run_async
def exec_cmd(bot, update, args):
    command = update.message.text.replace('/exec ', '')
    if isAuthorizedID(update.message.from_user.id, update.message.from_user.name):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = output.stdout.read().decode('utf-8')
        output = '`{0}`'.format(output)

        bot.sendMessage(chat_id=update.message.chat_id,
                        text=output, parse_mode="Markdown")
    else:
        return "Don't try " + update.message.from_user.name


def inlinequery(bot, update):
    query = update.inline_query.query
    o = execute(query, update, direct=False)
    results = list()

    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title=query,
                                            description=o,
                                            input_message_content=InputTextMessageContent(
                                                '*{0}*\n\n{1}'.format(query, o),
                                                parse_mode="Markdown")))

    bot.answerInlineQuery(update.inline_query.id, results=results, cache_time=10)


def isAuthorized(update):
    return str(update.message.from_user.id) in sudo_users or update.message.from_user.name in sudo_usernames


def isAuthorizedID(userid, username):
    return str(userid) in sudo_users and username in sudo_usernames


def sendNotAuthorizedMessage(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="@" + update.message.from_user.username + " isn't authorized for this task!")


dispatcher.add_handler(CommandHandler('restart', restart))
dispatcher.add_handler(InlineQueryHandler(inlinequery))
dispatcher.add_handler(CommandHandler('id', id))
dispatcher.add_handler(CommandHandler('exec', exec_cmd, pass_args=True))
dispatcher.add_handler(CommandHandler('ip', ip))
dispatcher.add_handler(CommandHandler('update', update))
dispatcher.add_handler(CommandHandler('publishbeta', publishbeta))
dispatcher.add_handler(CommandHandler('publishalpha', publishalpha))
dispatcher.add_handler(CommandHandler('beta', latest_beta_build))
dispatcher.add_handler(CommandHandler('alpha', latest_alpha_build))
dispatcher.add_handler(CommandHandler('stable', latest_stable_build))
dispatcher.add_handler(CommandHandler('test', latest_test_build))

updater.start_polling(clean=True)
updater.idle()
