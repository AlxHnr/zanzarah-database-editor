#!/usr/bin/python3

# Database editor for the game "ZanZarah - The Hidden Portal"
# Original repository: https://github.com/AlxHnr/zanzarah-database-editor
#
# The FBS files in the game can't be edited directly with this tool. They must
# be converted to an sqlite database first, by using a converter which can be
# found here:
# https://github.com/Helco/zzio/tree/02a9cee6e3317e80c52f55950310c7b8ff371257
#
# Dependencies:
#   tkinter
#   idlelib
#   pip install --upgrade matplotlib Pillow sv-ttk
#
#
# Copyright (c) 2023 Alexander Heinrich
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from dataclasses import dataclass
from itertools import islice
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from random import randrange
import idlelib.colorizer as colorizer
import idlelib.percolator as percolator
import matplotlib
import re
import sqlite3
import subprocess
import sv_ttk
import sys
import time
import tkinter as tk
import tkinter.filedialog as tkfiledialog
import tkinter.font as tkfont
import tkinter.messagebox as tkmessagebox
import tkinter.scrolledtext as scrolledtext
import tkinter.ttk as ttk


# The order in the following lists is important
NONE_STRING = '-/-'
ELEMENT_CLASSES = [NONE_STRING, 'Nature', 'Air', 'Water', 'Light', 'Energy',
                   'Psi', 'Stone', 'Ice', 'Fire', 'Dark', 'Chaos', 'Metal',
                   '✱']  # See makeStringSearchable()
MANA_LEVELS = [5, 15, 30, 40, 55, NONE_STRING]
FAIRY_GLOWS_WITH_INTENSITY = [
    (NONE_STRING, 0),
    ('White sparkles (teleport)', 3),
    ('Key unlock animation', 2),
    ('White ice', 1),
    ('Blue particles (item effect)', 2),
    ('Grey stones', 3),
    ('Green rays with blue particles', 2),
    ('Blue/white water bubbles (nature card animation)', 3),
    ('Red with fire particles', 1),
    ('Purple with lightning', 1),
    ('Green', 1),
    ('Grey-turquoise sphere with greyish particles', 1),
    ('Orange with pink particles', 1),
    ('Blue with waves', 1),
    ('Red with purple particles', 1),
    ('Green with big orange particles', 3),
    ('Purple glow with lightblue particles', 3),
    ('White glow with purple outline and big particles', 3),
    ('White glow with falling particles', 1),
    ('White air vortex (jumping swirls)', 2),
    ('White glow (teleport trigger)', 3),
    ('Yellow sparkles (trigger for secrets)', 2),
    ('Purple', 2),
    ('Blue light swirl', 2),
    ('Green with weak orange particles', 2),
    ('Grey stones', 2),
    ('Red with fire particles (fast)', 1),
    ('Rain cloud with lightning', 2),
    ('Orange prison sphere', 3),
    ('Grey stones', 1),
    ('Purple sphere with rays', 2),
    ('Orange sphere with yellow rays', 2),
    ('Blue sphere with rays', 2),
    ('Purple laser (fairy catch animation)', 2),
    ('Blue weak bubbles', 1),
    ('Blue particles', 2),
    ('Purple particles', 2),
    ('Blue with purple particles', 1),
    ('Grey dust', 1),
]
ACTIVE_SPELL_CRIT_EFFECTS = [
    # Derived, modified and corrected from
    # https://github.com/Helco/zzdocs/blob/9be46e8300fff4666832d5381690a4c6f1deac3c/docs/resources/FBS/fb0x03.md#behavior
    NONE_STRING,
    '20% higher chance for a critical hit',
    '40% higher chance for a critical hit',
    '60% higher chance for a critical hit',
    '80% higher chance for a critical hit',
    '100% higher chance for a critical hit',
    'Extra 5 damage',
    'Extra 10 damage',
    'Extra 25 damage',
    'Extra 30 damage',
    'Extra 50 damage',
    '20% Slower movement',
    '40% Slower movement',
    '60% Slower movement',
    '80% Slower movement',
    '100% Slower movement',
    '20% Slower cast speed',
    '40% Slower cast speed',
    '60% Slower cast speed',
    '80% Slower cast speed',
    '100% Slower cast speed',
    '50% Less jump power',
    '100% Less jump power',
    '20% Mana loss',
    '40% Mana loss',
    '60% Mana loss',
    '80% Mana loss',
    '100% Mana loss',
    'Disable attack spells',
    'Disable support spell',
    'Disable jumping',
    'Enemy spins around',
    'Condition: poison',
    'Condition: burn',
    'Condition: curse',
    'Condition: frozen',
    'Condition: silent',
    "Enemy can't land critical hits",
    'Instant spell burst',
    'Enemy takes own damage',
    'Invert control',
    'Teleport enemy to a random location',
    'Enemy is blinded',
]
PASSIVE_SPELL_EFFECTS = [
    NONE_STRING,
    'Receive 20% less damage',
    'Receive 50% less damage',
    'Receive 80% less damage',
    'Receive 100% less damage',
    '20% more damage',
    '40% more damage',
    '60% more damage',
    '80% more damage',
    '100% more damage',
    '20% more damage in case of a critical hit',
    '40% more damage in case of a critical hit',
    '60% more damage in case of a critical hit',
    '80% more damage in case of a critical hit',
    '100% more damage in case of a critical hit',
    '??? 20% more damage in case of a critical hit',
    '??? 40% more damage in case of a critical hit',
    '??? 60% more damage in case of a critical hit',
    '??? 80% more damage in case of a critical hit',
    '??? 100% more damage in case of a critical hit',
    '20% faster cast speed',
    '40% faster cast speed',
    '60% faster cast speed',
    '80% faster cast speed',
    '100% faster cast speed',
    '20% higher chance for a critical hit',
    '40% higher chance for a critical hit',
    '60% higher chance for a critical hit',
    '80% higher chance for a critical hit',
    '100% higher chance for a critical hit',
    '15% faster movement',
    '30% faster movement',
    '45% faster movement',
    '60% faster movement',
    '75% faster movement',
    '20% faster jump power loadup',
    '40% faster jump power loadup',
    '60% faster jump power loadup',
    '80% faster jump power loadup',
    '100% faster jump power loadup',
    'Heal 1 hitpoint',
    'Heal 5 hitpoint',
    'Heal 10 hitpoint',
    'Heal 20 hitpoint',
    'Heal 50 hitpoint',
    'Critical hits have no effect',
    'Received damage is also applied to enemy',
    'Reflect damage',
    'Use support spell instead off jumppower',
    "Can't be poisoned",
    "Can't be frozen",
    "Can't be silenced",
    "Can't be cursed",
    "Can't be burned",
    'Prevents status changes',
]
MAX_LEVEL = 60  # See other hard-coded instances of 60
MAX_EXPERIENCE = 15000


def splitByWhitespace(string):
    """
    Splits the given string by whitespaces and returns every non-empty
    substring.
    """
    return list(filter(None, string.split(' ')))


def extractUid(string):
    """
    'NPC(E12F912) Rufus' -> 'E12F912'
    """
    return string.split('(')[1].split(')')[0]


def fetchString(sql_connection, query_string, params):
    sql_cursor = sql_connection.cursor()
    sql_cursor.execute(query_string, params)
    return sql_cursor.fetchone()


def fetchStringOrNull(sql_connection, query_string, params):
    result = fetchString(sql_connection, query_string, params)
    if result is None:
        return 'NULL'
    return result[0]


def resolveLabel(sql_connection, uid):
    return fetchStringOrNull(sql_connection,
                             'select col_0_String from _fb0x02 where UID =?',
                             (uid,))


def resolveDialog(sql_connection, uid):
    return fetchStringOrNull(sql_connection,
                             'select col_0_String from _fb0x06 where UID =?',
                             (uid,))


def resolveMana(id):
    if id == len(MANA_LEVELS) - 1:
        return MANA_LEVELS[-1]
    elif id < 0 or id >= len(MANA_LEVELS):
        return 'NULL'
    return str(MANA_LEVELS[id])


def fetchAllNpcScripts(sql_connection, npc_uid):
    sql_cursor = sql_connection.cursor()
    sql_cursor.execute("""select col_2_String, col_3_String, col_1_String,
    col_5_String, col_4_String from _fb0x05 where UID =?""", (npc_uid,))
    result = sql_cursor.fetchall()
    if result is None:
        return None
    return {
        'Init':       str(result[0][0]),
        'Update':     str(result[0][1]),
        'Trigger':    str(result[0][2]),
        'Victorious': str(result[0][3]),
        'Defeated':   str(result[0][4]),
    }


def getCardEntityId(card_id):
    """Strips the entity id from the given card id"""
    return (card_id >> 16) & 0xffff


def resolveCardIdName(sql_connection, query_string, entity_id):
    entity_id = str(entity_id)

    sql_cursor = sql_connection.cursor()
    sql_cursor.execute(query_string)
    card_values = sql_cursor.fetchall()
    for name_id, card_id in card_values:
        if str(getCardEntityId(card_id)) == entity_id:
            return resolveLabel(sql_connection, name_id.split('|')[0])
    return 'NULL'


def resolveFairyName(sql_connection, fairy_id):
    query_string = 'select col_1_ForeignKey, col_3_Integer from _fb0x01'
    return resolveCardIdName(sql_connection, query_string, fairy_id)


def resolveUid(sql_connection, query, entity_id):
    """
    Takes a query which returns a list of pairs: [uid, card_id]. Returns None
    if no matching card id was found.
    """
    sql_cursor = sql_connection.cursor()
    sql_cursor.execute(query)
    for uid, card_id in sql_cursor.fetchall():
        if str(getCardEntityId(card_id)) == entity_id:
            return uid
    return None


def generateRowUid(table_number):
    return hex(randrange(16))[-1].upper() + \
            hex(int(time.time() * 10))[-6:].upper() + \
            str(table_number - 1)


def resolveCardDescription(sql_connection, card_type, card_id):
    card_type = str(card_type)
    card_id = str(card_id)

    if card_type == '0':
        query_string = 'select col_0_ForeignKey, col_1_Integer from _fb0x04'
        spell_name = resolveCardIdName(sql_connection, query_string, card_id)
        return 'Item: ' + spell_name
    elif card_type == '1':
        query_string = 'select col_0_ForeignKey, col_2_Integer from _fb0x03'
        spell_name = resolveCardIdName(sql_connection, query_string, card_id)
        return 'Spell: ' + spell_name
    elif card_type == '2':
        return 'Fairy: ' + resolveFairyName(sql_connection, card_id)
    elif card_type == '3':
        return 'Blank'
    return 'NULL'


def replaceEntryContent(entry_box, new_content_string):
    entry_box.delete(0, tk.END)
    entry_box.insert(tk.END, new_content_string)


def insertStringIntoDatabase(sql_connection, string_type, string):
    new_uid = generateRowUid(2)

    sql_cursor = sql_connection.cursor()
    sql_cursor.execute("""insert into
        _fb0x02 (UID, col_0_String, col_1_Integer, col_2_String)
        values (?, ?, ?, ?)""", [
        new_uid,
        string,
        string_type,
        '',  # Not needed
    ])
    return new_uid


