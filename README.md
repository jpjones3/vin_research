# VIN Research
The python code contained here is the basis for some bots that I created in order to gather every VIN for a year/make/model of a car. The specific case I will discuss here is for the 2022 Ford Mustang.

# Background
As with most VINs, Ford VINs contain a sequential number in the last 6 digits. The first 11 characters contain a ‘model descriptor’. This model descriptor covers where it was manufactured as well as details on body style, engine and safety features. In any given model year, there will only be one car manufactured with a given sequential number and there are only so many other variations of the other values. So, for example, for sequential number 109059 there are four possible VINs depending on whether that car is a Mustang GT or Ecoboost and also whether it is a coupe or convertible. I happen to know that 109059 is an Ecoboost Coupe. The other three do not represent real cars –

    1FA6P8TH5P5109059 – 2022 Ecoboost Coupe (real)
    1FA6P8CF7P5109059 – 2022 GT Coupe (not real)
    1FATP8FF9P5109059 – 2022 GT Convertible (not real)
    1FATP8UH3P5109059 – 2022 Ecoboost Convertible (not real)

The goal was to figure out which of these was the real VIN for sequence number 109059 and to repeat this for every sequqnce number from 100000 through approximately 156000 (or whatever would turb out to be the highest VIN assigned during the 2022 model year).

# Solution
For any VIN, Carfax can be checked to see how may records exist for the VIN. If the VIN does not represent a real car, then the number of Carfax records is 0. If there is a car, then the number of records is greater than 0.

It is not possible for just anyone to call the Carfax API to find the number of records. This is reserved for Carfax service subscribers. Not being a Carfax ervice subscriber, I found an alteratnive way to check the number of Carfax records and that was through a webservice called Carfax Checks which is available through the [Rapid API Marketplace](https://rapidapi.com/carsimulcast/api/carfax-checks). This is one API of several available on Rapid API Marketplace and similar sites.

# Features
* When the python script is called it can be passed an instance number so that multiple instances can be run simuultaneously
* The script is driven from and the results are stored in a database. The database is seeded before the first run with the sequence numbers that are to be considered
* The script can be passed a sequence number from which to start processing. If no number is passed then a sequence number is picked randomly
* The script will pause between calls such as to not overwhelm the api being called

# Database
This is the syntax to create the table referenced by the python script. It is for MariaDB

    CREATE TABLE `vin_2021` (
      `ID` int(11) NOT NULL AUTO_INCREMENT,
      `sequence` varchar(45) DEFAULT NULL,
      `vin` varchar(45) DEFAULT NULL,
      `carfax_records` int(11) DEFAULT NULL,
      `autocheck_records` int(11) DEFAULT NULL,
      `name` varchar(255) DEFAULT NULL,
      `bot` varchar(45) DEFAULT NULL,
      `checked_on` datetime DEFAULT NULL,
      `notes` varchar(255) DEFAULT NULL,
      `type` varchar(45) DEFAULT NULL,
      PRIMARY KEY (`ID`)
    ) ENGINE=InnoDB AUTO_INCREMENT=346770 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

