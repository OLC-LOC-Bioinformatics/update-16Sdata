# Update Bacterial 16S Data
Written by Devon Mack 2017-03-27 

When run, this program will automatically update a local bacterial 16S database. The local copy will be compared to the latest version on the NCBI database located at https://ftp.ncbi.nih.gov/. If it is out of date, a new version will be downloaded automatically.

## Installation
Clone the github repository. Edit the script and change line 4 to your preferred directory to store the database.

`dir = "DIRECTORY"`

Change line 7 to your preferred directory to store the logs:

`logdir = "LOGDIRECTORY"`

## Usage
Each time you run the script it will check your database directory and update it if necessary. A log will be outputted to your chosen log directory. A cron job can also be set up to run it automatically on a schedule.

### Setting the program up as a cron job

Edit the cron config file through your terminal:                                                               
`$ crontab -e`                                                                  
Add this line to the bottom of the file (must have return character after):                                                 
`0 7 * * 1 python3 <PATH TO "cleanDocker.sh">`
##### Parameters (* = any):
1. Minute (0 - 59)
2. Hour (0 - 23)
3. Day of month (1 - 31) 
4. Month (1 - 12)
5. Day of week (0 - 7) (where both 0 and 7 mean Sun, 1 = Mon, 2 = Tue, etc)
6. Command line to be executed (eg. python3 /home/update-16Sdata/updateDatabase.py) 

This setup will make it run every Monday at 7:00 AM.
