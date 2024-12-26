#!/usr/bin/env python
# coding: utf-8

# In[12]:


import requests
import pandas as pd
import time 

base_url = 'https://erpv14.electrolabgroup.com/'
endpoint = 'api/resource/OTP Request Form'
url = base_url + endpoint

headers = {
    'Authorization': 'token 3ee8d03949516d0:6baa361266cf807'
}

# Initialize variables for pagination
limit_start = 0
limit_page_length = 1000
all_data = []  # List to store all fetched data

while True:
    
    # Set pagination parameters
    params = {
    'fields': '["name","mac_id","product","code","model_no","build_no","mode","ip_address","otp"]',
    'limit_start': limit_start,
    'limit_page_length': limit_page_length,
    'filters': '[["otp", "=", ""]]'# Filter for otp being None
}
    
    # Make the API request
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        fetched_data = data['data']
        
        # Check if any data is returned
        if not fetched_data:
            print("All data has been fetched.")
            break
        
        # Append the fetched data to the list
        all_data.extend(fetched_data)
        
        # Update limit_start for the next batch
        limit_start += limit_page_length
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        print("Response:", response.json())
        break

# Convert the collected data into a DataFrame
otp_df = pd.DataFrame(all_data)
otp_df.head()


# In[13]:


# Define the helper function for encoding mode
def encode_mode(mode):
    """Encode mode into a numeric value."""
    mode_mapping = {
        "Power On": "1",
        "Display Update": "2",
        "Model Selection": "3",
    }
    return mode_mapping.get(mode, "0")  # Default to "0" if the mode is unrecognized

# Define the function to generate OTP using the binary file
def generate_otp(mac_id, serial_no, firmware_no, mode, build_no):
    """Generate OTP using the binary file."""
    binary_file = r'C:\path\to\.OTP_Process' 
    encoded_mode = encode_mode(mode)
    command_input = f"{mac_id}{serial_no}{firmware_no}{encoded_mode}{build_no}{firmware_no}"
    command = [binary_file, command_input]
    
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()  # Extract the OTP from the output
    except subprocess.CalledProcessError as e:
        print(f"Error generating OTP for MAC {mac_id}: {e}")
        return None

# Function to apply the OTP generation on the DataFrame row-by-row
def apply_generate_otp(row):
    mac_id = row['mac_id']
    serial_no = row['product']  # Assuming 'product' is the serial number or adjust accordingly
    firmware_no = row['model_no']  # Assuming 'model_no' is firmware version or adjust
    mode = row['mode']
    build_no = row['build_no']
    
    return generate_otp(mac_id, serial_no, firmware_no, mode, build_no)

# Assuming otp_df is the DataFrame that contains the data
otp_df['generated_otp'] = otp_df.apply(apply_generate_otp, axis=1)

# Show the resulting DataFrame with OTPs
print(otp_df[['name', 'mac_id', 'generated_otp']].head())


# In[ ]:




