from __future__ import annotations

import datetime
import glob
import json
import statistics
import time
from enum import Enum
import os
import pytz
import tweepy


class DataType:
    def __init__(self, symbol: str, unit: str, fileName: str, italianName: str, precision: int = 2):
        self.symbol = symbol
        self.unit = unit
        self.fileName = fileName
        self.italianName = italianName
        self.precision = precision


class DataTypeArchive:
    data = [
        DataType("T", "°C", "temperature.csv", "Temperatura"),
        DataType("H", "%", "humidity.csv", "Umidità"),
        DataType("P", "hPa", "pressure.csv", "Pressione"),
        DataType("PM10", "µg/m³", "pm10.csv", "PM10"),
        DataType("PM25", "µg/m³", "pm25.csv", "PM2,5"),
        DataType("S", "µg/m³", "smoke.csv", "Fumo e vapori infiammabili")
    ]

    class Symbols(Enum):
        temperature = "T"
        humidity = "H"
        pressure = "P"
        pm10 = "PM10"
        pm25 = "PM25"
        smoke = "S"

    @staticmethod
    def fromSymbol(symbol: str) -> DataType | None:
        for dataType in DataTypeArchive.data:
            if dataType.symbol == symbol:
                return dataType
        return None

    @staticmethod
    def fromUnit(unit: str) -> DataType | None:
        for dataType in DataTypeArchive.data:
            if dataType.unit == unit:
                return dataType
        return None

    @staticmethod
    def fromFileName(fileName: str) -> DataType | None:
        for dataType in DataTypeArchive.data:
            if dataType.fileName == fileName:
                return dataType
        return None

    @staticmethod
    def fromItalianName(italianName: str) -> DataType | None:
        for dataType in DataTypeArchive.data:
            if dataType.italianName == italianName:
                return dataType
        return None


class Value:
    def __init__(self, value: float, symbol: DataTypeArchive.Symbols = DataTypeArchive.Symbols.temperature,
                 instant: datetime.datetime = datetime.datetime.now()):
        self.value = round(value, DataTypeArchive.fromSymbol(symbol.value).precision)
        self.symbol = symbol
        self.instant = instant


class DataArchive:

    @staticmethod
    def report() -> str:
        with open("dati/report.txt") as r:
            return r.read()

    @staticmethod
    def current() -> dict:
        with open("dati/last.json") as r:
            return json.loads(r.read())

    @staticmethod
    def __lastPathElement(path: str) -> str:
        return path.split("/")[-1]

    @staticmethod
    def betweenDatetimes(start: datetime.datetime, end: datetime.datetime) -> list[Value]:
        list = []
        for yPath in glob.glob("dati/2*"):
            year = int(DataArchive.__lastPathElement(yPath))
            for mPath in glob.glob(yPath + "/*"):
                month = int(DataArchive.__lastPathElement(mPath))
                for dPath in glob.glob(mPath + "/*"):
                    day = int(DataArchive.__lastPathElement(dPath))
                    pivot = datetime.datetime.strptime(
                        str(year).zfill(4) + "-" + str(month).zfill(2) + "-" + str(day).zfill(2), "%Y-%m-%d")
                    if start > pivot or pivot > end:
                        continue
                    for elementPath in glob.glob(dPath + "/*.csv"):
                        lep = DataArchive.__lastPathElement(elementPath)
                        type = DataTypeArchive.Symbols(DataTypeArchive.fromFileName(lep).symbol)
                        with open(elementPath, "r") as f:
                            for line in f.readlines():
                                l = line.split(",")
                                if len(l) < 2:
                                    continue
                                dateT = datetime.datetime.strptime(l[0], '%Y-%m-%d %H:%M:%S')
                                if start > dateT or end < dateT:  # It should not be necessary, but I guess
                                    continue
                                list.append(Value(float(l[1]), type, dateT))
        return list

    @staticmethod
    def day() -> list[Value]:
        start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = datetime.datetime.now()
        return DataArchive.betweenDatetimes(start, end)

    @staticmethod
    def week() -> list[Value]:
        now = datetime.datetime.now()
        monday = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return DataArchive.betweenDatetimes(monday, now)

    @staticmethod
    def month() -> list[Value]:
        start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, day=1)
        end = datetime.datetime.now()
        return DataArchive.betweenDatetimes(start, end)

    @staticmethod
    def latestDatetime() -> str:
         mY = int(datetime.datetime.now().strftime("%Y"))
         mM = 12
         mD = 31
         tdate = ""
         for i in range(mY):
             yPath = "dati/"+str(mY-i)
             if os.path.isdir(yPath):
                 for j in range(mM):
                     mPath = yPath + "/" + str(mM-j).zfill(2)
                     if os.path.isdir(mPath):
                         for k in range(mD):
                             dPath = mPath + "/" + str(mD-k).zfill(2)
                             if os.path.isdir(dPath):
                                 tfile = open(dPath+"/temperature.csv","r")
                                 lines = tfile.readlines()
                                 for line in lines:
                                      r = line.split(",")
                                      if len(r)<2:
                                          continue
                                      tdate = r[0]
                                 if len(tdate) == 0:
                                     return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                 else:
                                     return datetime.datetime.strptime(tdate,"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")