# Source:
# https://github.com/Helco/zzio/blob/02a9cee6e3317e80c52f55950310c7b8ff371257/zzsc/zzsc.cs
SCRIPT_COMMANDS = {
    '!': 'say',
    'C': 'setModel',
    '"': 'choice',
    '#': 'waitForUser',
    '$': 'label',
    '&': 'setCamera',
    '%': 'exit',
    "'": 'wizform',
    '(': 'spell',
    '8': 'else',
    ')': 'changeWaypoint',
    '*': 'fight',
    '+': 'lookAtPlayer',
    ',': 'changeDatabase',
    '-': 'removeNpc',
    '.': 'catchWizform',
    '0': 'killPlayer',
    '5': 'tradingCurrency',
    '2': 'tradingItem',
    '3': 'tradingSpell',
    '4': 'tradingWizform',
    '1': 'givePlayerCards',
    'B': 'setupGambling',
    '6': 'ifPlayerHasCards',
    '@': 'ifPlayerHasSpecials',
    '=': 'ifTriggerIsActive',
    '9': 'removePlayerCards',
    ':': 'moveSystem',
    '?': 'movementSpeed',
    ';': 'modifyWizform',
    '<': 'lockUserInput',
    '>': 'modifyTrigger',
    'A': 'playAnimation',
    'D': 'ifIsWizform',
    'E': 'startPrelude',
    'F': 'npcWizFormEscapes',
    'G': 'dance',
    'H': 'setGlobal',
    'I': 'beginIf_global',
    'J': 'talk',
    'K': 'goto',
    'L': 'gotoRandomLabel',
    'M': 'ask',
    'N': 'chafferWizForms',
    'O': 'setNpcType',
    'P': 'deployNpcAtTrigger',
    'Q': 'delay',
    'R': 'gotoLabelByRandom',
    'S': 'ifCloseToWaypoint',
    'T': 'removeWizForms',
    'U': 'ifNpcModifierHasValue',
    'V': 'setNpcModifier',
    'W': 'defaultWizForm',
    'X': 'idle',
    'Y': 'ifPlayerIsClose',
    'Z': 'ifNumberOfNpcsIs',
    '[': 'startEffect',
    '\\': 'setTalkLabels',
    ']': 'setCollision',
    '^': 'tradeWizform',
    '_': 'createDynamicItems',
    '`': 'playVideo',
    'a': 'removeNpcAtTrigger',
    'b': 'revive',
    'c': 'lookAtTrigger',
    'd': 'ifTriggerIsEnabled',
    'e': 'playSound',
    'f': 'playInArena',
    'g': 'startActorEffect',
    'h': 'endActorEffect',
    'i': 'createSceneObjects',
    'j': 'evolveWizForm',
    'k': 'removeBehaviour',
    'l': 'unlockDoor',
    'm': 'endGame',
    'n': 'defaultDeck',
    'o': 'subGame',
    'p': 'modifyEffect',
    'q': 'playPlayerAnimation',
    's': 'playAmyVoice',
    'r': 'createDynamicModel',
    't': 'deploySound',
    'u': 'givePlayerPresent',
    '7': 'endIf',
}
REVERSE_SCRIPT_COMMANDS = {}
for key, value in SCRIPT_COMMANDS.items():
    REVERSE_SCRIPT_COMMANDS[value] = key

# All commands not in this dictionary take zero arguments.
script_command_parameters = {
    'label': ['id'],
    'goto': ['labelId'],
    'gotoRandomLabel': ['int', 'int'],
    'say': ['dialogUid', 'silent'],
    'setModel': ['id'],
    'choice': ['ladelId', 'uid'],
    'setCamera': ['code'],
    'wizform': ['deckSlot', 'fairyId', 'level'],
    'spell': ['deckSlot', 'spellSlot', 'spellId'],
    'changeWaypoint': ['startId', 'endId'],
    'fight': ['sceneId', 'multipleEnemiesBool'],  # Can flee bool?
    'lookAtPlayer': ['seconds/10', 'mode'],
    'changeDatabase': ['uid'],
    'tradingCurrency': ['uid'],
    'tradingItem': ['price', 'uid'],
    'tradingSpell': ['price', 'uid'],
    'tradingWizform': ['price', 'uid'],
    'givePlayerCards': ['amount', 'cardType', 'id'],
    'setupGambling': ['amount', 'cardType', 'id'],
    'ifPlayerHasCards': ['amount', 'cardType', 'id'],
    'ifPlayerHasSpecials': ['condition', 'argument'],
    'ifTriggerIsActive': ['id'],
    'ifIsWizform': ['fairyId'],
    'removePlayerCards': ['amount', 'cardType', 'id'],
    'moveSystem': ['waypointMode', 'waypointCategory'],
    'movementSpeed': ['int'],
    'modifyWizform': ['subcommand', 'argument'],
    'lockUserInput': ['bool'],
    'modifyTrigger': ['enable', 'id', 'triggerId'],
    'playAnimation': ['animationType', 'UNUSED'],
    'talk': ['uid'],
    'chafferWizForms': ['uid1', 'uid2', 'uid3'],
    'setNpcType': ['int'],
    'deployNpcAtTrigger': ['id', 'NpcOrPlayerBool'],
    'delay': ['duration'],
    'ifCloseToWaypoint': ['waypointId'],
    'ifNpcModifierHasValue': ['id'],
    'setNpcModifier': ['scene', 'triggerId', 'value'],
    'defaultWizForm': ['fairyId', 'groupOrSlot', 'level'],
    'ifPlayerIsClose': ['distance'],
    'ifNumberOfNpcsIs': ['amount', 'uid'],
    'startEffect': ['effectType', 'triggerId'],
    'setTalkLabels': ['yes', 'no', 'talkMode'],
    'setCollision': ['isSolidBool'],
    'tradeWizform': ['id'],
    'createDynamicItems': ['itemId', 'count', 'triggerId'],
    'playVideo': ['videoId'],
    'removeNpcAtTrigger': ['triggerId'],
    'lookAtTrigger': ['duration', 'triggerId'],
    'ifTriggerIsEnabled': ['triggerId'],
    'playSound': ['soundId'],
    'playInArena': ['arg', 'UNUSED'],
    'createSceneObjects': ['objectType'],
    'removeBehaviour': ['id'],
    'unlockDoor': ['id', 'isMetalDoorBool'],
    'defaultDeck': ['groupId', 'level', 'UNUSED'],
    'subGame': ['gameType', 'size', 'exitLabel'],
    'playPlayerAnimation': ['animationType', 'UNUSED'],
    'playAmyVoice': ['string'],
    'createDynamicModel': ['UNUSED', 'UNUSED', 'UNUSED'],
    'deploySound': ['id', 'triggerId'],
    'givePlayerPresent': ['UNUSED'],
    'startActorEffect': ['id'],
}

# Source:
# https://github.com/Helco/zzio/blob/02a9cee6e3317e80c52f55950310c7b8ff371257/zzio/AnimationType.cs#L5
AVAILABLE_ANIMATIONS = [
    'Idle0', 'Jump', 'Run', 'RunForwardLeft', 'RunForwardRight', 'Back',
    'Dance', 'Fall', 'Rotate', 'Right', 'Left', 'Idle1', 'Idle2', 'Talk0',
    'Talk1', 'Talk2', 'Talk3', 'Walk0', 'Walk1', 'Walk2', 'SpecialIdle0',
    'SpecialIdle1', 'SpecialIdle2', 'FlyForward', 'FlyBack', 'FlyLeft',
    'FlyRight', 'Loadup', 'Hit', 'Joy', 'ThudGround', 'UseFairyPipe',
    'UseSeaShell', 'Smith', 'Astonished', 'Surprise0', 'Surprise1', 'Stop',
    'ThudGround2', 'PixieFlounder', 'JumpHigh',
]


def makeError(line_counter, message):
    return 'Line ' + str(line_counter + 1) + ': ' + message


def compile(script):
    """
    Try to compile the given script.

    Returns either:
    [True, '...compiled code...']
    [False, ['error 1', 'error 2', ...]]
    """
    output = ""
    errors = []
    for index, line in enumerate(script.split('\n')):
        line_without_comments = line.split('//')[0]
        tokens = splitByWhitespace(line_without_comments)
        if len(tokens) == 0:
            pass
        elif not tokens[0] in REVERSE_SCRIPT_COMMANDS:
            errors.append(makeError(index, 'Unknown command: ' + tokens[0]))
            continue
        else:
            command = tokens[0]
            if command in script_command_parameters:
                parameters = script_command_parameters[command]
                if len(tokens) - 1 != len(parameters):
                    errors.append(makeError(
                        index, 'Command ' + command + ' takes exactly ' +
                        str(len(parameters)) + ' arguments: ' +
                        ', '.join(parameters)))
                    continue

            elif len(tokens) != 1:
                errors.append(makeError(
                    index, 'Command takes no arguments: ' + command))
                continue

            if index > 0:
                output += '\n'
            output += REVERSE_SCRIPT_COMMANDS[command]
            if len(tokens) > 1:
                output += '.'
        output += '.'.join(tokens[1:])
    if len(errors) == 0:
        return [True, output + '\n']
    else:
        return [False, errors]


def compileAndShowErrorMessage(script):
    status, script_or_messages = compile(script)
    if status is False:
        tkmessagebox.showerror('Script Error', '\n'.join(script_or_messages))
    return [status, script_or_messages]


def decompile(sql_connection, script):
    result = ""
    indentation = 0
    for line in script.split('\n'):
        tokens = line.strip().split('.')
        if tokens[0] in SCRIPT_COMMANDS:
            command = SCRIPT_COMMANDS[tokens[0]]
            if command == 'endIf':
                indentation = max(indentation - 4, 0)
            if command != 'else':
                result += ' ' * indentation
            result += command
            if len(tokens) > 1:
                result += ' ' + ' '.join(tokens[1:])
            if command.startswith('if'):
                indentation += 4
            if command in script_command_parameters:
                result += makeDecompiledParameterComment(
                    command, tokens[1:], sql_connection)
        else:
            result += line
        result += '\n'
    return result


def indexListByMaybeInt(string_list, maybe_integer):
    try:
        index = int(maybe_integer)
        if index >= 0 and index < len(string_list):
            return string_list[index]
    except ValueError:
        pass
    return 'NULL'


def makeDecompiledParameterComment(command, arguments, sql_connection):
    parameter_names = script_command_parameters[command]
    result = ' // ' + ', '.join(parameter_names)
    if command == 'wizform':
        result += '; '
        result += resolveFairyName(sql_connection, arguments[1])
    elif command == 'defaultWizForm' or command == 'ifIsWizform':
        result += '; '
        result += resolveFairyName(sql_connection, arguments[0])
    elif command == 'say' or command == 'talk':
        result += '; ' + resolveDialog(sql_connection, arguments[0])
    elif command == 'choice':
        result += '; ' + resolveDialog(sql_connection, arguments[1])
    elif command == 'givePlayerCards' or \
            command == 'setupGambling' or \
            command == 'ifPlayerHasCards' or \
            command == 'removePlayerCards':
        result += '; '
        result += resolveCardDescription(
            sql_connection, arguments[1], arguments[2])
    elif command == 'modifyWizform':
        subcommand_descriptions = {
            '0': '; Heal',
            '1': '; Add exp',
            '2': '; Clear status effects',
            '8': '; Add exp to almost next level',
            '16': '; Revive fairy',
            '17': '; Fill up mana',
            '18': '; Rename fairy',
        }
        if arguments[0] == '7':
            result += '; Evolve to '
            result += resolveFairyName(sql_connection, arguments[1])
        elif arguments[0] in subcommand_descriptions:
            result += '; ' + subcommand_descriptions[arguments[0]]
    elif command == 'ifPlayerHasSpecials':
        result += makeDecompiledSpecialsComment(arguments)
    elif command == 'lookAtPlayer':
        modes = {
            '-1': "Idle: Don't look at player",
            '1': 'Rotate to player',
            '2': 'Rotate to player smoothly',
            '3': 'Rotate to player like a billboard',
        }
        if arguments[1] in modes:
            result += '; ' + modes[arguments[1]]
    elif command == 'playAnimation' or command == 'playPlayerAnimation':
        result += '; Animation: '
        result += indexListByMaybeInt(AVAILABLE_ANIMATIONS, arguments[0])
    elif command == 'startActorEffect':
        result += makeActorEffectComment(arguments[0])

    return result


def makeDecompiledSpecialsComment(arguments):
    result = ''
    if arguments[0] == '1':
        result += '; Player has'
        result += ' no' if arguments[1] == '0' else ''
        result += ' Fairy in Deck'
    elif arguments[0] == '2':
        result += '; Player has at least n fairies'
    elif arguments[0] == '3':
        result += '; Player can show '
        result += indexListByMaybeInt(ELEMENT_CLASSES, arguments[1])
        result += ' Fairy'
    return result


def makeActorEffectComment(id_argument):
    if id_argument == '0':
        return '; Rain clouds with lightning'
    elif id_argument == '1':
        return '; Orange sphere'
    else:
        return ''


def makeResizedFont():
    font = tkfont.nametofont('TkFixedFont')
    font['size'] = 12
    return font


def makeTextBox(parent_frame, constructor):
    return constructor(parent_frame, font=makeResizedFont(),
                       fg='#cdcecf', bg='#192330')


def makeCombobox(frame):
    combobox = ttk.Combobox(frame, state='readonly')
    combobox.bind('<<ComboboxSelected>>',
                  lambda _: combobox.selection_clear())
    return combobox


def autoAdjustComboboxWidth(combobox):
    combobox['width'] = len(max(combobox['values'], key=len))


def makeCheckedEntry(frame, validation_regex_string):
    entry = tk.Entry(frame, validate='key')
    entry['validatecommand'] = [
        entry.register(
            lambda string:
            re.match(validation_regex_string, string, re.S) is not None
        ), '%P'
    ]
    return entry


