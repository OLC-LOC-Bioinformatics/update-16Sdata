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


class UpdateDatabase(object):
    def main(self):
        """Main Program, updates the database"""

        # Parse the config file and create if necessary
        self.parse_config()
        self.set_up_logging()

        # Checks the hash against the NCBI database and downloads new database if necessary
        self.check_download()

        # Get the most recent database
        most_recent = self.get_most_recent()

        # Extracts the tar from the most recent database if it has a tar file and it's not already extracted
        self.extract_archive(most_recent)

        # Converts the extracted archive to fasta
        self.convert_fasta(os.path.join(self.database_dir, most_recent, self.database_name.replace("tar.gz", "fasta")), most_recent)
        
        logging.info(self.C_GREEN + "Completed." + self.C_END)

    @staticmethod
    def more_recent(date, than):
        """This function checks if a date in the format Y-M-D is bigger than another date"""
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

    def download_database(self, data_dir):
        """This function downloads a 16S Database from NCBI and stores it in the correct folder"""
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
                                   os.path.join(folder, self.database_name))
        logging.info("Successfully retrieved file, stored in " + os.path.join(folder, self.database_name))

        # Compares the hashes
        logging.info("Checking that md5 hash matches one on server (in case of corruption)")
        if self.check_hash(folder):
            logging.info(self.C_GREEN + "File not corrupted." + self.C_END)
        else:
            self.tries += 1
            logging.warning("Hash doesn't match downloaded file, corrupted? Redownloading...")
            warnings.warn("Hash doesn't match downloaded file, corrupted? Redownloading...")
            # Since the database is corrupted, redownload
            if self.tries > 4:
                logging.error("Can't download database! Hash won't match.")
                warnings.warn("Can't download database! Hash won't match.")
                exit()
            self.download_database(data_dir)

    def get_most_recent(self):
        """Find the most recent downloaded database"""
        ret = "0-0-0"
        if not os.path.exists(self.database_dir):
            os.mkdir(self.database_dir)
        for file in os.listdir(self.database_dir):
            if os.path.isfile(os.path.join(self.database_dir, file, self.database_name)):
                if self.more_recent(file, ret):
                    ret = file
            else:
                logging.warning("Ignoring folder " + os.path.join(self.database_dir,file,"")
                                + " when finding most recent local database because it has no " + self.database_name)
        return ret

    def parse_config(self):
        """This function will parse the config file located in the same directory as the program"""
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
                if self.database_dir is None:
                    self.database_dir = config['Directories']['DatabaseDirectory']
                else:
                    config['Directories']['DatabaseDirectory'] = self.database_dir
                if self.log_directory is None:
                    self.log_directory = config['Directories']['LogDirectory']
                else:
                    config['Directories']['LogDirectory'] = self.log_directory
                config.write(f)
            except (configparser.Error, KeyError):
                warnings.warn("Invalid config file!")
                if self.database_dir is not None and self.log_directory is not None:
                    warnings.warn("Using arguments given and repairing config file...")
                    config = configparser.ConfigParser()
                    create = True
                else:
                    warnings.warn("Fix the config file or try again with arguments for directory and log directory")
                    exit()

        if create:  # New file
            if self.database_dir is None:
                try:
                    config['Directories']['DatabaseDirectory'] = self.default_dir
                except KeyError:
                    config['Directories'] = {}
                    config['Directories']['DatabaseDirectory'] = self.default_dir
                self.database_dir = self.default_dir
            else:
                try:
                    config['Directories']['DatabaseDirectory'] = self.database_dir
                except KeyError:
                    config['Directories'] = {}
                    config['Directories']['DatabaseDirectory'] = self.database_dir
            if self.log_directory is None:
                try:
                    config['Directories']['LogDirectory'] = self.default_log_dir
                except KeyError:
                    config['Directories'] = {}
                    config['Directories']['LogDirectory'] = self.default_dir
                self.log_directory = self.default_log_dir
            else:
                try:
                    config['Directories']['LogDirectory'] = self.log_directory
                except KeyError:
                    config['Directories'] = {}
                    config['Directories']['LogDirectory'] = self.log_directory
            config.write(f)

    def set_up_logging(self):
        """Set up logging"""
        try:
            if not os.path.exists(self.log_directory):
                os.makedirs(self.log_directory)
        except (os.error, TypeError):
            print("Invalid directory " + str(self.log_directory))
            exit()

        self.log_directory = os.path.join(self.log_directory, time.strftime("%Y-%m-%d_%H:%M:%S") + ".txt")
        logging.basicConfig(filename=self.log_directory, level=logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    def check_download(self):
        """Checks hash against current NCBI database and downloads if necessary"""

        # If no database found locally then print message and download from NCBI
        logging.info("Checking for local database...")
        most_recent = self.get_most_recent()

        if most_recent == "0-0-0":
            logging.info("Can't find a local database.")
            self.download_database(self.database_dir)
        else:
            logging.info("Found local database at " + os.path.join(self.database_dir, most_recent, ""))
            if self.check_hash(most_recent):
                logging.info(self.C_GREEN + "Up to date (" +
                             os.path.join(self.database_dir, most_recent, "") + ")." + self.C_END)
            else:
                # Since the database isn't up to date, must download new version
                self.download_database(self.database_dir)

    def extract_archive(self, to_extract):
        """This function will extract the tar file in the directory specified"""

        directory_list = os.listdir(os.path.join(self.database_dir, to_extract, ""))
        # If the most up to date database folder doesn't already have an extracted archive
        if len(directory_list) == 1 and directory_list[0] == self.database_name:
            # try to extract
            try:
                logging.info("Extracting " + os.path.join(self.database_dir, to_extract, self.database_name) + " to "
                             + os.path.join(self.database_dir, to_extract, ""))

                tar = tarfile.open(os.path.join(self.database_dir, to_extract, self.database_name), 'r:gz')
                tar.extractall(path=os.path.join(self.database_dir, to_extract, ""))

                logging.info("Extracted " + os.path.join(self.database_dir, to_extract, self.database_name) + " to "
                             + os.path.join(self.database_dir, to_extract, ""))
            except FileNotFoundError:
                logging.error("Can't find file " + os.path.join(self.database_dir, to_extract, self.database_name))
                warnings.warn("Can't find file " + os.path.join(self.database_dir, to_extract, self.database_name))
                exit()

    def convert_fasta(self, fasta_dir, recent_dir):
        """Converts the bash database in the specified directory to a fasta"""
        # If there is no fasta file already in the folder
        if not self.database_name.replace("tar.gz", "fasta") in os.listdir(
                os.path.join(self.database_dir, recent_dir, "")):
            # Convert the database back to fasta
            logging.info("No fasta found in most recent database " + os.path.join(self.database_dir, recent_dir, ""))
            logging.info("Converting blast database to fasta in " + os.path.join(self.database_dir, recent_dir, ""))

            # eg. blastdbcmd -db ~/16S/2017-04-11/16SMicrobial -out ~/16S/2017-04-11/16SMicrobial.fasta -outfmt %f -entry 'all'
            blast_args = ["blastdbcmd", "-db",
                          os.path.join(self.database_dir, recent_dir, self.database_name.replace(".tar.gz", "")),
                          "-out",
                          fasta_dir,
                          "-outfmt", "%f", "-entry", "all"]

            logging.info("Running blastdbcmd with arguments " + str(blast_args))

            convert_fasta = subprocess.Popen(blast_args)
            convert_fasta.wait()

            # If the fasta file was created and fasta has text in it
            if self.database_name.replace("tar.gz", "fasta") in os.listdir(
                    os.path.join(self.database_dir, recent_dir, "")) \
                    and os.stat(fasta_dir).st_size != 0:
                logging.info("Successfully created " + fasta_dir)
            else:
                logging.error("Failed to create " + fasta_dir)
                warnings.warn("Failed to create " + fasta_dir)
                exit()

            # Parse the newly created fasta for issues with multiple headers detailed in this post
            # http://bioinformaticstips.com/2015/10/05/how-to-get-a-fasta-file-of-the-16s-rrna-database-from-ncbi/
            print("Repairing duplicate headers on the same line for file " + fasta_dir + " ...")
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

    def check_hash(self, check_dir):
        """Checks the hash of the tar file in specified directory and returns if it matches the NCBI hash"""
        logging.info("Downloading current md5 hash from https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5 ...")
        webhash = requests.get('https://ftp.ncbi.nih.gov/blast/db/16SMicrobial.tar.gz.md5')
        logging.info("Downloaded current md5 hash...")
        logging.info("Getting local md5 hash...")
        # Gets the local hash and compares it to the one on the server
        logging.info("Getting local hash from folder " + os.path.join(self.database_dir, check_dir, "") + " ...")

        # Gets local hash
        current_hash = subprocess.Popen(["md5sum", os.path.join(self.database_dir, check_dir, self.database_name)],
                                        stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        a = ""
        for line in iter(current_hash.stdout.readline, b''):
            a = line.decode("utf-8")
        logging.info("Got local md5 hash...")
        logging.info("Comparing local and current hashes...")

        # Compares the hashes
        if a[:a.index(" ")] == webhash.text[:webhash.text.index(" ")]:
            return True
        else:
            return False
            
    def __init__(self):
        self.tries = 0

        # Constants
        self.default_dir = os.path.join(os.getenv("HOME"), '16S', '')
        self.default_log_dir = os.path.join(os.getenv("HOME"), '16SLogs', '')
        self.database_name = "16SMicrobial.tar.gz"
        self.C_RED = '\033[91m'
        self.C_GREEN = '\033[92m'
        self.C_END = '\033[0m'

        # Arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--directory", type=str, help="set the directory to store the database (default: ~/16S/")
        parser.add_argument("-l", "--log_directory", type=str, help="set the directory to store the logs (default: ~/16SLogs/")
        self.args = parser.parse_args()
        self.database_dir = self.args.directory
        self.log_directory = self.args.log_directory

        self.main()
        
# Program
if __name__ == '__main__':
    UpdateDatabase()
