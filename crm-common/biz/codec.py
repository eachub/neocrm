#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mtkext.cipher import SimpleCipher
import re
from sanic.log import logger

_regex = re.compile(r'\d+')


def define_cipher(key):
    if not key:
        logger.info("encrypt-mode is off, use PLAIN text")
        return None
    logger.info(f"encrypt-mode is open, key-size={len(key)}")
    return SimpleCipher("AES", key, shorten=True, safe=False)


def encrypt_item(aes, plain):
    return "$" + aes.encrypt(plain) + "$" if aes else plain


def decrypt_item(aes, encrypted):
    try:
        if aes and encrypted.startswith("$"):
            ret = aes.decrypt(encrypted.strip("$"))
            logger.info(f"解析数据{encrypted}==>{ret}")
            return ret
    except Exception as ex:
        logger.info(f"解密错误{encrypted}")
        return encrypted
    return encrypted


def phone_add_mask(aes, phone):
    phone = decrypt_item(aes, phone)
    if phone.startswith("$"): return "", "", ""
    _phone = phone[:3] + "*****" + phone[8:] if len(phone) >= 8 else "***"
    return _phone


if __name__ == '__main__':
    KEY = "EROS#CRM987"
    cipher = define_cipher(KEY)
    phone = '13270357060'
    print(encrypt_item(cipher, phone))
    # print(decrypt_item(cipher, "$Cgfm8gCdlyhcCjsg604Sbw==$"))
    phone = phone_add_mask(cipher, phone)
    print(phone)