def makeLevelEntry(frame):
    entry = makeCheckedEntry(frame, r'^(|[1-5]?[0-9]|60)$')  # MAX_LEVEL
    entry['width'] = 5
    return entry


def makeListChooser(frame, row, label_text, items):
    tk.Label(frame, text=label_text).grid(row=row, column=0, sticky='w')
    chooser_frame = tk.Frame(frame)
    chooser_frame.grid(row=row, column=1, sticky='w')
    integer_value = tk.IntVar()
    for index, button_label in enumerate(items):
        radio_button = ttk.Radiobutton(
            chooser_frame, text=str(button_label), value=index,
            variable=integer_value)
        radio_button.pack(fill=tk.BOTH, expand=False, side=tk.LEFT)
    return integer_value


def makeStatChooser(frame, row, label_text):
    level_strings = ['' for s in range(5)]
    return makeListChooser(frame, row, label_text, level_strings)


def toCircleString(value, max_value):
    return value * '●' + (max_value - value) * '○'


def toStatString(value):
    """
    Expands a value like 2 to '●●●○○'
    """
    return toCircleString(value + 1, 5)


def makeStringSearchable(string):
    return string \
        .replace('●', '*') \
        .replace('○', '') \
        .replace(ELEMENT_CLASSES[-1], '*')


DIALOG_INCOMPLETE_REGEX = r'\{[^\{\}\n]*(\{|\n|$)'
DIALOG_HIGHLIGHT_REGEX = \
    r'(?P<DIALOGINCOMPLETE>' + DIALOG_INCOMPLETE_REGEX + \
    r')|(?P<DIALOGSTART>\{[0-9]*\*)(?P<DIALOG>[^\}\n]*)(?P<DIALOGEND>\})'


def addDialogHighlightGroups(tagdefs):
    tagdefs['DIALOGSTART'] = {'foreground': '#86abdc'}
    tagdefs['DIALOG'] = {'foreground': '#81b29a'}
    tagdefs['DIALOGEND'] = tagdefs['DIALOGSTART']
    tagdefs['DIALOGINCOMPLETE'] = {'foreground': '#a5222f'}


class StringDialogBox:
    def __init__(self, parent_frame):
        self.text_box = makeTextBox(parent_frame, tk.Text)
        self.text_box.configure(undo=True, maxundo=-1)

        self.delegator = colorizer.ColorDelegator()
        self.delegator.prog = re.compile(DIALOG_HIGHLIGHT_REGEX, re.S)
        addDialogHighlightGroups(self.delegator.tagdefs)
        percolator.Percolator(self.text_box).insertfilter(self.delegator)

    def append(self, text):
        state = self.__popState()
        self.text_box.insert(tk.END, str(text))
        self.__restoreState(state)

    def get(self):
        return self.text_box.get('1.0', 'end-1c')

    def getErrorMessage(self):
        """
        Check the content of this text box for errors. Returns None on success.
        """
        if re.search(DIALOG_INCOMPLETE_REGEX, self.get(), re.S) is not None:
            return 'Incomplete highlighting sequence is missing "}"'
        return None

    def reformat(self):
        current_text = self.get()
        new_text = re.sub(r'\n+', ' ', current_text).rstrip()
        if new_text == current_text:
            return

        state = self.__popState()
        self.text_box['autoseparator'] = False
        self.text_box.replace('1.0', tk.END, new_text)
        self.text_box['autoseparator'] = True
        self.delegator.notify_range('1.0', tk.END)
        self.__restoreState(state)

    def resetUndoHistory(self):
        self.text_box.edit_reset()

    def fullReset(self):
        state = self.__popState()
        self.text_box.delete('1.0', 'end')
        self.resetUndoHistory()
        self.__restoreState(state)

    def pack(self, **kwargs):
        self.text_box.pack(kwargs)

    def grid(self, **kwargs):
        self.text_box.grid(kwargs)

    def gridForget(self):
        self.text_box.grid_forget()

    def setGreenBackground(self):
        self.text_box['bg'] = '#2e4045'

    def setRedBackground(self):
        self.text_box['bg'] = '#3c2c3c'

    def disable(self):
        self.text_box['state'] = 'disabled'

    def prepareForWritingToDB(self):
        error_message = self.getErrorMessage()
        if error_message is not None:
            tkmessagebox.showerror('Invalid Text', error_message)
            return False
        self.reformat()
        return True

    def __popState(self):
        current_state = self.text_box['state']
        self.text_box['state'] = 'normal'
        return current_state

    def __restoreState(self, state):
        self.text_box['state'] = state


