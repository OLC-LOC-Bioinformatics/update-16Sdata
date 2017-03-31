#!/usr/bin/env python3
import requests, subprocess, urllib.request, time, os, logging, sys, argparse, configparser, warnings

CRED = '\033[91m'
CGREEN = '\033[92m'
CEND = '\033[0m'

#Constants
defaultDir = os.path.join(os.getenv("HOME"), '16S','')
defaultLogdir = os.path.join(os.getenv("HOME"),'16SLogs','')

parser = argparse.ArgumentParser()
parser.add_argument("-d","--directory", type=str,help="set the directory to store the database (default: ~/16S/")
parser.add_argument("-l","--logdirectory", type=str,help="set the directory to store the logs (default: ~/16SLogs/")
args = parser.parse_args()

dir = args.directory
logdir = args.logdirectory
try:
    f = open("config.ini", "r")
    create = False
    f.close()
    f = open("config.ini", "r+")
except FileNotFoundError:
    warnings.warn("No config file found, creating \"config.ini\"...")
    try:
        f = open("config.ini", "w")
        create = True
    except:
        warnings.warn("Couldn't create config.ini")
        exit()

#Load config
config = configparser.ConfigParser()

if create == False: #Config file already exists
    try:
        config.read("config.ini")
        if dir is None:
            dir = config['Directories']['DatabaseDirectory']
        else:
            config['Directories']['DatabaseDirectory'] = dir
        if logdir is None:
            logdir = config['Directories']['LogDirectory']
        else:
            config['Directories']['LogDirectory'] = logdir
        config.write(f)
    except:
        warnings.warn("Invalid config file!")
        if not dir is None and not logdir is None:
            warnings.warn("Using arguments given and repairing config file...")
            config = configparser.ConfigParser()
            create = True
        else:
            warnings.warn("Fix the config file or try again with arguments for directory and log directory")
            exit()
if create == True:  # New file
    if dir is None:
        try:
            config['Directories']['DatabaseDirectory'] = defaultDir
        except:
            config['Directories'] = {}
            config['Directories']['DatabaseDirectory'] = defaultDir
        dir = defaultDir
    else:
        try:
            config['Directories']['DatabaseDirectory'] = dir
        except:
            config['Directories'] = {}
            config['Directories']['DatabaseDirectory'] = dir
    if logdir is None:
        try:
            config['Directories']['LogDirectory'] = defaultLogdir
        except:
            config['Directories'] = {}
            config['Directories']['LogDirectory'] = defaultDir
        logdir = defaultLogdir
    else:
        try:
            config['Directories']['LogDirectory'] = logdir
        except:
            config['Directories'] = {}
            config['Directories']['LogDirectory'] = logdir
    config.write(f)


#Set up logging
try:
    if not os.path.exists(logdir):
        os.makedirs(logdir)
except:
    print("Invalid directory " + logdir)
    exit()

logdir = os.path.join(logdir, time.strftime("%Y-%m-%d_%H:%M:%S") + ".txt")
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
    folder = os.path.join(dir,time.strftime("%Y-%m-%d"))
    i = 0
    while os.path.exists(folder):
        i += 1
        folder = os.path.join(dir, time.strftime("%Y-%m-%d") + ":" + str(i))
    else:
        os.makedirs(folder)
    urllib.request.urlretrieve("https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz", os.path.join(folder,"16SMicrobial.tar.gz"))
    logging.info("Successfully retrieved file, stored in " + os.path.join(folder, "16SMicrobial.tar.gz"))

logging.info("Checking if NCBI 16S database matches local database...")
logging.info("Downloading current md5 hash from https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5 ...")
r = requests.get('https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5')
logging.info("Downloaded current md5 hash...")
logging.info("Getting local md5 hash...")

#Find the most recent downloaded database
mostRecent = "0-0-0"
if not os.path.exists(dir):
    os.mkdir(dir)
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
    currentHash = subprocess.Popen(["md5sum", os.path.join(dir, mostRecent, "16SMicrobial.tar.gz")], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    for line in iter(currentHash.stdout.readline, b''):
        a = line.decode("utf-8")
    logging.info("Got local md5 hash...")
    logging.info("Comparing local and current hashes...")

    #Compares the hashes
    if a[:a.index(" ")] == r.text[:r.text.index(" ")]:
        logging.info(CGREEN + "Up to date." + CEND)
    else:
        #Since the database isn't up to date, must download new version
        downloadDatabase(dir)

logging.info(CGREEN + "Completed." + CEND)