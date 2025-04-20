############################################################################################
# database.py
# 
#   database functions used to support VIn searching. This includes reading a row from the 
#       database, tagging a row in the database as 'being processed' and updating a row
#       from the database with the result
#
############################################################################################
import mariadb
import logging

def fetch_row(database_config, table_name, type, start_sequence = None):
    """
    Connects to the MariaDB database and retrieves a random, unprocessed row from the specified table.
    
    :param database_config: Dictionary containing database connection parameters
    :param table_name: Name of the table to query
    :param: type: the type of VIN which is used for querying a subset of VINs
    :start_sequence: optional. the sequence number which to start searching. If this is specified, the searching is not random but sequentially in order starting at start_sequence 
    :return: The row as a dictionary, or None if no row is found
    """
    try:
        # Connect to the database
        connection = mariadb.connect(**database_config)
        cursor = connection.cursor(dictionary=True)
        #randomly select a row from those that we have not yet processed; order does not matter
        query = f"SELECT * FROM {table_name} WHERE vin is NULL and checked_on is NULL and bot is NULL and type = '{type}' ORDER BY RAND() LIMIT 1"
        if start_sequence is not None:
            query = f"SELECT * FROM {table_name} WHERE vin is NULL and checked_on is NULL and bot is NULL and type = '{type}' and CAST(sequence AS UNSIGNED) >= CAST({start_sequence} AS UNSIGNED) ORDER BY CAST(sequence AS UNSIGNED) LIMIT 1"
        cursor.execute(query)

        # Fetch the result
        row = cursor.fetchone()
        return row

    except mariadb.Error as e:
        logging.error(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

    return None

def update_row(database_config, table_name, row_id, vin, carfax_records, autocheck_records, name, api):
    """
    Connects to the MariaDB database and updates a row from the specified table where ID = row_id
    
    :param database_config: dictionary containing database connection parameters
    :param table_name: tame of the table to query
    :param row_id: the key used to locate the row to update
    :param vin: the VIN of the car
    :param carfax_records: the number of Carfax records
    :param autocheck_records: the number of Autocheck records
    :param name: the name of the car (usually year, make, model)
    :param api: the name of the bot used to find the VIN from a web service
    """
    try:
        # Connect to the database
        connection = mariadb.connect(**database_config)
        cursor = connection.cursor(dictionary=True)

        #update the database row to indicate we have processed this sequence number and also indicate the result
        query = f"UPDATE {table_name} SET vin = '{vin}', carfax_records = '{carfax_records}', autocheck_records = '{autocheck_records}', name = '{name}', bot = '{api}',checked_on = NOW() WHERE ID = {row_id}"
        cursor.execute(query)
        connection.commit()

    except mariadb.Error as e:
        logging.error(f"Error: {e}")
        connection.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

    return None

def tag_row(database_config, table_name, row_id, api):
    """
    Connects to the MariaDB database and updates a row from the specified table where ID = row_id
    
    :param database_config: Dictionary containing database connection parameters
    :param table_name: Name of the table to query
    :param row_id: The key used to locate the row to update
    :param found: a value which indicates the result; "n" - not found, "gt" - GT sticker found, "eco" - Ecoboost sticker found
    """
    try:
        # Connect to the database
        connection = mariadb.connect(**database_config)
        cursor = connection.cursor(dictionary=True)

        # Check if `api` should be NULL
        api_value = "NULL" if api is None else f"'{api}'"

        #update the database row to indicate we have processed this sequence number and also indicate the result
        query = f"UPDATE {table_name} SET bot = {api_value} WHERE ID = {row_id}"
        cursor.execute(query)
        connection.commit()

    except mariadb.Error as e:
        logging.error(f"Error: {e}")
        connection.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

    return None