############################################################################################
# generate_vin.py
# 
#   VIN functions used to support VIN searching.
#
############################################################################################
import logging

def add_check_digit(vin):
    """
    Validates the check digit of a given 17-character VIN.
    
    param:
        vin (str): The Vehicle Identification Number to validate.
        
    Returns:
        vin: None if VIN fails validation (except for check digit)
    """
    if len(vin) != 17:
        logging.error("Invalid VIN length. Must be exactly 17 characters.")
        return False
    
    vin = vin.upper()  # Ensure VIN is in uppercase
    weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
    transliterations = {
        **{str(i): i for i in range(10)},  # 0-9 map to themselves
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
        'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
    }

    try:
        # Compute the weighted sum
        weighted_sum = 0
        for i, char in enumerate(vin):
            if char not in transliterations:
                raise ValueError(f"Invalid character '{char}' in VIN.")
            value = transliterations[char]
            weighted_sum += value * weights[i]

        # Calculate the check digit
        remainder = weighted_sum % 11
        calculated_check_digit = 'X' if remainder == 10 else str(remainder)

        correct_vin = vin[:8] + calculated_check_digit + vin[9:]

        return correct_vin

    except ValueError as e:
        logging.error(e)
        return None

if __name__ == "__main__":				
        vin = '1FA6P8R00P5502924'
        corrected_vin = add_check_digit(vin)
        print(f"The VIN '{corrected_vin}' is corrected.")