class CodeBox:
    def __init__(self, parent_frame):
        frame = tk.Frame(parent_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        self.text_box = makeTextBox(frame, scrolledtext.ScrolledText)
        self.text_box.configure(wrap='none', undo=True, maxundo=-1)
        self.text_box.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.text_box.bind('<KeyRelease>', self.__checkScriptForErrors)
        self.delegator = self.__makeColorDelegator()
        percolator.Percolator(self.text_box).insertfilter(self.delegator)

        self.error_bar = tk.Label(
            frame, foreground='#dfdfe0', background='#3c2c3c',
            font=makeResizedFont(), anchor=tk.W, justify=tk.LEFT)

    def getContent(self):
        return self.text_box.get('1.0', 'end-1c')

    def replaceContent(self, new_text):
        if new_text == self.getContent():
            return

        state = self.__popState()
        self.text_box['autoseparator'] = False
        self.text_box.replace('1.0', tk.END, new_text)
        self.text_box['autoseparator'] = True
        self.delegator.notify_range('1.0', tk.END)
        self.__restoreState(state)

    def resetUndoHistory(self):
        self.text_box.edit_reset()

    def fullReset(self):
        state = self.__popState()
        self.text_box.delete('1.0', 'end')
        self.resetUndoHistory()
        self.__restoreState(state)

    def setBackground(self, color):
        self.text_box['bg'] = color

    def disable(self):
        self.text_box['state'] = 'disabled'

    def __checkScriptForErrors(self, _):
        status, error_messages = compile(self.getContent())
        if status is True:
            self.error_bar.pack_forget()
        else:
            self.error_bar['text'] = '\n'.join(error_messages)
            self.error_bar.pack(fill=tk.BOTH, expand=False, side=tk.BOTTOM)

    def __makeColorDelegator(self):
        """
        Return a ColorDelegator for syntax highlighting in scripts.
        """
        jumplabels = ['label', 'goto', 'gotoRandomLabel']
        commands = (s for s in SCRIPT_COMMANDS.values() if s not in jumplabels)

        delegator = colorizer.ColorDelegator()
        regex = r'\b(?P<JUMPLABEL>(' + r'|'.join(jumplabels) + r'))\b' + \
            r'|' + r'\b(?P<COMMAND>(' + r'|'.join(commands) + r'))\b' + \
            r'|' + r'\b(?P<NUMBER>[0-9]{1,4})\b' + r'|' + \
            r'(?P<COMMENT>//[^;\n]*)((?P<SPECIAL>;)(?P<INFOSTRING>[^\n]*))?'
        delegator.prog = re.compile(regex, re.S)
        delegator.tagdefs['JUMPLABEL'] = {'foreground': '#9d79d6'}
        delegator.tagdefs['COMMAND'] = {'foreground': '#86abdc'}
        delegator.tagdefs['NUMBER'] = {'foreground': '#f4a261'}
        delegator.tagdefs['COMMENT'] = {'foreground': '#738091'}
        delegator.tagdefs['SPECIAL'] = delegator.tagdefs['COMMENT']
        delegator.tagdefs['INFOSTRING'] = {'foreground': '#81b29a'}
        return delegator

    def __popState(self):
        current_state = self.text_box['state']
        self.text_box['state'] = 'normal'
        return current_state

    def __restoreState(self, state):
        self.text_box['state'] = state


class ElementClassComboboxSet:
    def __init__(self, parent_frame, parent_grid_row, parent_grid_column):
        self.slots_frame = tk.Frame(parent_frame)
        self.show(parent_grid_column, parent_grid_column)
        self.comboboxes = [
            self.__makeSlotCombobox(self.slots_frame),
            self.__makeSlotCombobox(self.slots_frame),
            self.__makeSlotCombobox(self.slots_frame),
        ]
        self.__connectSlotComboboxes(self.comboboxes[0], self.comboboxes[1])
        self.__connectSlotComboboxes(self.comboboxes[1], self.comboboxes[2])
        self.comboboxes[0].event_generate('<<ComboboxSelected>>')

    def get(self, slot_index):
        self.__assertSlotIndex(slot_index)
        return ELEMENT_CLASSES.index(self.comboboxes[slot_index].get())

    def set(self, slot_index, new_value):
        self.__assertSlotIndex(slot_index)
        self.comboboxes[slot_index].set(ELEMENT_CLASSES[new_value])
        self.comboboxes[slot_index].event_generate('<<ComboboxSelected>>')

    def hide(self):
        self.slots_frame.grid_forget()

    def show(self, row, column):
        self.slots_frame.grid(row=row, column=column, sticky='nwse')

    def __makeSlotCombobox(self, frame):
        combobox = makeCombobox(frame)
        combobox.configure(values=ELEMENT_CLASSES)
        combobox.set(combobox['values'][0])
        autoAdjustComboboxWidth(combobox)
        combobox.pack(fill=tk.BOTH, expand=False, side=tk.LEFT)
        return combobox

    def __connectSlotComboboxes(self, combobox, following_combobox):
        """
        Reset and disable `following_combobox` when the given combobox is set
        to '-/-,
        """
        combobox.bind('<<ComboboxSelected>>', lambda _:
                      self.__updateSlotCombobox(combobox, following_combobox))

    def __updateSlotCombobox(self, combobox, following_combobox):
        if combobox.get() == ELEMENT_CLASSES[0]:
            following_combobox['state'] = 'disabled'
            following_combobox.set(ELEMENT_CLASSES[0])
            following_combobox.event_generate('<<ComboboxSelected>>')
        else:
            following_combobox['state'] = 'readonly'
        combobox.selection_clear()

    def __assertSlotIndex(self, slot_index):
        if slot_index not in [0, 1, 2]:
            raise ValueError('Invalid slot index: ' + str(slot_index))


class SpellSlotProgressionTable:
    def __init__(self, parent_frame):
        self.row_limit = 10
        parent_frame.rowconfigure(list(range(self.row_limit + 1)), weight=0)
        parent_frame.rowconfigure(self.row_limit + 1, weight=1)
        parent_frame.columnconfigure(list(range(4)), weight=1)

        column_titles = ['Level', 'Slot Position', 'Slot Configuration']
        for column, text in enumerate(column_titles):
            label = tk.Label(parent_frame, text=text)
            label.grid(row=0, column=column, sticky='we')

        self.active_rows = []
        self.inactive_rows = []
        for index in range(self.row_limit):
            self.inactive_rows.append(
                self.__Row(parent_frame, self.__deactivateRow))

        self.add_row_button = tk.Button(
            parent_frame, text='Add Row', command=self.__addNewRow)

    def loadValues(self, progression_values):
        """
        Takes a list of 10 integers which describe spell slots. Values of -1
        represent blanks.
        """
        assert len(progression_values) == self.row_limit

        active_values = [value for value in progression_values if value != -1]

        while len(self.active_rows) > len(active_values):
            self.__deactivateRow(self.active_rows[0])
        while len(self.active_rows) < len(active_values):
            self.__activateRow(0)

        for row, new_value in zip(self.active_rows, active_values):
            row.setValue(new_value)

    def getValues(self):
        """
        Return a list of sorted integers for storage in the database. Unset
        values will be returned as -1.

        If this progression table contains incomplete informations, this
        function will return None.
        """
        values = [row.getValue() for row in self.active_rows]
        if None in values:
            return None

        values.sort()
        while len(values) < self.row_limit:
            values.append(-1)
        return values

    def __addNewRow(self):
        self.__activateRow(0)

    def __activateRow(self, new_value):
        row = self.inactive_rows.pop()
        row.setValue(new_value)
        row.show(len(self.active_rows) + 1)  # Account for title row.
        self.active_rows.append(row)
        self.__updateAddButton()

    def __deactivateRow(self, row):
        row.hide()
        self.active_rows.remove(row)
        self.inactive_rows.append(row)

        for index, row in enumerate(self.active_rows):
            row.show(index + 1)

        self.__updateAddButton()

    def __updateAddButton(self):
        if len(self.inactive_rows) == 0:
            self.add_row_button.grid_forget()
        else:
            self.add_row_button.grid(
                row=len(self.active_rows) + 1, column=0,
                columnspan=5, sticky='we')

    class __Row:
        def __init__(self, row_frame, remove_row_callback):
            self.remove_row_callback = remove_row_callback
            self.hidden = True

            self.entry = makeLevelEntry(row_frame)

            self.deck_slot = tk.IntVar()
            self.radio_button_frame = tk.Frame(row_frame)
            for column in range(4):
                radio_button = ttk.Radiobutton(self.radio_button_frame,
                                               value=column,
                                               variable=self.deck_slot)
                radio_button.pack(fill=tk.BOTH, expand=False, side=tk.LEFT)

            self.combobox_set = ElementClassComboboxSet(row_frame, 0, 0)
            self.combobox_set.hide()
            self.remove_button = \
                tk.Button(row_frame, text='Remove', command=self.__remove)

        def getValue(self):
            if len(self.entry.get()) == 0:
                return None

            slot0 = self.combobox_set.get(0)
            slot1 = self.combobox_set.get(1)
            slot2 = self.combobox_set.get(2)
            level = int(self.entry.get())
            slot_position = self.deck_slot.get()

            return (slot2 & 0xf) | ((slot1 & 0xf) << 4) | \
                   ((slot0 & 0xf) << 8) | ((slot_position & 0b11) << 12) | \
                   ((level & 0xffff) << 16)

        def setValue(self, integer_bits):
            slot2 = min((integer_bits >> 0) & 0xf, len(ELEMENT_CLASSES) - 1)
            slot1 = min((integer_bits >> 4) & 0xf, len(ELEMENT_CLASSES) - 1)
            slot0 = min((integer_bits >> 8) & 0xf, len(ELEMENT_CLASSES) - 1)
            slot_position = min((integer_bits >> 12) & 0b11, 3)
            level = (integer_bits >> 16) & 0xffff

            self.deck_slot.set(slot_position)
            replaceEntryContent(self.entry, str(level))
            self.combobox_set.set(2, slot2)
            self.combobox_set.set(1, slot1)
            self.combobox_set.set(0, slot0)

        def show(self, row):
            self.entry.grid(row=row, column=0, sticky='w')
            self.radio_button_frame.grid(row=row, column=1, sticky='nwse')
            self.combobox_set.show(row, 2)
            self.remove_button.grid(row=row, column=3, sticky='nswe')
            self.hidden = False

        def hide(self):
            self.radio_button_frame.grid_forget()
            self.entry.grid_forget()
            self.combobox_set.hide()
            self.remove_button.grid_forget()
            self.hidden = True

        def isHidden(self):
            return self.hidden

        def __remove(self):
            self.remove_row_callback(self)


class NPCNameCombobox:
    def __init__(self, parent_frame, sql_connection, row, column):
        self.sql_connection = sql_connection
        self.combobox = makeCombobox(parent_frame)
        self.combobox.grid(row=row, column=column, sticky='we')

    def reloadNamesFromDatabase(self):
        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""select UID, col_0_String from _fb0x02
        where col_1_Integer = 5 order by col_0_String""")
        npc_info_pairs = sql_cursor.fetchall()
        if npc_info_pairs is None:
            return False
        all_npc_names = []
        for name_uid, name in npc_info_pairs:
            all_npc_names.append('String(' + name_uid + ') ' + name)

        self.combobox['values'] = all_npc_names
        return True

    def getName(self):
        return re.sub(r'^String\([^\)]+\) ', '', self.combobox.get())

    def getUid(self):
        return extractUid(self.combobox.get())

    def getCurrentIndex(self):
        return self.combobox.current()

    def setName(self, name_uid, name):
        self.combobox.set('String(' + name_uid + ') ' + name)
        self.combobox.event_generate('<<ComboboxSelected>>')

    def setToFirstEntry(self):
        self.combobox.set(self.combobox['values'][0])
        self.combobox.event_generate('<<ComboboxSelected>>')

    def prependCustomNameEntry(self, string):
        self.combobox['values'] = [string] + list(self.combobox['values'])

    def setCallback(self, callback):
        def wrappedCallback(_):
            self.combobox.selection_clear()
            callback()
        self.combobox.bind('<<ComboboxSelected>>', wrappedCallback)


class FairyEditorView:
    def __init__(self, parent_frame, sql_connection):
        self.sql_connection = sql_connection
        self.current_fairy_uid = None
        fairy_frame = tk.Frame(parent_frame)
        fairy_frame.pack(fill=tk.BOTH, expand=True)
        fairy_frame.rowconfigure(tuple(range(9)), weight=0)
        fairy_frame.rowconfigure(9, weight=1)
        fairy_frame.columnconfigure(0, weight=0)
        fairy_frame.columnconfigure(1, weight=0)
        fairy_frame.columnconfigure(2, weight=1)

        self.move_speed = makeStatChooser(fairy_frame, 0, 'Movement Speed')
        self.jump_ability = makeStatChooser(fairy_frame, 1, 'Jump Ability')
        self.special = makeStatChooser(fairy_frame, 2, 'Special')

        max_int_regex = r'^(|[1-9][0-9]{0,10})$'
        self.__makeRowLabel(fairy_frame, 'HP at Max Level', 3)
        self.hp_limit_entry = makeCheckedEntry(fairy_frame, max_int_regex)
        self.hp_limit_entry.grid(row=3, column=1, sticky='we')

        self.__makeRowLabel(fairy_frame, 'Model/Mesh', 4)
        self.model_entry = tk.Entry(fairy_frame)
        self.model_entry.grid(row=4, column=1, sticky='we')

        self.__makeRowLabel(fairy_frame, 'Element Class', 5)
        self.element_class_combobox = makeCombobox(fairy_frame)
        self.element_class_combobox.configure(values=ELEMENT_CLASSES,
                                              state='readonly')
        self.element_class_combobox.grid(row=5, column=1, sticky='we')

        self.__makeRowLabel(fairy_frame, 'Evolves to', 6)
        evolution_frame = tk.Frame(fairy_frame)
        evolution_frame.grid(row=6, column=1, sticky='we')
        evolution_frame.rowconfigure(0, weight=1)
        evolution_frame.columnconfigure(0, weight=1)
        evolution_frame.columnconfigure(1, weight=0)
        evolution_frame.columnconfigure(2, weight=0)
        self.evolution_combobox = makeCombobox(evolution_frame)
        self.evolution_combobox.grid(row=0, column=0, sticky='we')
        self.evolution_combobox.bind('<<ComboboxSelected>>',
                                     self.__updateEvolutionCombobox)
        self.evolution_label = tk.Label(evolution_frame, text='At Level')
        self.evolution_level_entry = makeLevelEntry(evolution_frame)
        self.__setupEvolutionLevelInfo()

        sortable_glow_list = []
        for index, pair in enumerate(FAIRY_GLOWS_WITH_INTENSITY):
            string, intensity = pair
            sortable_glow_list.append(
                (string[:5] + str(intensity), string, intensity, index)
            )
        sortable_glow_list.sort(key=lambda values: values[0])
        glow_combobox_values = []
        self.glow_to_id_mapping = {}
        for _, string, intensity, index in sortable_glow_list:
            full_string = toCircleString(intensity, 3) + ' ' + string
            self.glow_to_id_mapping[full_string] = index
            glow_combobox_values.append(full_string)
        self.id_to_glow_mapping = {}
        for key, value in self.glow_to_id_mapping.items():
            self.id_to_glow_mapping[value] = key

        self.__makeRowLabel(fairy_frame, 'Glow Effect', 7)
        self.glow_combobox = makeCombobox(fairy_frame)
        self.glow_combobox.grid(row=7, column=1, sticky='we')
        self.glow_combobox['value'] = glow_combobox_values
        autoAdjustComboboxWidth(self.glow_combobox)

        tabs = ttk.Notebook(fairy_frame)
        tabs.grid(row=8, column=0, columnspan=2, sticky='nsw')

        progression_table_frame = tk.Frame(tabs)
        tabs.add(progression_table_frame, text='Spell Progression Table')
        self.progression_table = \
            SpellSlotProgressionTable(progression_table_frame)

        exp_curve_frame = ttk.Frame(tabs)
        exp_curve_frame.columnconfigure(0, weight=1)
        exp_curve_frame.columnconfigure(1, weight=50)
        tabs.add(exp_curve_frame, text='Experience Curve')

        self.__makeRowLabel(exp_curve_frame, 'Coefficient', 0)
        coefficient_entry = makeCheckedEntry(exp_curve_frame, max_int_regex)
        coefficient_entry.grid(row=0, column=1, sticky='w')
        self.exp_coefficient = tk.StringVar()
        self.exp_coefficient.trace_add('write', self.__updateExpCoefficient)
        coefficient_entry['textvariable'] = self.exp_coefficient

        plot_figure = Figure(figsize=(6, 3.5))
        plot_axis = plot_figure.add_subplot()
        plottet_levels = range(0, MAX_LEVEL + 1)
        self.plotted_values, = plot_axis.plot(
            plottet_levels, plottet_levels, color='#86abdc')
        plot_axis.set_xlim([0, MAX_LEVEL])
        plot_axis.set_xticks(range(0, MAX_LEVEL + 1, 5))
        plot_axis.set_yticks(range(0, MAX_EXPERIENCE + 1,
                                   int(MAX_EXPERIENCE / 10)))
        plot_axis.xaxis.grid(True, linestyle='--')
        plot_axis.yaxis.grid(True, linestyle='--')
        plot_axis.grid(color='#28384D')
        plot_axis.text(5, MAX_EXPERIENCE * 0.885, 'Experience\nrequired',
                       horizontalalignment='center')
        plot_axis.text(MAX_LEVEL - 3, MAX_EXPERIENCE * 0.025, 'Level',
                       horizontalalignment='center')
        plot_axis.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(self.__formatExperienceAxis)
        )
        self.plot_canvas = FigureCanvasTkAgg(plot_figure, exp_curve_frame)
        self.plot_canvas.get_tk_widget().grid(
            row=1, column=0, columnspan=2, sticky='nswe')
        plot_figure.tight_layout()

    def setupEditForID(self, fairy_id):
        self.current_fairy_uid = resolveUid(
            self.sql_connection, 'select UID, col_3_Integer from _fb0x01',
            fairy_id)
        if self.current_fairy_uid is None:
            return False

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""select
        col_0_String, col_2_Integer, col_5_Integer, col_6_Integer,
        col_7_Integer, col_8_Integer, col_9_Integer, col_10_Integer,
        col_11_Integer, col_12_Integer, col_13_Integer, col_14_Integer,
        col_16_Integer, col_17_Integer, col_18_Integer, col_19_Integer,
        col_20_Integer, col_21_Integer, col_23_Integer, col_25_Integer
        from _fb0x01 where UID = ?""", [self.current_fairy_uid])
        query_result = sql_cursor.fetchone()
        if query_result is None:
            return False

        model_string, element_class = query_result[:2]
        spell_slot_progression = query_result[2:12]
        hp_limit, evolution_fairy_id, evolution_level, move_speed, \
            jump_ability, special, glow_id, exp_coefficient = query_result[12:]

        sql_cursor.execute(
            'select col_1_ForeignKey, col_3_Integer from _fb0x01')
        query_result = sql_cursor.fetchall()
        if query_result is None:
            return False

        evolution_item = NONE_STRING
        fairy_name_pairs = []
        for name_uid, card_id in query_result:
            name_uid = name_uid.split('|')[0]
            name = resolveLabel(self.sql_connection, name_uid)
            fairy_id = getCardEntityId(card_id)
            description = 'Fairy(' + str(fairy_id) + ') ' + name
            fairy_name_pairs.append([name, description])
            if fairy_id == evolution_fairy_id:
                evolution_item = description
        fairy_name_pairs.sort(key=lambda pair: pair[0])
        full_fairy_list = [NONE_STRING]
        full_fairy_list += [pair[1] for pair in fairy_name_pairs]

        if element_class < 0 or element_class >= len(ELEMENT_CLASSES):
            self.element_class_combobox.set(ELEMENT_CLASSES[0])
        else:
            self.element_class_combobox.set(ELEMENT_CLASSES[element_class])
        replaceEntryContent(self.hp_limit_entry, str(hp_limit))
        self.move_speed.set(move_speed)
        self.jump_ability.set(jump_ability)
        self.special.set(special)

        self.evolution_combobox['values'] = full_fairy_list
        self.evolution_combobox.set(evolution_item)
        autoAdjustComboboxWidth(self.evolution_combobox)
        replaceEntryContent(self.evolution_level_entry, str(evolution_level))
        self.evolution_combobox.event_generate('<<ComboboxSelected>>')

        if glow_id in self.id_to_glow_mapping:
            self.glow_combobox.set(self.id_to_glow_mapping[glow_id])
        else:
            self.glow_combobox.set(self.id_to_glow_mapping[0])

        replaceEntryContent(self.model_entry, model_string)

        self.progression_table.loadValues(spell_slot_progression)
        self.exp_coefficient.set(exp_coefficient)

        return True

    def writeChangesToDatabase(self):
        if self.evolution_combobox.current() != 0 and \
                len(self.evolution_level_entry.get()) == 0:
            return self.__invalidInput('No evolution level specified')
        entries_to_check = [
            (self.hp_limit_entry, 'hp limit'),
            (self.exp_coefficient, 'experience coefficient'),
            (self.model_entry, 'model string'),
        ]
        for entry, description in entries_to_check:
            if len(entry.get()) == 0:
                return self.__invalidInput('No ' + description + ' specified')
            if entry.get() == '-':
                return self.__invalidInput(
                    'Incomplete ' + description + ' specified')

        spell_slot_progression = self.progression_table.getValues()
        if spell_slot_progression is None:
            return self.__invalidInput('Incomplete slot progression data')

        evolution_fairy_id = -1
        evolution_level = -1
        if self.evolution_combobox.current() != 0:
            evolution_fairy_id = \
                int(extractUid(self.evolution_combobox.get()))
            evolution_level = int(self.evolution_level_entry.get())

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""update _fb0x01 set
        col_0_String=?, col_2_Integer=?, col_5_Integer=?, col_6_Integer=?,
        col_7_Integer=?, col_8_Integer=?, col_9_Integer=?, col_10_Integer=?,
        col_11_Integer=?, col_12_Integer=?, col_13_Integer=?, col_14_Integer=?,
        col_16_Integer=?, col_17_Integer=?, col_18_Integer=?, col_19_Integer=?,
        col_20_Integer=?, col_21_Integer=?, col_23_Integer=?, col_25_Integer=?
        where UID = ?""", [
            self.model_entry.get(),
            ELEMENT_CLASSES.index(self.element_class_combobox.get()),
            spell_slot_progression[0], spell_slot_progression[1],
            spell_slot_progression[2], spell_slot_progression[3],
            spell_slot_progression[4], spell_slot_progression[5],
            spell_slot_progression[6], spell_slot_progression[7],
            spell_slot_progression[8], spell_slot_progression[9],
            int(self.hp_limit_entry.get()),
            evolution_fairy_id,
            evolution_level,
            self.move_speed.get(),
            self.jump_ability.get(),
            self.special.get(),
            self.glow_to_id_mapping[self.glow_combobox.get()],
            int(self.exp_coefficient.get()),
            self.current_fairy_uid,
        ])

        return True

    def __makeRowLabel(self, frame, text, row, column=0):
        label = tk.Label(frame, text=text)
        label.grid(row=row, column=column, sticky='w')
        return label

    def __updateEvolutionCombobox(self, _):
        self.evolution_combobox.selection_clear()
        if self.evolution_combobox.current() == 0:
            self.evolution_label.grid_forget()
            self.evolution_level_entry.grid_forget()
        else:
            self.__setupEvolutionLevelInfo()

    def __setupEvolutionLevelInfo(self):
        self.evolution_label.grid(row=0, column=1, sticky='w')
        self.evolution_level_entry.grid(row=0, column=2, sticky='w')

    def __invalidInput(self, error_message):
        tkmessagebox.showerror('Invalid Input Data', error_message)
        return False

    def __updateExpCoefficient(self, ignore1, ignore2, ignore3):
        if self.exp_coefficient.get() == '':
            return
        coefficient = int(self.exp_coefficient.get())
        limit = 70000  # Value which works best with the formula
        if coefficient > limit:
            coefficient = limit
            self.exp_coefficient.set(coefficient)

        self.plotted_values.set_ydata([
            self.__getExpForLevel(level, coefficient)
            for level in range(0, MAX_LEVEL + 1)
        ])
        self.plot_canvas.draw()

    def __formatExperienceAxis(self, value, _):
        if value == 0:
            return '0'
        else:
            return '{:.1f}'.format(value / 1000) + 'k'

    # https://github.com/Helco/zzio/blob/02a9cee6e3317e80c52f55950310c7b8ff371257/zzre/game/Inventory.GameLogic.cs#L180
    def __getExpForLevel(self, level, coefficient):
        exponent_factor = 0.001
        base_exp = pow(MAX_EXPERIENCE, coefficient * exponent_factor)
        exponent = 1.0 / (coefficient * exponent_factor)
        return pow(base_exp * level / MAX_LEVEL, exponent)


class StringDialogEditorView:
    def __init__(self, parent_frame, sql_connection, table_name):
        self.sql_connection = sql_connection
        self.table_name = table_name
        self.string_dialog_box = StringDialogBox(parent_frame)
        self.string_dialog_box.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        self.current_string_uid = None

    def setupEditForID(self, string_uid):
        self.current_string_uid = None
        self.string_dialog_box.fullReset()

        content = fetchString(
            self.sql_connection,
            'select col_0_String from ' + self.table_name + ' where UID =?',
            [string_uid])
        if content is None:
            return False

        self.current_string_uid = string_uid
        self.string_dialog_box.append(content[0])
        self.string_dialog_box.resetUndoHistory()
        return True

    def writeChangesToDatabase(self):
        if self.current_string_uid is None:
            return False
        if not self.string_dialog_box.prepareForWritingToDB():
            return False

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute(
            'update ' + self.table_name +
            ' set col_0_String = ? where UID = ?',
            [self.string_dialog_box.get(), self.current_string_uid])

        return True


class SpellEditorView:
    def __init__(self, parent_frame, sql_connection):
        self.sql_connection = sql_connection
        self.current_spell_uid = None
        self.current_spell_uid_db_suffix = ''
        self.spell_info_to_uid_mapping = {}

        spell_frame = tk.Frame(parent_frame)
        spell_frame.pack(fill=tk.BOTH, expand=True)
        spell_frame.rowconfigure(tuple(range(50)), weight=1)
        spell_frame.columnconfigure(0, weight=1)
        spell_frame.columnconfigure(1, weight=50)

        tk.Label(spell_frame, text='Type').grid(row=0, column=0, sticky='w')
        type_frame = tk.Frame(spell_frame)
        type_frame.grid(row=0, column=1, sticky='nwse')
        self.type_value = tk.IntVar()
        self.type_value.trace_add('write', callback=self.__toggleSpellType)
        active_button = ttk.Radiobutton(
            type_frame, text='Active', value=0, variable=self.type_value)
        active_button.pack(fill=tk.BOTH, expand=False, side=tk.LEFT)
        passive_button = ttk.Radiobutton(
            type_frame, text='Passive', value=1, variable=self.type_value)
        passive_button.pack(fill=tk.BOTH, expand=False, side=tk.LEFT)

        tk.Label(spell_frame, text='Required Slots').grid(
            row=1, column=0, sticky='w')
        self.slot_comboboxes = ElementClassComboboxSet(spell_frame, 1, 1)

        self.damage_value = makeStatChooser(spell_frame, 2, 'Damage')
        self.cast_speed_value = makeStatChooser(spell_frame, 3, 'Cast Speed')
        self.mana_value = makeListChooser(spell_frame, 4, 'Mana Points',
                                          MANA_LEVELS)

        self.effect_label, self.effect_combobox = \
            self.__makeLabeledEffectCombobox(spell_frame, 5, '')
        _, self.effect_info_combobox = \
            self.__makeLabeledEffectCombobox(spell_frame, 6, 'Info Text')

        self.missile_entry = self.__makeEffectEntryBox(
            spell_frame, 7, 'Missile Effect\n(Animation)')
        self.impact_entry = self.__makeEffectEntryBox(
            spell_frame, 8, 'Impact Effect\n(Animation)')

    def setupEditForID(self, spell_id):
        self.current_spell_uid = None

        uid = resolveUid(
            self.sql_connection, 'select UID, col_2_Integer from _fb0x03',
            spell_id)
        if uid is None:
            return False

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""select col_1_Integer, col_3_Byte, col_4_Byte,
        col_5_Byte, col_6_ForeignKey, col_7_Integer, col_8_Integer,
        col_10_Integer, col_11_Integer, col_12_Integer, col_13_Integer
        from _fb0x03 where UID = ?""", [uid])
        query_result = sql_cursor.fetchone()
        if query_result is None:
            return False

        is_passive, slot_0, slot_1, slot_2, info_uid, mana, cast_speed, \
            missile_effect, impact_effect, damage, spell_effect = query_result
        self.current_spell_uid_db_suffix = info_uid.split('|')[1]
        info_uid = info_uid.split('|')[0]

        sql_cursor.execute("""select UID, col_0_String from _fb0x02
        where col_1_Integer = 10 order by col_0_String""")
        spell_info_pairs = sql_cursor.fetchall()
        if spell_info_pairs is None:
            return False
        spell_info_strings = [s[1] for s in spell_info_pairs]

        self.type_value.set(is_passive)
        self.slot_comboboxes.set(0, slot_0)
        self.slot_comboboxes.set(1, slot_1)
        self.slot_comboboxes.set(2, slot_2)
        self.damage_value.set(damage)
        self.cast_speed_value.set(cast_speed)
        self.mana_value.set(mana)
        self.effect_combobox.set(self.effect_combobox['values'][spell_effect])
        self.effect_info_combobox['values'] = spell_info_strings
        self.effect_info_combobox.set(
            resolveLabel(self.sql_connection, info_uid))
        replaceEntryContent(self.missile_entry, str(missile_effect))
        replaceEntryContent(self.impact_entry, str(impact_effect))

        all_spell_strings = ACTIVE_SPELL_CRIT_EFFECTS + \
            PASSIVE_SPELL_EFFECTS + spell_info_strings
        effect_combobox_len = len(max(all_spell_strings, key=len))
        self.effect_combobox['width'] = effect_combobox_len
        self.effect_info_combobox['width'] = effect_combobox_len

        self.spell_info_to_uid_mapping = {}
        for info_uid, info_string in spell_info_pairs:
            self.spell_info_to_uid_mapping[info_string] = info_uid

        self.current_spell_uid = uid
        return True

    def writeChangesToDatabase(self):
        if self.current_spell_uid is None:
            return False

        if self.effect_info_combobox.get() not in \
                self.spell_info_to_uid_mapping:
            tkmessagebox.showerror(
                'Invalid String', 'Unknown effect info text selected: ' +
                self.effect_info_combobox.get())
            return False

        effect_animation_regex = re.compile(r'^(-1|[0-9]+)$', re.S)
        for entry, name in [[self.missile_entry, 'Missile'],
                            [self.impact_entry, 'Impact']]:
            if not effect_animation_regex.match(entry.get()):
                tkmessagebox.showerror(
                    'Invalid Integer',
                    name + ' effect entry contains invalid integer')
                return False
        info_uid = \
            self.spell_info_to_uid_mapping[self.effect_info_combobox.get()] + \
            '|' + self.current_spell_uid_db_suffix

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""update _fb0x03 set
        col_1_Integer=?, col_3_Byte=?, col_4_Byte=?, col_5_Byte=?,
        col_6_ForeignKey=?, col_7_Integer=?, col_8_Integer=?, col_10_Integer=?,
        col_11_Integer=?, col_12_Integer=?, col_13_Integer=?
        where UID = ?""", [
            self.type_value.get(),
            self.slot_comboboxes.get(0),
            self.slot_comboboxes.get(1),
            self.slot_comboboxes.get(2),
            info_uid,
            self.mana_value.get(),
            self.cast_speed_value.get(),
            int(self.missile_entry.get()),
            int(self.impact_entry.get()),
            self.damage_value.get(),
            self.effect_combobox.current(),
            self.current_spell_uid,
        ])

        return True

    def __toggleSpellType(self, ignore1, ignore2, ignore3):
        if self.type_value.get() == 0:
            self.effect_label['text'] = 'On Critical Hit'
            self.effect_combobox['values'] = ACTIVE_SPELL_CRIT_EFFECTS
        else:
            self.effect_label['text'] = 'Support Effect'
            self.effect_combobox['values'] = PASSIVE_SPELL_EFFECTS
        self.effect_combobox.set(self.effect_combobox['values'][0])

    def __makeLabeledEffectCombobox(self, frame, row, label_text):
        label = tk.Label(frame, text=label_text)
        label.grid(row=row, column=0, sticky='w')
        combobox = makeCombobox(frame)
        combobox.grid(row=row, column=1, sticky='w')
        return [label, combobox]

    def __makeEffectEntryBox(self, frame, row, label_text):
        tk.Label(frame, text=label_text).grid(row=row, column=0, sticky='w')
        entry = makeCheckedEntry(frame, r'^-?[0-9]*$')
        entry.grid(row=row, column=1, sticky='w')
        return entry


class ItemEditorView:
    def __init__(self, parent_frame, sql_connection):
        self.sql_connection = sql_connection
        self.code_box = CodeBox(parent_frame)
        self.current_item_uid = None

    def setupEditForID(self, item_id):
        self.current_item_uid = None
        self.code_box.fullReset()

        uid, decompiled_script = self.fetchUidAndDecompiledScript(item_id)
        if uid is None:
            return False

        self.current_item_uid = uid
        self.code_box.replaceContent(decompiled_script)
        self.code_box.resetUndoHistory()
        return True

    def fetchUidAndDecompiledScript(self, item_id):
        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute(
            'select UID, col_1_Integer, col_4_String from _fb0x04')
        for uid, card_id, script in sql_cursor.fetchall():
            if str(getCardEntityId(card_id)) == item_id:
                return [uid, decompile(self.sql_connection, str(script))]
        return None

    def writeChangesToDatabase(self):
        if self.current_item_uid is None:
            return False

        success, compiled_script = \
            compileAndShowErrorMessage(self.code_box.getContent())
        if success is False:
            return False

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute(
            'update _fb0x04 set col_4_String = ? where UID = ?',
            [compiled_script, self.current_item_uid])

        reformated_script = decompile(self.sql_connection, compiled_script)
        self.code_box.replaceContent(reformated_script)
        return True


class NPCEditorView:
    def __init__(self, parent_frame, sql_connection, add_settings_tab=True):
        self.code_boxes = {}
        self.code_box_names = ['Init', 'Update', 'Trigger',
                               'Victorious', 'Defeated']
        self.sql_connection = sql_connection
        self.current_npc_uid = None
        self.name_uid_suffix = None

        tabs = ttk.Notebook(parent_frame)
        for text in self.code_box_names:
            frame = tk.Frame(tabs)
            tabs.add(frame, text=text)
            self.code_boxes[text] = CodeBox(frame)
        tabs.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        settings_frame = tk.Frame(tabs)
        settings_frame.rowconfigure(0, weight=0)
        settings_frame.rowconfigure(1, weight=1)
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=50)
        if add_settings_tab:
            tabs.add(settings_frame, text='NPC Settings')

        name_label = tk.Label(settings_frame, text='NPC Name')
        name_label.grid(row=0, column=0, sticky='w')
        self.name_combobox = NPCNameCombobox(
            settings_frame, sql_connection, 0, 1)

    def setupEditForID(self, npc_uid):
        self.fullReset()

        scripts = fetchAllNpcScripts(self.sql_connection, npc_uid)
        if scripts is None:
            return False
        if not self.name_combobox.reloadNamesFromDatabase():
            return False

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute(
            "select col_0_ForeignKey from _fb0x05 where UID = ?",
            [npc_uid])
        name_uid = sql_cursor.fetchone()
        if name_uid is None:
            return False
        self.name_uid_suffix = name_uid[0].split('|')[1]
        name_uid = name_uid[0].split('|')[0]
        name = resolveLabel(self.sql_connection, name_uid)

        self.name_combobox.setName(name_uid, name)

        for name, script in scripts.items():
            decompiled_script = decompile(self.sql_connection, script)
            self.code_boxes[name].replaceContent(decompiled_script)
            self.code_boxes[name].resetUndoHistory()
        self.current_npc_uid = npc_uid

        return True

    def writeChangesToDatabase(self):
        if self.current_npc_uid is None:
            return False

        compiled_scripts = {}
        for index, name in enumerate(self.code_box_names):
            success, compiled_script = \
                compileAndShowErrorMessage(self.code_boxes[name].getContent())
            if success is False:
                return False
            compiled_scripts[name] = compiled_script
        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""update _fb0x05 set
            col_0_ForeignKey = ?,
            col_2_String = ?,
            col_3_String = ?,
            col_1_String = ?,
            col_5_String = ?,
            col_4_String = ?
            where UID = ?""", (
            self.name_combobox.getUid() + '|' + self.name_uid_suffix,
            compiled_scripts[self.code_box_names[0]],
            compiled_scripts[self.code_box_names[1]],
            compiled_scripts[self.code_box_names[2]],
            compiled_scripts[self.code_box_names[3]],
            compiled_scripts[self.code_box_names[4]],
            self.current_npc_uid,
        ))

        for name in self.code_box_names:
            raw_script = compiled_scripts[name]
            reformated_script = decompile(self.sql_connection, raw_script)
            self.code_boxes[name].replaceContent(reformated_script)

        return 'NPC(' + self.current_npc_uid + ') ' + \
            self.name_combobox.getName()

    def fullReset(self):
        self.current_npc_uid = None
        for name in self.code_box_names:
            self.code_boxes[name].fullReset()

    def disable(self):
        """
        Disables all active editing elements in this view.
        """
        for code_box in self.code_boxes.values():
            code_box.disable()

    def setCodeboxBackground(self, color):
        for code_box in self.code_boxes.values():
            code_box.setBackground(color)


