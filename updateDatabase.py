#!/usr/bin/env python3
import requests, subprocess, urllib.request, time, os, logging, sys

#Directory to store all files in (eg. /home)
dir = "/home/devon/16S/"

#Directory to store logs
logdir = "/home/devon/16SLogs/"

#Set up logging
if not os.path.exists(logdir):
    os.mkdir(logdir)
logdir += time.strftime("%Y-%m-%d_%H:%M:%S")
logging.basicConfig(filename=logdir, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

#This function checks if a date in the format Y-M-D is bigger than another date
def moreRecent(date,than):
    tieThan = 0
    tieDate = 0

    if ":" in than:
        tieThan = int(than[than.index(":")+1:])
    if ":" in date:
        tieDate = int(date[date.index(":")+1:])

    than = than.split("-")
    date = date.split("-")

    for i in range (0,3):
        if date[i] != than[i]:
            return date[i] > than[i]

    return tieDate >= tieThan

#This function downloads a 16S Database from NCBI and stores it in the correct folder
def downloadDatabase(dir):
    logging.info("Not up to date, downloading new database from https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz ...")
    folder = dir + time.strftime("%Y-%m-%d")
    i = 0
    while os.path.exists(folder):
        i += 1
        folder = dir + time.strftime("%Y-%m-%d") + ":" + str(i)
    else:
        os.makedirs(folder)
    urllib.request.urlretrieve("https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz", folder + "/16SMicrobial.tar.gz")
    logging.info("Successfully retrieved file, stored in " + folder + "/16SMicrobial.tar.gz")

logging.info("Checking if NCBI 16S database matches local database...")
logging.info("Downloading current md5 hash from https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5 ...")
r = requests.get('https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5')
logging.info("Downloaded current md5 hash...")
logging.info("Getting local md5 hash...")

#Find the most recent downloaded database
mostRecent = "0-0-0"
for file in os.listdir(dir):
    if moreRecent(file, mostRecent):
        mostRecent = file

#If no database found locally then print message and download from NCBI
if mostRecent == "0-0-0":
    logging.info("Can't find a local database.")
    downloadDatabase(dir)
else:
    #Gets the local hash and compares it to the one on the server
    logging.info("Getting local hash from folder " + dir + mostRecent + " ...")

    #Gets local hash
    currentHash = subprocess.Popen(["md5sum", dir + mostRecent + "/16SMicrobial.tar.gz"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    for line in iter(currentHash.stdout.readline, b''):
        a = line.decode("utf-8")
    logging.info("Got local md5 hash...")
    logging.info("Comparing local and current hashes...")

    #Compares the hashes
    if a[:a.index(" ")] == r.text[:r.text.index(" ")]:
        logging.info("Up to date.")
    else:
        #Since the database isn't up to date, must download new version
        downloadDatabase(dir)

logging.info("Completed.")