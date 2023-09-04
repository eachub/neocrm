# -*- coding: utf-8 -*-

import hashlib
import time
import random
from collections import defaultdict

from datetime import datetime, timedelta, date
from mtkext.dt import datetimeToTimestamp, timestampToDatetime
from mtkext.dt import datetimeFromString, datetimeToString
from mtkext.dt import timestampFromString, timestampToString, dateFromString
from mtkext.auth import require

from sanic.kjson import json_loads, json_dumps
from sanic.log import logger
from sanic.blueprints import Blueprint
from sanic.response import json, file, text, html, raw, redirect
from peewee import DoesNotExist