class AddNPCEditorView:
    def __init__(self, parent_frame, sql_connection):
        self.sql_connection = sql_connection
        parent_frame.rowconfigure(0, weight=0)
        parent_frame.rowconfigure(1, weight=1)
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=50)

        label = tk.Label(parent_frame, text='NPC Name')
        label.grid(row=0, column=0, sticky='w')

        self.string_dialog_box = StringDialogBox(parent_frame)
        self.string_dialog_box.setGreenBackground()

        self.name_combobox = NPCNameCombobox(
            parent_frame, sql_connection, 0, 1)
        self.name_combobox.setCallback(self.__updateNameCombobox)

    def setupEditForID(self, npc_uid):
        self.string_dialog_box.fullReset()

        if not self.name_combobox.reloadNamesFromDatabase():
            return False

        self.name_combobox.prependCustomNameEntry('--- Create New String ---')
        self.name_combobox.setToFirstEntry()
        return True

    def writeChangesToDatabase(self):
        if not self.string_dialog_box.prepareForWritingToDB():
            return False

        with self.sql_connection:
            if self.__shouldCreateNewNameString():
                name = self.string_dialog_box.get()
                name_uid = insertStringIntoDatabase(
                    self.sql_connection,
                    5,  # NPC string type
                    self.string_dialog_box.get())
            else:
                name = self.name_combobox.getName()
                name_uid = self.name_combobox.getUid()

            npc_uid = generateRowUid(5)
            magic_suffix = '|0012F394'  # Extracted from game, unknown meaning

            sql_cursor = self.sql_connection.cursor()
            sql_cursor.execute("""insert into
            _fb0x05 (UID, col_0_ForeignKey, col_1_String, col_2_String,
                     col_3_String, col_4_String, col_5_String, col_6_String)
            values (?, ?, ?, ?, ?, ?, ?, ?)""", [
                npc_uid,
                name_uid + magic_suffix,
                '',  # Trigger script
                '',  # Init script
                '',  # Update script
                '',  # Defeated script
                '',  # Victorious script
                '',  # Internal name string, probably not needed
            ])

            return ('NPC', npc_uid, name)

    def __shouldCreateNewNameString(self):
        return self.name_combobox.getCurrentIndex() == 0

    def __updateNameCombobox(self):
        if self.__shouldCreateNewNameString():
            self.string_dialog_box.grid(row=1, column=0, columnspan=2,
                                        sticky='nswe')
            self.string_dialog_box.fullReset()
        else:
            self.string_dialog_box.gridForget()


