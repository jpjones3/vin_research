############################################################################################
# rapidapi_carfax-checks.py
# 
#   VIN searching - this is the main class to call when starting a 'bot' to search for VINs
#       using an API which provides the number of carfax and/or autocheck records when given
#       a VIN
#
# usage - 
#   rapidapi_carfax-checks.py instance target start_sequence
#   where - 
#       instance - the instance of
#       target - the subset of VINS to target. See config.json for the targets for which
#           examples would be '2021' ot '2021mach1'
#       start_sequence - the sequence number at which to start the search
#   example - 
#       rapidapi_carfax-checks.py 1 2021 120000
#
############################################################################################
import requests
import generate_vin
import time
import random
import database
import logging
import sys
import json
import os

MAX_DELAY_SEC_BETWEEN_REQUESTS = 60 #the number of seconds to wait between successive requests so that we don't unnecessarily impact the web service
CARFAX_WEB_SERVICE = "https://carfax-checks.p.rapidapi.com/checkrecords/"
API = "rapidapi_carfax-checks"
LOG_PATH = "logs/"

def check_carfax(vin):

    # Define the URL of the web service
    url = CARFAX_WEB_SERVICE + vin

    # Set headers (optional, but recommended for JSON requests)
    headers = {
        "Accept": "application/json",
        "x-rapidapi-key": "a846f4c19emsh0ea8c5fb7f5c009p1a678bjsn1170fed29ff0",
        "x-rapidapi-host": "carfax-checks.p.rapidapi.com",
        "User-Agent": "MyVINResearchBot/1.0 (+https://yourwebsite.com/botpolicy/)"
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)

        # This is an example response
        #{"vin":"1C6RD6FT1CS310366",
        # "autocheck_records":37,
        # "carfax_records":33,
        # "vehicle":"2012 RAM 1500 EXPRESS",
        # "auction_record":true,
        # "image_count":11,
        # "base_image":"https:\/\/vis.iaai.com\/resizer?imageKeys=28098911~SID~B423~S0~I1~RW2592~H1944~TH0&width=640&height=480",
        # "sticker_report":true,
        # "carfax_available":true,
        # "autocheck_available":true}

        # Check the response
        if response.status_code == 200:
            logging.info("Request successful!")
            logging.info("Response JSON:" + str(response.json()))  # Parse the JSON response
            response_data = response.json()

            carfax_records = -1
            autocheck_records = -1
            name = "not found"
            success = False
            
            if "vin" in response_data and response_data["vin"]:
                carfax_records = response_data['carfax_records']
                autocheck_records = response_data['autocheck_records']
                name =  response_data['vehicle']
                if carfax_records > 0 or autocheck_records > 0:
                    success = True

            return_values = {
                'name': name,
                'carfax_records': carfax_records,
                'autocheck_records': autocheck_records,
                'success': success
            }

            return return_values

        else:
            logging.error(f"Request failed with status code {response.status_code}")
            logging.error("Response content:", response.text)

            return None
        
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")  # Catches 4xx and 5xx errors
        return None
    except requests.exceptions.ConnectionError:
        logging.error("Failed to connect to the server.")
        return None
    except requests.exceptions.Timeout:
        logging.error("Request timed out.")
        return None
    except requests.exceptions.RequestException as err:
        logging.error(f"An error occurred: {err}")  # Catches all other request-related errors
        return None
    
if __name__ == "__main__":

    #get the parameters from the command line; have some defaults just in case
    instance = '1'
    if len(sys.argv) > 1:
        instance = sys.argv[1]

    target = '2021'
    if len(sys.argv) > 2:
        target = sys.argv[2]

    start_sequence = None
    if len(sys.argv) > 3:
        start_sequence = sys.argv[3]

    bot = API + "_" + instance

    #Get the configuration parameters
    with open("config.json", "r") as file:
        CONFIGS = json.load(file)

    # Extract global constants
    GLOBAL_CONFIG = CONFIGS.get("GLOBAL", {})

    # Retrieve selected configuration based on target type and merge with global constants
    selected_config = {**GLOBAL_CONFIG, **CONFIGS[target]}

    # Not take that combined config and aassign constants
    DB_HOST = selected_config["DB_HOST"]  # Global constant
    DB_TABLE = selected_config["DB_TABLE"] # target constants...
    MODEL_TYPE = selected_config["TYPE"]
    DB_DATABASE = selected_config["DB_DATABASE"]
    DB_PORT = selected_config["DB_PORT"]
    DB_USER = selected_config["DB_USER"]
    DB_PASSWORD = selected_config["DB_PASSWORD"]

    # Extract all VIN_PREFIX for this target
    VIN_PREFIXES = {key: value for key, value in selected_config.items() if key.startswith("VIN_PREFIX")}

    # Build the log file path
    log_filename = f"{LOG_PATH}{DB_TABLE}-{bot}.log"

    # Ensure the directory exists
    log_dir = os.path.dirname(log_filename)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=log_filename,
        filemode="a",
    )

    logging.info("STARTING")

    # Database configuration
    database_config = {
        'host': DB_HOST,
        'database': DB_DATABASE,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD
    }
    
    table_name = DB_TABLE

    #put the VIN prefixes into an array. This will allow us to reorder how we process them as we learn more
    prefix = [""] * len(VIN_PREFIXES)
    i = 0
    for key, value in VIN_PREFIXES.items():
            prefix[i] = value
            i = i + 1
    #we will track which prefix in the list was the last hit
    last_i = 0

    #get the row to process from our database
    row = database.fetch_row(database_config, table_name, MODEL_TYPE, start_sequence)

    api_failed = False

    while (row) and not api_failed:

        #get values from the row
        sequence = row.get("sequence")
        id = row.get("ID")

        #update the database for this sequence number to indicate that it is being processed
        database.tag_row(database_config, table_name, id, bot)

        found = False

        logging.debug(f"Last i value was = {last_i}")

        #prioritize the last type we found
        if last_i > 0:
            for j in range(i, 0, -1):
                prefix_temp = prefix[j - 1]
                prefix[j - 1] = prefix[j]
                prefix[j] = prefix_temp

        i = 0

        while True:

            #build te VIN from the prefix and thr seqeunce number
            vin = prefix[i] + str(sequence)
            #since our prefix always has a check digit of '0' we need to make it valid
            corrected_vin = generate_vin.add_check_digit(vin)

            logging.info(f"The VIN '{corrected_vin}' is corrected.")
            
            #call the api
            response_data = check_carfax(corrected_vin)
            
            #wait a defined period
            time.sleep(random.randint(1, MAX_DELAY_SEC_BETWEEN_REQUESTS))

            if response_data is not None:
                name = response_data['name']
                carfax_records = response_data['carfax_records']
                autocheck_records = response_data['autocheck_records']
                success = response_data['success']

                if (success and carfax_records > 0) or i >= len(VIN_PREFIXES) - 1:
                    break

                i = i + 1
            else:
                api_failed = True
                break

        if not api_failed:
            #update the database for this sequence number
            database.update_row(database_config, table_name, id, corrected_vin, carfax_records, autocheck_records, name, bot)

            #keep track of where we were in the list of VINs so we can check this VIN prefix first on the next
            last_i = i

            #get the next row to process
            row = database.fetch_row(database_config, table_name, MODEL_TYPE, start_sequence)
            
        else:
            database.tag_row(database_config, table_name, id, None)
            last_i = 0

    else:
        if api_failed:
            logging.error("API Failed")
        else:
            logging.info(f"COMPLETE - No more rows found")