class Stats:
    def __init__(self, dataList: list):
        tempMap = {}
        resultMap = {}
        for el in dataList:

            # (el.instant)
            if el.symbol not in tempMap.keys():
                tempMap[el.symbol] = {"list": [], "iList": []}
            if el.symbol not in resultMap.keys():
                resultMap[el.symbol] = {"max": Value(-10E6), "min": Value(10E6), "itemCount": 0}

            if el.value > resultMap[el.symbol]["max"].value:
                resultMap[el.symbol]["max"] = el
            elif el.value < resultMap[el.symbol]["min"].value:
                resultMap[el.symbol]["min"] = el

            tempMap[el.symbol]["list"].append(el.value)
            tempMap[el.symbol]["iList"].append(int(el.value))
            resultMap[el.symbol]["itemCount"] += 1

        for symbol in resultMap.keys():
            resultMap[symbol]["stdev"] = statistics.stdev(tempMap[symbol]["list"])
            resultMap[symbol]["mean"] = statistics.mean(tempMap[symbol]["list"])
            resultMap[symbol]["mode"] = float(statistics.mean(tempMap[symbol]["iList"]))

        self.results = resultMap


class TweetGenerator:

    @staticmethod
    def current() -> list[str]:  # git log -1 --format=%ct  as data variable
        ldt = DataArchive.latestDatetime()
        c = DataArchive.current()
        return ["Dati Meteorologici:\nUltimo aggiornamento: " + ldt + "\n--------------\nTemperatura: " + (
            "{:.2f}".format(c["T"])) + " °C\n" + "Umidità: " + (
                    "{:.2f}".format(c["H"])) + " %\n" + "Pressione: " + (
                    "{:.2f}".format(c["P"])) + " hPa\n" + "PM10: " + (
                    "{:.2f}".format(c["PM10"])) + " µg/m³\n" + "PM2,5: " + (
                    "{:.2f}".format(c["PM25"])) + " µg/m³\n" + "Fumo e vapori infiammabili: " + (
                    "{:.2f}".format(c["S"])) + " µg/m³"]

    @staticmethod
    def report() -> list[str]:
        return [DataArchive.report()]

    @staticmethod
    def week() -> list[str]:
        i = 0
        list = []
        s = Stats(DataArchive.week()).results
        l = len(s.keys())
        for symbol in s.keys():
            dta = DataTypeArchive.fromSymbol(symbol.value)
            ssm = s[symbol]
            list.append(
                "(" + str(i + 1) + "/" + str(
                    l) + ") Dati di questa settimana\n---" + dta.italianName + "---\nMedia: " + (
                    "{:.2f}".format(ssm["mean"])) + " " + dta.unit + "\nModa: " + (
                    "{:.2f}".format(ssm["mode"])) + " " + dta.unit + "\nMassimo: " + (
                    "{:.2f}".format(ssm["max"].value)) + " " + dta.unit + " (" + ssm["max"].instant.strftime(
                    "%d/%m/%Y %H:%M:%S") + ") " + "\nMinimo: " + (
                    "{:.2f}".format(ssm["min"].value)) + " " + dta.unit + " (" + ssm["min"].instant.strftime(
                    "%d/%m/%Y %H:%M:%S") + ") " + "\nDeviazione Standard: " + (
                    "{:.2f}".format(ssm["stdev"])) + " " + dta.unit + "\nModa: " + (
                    "{:.2f}".format(ssm["mean"])) + " " + dta.unit + "\nNumero di rilevazioni: " + (
                    "{:.2f}".format(ssm["itemCount"])))
            i += 1
        return list

    @staticmethod
    def month() -> list[str]:
        i = 0
        list = []
        s = Stats(DataArchive.month()).results
        l = len(s.keys())
        for symbol in s.keys():
            dta = DataTypeArchive.fromSymbol(symbol.value)
            ssm = s[symbol]
            list.append(
                "(" + str(i + 1) + "/" + str(l) + ") Dati di questo mese\n---" + dta.italianName + "---\nMedia: " + (
                    "{:.2f}".format(ssm["mean"])) + " " + dta.unit + "\nModa: " + (
                    "{:.2f}".format(ssm["mode"])) + " " + dta.unit + "\nMassimo: " + (
                    "{:.2f}".format(ssm["max"].value)) + " " + dta.unit + " (" + ssm["max"].instant.strftime(
                    "%d/%m/%Y %H:%M:%S") + ") " + "\nMinimo: " + (
                    "{:.2f}".format(ssm["min"].value)) + " " + dta.unit + " (" + ssm["min"].instant.strftime(
                    "%d/%m/%Y %H:%M:%S") + ") " + "\nDeviazione Standard: " + (
                    "{:.2f}".format(ssm["stdev"])) + " " + dta.unit + "\nModa: " + (
                    "{:.2f}".format(ssm["mean"])) + " " + dta.unit + "\nNumero di rilevazioni: " + (
                    "{:.2f}".format(ssm["itemCount"])))
            i += 1
        return list

    @staticmethod
    def day() -> list[str]:
        i = 0
        list = []
        s = Stats(DataArchive.day()).results
        l = len(s.keys())
        for symbol in s.keys():
            dta = DataTypeArchive.fromSymbol(symbol.value)
            ssm = s[symbol]
            list.append(
                "(" + str(i + 1) + "/" + str(l) + ") Dati di oggi\n---" + dta.italianName + "---\nMedia: " + (
                    "{:.2f}".format(ssm["mean"])) + " " + dta.unit + "\nModa: " + (
                    "{:.2f}".format(ssm["mode"])) + " " + dta.unit + "\nMassimo: " + (
                    "{:.2f}".format(ssm["max"].value)) + " " + dta.unit + " (" + ssm["max"].instant.strftime(
                    "%d/%m/%Y %H:%M:%S") + ") " + "\nMinimo: " + (
                    "{:.2f}".format(ssm["min"].value)) + " " + dta.unit + " (" + ssm["min"].instant.strftime(
                    "%d/%m/%Y %H:%M:%S") + ") " + dta.unit + "\nDeviazione Standard: " + (
                    "{:.2f}".format(ssm["stdev"])) + " " + dta.unit + "\nModa: " + (
                    "{:.2f}".format(ssm["mean"])) + " " + dta.unit + "\nNumero di rilevazioni: " + (
                    "{:.2f}".format(ssm["itemCount"])))
            i += 1
        return list