class DeleteNPCEditorView:
    def __init__(self, parent_frame, sql_connection):
        self.sql_connection = sql_connection
        self.current_npc_uid = None
        self.current_npc_string_uid = None

        parent_frame.rowconfigure(0, weight=0)
        parent_frame.rowconfigure(1, weight=1)
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=50)

        label = tk.Label(
            parent_frame, text='Open name-string deletion dialog afterwards')
        label.grid(row=0, column=0, sticky='w')

        self.proceed_with_name_deletion = tk.IntVar()
        checkbox = ttk.Checkbutton(
            parent_frame, variable=self.proceed_with_name_deletion)
        checkbox.grid(row=0, column=1, sticky='w')

        editor_view_frame = tk.Frame(parent_frame)
        editor_view_frame.grid(row=1, column=0, columnspan=2, sticky='nwse')
        self.editor_view = NPCEditorView(
            editor_view_frame, sql_connection, False)
        self.editor_view.disable()
        self.editor_view.setCodeboxBackground('#3c2c3c')

    def setupEditForID(self, npc_uid):
        self.__fullReset()

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute(
            'select col_0_ForeignKey from _fb0x05 where UID = ?',
            [npc_uid])
        sql_result = sql_cursor.fetchone()
        if sql_result is None:
            return False

        if not self.editor_view.setupEditForID(npc_uid):
            return False

        self.current_npc_uid = npc_uid
        self.current_npc_string_uid = sql_result[0].split('|')[0]

        return True

    def writeChangesToDatabase(self):
        if self.current_npc_uid is None:
            return False

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute('delete from _fb0x05 where uid = ?',
                           [self.current_npc_uid])

        result = ('IntroductionFrame', '', '')
        if self.proceed_with_name_deletion.get() == 1:
            result = ('DeleteTextItem',
                      self.current_npc_string_uid,
                      self.current_npc_string_uid)

        self.__fullReset()
        return result

    def __fullReset(self):
        self.current_npc_uid = None
        self.current_npc_string_uid = None
        self.proceed_with_name_deletion.set(0)
        self.editor_view.fullReset()


