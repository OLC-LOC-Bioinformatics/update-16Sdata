# Update Bacterial 16S Data
Written by Devon Mack 2017-03-27 

When run, this program will automatically update a local bacterial 16S database. The local copy will be compared to the latest version on the NCBI database located at https://ftp.ncbi.nih.gov/. If it is out of date, a new version will be downloaded automatically.

## Prerequisites

- [Python 3](https://www.python.org/downloads/)
- [Blast](https://blast.ncbi.nlm.nih.gov/Blast.cgi)

## Installation
Clone the github repository:
https://github.com/devonpmack/update-16Sdata.git

## Usage
Each time you run the script it will check your database directory and update it if necessary. A log will be outputted to your chosen log directory. A cron job can also be set up to run it automatically on a schedule.

Run the script with

```console
python3 updateDatabase.py
```

It will automatically create the default config file which stores the database and logs in your home directory. To change these directories, set the path using the paramaters.

```console
python3 updateDatabase.py -d PATH_TO_DATABASE -l PATH_TO_LOGS
```

Change `PATH_TO_DATABASE` and `PATH_TO_LOGS` to a folder where you would like to store your database/logs.

___

### Setting the program up as a cron job

Make the script executable with:
```console
chmod +x updateDatabase.py`
```

Edit the cron config file through your terminal:

```console
crontab -e`                                                                  
```

Add this line to the bottom of the file (must have return character after):                                                 

```ceylon
0 7 * * 1 PATH_TO_SCRIPT
```

This setup will make it run every Monday at 7:00 AM.

Parameter Number | Parameter (`*` means it doesn't matter when)
--- | ---
1 | Minute (0 - 59)
2 | Hour (0 - 23)
3 | Day of month (1 - 31) 
4 | Month (1 - 12)
5 | Day of week (0 - 7) (where both 0 and 7 mean Sun, 1 = Mon, 2 = Tue, etc)
6 | Command line to be executed (eg. /home/update-16Sdata/updateDatabase.py) 


