#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
import socket


def ip2long(ip):
    _ip = socket.inet_aton(ip)
    return struct.unpack("!L", _ip)[0]


def isip(ip):
    p = ip.split(".")

    if len(p) != 4: return False
    for pp in p:
        if not pp.isdigit(): return False
        if len(pp) > 3: return False
        if int(pp) > 255: return False

    return True


def getLong(b, offset):
    t = b[offset:offset + 4]
    if len(t) == 4:
        return struct.unpack('I', t)[0]
    return 0


class Ipv4Finder(object):
    __INDEX_BLOCK_LENGTH = 12
    __buffer = b''
    __start = 0
    __final = 0
    __count = 0

    def __init__(self, dbfile):
        if self.__buffer: return

        with open(dbfile, "rb") as fp:
            self.__buffer = fp.read()
            self.__start = getLong(self.__buffer, 0)
            self.__final = getLong(self.__buffer, 4)
            self.__count = int((self.__final - self.__start) / self.__INDEX_BLOCK_LENGTH) + 1


    def search(self, ip):
        if not ip.isdigit(): ip = ip2long(ip)

        left, right, dataPtr = (0, self.__count, 0)
        while left <= right:
            middle= int((left + right) >> 1)
            p = self.__start + middle * self.__INDEX_BLOCK_LENGTH
            sip = getLong(self.__buffer, p)

            if ip < sip:
                right = middle - 1
            else:
                eip = getLong(self.__buffer, p + 4)
                if ip > eip:
                    left = middle + 1;
                else:
                    dataPtr = getLong(self.__buffer, p + 8)
                    break

        return (0, "") if dataPtr == 0 else self.returnData(dataPtr)


    def returnData(self, dataPtr):
        """
        " get ip data from db file by data start ptr
        """
        dataLen = (dataPtr >> 24) & 0xFF
        dataPtr = dataPtr & 0x00FFFFFF

        data = self.__buffer[dataPtr:dataPtr+dataLen]
        return getLong(data, 0), data[4:].decode('utf-8')


if __name__ == "__main__":
    finder = Ipv4Finder("./ip2region.db")
    city_id, region = finder.search("58.247.102.162")
    print("%s, %s " % (city_id, region))