class AddStringDialogView:
    """
    This class is responsible for creating either database strings or dialog
    texts.
    """

    def __init__(self, parent_frame, sql_connection):
        self.sql_connection = sql_connection

        grid_frame = tk.Frame(parent_frame)
        grid_frame.rowconfigure(0, weight=0)
        grid_frame.rowconfigure(1, weight=1)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=50)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(grid_frame, text='New Item Type')
        label.grid(row=0, column=0, sticky='w')
        self.type_combobox = makeCombobox(grid_frame)
        self.type_combobox.grid(row=0, column=1, sticky='we')
        self.type_combobox['values'] = [
            'Dialog Text', 'NPC Name', 'Spell Info Text',
        ]
        self.type_combobox.set(self.type_combobox['values'][0])

        self.string_dialog_box = StringDialogBox(grid_frame)
        self.string_dialog_box.setGreenBackground()
        self.string_dialog_box.grid(
            row=1, column=0, columnspan=2, sticky='nswe')

    def setupEditForID(self, _):
        self.type_combobox.set(self.type_combobox['values'][0])
        self.string_dialog_box.fullReset()
        return True

    def writeChangesToDatabase(self):
        if not self.string_dialog_box.prepareForWritingToDB():
            return False

        if self.type_combobox.get() == 'Dialog Text':
            return self.__saveAsDialogText()
        elif self.type_combobox.get() == 'NPC Name':
            return self.__saveAsString(5)  # NPC string type
        elif self.type_combobox.get() == 'Spell Info Text':
            return self.__saveAsString(10)  # Spell string type
        return False

    def __saveAsDialogText(self):
        new_uid = generateRowUid(6)

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""insert into
            _fb0x06 (UID, col_0_String, col_1_Integer, col_2_String)
            values (?, ?, ?, ?)""", [
            new_uid,
            self.string_dialog_box.get(),
            0,  # NPC UID, probably not needed
            '',  # Always empty
        ])

        return ('Dialog', new_uid, new_uid)

    def __saveAsString(self, string_type):
        new_uid = insertStringIntoDatabase(
            self.sql_connection, string_type, self.string_dialog_box.get())
        return ('String', new_uid, new_uid)


class DeleteStringDialogView:
    def __init__(self, parent_frame, sql_connection):
        self.sql_connection = sql_connection
        self.current_entry_id = None

        self.string_dialog_box = StringDialogBox(parent_frame)
        self.string_dialog_box.setRedBackground()
        self.string_dialog_box.disable()
        self.string_dialog_box.pack(fill=tk.BOTH, expand=True)

    def canDelete(self, entry_id):
        return self.__isDeleteableString(entry_id) or \
                self.__isDeleteableDialog(entry_id)

    def setupEditForID(self, entry_id):
        self.string_dialog_box.fullReset()
        self.current_entry_id = None

        if self.__isDeleteableString(entry_id):
            self.string_dialog_box.append(
                resolveLabel(self.sql_connection, entry_id))
        elif self.__isDeleteableDialog(entry_id):
            self.string_dialog_box.append(
                resolveDialog(self.sql_connection, entry_id))
        else:
            return False

        self.current_entry_id = entry_id
        return True

    def writeChangesToDatabase(self):
        if self.current_entry_id is None:
            return False

        table = ''
        if self.__isDeleteableString(self.current_entry_id):
            table = '_fb0x02'
        elif self.__isDeleteableDialog(self.current_entry_id):
            table = '_fb0x06'
        else:
            return False

        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute('delete from ' + table + ' where uid = ?',
                           [self.current_entry_id])
        self.current_entry_id = None

        return ('IntroductionFrame', '', '')

    def __isDeleteableString(self, string_uid):
        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute("""select 1 from _fb0x02
        where UID = ? and (col_1_Integer == 5 or col_1_Integer is 10)
        """, [string_uid])
        return sql_cursor.fetchone() is not None

    def __isDeleteableDialog(self, dialog_uid):
        sql_cursor = self.sql_connection.cursor()
        sql_cursor.execute('select 1 from _fb0x06 where UID = ?', [dialog_uid])
        return sql_cursor.fetchone() is not None


class EditorViewContainer:
    """
    View with save button responsible for dispatching pairs like
    ['NPC', 'E12F912'] by setting up the proper widgets in the given edit
    frame.
    """

    def __init__(self, edit_frame, sql_connection):
        self.sql_connection = sql_connection

        self.top_frame = tk.Frame(edit_frame)
        self.top_frame.rowconfigure(0, weight=1)
        self.top_frame.columnconfigure(tuple(range(30)), weight=1)
        self.top_frame.pack(fill=tk.BOTH, expand=False, side=tk.TOP)

        self.edit_label = tk.Label(self.top_frame)
        self.edit_label.grid(row=0, column=0, sticky='WE')
        self.save_button = tk.Button(
            self.top_frame, text='Save (Control + S)',
            state='disabled', command=self.writeChangesToDatabase
        )
        self.save_button.grid(row=0, column=39)

        self.intro_frame_pair = self.__WidgetFramePair(edit_frame)
        self.intro_frame_pair.widget = tk.Label(
            self.intro_frame_pair.frame,
            text=self.__introduction_text,
            justify=tk.LEFT,
            font=makeResizedFont())
        self.intro_frame_pair.widget.pack(
            fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        self.intro_frame_pair.frame.pack(
            fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        self.current_frame_pair = self.intro_frame_pair

        self.fairy_frame_pair = self.__WidgetFramePair(edit_frame)
        self.fairy_frame_pair.widget = FairyEditorView(
            self.fairy_frame_pair.frame, sql_connection)

        self.string_frame_pair = self.__WidgetFramePair(edit_frame)
        self.string_frame_pair.widget = StringDialogEditorView(
            self.string_frame_pair.frame, sql_connection, '_fb0x02')

        self.spell_frame_pair = self.__WidgetFramePair(edit_frame)
        self.spell_frame_pair.widget = \
            SpellEditorView(self.spell_frame_pair.frame, sql_connection)

        self.item_frame_pair = self.__WidgetFramePair(edit_frame)
        self.item_frame_pair.widget = \
            ItemEditorView(self.item_frame_pair.frame, sql_connection)

        self.npc_frame_pair = self.__WidgetFramePair(edit_frame)
        self.npc_frame_pair.widget = \
            NPCEditorView(self.npc_frame_pair.frame, sql_connection)

        self.dialog_frame_pair = self.__WidgetFramePair(edit_frame)
        self.dialog_frame_pair.widget = StringDialogEditorView(
            self.dialog_frame_pair.frame, sql_connection, '_fb0x06')

        self.add_text_frame_pair = self.__WidgetFramePair(edit_frame)
        self.add_text_frame_pair.widget = AddStringDialogView(
            self.add_text_frame_pair.frame, sql_connection)

        self.delete_text_frame_pair = self.__WidgetFramePair(edit_frame)
        self.delete_text_frame_pair.widget = DeleteStringDialogView(
            self.delete_text_frame_pair.frame, sql_connection)

        self.add_npc_pair = self.__WidgetFramePair(edit_frame)
        self.add_npc_pair.widget = AddNPCEditorView(
            self.add_npc_pair.frame, sql_connection)

        self.delete_npc_pair = self.__WidgetFramePair(edit_frame)
        self.delete_npc_pair.widget = DeleteNPCEditorView(
            self.delete_npc_pair.frame, sql_connection)

        self.frame_table = {
            'IntroductionFrame': self.intro_frame_pair,
            'Fairy': self.fairy_frame_pair,
            'String': self.string_frame_pair,
            'Spell': self.spell_frame_pair,
            'Item': self.item_frame_pair,
            'NPC': self.npc_frame_pair,
            'Dialog': self.dialog_frame_pair,
            'AddTextItem': self.add_text_frame_pair,
            'DeleteTextItem': self.delete_text_frame_pair,
            'AddNPC': self.add_npc_pair,
            'DeleteNPC': self.delete_npc_pair,
        }

        self.after_db_update_callback = None

    def canEdit(self, entry_type):
        return entry_type in self.frame_table

    def canDelete(self, entry_type, entry_id):
        if entry_type == 'Dialog' or entry_type == 'String':
            return self.delete_text_frame_pair.widget.canDelete(entry_id)
        return entry_type == 'NPC'

    def startEditing(self, entry_type, entry_id, short_description=''):
        matching_editor_view = None
        if not self.canEdit(entry_type):
            return

        matching_editor_view = self.frame_table[entry_type]
        new_label_text = entry_type + '(' + entry_id + ') '
        new_label_text += short_description

        if entry_type != 'IntroductionFrame' and \
                matching_editor_view.widget.setupEditForID(entry_id):
            self.save_button['state'] = 'normal'
            self.edit_label['text'] = new_label_text
        else:
            self.save_button['state'] = 'disabled'
            self.edit_label['text'] = ''
            matching_editor_view = self.intro_frame_pair

        if matching_editor_view is not self.current_frame_pair:
            self.current_frame_pair.frame.pack_forget()
            self.current_frame_pair = matching_editor_view
            self.current_frame_pair.frame.pack(
                fill=tk.BOTH, expand=True, side=tk.BOTTOM)

    def setAfterDBUpdateCallback(self, callback):
        """
        Register a function to be called after a successful database update.
        """
        self.after_db_update_callback = callback

    def writeChangesToDatabase(self):
        if self.current_frame_pair is self.intro_frame_pair:
            return

        write_result = self.current_frame_pair.widget.writeChangesToDatabase()
        if write_result is False or write_result is None:
            return

        self.sql_connection.commit()
        if self.after_db_update_callback is not None:
            self.after_db_update_callback()

        if isinstance(write_result, str):
            self.edit_label['text'] = write_result
        elif isinstance(write_result, tuple):
            entry_type, entry_id, short_description = write_result
            self.startEditing(entry_type, entry_id, short_description)

    def pressSaveButton(self):
        if self.save_button['state'] == 'disabled':
            return

        self.save_button['state'] = 'active'
        self.save_button['relief'] = tk.SUNKEN
        self.save_button.update_idletasks()

        self.save_button.invoke()

        self.save_button['state'] = 'normal'
        self.save_button['relief'] = tk.RAISED

    class __WidgetFramePair:
        def __init__(self, parent_frame):
            self.widget = None
            self.frame = tk.Frame(parent_frame)
            self.frame.rowconfigure(0, weight=1)
            self.frame.columnconfigure(0, weight=1)

    __introduction_text = """
Search the database and select entries by right-clicking.

Searching for "rafi npc" will list everything that
contains "npc", "Npc" and "rafi", "RAFI", ...

To list all fairies with a jump power of 1, search
for "jump(*)"