def lsave(fname, text) -> None:
    f = open(fname, "w")
    f.write(text),
    f.close()


class Tweet:

    def __init__(self, keyList):
        self.client = tweepy.Client(
            consumer_key=keyList["TWITTER_CONSUMER_API_KEY"],
            consumer_secret=keyList["TWITTER_CONSUMER_API_SECRET"],
            access_token=keyList["TWITTER_ACCESS_TOKEN"],
            access_token_secret=keyList["TWITTER_ACCESS_TOKEN_SECRET"]
        )

    def __truncate(self, tweetText: str) -> str:
        return tweetText[:280]

    def report(self) -> None:
        f = ""
        tweet = TweetGenerator.report()[0]
        print(tweet)
        f += tweet + "\n"
        self.client.create_tweet(text=self.__truncate(tweet))
        lsave("reports/hardware.txt", f)

    def week(self) -> None:
        f = ""
        for tweet in TweetGenerator.week():
            print(tweet)
            f += tweet + "\n"
            self.client.create_tweet(text=self.__truncate(tweet))
        lsave("reports/week.txt", f)

    def month(self) -> None:
        f = ""
        for tweet in TweetGenerator.month():
            print(tweet)
            f += tweet + "\n"
            self.client.create_tweet(text=self.__truncate(tweet))
        lsave("reports/month.txt", f)

    def day(self) -> None:
        f = ""
        for tweet in TweetGenerator.day():
            print(tweet)
            f += tweet + "\n"
            self.client.create_tweet(text=self.__truncate(tweet))
        lsave("reports/day.txt", f)

    def current(self) -> None:
        f = ""
        for tweet in TweetGenerator.current():
            print(tweet)
            f += tweet + "\n"
            self.client.create_tweet(text=self.__truncate(tweet))
        lsave("reports/current.txt", f)
