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


def latest_build(bot, update, args):
    build_type = "beta"
    try:
        build_type = update.message.text.replace('/latest ', '')
    except IndexError:
        pass
    if build_type not in ['beta', 'stable', 'alpha']: build_type = "beta"
    files = glob.glob(path + build_type + "/*")
    latest_file = max(files, key=os.path.getctime)
    latest_file = latest_file.replace(path + build_type + '/', '')
    build_link = "[{}]({})".format(latest_file, link + build_type + latest_file)
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
        subprocess.call(['bash', 'update.sh'])
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


exec_handler = CommandHandler('exec', exec_cmd, pass_args=True)
restart_handler = CommandHandler('restart', restart)
id_handler = CommandHandler('id', id)
ip_handler = CommandHandler('ip', ip)
update_handler = CommandHandler('update', update)
latest_handler = CommandHandler('latest', latest_build, pass_args=True)

dispatcher.add_handler(restart_handler)
dispatcher.add_handler(InlineQueryHandler(inlinequery))
dispatcher.add_handler(id_handler)
dispatcher.add_handler(exec_handler)
dispatcher.add_handler(ip_handler)
dispatcher.add_handler(update_handler)
dispatcher.add_handler(latest_handler)

updater.start_polling()
updater.idle()