"""


class SearchCache:
    def __init__(self):
        self.cache = []

    def appendToIndex(self, sort_key, displayed_text, search_suggestion,
                      extra_info=''):
        """
        The given extra_info is not displayed, but matched against substrings
        during searches.
        """
        string_to_search = sort_key.casefold() + displayed_text.casefold() + \
            extra_info.casefold()
        self.cache.append(self.__IndexedItem(
            sort_key.casefold(),
            displayed_text.replace('\n', ' '),
            makeStringSearchable(string_to_search),
            search_suggestion,
        ))

    def searchSubstrings(self, substring_list):
        """
        Case-insensitive, order-independent search for substrings in the
        cache. E.g. searchSubstrings(['rafi', 'npc']) returns everything that
        contains both "npc" and "rafi".

        The returned result contains a list of pairs in the order they got
        inserted, example: [['displayed_text', 'search_suggestion'], ...]
        """
        matches = self.cache
        substring_list = [s.casefold() for s in substring_list]
        for substring in substring_list:
            matches = [
                item for item in matches if substring in item.string_to_search
            ]
        return [
            [item.displayed_text, item.search_suggestion] for item in matches
        ]

    def reset(self):
        self.cache = []

    def sort(self):
        self.cache.sort(key=lambda item: item.sort_key)

    def appendOtherCache(self, other_cache):
        self.cache += other_cache.cache

    @dataclass
    class __IndexedItem:
        # Case-folded
        sort_key: str
        displayed_text: str
        # Case-folded
        string_to_search: str
        # Suggested in the right-click contextmenu in "Search for ..."
        search_suggestion: str


class DBSearchView:
    def __init__(self, parent_frame, sql_connection, editor_view):
        self.sql_connection = sql_connection
        self.parent_frame = parent_frame
        self.editor_view = editor_view

        top_frame = tk.Frame(parent_frame)
        top_frame.rowconfigure(0, weight=1)
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=10)
        top_frame.pack(fill=tk.BOTH, expand=False, side=tk.TOP)

        bottom_frame = tk.Frame(parent_frame)
        bottom_frame.rowconfigure(0, weight=1)
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        search_label = tk.Label(top_frame, text='Search (Control + L)')
        search_label.grid(row=0, column=0, sticky='WE')
        self.filter_input_string = tk.StringVar()
        self.filter_input_string \
            .trace_add('write', lambda ignore1, ignore2, ignore3:
                       self.refreshSearch(self.filter_input_string.get()))
        self.filter_input_box = tk.Entry(
            top_frame, textvariable=self.filter_input_string)
        self.filter_input_box.grid(row=0, column=1, sticky='WE')

        self.text_box = makeTextBox(bottom_frame, tk.Text)
        self.text_box.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        self.delegator = self.makeColorDelegator()
        percolator.Percolator(self.text_box).insertfilter(self.delegator)

        self.context_menu = tk.Menu(parent_frame, tearoff=0)
        self.text_box.bind('<Button-3>', self.openContextMenu)

        self.db_cache = SearchCache()
        self.reloadDB()

    def focusSearchBox(self):
        self.filter_input_box.focus()
        self.filter_input_box.selection_range(0, tk.END)

    def makeColorDelegator(self):
        """
        Return a ColorDelegator for syntax highlighting db content.
        """
        delegator = colorizer.ColorDelegator()
        delegator.tagdefs['HIGHLIGHTED'] = {
            'foreground': '#cdcecf', 'background': '#3c5372'
        }
        delegator.tagdefs['TRUNCATED'] = {'foreground': '#c94f6d'}
        delegator.tagdefs['TYPE'] = {'foreground': '#9d79d6'}
        delegator.tagdefs['UID'] = {'foreground': '#86abdc'}
        delegator.tagdefs['CLOSINGPAREN'] = delegator.tagdefs['TYPE']
        delegator.tagdefs['SLOTSSTART'] = {'foreground': '#f6b079'}
        delegator.tagdefs['SLOTS'] = {'foreground': '#dbc074'}
        delegator.tagdefs['SLOTSEND'] = delegator.tagdefs['SLOTSSTART']
        delegator.tagdefs['ATTRIBSTART'] = delegator.tagdefs['SLOTSSTART']
        delegator.tagdefs['ATTRIBVARS'] = delegator.tagdefs['SLOTS']
        delegator.tagdefs['ATTRIBEND'] = delegator.tagdefs['ATTRIBSTART']
        addDialogHighlightGroups(delegator.tagdefs)
        return delegator

    def rebuildDBCache(self):
        self.db_cache.reset()
        sql_cursor = self.sql_connection.cursor()

        # Strings
        sql_cursor.execute('select UID, col_0_String from _fb0x02')
        for uid, string in sql_cursor.fetchall():
            self.db_cache.appendToIndex(
                string, 'String(' + uid + ') ' + string, uid
            )

        # Fairies
        sql_cursor.execute("""select col_0_String, col_1_ForeignKey,
        col_2_Integer, col_3_Integer, col_15_ForeignKey, col_16_Integer,
        col_17_Integer, col_18_Integer, col_19_Integer, col_20_Integer,
        col_21_Integer, col_23_Integer from _fb0x01""")
        for model_uid, name_uid, element_class, card_id, info_uid, hp, \
                evolution_id, evolution_level, speed, jump_ability, special, \
                glow_id in sql_cursor.fetchall():
            name_uid = name_uid.split('|')[0]
            name = resolveLabel(self.sql_connection, name_uid)
            evolution_info = NONE_STRING
            if evolution_id != -1:
                evolution_name = resolveFairyName(self.sql_connection,
                                                  evolution_id)
                evolution_info = str(evolution_level) + ' -> ' + evolution_name
            glow_text = ''
            if glow_id >= 0 and glow_id < len(FAIRY_GLOWS_WITH_INTENSITY):
                glow_text = FAIRY_GLOWS_WITH_INTENSITY[glow_id][0]
            displayed_text = \
                'Fairy(' + str(getCardEntityId(card_id)) + ') ' + \
                name + \
                ' [' + self.__resolveElementClass(element_class) + ']' + \
                ' MaxHP(' + str(hp) + ')' + \
                ' Speed(' + toStatString(speed) + ')' + \
                ' Jump(' + toStatString(jump_ability) + ')' + \
                ' Special(' + toStatString(special) + ')' + \
                ' Evolution(' + evolution_info + ')' + \
                ' Model(' + model_uid + ')'
            self.db_cache.appendToIndex(
                name, displayed_text,
                name, name_uid + info_uid + glow_text,
            )

        # Spells
        sql_cursor.execute("""select col_0_ForeignKey, col_1_Integer,
        col_2_Integer, col_3_Byte, col_4_Byte, col_5_Byte, col_6_ForeignKey,
        col_7_Integer, col_8_Integer, col_12_Integer, col_13_Integer
        from _fb0x03""")
        for name_uid, is_passive, card_id, slot_0, slot_1, slot_2, \
                info_uid, mana, cast_speed, damage, spell_effect \
                in sql_cursor.fetchall():
            name_uid = name_uid.split('|')[0]
            info_uid = info_uid.split('|')[0]
            name = resolveLabel(self.sql_connection, name_uid)
            spell_type = 'passive' if str(is_passive) == '1' else 'active'
            slots = [self.__resolveElementClass(slot_0),
                     self.__resolveElementClass(slot_1),
                     self.__resolveElementClass(slot_2)]
            slots = [s for s in slots if NONE_STRING not in s]
            if len(slots) == 0:
                slots = [ELEMENT_CLASSES[0]]
            displayed_text = \
                'Spell(' + str(getCardEntityId(card_id)) + \
                ', ' + spell_type + ') ' + name + \
                ' [' + ', '.join(slots) + ']' + \
                ' Damage(' + toStatString(damage) + ')' + \
                ' Speed(' + toStatString(cast_speed) + ')' + \
                ' Mana(' + resolveMana(mana) + ')' + \
                ' ' + resolveLabel(self.sql_connection, info_uid)

            effect_description = ''
            effect_description_list = \
                PASSIVE_SPELL_EFFECTS if str(is_passive) == '1' \
                else ACTIVE_SPELL_CRIT_EFFECTS
            if spell_effect >= 0 and \
                    spell_effect < len(effect_description_list):
                effect_description = effect_description_list[spell_effect]
            self.db_cache.appendToIndex(
                name, displayed_text, name,
                name_uid + info_uid + effect_description)

        # Items
        sql_cursor.execute("""select col_0_ForeignKey, col_1_Integer,
        col_2_ForeignKey, col_4_String from _fb0x04""")
        for name_uid, card_id, info_uid, script in sql_cursor.fetchall():
            name_uid = name_uid.split('|')[0]
            info_uid = info_uid.split('|')[0]
            name = resolveLabel(self.sql_connection, name_uid)
            decompiled_script = decompile(self.sql_connection, str(script))
            displayed_text = \
                'Item(' + str(getCardEntityId(card_id)) + ') ' + name + \
                ' -- ' + resolveLabel(self.sql_connection, info_uid)
            self.db_cache.appendToIndex(
                name,
                displayed_text,
                name,
                name_uid + info_uid + decompiled_script,
            )

        # Dialogs
        sql_cursor.execute('select UID, col_0_String from _fb0x06')
        for uid, dialog_text in sql_cursor.fetchall():
            self.db_cache.appendToIndex(
                str(dialog_text),
                'Dialog(' + uid + ') ' + str(dialog_text),
                uid
            )

        # Built-in script commands
        for command in SCRIPT_COMMANDS.values():
            displayed_text = 'Command(' + command + ')'
            if command in script_command_parameters:
                parameters = script_command_parameters[command]
                displayed_text += ' ' + ', '.join(parameters)
            self.db_cache.appendToIndex(
                command,
                displayed_text,
                command
            )

        self.db_cache.sort()

        # Append NPCs last to cleanup presented results.
        npc_cache = SearchCache()
        sql_cursor.execute('select UID, col_0_ForeignKey from _fb0x05')
        for uid, name_uid in sql_cursor.fetchall():
            name_uid = name_uid.split('|')[0]
            name = resolveLabel(self.sql_connection, name_uid)
            scripts = fetchAllNpcScripts(self.sql_connection, uid).values()
            decompiled_scripts = [
                decompile(self.sql_connection, str(s)) for s in scripts
            ]

            npc_cache.appendToIndex(
                name,
                'NPC(' + uid + ') ' + name,
                name,
                name_uid + ''.join(decompiled_scripts) +
                self.__toRawIntString(uid),
            )
        npc_cache.sort()
        self.db_cache.appendOtherCache(npc_cache)

    def searchDBCache(self, search_query):
        """
        Takes space-separated substrings and returns all DB entries matching
        it. E.g. searchDBCache('rafi npc') returns everything that contains
        both "npc" and "rafi", case insensitive.
        """
        return self.db_cache.searchSubstrings(splitByWhitespace(search_query))

    def refreshSearch(self, search_query):
        found_results = self.searchDBCache(search_query)
        text_box_content = \
            found_results[0][0] if len(found_results) > 0 else ''
        for line, _ in islice(found_results, 1, None):
            text_box_content += '\n' + line
            if len(text_box_content) > 15000:
                text_box_content += '\n...truncated, too many results'
                break

        if self.text_box.get('1.0', 'end-1c') != text_box_content:
            self.text_box['state'] = 'normal'
            self.text_box.delete('1.0', 'end')
            self.text_box.insert(tk.END, text_box_content)
            self.text_box['state'] = 'disabled'
        else:
            self.delegator.notify_range('1.0', tk.END)

        regex = r'(?P<TRUNCATED>(^|\n)\.\.\.truncated.*$)' + \
                r'|(^|\n)(?P<TYPE>(Command|Dialog|Fairy|Item|NPC|' + \
                r'Spell|String)\()(?P<UID>[^\)]+)(?P<CLOSINGPAREN>\))' + \
                r'|(?P<SLOTSSTART>\[)(?P<SLOTS>[^\]]+)(?P<SLOTSEND>\])' + \
                r'|(?P<ATTRIBSTART> (Mana|Speed|Damage|Model|MaxHP|Speed' + \
                r'|Jump|Special|Evolution)\()(?P<ATTRIBVARS>[^\)]+)' + \
                r'(?P<ATTRIBEND>\))|' + DIALOG_HIGHLIGHT_REGEX

        search_strings = splitByWhitespace(self.filter_input_string.get())
        if len(search_strings) > 0:
            regex += r'|(?P<HIGHLIGHTED>('
            regex += '|'.join([re.escape(s) for s in search_strings])
            regex += r'))'
        self.delegator.prog = re.compile(regex, re.IGNORECASE)

    def openContextMenu(self, event):
        line, column = [
            int(s) for s in self.text_box.index(tk.CURRENT).split('.')
        ]
        search_results = self.searchDBCache(self.filter_input_string.get())

        self.context_menu.delete(0, 'end')
        if line > len(search_results):
            selected_line = ''
            entry_type = ''
            entry_id = ''
            search_suggestion = ''
        else:
            selected_line = search_results[line - 1][0]
            entry_type = selected_line.split('(')[0]
            entry_id = extractUid(selected_line).split(',')[0]
            search_suggestion = search_results[line - 1][1]
            self.context_menu \
                .add_command(label='Search for ' + search_suggestion,
                             command=lambda:
                             self.filter_input_string.set(search_suggestion))

        if len(selected_line) > 50:
            selected_line = selected_line[:47] + '...'

        if self.editor_view.canEdit(entry_type):
            self.context_menu.add_command(
                label='Edit ' + selected_line, command=lambda:
                self.editor_view.startEditing(entry_type,
                                              entry_id,
                                              search_suggestion))
            if entry_type == 'NPC':
                self.context_menu.add_command(
                    label='Copy UID as Raw Integer',
                    command=lambda:
                    self.__copyToClipboard(self.__toRawIntString(entry_id)))

        if self.editor_view.canDelete(entry_type, entry_id):
            command = 'DeleteNPC' if entry_type == 'NPC' else 'DeleteTextItem'
            self.context_menu.add_command(
                label='Delete ' + selected_line, command=lambda:
                self.editor_view.startEditing(command,
                                              entry_id,
                                              search_suggestion))

        if self.editor_view.canEdit(entry_type):
            self.context_menu.add_separator()

        self.context_menu.add_command(
            label='Add String or Dialog Text',
            command=lambda:
            self.editor_view.startEditing('AddTextItem', '', ''))
        self.context_menu.add_command(
            label='Add NPC',
            command=lambda:
            self.editor_view.startEditing('AddNPC', '', ''))
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def reloadDB(self):
        self.rebuildDBCache()
        self.refreshSearch(self.filter_input_string.get())

    def __resolveElementClass(self, id):
        if id < 0 or id >= len(ELEMENT_CLASSES):
            return 'NULL'
        return ELEMENT_CLASSES[id]

    def __toRawIntString(self, uid_string):
        return str(int(uid_string, 16))

    def __copyToClipboard(self, string):
        self.parent_frame.clipboard_clear()
        self.parent_frame.clipboard_append(string)


if len(sys.argv) > 1:
    db_path = sys.argv[1]
else:
    db_path = tkfiledialog.askopenfilename(
        title='Select Database File',
        filetypes=[
            ['SQLite3 Database', '*.db'],
            ['SQLite3 Database', '*.sqlite'],
        ])
    if len(db_path) == 0:
        exit(1)

if len(sys.argv) > 2:
    after_commit_command = sys.argv[2]
else:
    after_commit_command = None


matplotlib.use('TkAgg')
matplotlib.rcParams['figure.facecolor'] = '#1c1c1c'
matplotlib.rcParams['axes.facecolor'] = '#192330'
for color in ['text', 'xtick', 'ytick']:
    matplotlib.rcParams[color + '.color'] = '#cdcecf'

root_window = tk.Tk()
root_window.minsize(680, 300)
root_window.geometry('1280x720')
root_window.title('ZanZarah - Database Editor')
sv_ttk.set_theme('dark')

paned_window = ttk.PanedWindow(root_window, orient=tk.HORIZONTAL)
left_frame = tk.Frame(paned_window)
right_frame = tk.Frame(paned_window)
left_frame.pack_propagate(0)
right_frame.pack_propagate(0)
paned_window.add(left_frame, weight=1)
paned_window.add(right_frame, weight=1)
paned_window.pack(fill=tk.BOTH, expand=True)

with sqlite3.connect(db_path) as sql_connection:
    editor_view = EditorViewContainer(right_frame, sql_connection)
    db_search = DBSearchView(left_frame, sql_connection, editor_view)

    def afterDbReload():
        db_search.reloadDB()
        if after_commit_command is not None:
            try:
                subprocess.Popen(
                    after_commit_command, shell=True,
                    stdout=sys.stdout, stderr=sys.stderr,
                ).wait()
            except Exception as exception:
                sys.stderr.write(f'{exception}\n')
    editor_view.setAfterDBUpdateCallback(afterDbReload)

    root_window.bind_all(
        '<Control-l>', lambda _: db_search.focusSearchBox())
    root_window.bind_all(
        '<Control-s>', lambda _: editor_view.pressSaveButton())

    db_search.focusSearchBox()
    tk.mainloop()
