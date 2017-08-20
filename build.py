#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import logging
import os
import subprocess
import glob

import time

import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent
from uuid import uuid4

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('bot.ini')

updater = Updater(token=config['KEYS']['bot_api'])
path = config['PATH']['path']
sudo_users = config['ADMIN']['sudo']
sudo_usernames =  config['ADMIN']['usernames']
dispatcher = updater.dispatcher


def id(bot, update):
    update.message.reply_text(str(update.message.chat_id))

def build(bot, update):
    if isAuthorized(update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Building and uploading to the chat")
        os.chdir(path)
        build_command = ['./gradlew', 'assembleDebug']
        subprocess.call(build_command)
        filename = glob.glob(path+"app/build/outputs/apk/debug/*.apk")[0]
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.UPLOAD_DOCUMENT)
        bot.sendDocument(
            document=open(filename, "rb"),
            chat_id=update.message.chat_id)
    else:
        sendNotAuthorizedMessage(bot, update)


def restart(bot, update):
    if isAuthorized(update):
        bot.sendMessage(update.message.chat_id, "Bot is restarting...")
        time.sleep(0.2)
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        sendNotAuthorizedMessage(bot, update)

def isAuthorized(update):
    return str(update.message.from_user.id) in sudo_users and update.message.from_user.name in sudo_usernames

def sendNotAuthorizedMessage(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id,
                        action=ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="@" + update.message.from_user.username + " isn't authorized for this task!")


build_handler = CommandHandler('build', build)
restart_handler = CommandHandler('restart', restart)

dispatcher.add_handler(build_handler)
dispatcher.add_handler(restart_handler)

updater.start_polling()
updater.idle()
