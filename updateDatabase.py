#!/usr/bin/env python3
import requests
import subprocess
import urllib.request
import time
import os
import logging
import sys
import argparse
import configparser
import warnings
import tarfile
from Bio import SeqIO

C_RED = '\033[91m'
C_GREEN = '\033[92m'
C_END = '\033[0m'

# Constants
defaultDir = os.path.join(os.getenv("HOME"), '16S', '')
defaultLogDir = os.path.join(os.getenv("HOME"), '16SLogs', '')
database_name = "16SMicrobial.tar.gz"

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--directory", type=str, help="set the directory to store the database (default: ~/16S/")
parser.add_argument("-l", "--log_directory", type=str, help="set the directory to store the logs (default: ~/16SLogs/")
args = parser.parse_args()

database_dir = args.directory
log_directory = args.log_directory

try:
    # Attempt to open the config file
    f = open("config.ini", "r")
    # Since it succeeded in reading the file, that means it exists
    create = False
    f.close()
    # Since the file exists we will read and write to it
    f = open("config.ini", "r+")
except FileNotFoundError:
    warnings.warn("No config file found, creating \"config.ini\"...")
    # Create the file
    f = open("config.ini", "w")
    create = True

# Instantiate config
config = configparser.ConfigParser()

if not create:  # Config file already exists
    try:
        config.read("config.ini")
        if database_dir is None:
            database_dir = config['Directories']['DatabaseDirectory']
        else:
            config['Directories']['DatabaseDirectory'] = database_dir
        if log_directory is None:
            log_directory = config['Directories']['LogDirectory']
        else:
            config['Directories']['LogDirectory'] = log_directory
        config.write(f)
    except (configparser.Error, KeyError):
        warnings.warn("Invalid config file!")
        if database_dir is not None and log_directory is not None:
            warnings.warn("Using arguments given and repairing config file...")
            config = configparser.ConfigParser()
            create = True
        else:
            warnings.warn("Fix the config file or try again with arguments for directory and log directory")
            exit()

if create:  # New file
    if database_dir is None:
        try:
            config['Directories']['DatabaseDirectory'] = defaultDir
        except KeyError:
            config['Directories'] = {}
            config['Directories']['DatabaseDirectory'] = defaultDir
        database_dir = defaultDir
    else:
        try:
            config['Directories']['DatabaseDirectory'] = database_dir
        except KeyError:
            config['Directories'] = {}
            config['Directories']['DatabaseDirectory'] = database_dir
    if log_directory is None:
        try:
            config['Directories']['LogDirectory'] = defaultLogDir
        except KeyError:
            config['Directories'] = {}
            config['Directories']['LogDirectory'] = defaultDir
        log_directory = defaultLogDir
    else:
        try:
            config['Directories']['LogDirectory'] = log_directory
        except KeyError:
            config['Directories'] = {}
            config['Directories']['LogDirectory'] = log_directory
    config.write(f)

# Set up logging
try:
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
except (os.error, TypeError):
    print("Invalid directory " + str(log_directory))
    exit()

log_directory = os.path.join(log_directory, time.strftime("%Y-%m-%d_%H:%M:%S") + ".txt")
logging.basicConfig(filename=log_directory, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


# This function checks if a date in the format Y-M-D is bigger than another date
def more_recent(date, than):
    tie_than = 0
    tie_date = 0

    if ":" in than:
        tie_than = int(than[than.index(":") + 1:])
    if ":" in date:
        tie_date = int(date[date.index(":") + 1:])

    than = than.split("-")
    date = date.split("-")

    for i in range(0, 3):
        if date[i] != than[i]:
            return date[i] > than[i]

    return tie_date >= tie_than


# This function downloads a 16S Database from NCBI and stores it in the correct folder
tries = 0


def download_database(data_dir):
    global tries
    logging.info("Not up to date, downloading new database from "
                 "https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz ...")
    folder = os.path.join(data_dir, time.strftime("%Y-%m-%d"))
    i = 0
    while os.path.exists(folder):
        i += 1
        folder = os.path.join(data_dir, time.strftime("%Y-%m-%d") + ":" + str(i))
    else:
        os.makedirs(folder)
    urllib.request.urlretrieve("https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz",
                               os.path.join(folder, database_name))
    logging.info("Successfully retrieved file, stored in " + os.path.join(folder, database_name))
    logging.info("Checking that md5 hash matches one on server (in case of corruption)")
    logging.info("Getting hash of " + os.path.join(folder, database_name) + "...")
    check_hash = subprocess.Popen(["md5sum", os.path.join(folder, database_name)],
                                   stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    hash = ""
    for line in iter(check_hash.stdout.readline, b''):
        hash = line.decode("utf-8")
    logging.info("Got local md5 hash...")
    logging.info("Comparing local and current hashes...")

    # Compares the hashes
    if hash[:hash.index(" ")] == r.text[:r.text.index(" ")]:
        logging.info(C_GREEN + "File not corrupted." + C_END)
    else:
        tries += 1
        logging.warning("Hash doesn't match downloaded file, corrupted? Redownloading...")
        warnings.warn("Hash doesn't match downloaded file, corrupted? Redownloading...")
        # Since the database is corrupted, redownload
        if tries > 4:
            logging.error("Can't download database! Hash won't match.")
            warnings.warn("Can't download database! Hash won't match.")
            exit()
        download_database(data_dir)

logging.info("Checking if NCBI 16S database matches local database...")
logging.info("Downloading current md5 hash from https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5 ...")
r = requests.get('https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5')
logging.info("Downloaded current md5 hash...")
logging.info("Getting local md5 hash...")


# Find the most recent downloaded database
def get_most_recent():
    ret = "0-0-0"
    if not os.path.exists(database_dir):
        os.mkdir(database_dir)
    for file in os.listdir(database_dir):
        if os.path.isfile(os.path.join(database_dir, file, database_name)):
            if more_recent(file, ret):
                ret = file
        else:
            logging.warning("Ignoring folder " + os.path.join(database_dir,file,"") + " when finding most recent local database because it has no "
                            + database_name)
    return ret

mostRecent = get_most_recent()

# If no database found locally then print message and download from NCBI
if mostRecent == "0-0-0":
    logging.info("Can't find a local database.")
    download_database(database_dir)
else:
    # Gets the local hash and compares it to the one on the server
    logging.info("Getting local hash from folder " + os.path.join(database_dir, mostRecent,"") + " ...")

    # Gets local hash
    currentHash = subprocess.Popen(["md5sum", os.path.join(database_dir, mostRecent, database_name)],
                                   stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    a = ""
    for line in iter(currentHash.stdout.readline, b''):
        a = line.decode("utf-8")
    logging.info("Got local md5 hash...")
    logging.info("Comparing local and current hashes...")

    # Compares the hashes
    if a[:a.index(" ")] == r.text[:r.text.index(" ")]:
        logging.info(C_GREEN + "Up to date (" + os.path.join(database_dir,mostRecent,"") + ")." + C_END)
    else:
        # Since the database isn't up to date, must download new version
        download_database(database_dir)

# If the directory only has one file
mostRecent = get_most_recent()
directorylist = os.listdir(os.path.join(database_dir, mostRecent, ""))

# If the most up to date database folder doesn't already have an extracted archive
if len(directorylist) == 1 and directorylist[0] == database_name:
    # try to extract
    try:
        tar = tarfile.open(os.path.join(database_dir, mostRecent, database_name), 'r:gz')
        tar.extractall(path=os.path.join(database_dir, mostRecent, ""))

        logging.info("Extracted " + os.path.join(database_dir, mostRecent, database_name) + " to "
                     + os.path.join(database_dir, mostRecent, ""))
    except FileNotFoundError:
        logging.error("Can't find file " + os.path.join(database_dir, mostRecent, database_name))
        warnings.warn("Can't find file " + os.path.join(database_dir, mostRecent, database_name))
        exit()


fasta_dir = os.path.join(database_dir,mostRecent,database_name.replace(".tar.gz",""))

# If there is no fasta file already in the folder
if not database_name.replace("tar.gz", "fasta") in os.listdir(os.path.join(database_dir, mostRecent, "")):
    # Convert the database back to fasta
    logging.info("No fasta found in most recent database " + os.path.join(database_dir,mostRecent, ""))
    logging.info("Converting blast database to fasta")

    # eg. blastdbcmd -db ~/16S/2017-04-11/16SMicrobial -out ~/16S/2017-04-11/16SMicrobial.fasta -outfmt %f -entry 'all'
    blast_args = ["blastdbcmd", "-db", os.path.join(database_dir,mostRecent,database_name.replace(".tar.gz","")), "-out",
                  fasta_dir,
                                      "-outfmt", "%f", "-entry", "all"]

    logging.info("Running blastdbcmd with arguments " + str(blast_args))

    convert_fasta = subprocess.Popen(blast_args)
    convert_fasta.wait()

    # If the fasta file was created and fasta has text in it
    if database_name.replace("tar.gz","fasta") in os.listdir(os.path.join(database_dir, mostRecent, "")) \
            and os.stat(fasta_dir).st_size != 0:
        logging.info("Successfully created " + fasta_dir)
    else:
        logging.error("Failed to create " + fasta_dir)
        warnings.warn("Failed to create " + fasta_dir)
        exit()

    # Parse the newly created fasta for issues with multiple headers detailed in this post
    # http://bioinformaticstips.com/2015/10/05/how-to-get-a-fasta-file-of-the-16s-rrna-database-from-ncbi/
    print("Repairing duplicate headers on the same line...")
    records = []
    for record in SeqIO.parse(open(fasta_dir, "rU"), "fasta"):
        # if genus in record.description and species in record.description:
        #     print(record.description)
        #     targets.append(record)
        if ">" in record.description:
            names = []
            for broken in record.description.split(">"):
                genus = broken.split("|")[-1].split()[0]
                if genus not in names:
                    names.append(genus)
                    record.description = broken
                    records.append(record)
        else:
            records.append(record)

    SeqIO.write(records, open(fasta_dir, "w"), 'fasta')


logging.info(C_GREEN + "Completed." + C_END)
