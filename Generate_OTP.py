import subprocess
import requests
import pandas as pd
import time

# Define the base URL and endpoint for ERP
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

# Fetch data from ERP
while True:
    params = {
        'fields': '["name","mac_id","product","code","model_no","build_no","mode","ip_address","otp"]',
        'limit_start': limit_start,
        'limit_page_length': limit_page_length,
        'filters': '[["otp", "=", ""]]'  # Filter for records with no OTP
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


# Define the helper function for encoding mode
def encode_mode(mode):
    """Encode mode into a numeric value."""
    mode_mapping = {
        "Power On": "1",
        "Display Update": "2",
        "Model Selection": "3",
    }
    return mode_mapping.get(mode, "0")  # Default to "0" if the mode is unrecognized


# Function to generate OTP using Docker command
def generate_otp_with_docker(mac_id, serial_no, firmware_no, mode, build_no):
    """Run the OTP Process command inside Docker to generate OTP."""
    # Encode the mode value
    encoded_mode = encode_mode(mode)

    # Construct the OTP input string
    command_input = f"{mac_id}{serial_no}{firmware_no}{encoded_mode}{build_no}{firmware_no}"

    # Docker command to run the OTP Process executable with installation steps
    docker_command = [
        'docker', 'run', '--rm', '-v', "$(pwd):/workspace", '-w', '/workspace',
        '--platform', 'linux/arm', '-it', 'arm32v7/debian', 'bash', '-c',
        '''
        apt update && \
        apt install -y libqt5gui5 libqt5widgets5 libqt5network5 && \
        ldconfig -p | grep libQt5Core.so.5 && \
        ./OTP_Process {} 
        '''.format(command_input)
    ]

    try:
        # Run the docker command
        result = subprocess.run(docker_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        otp = result.stdout.strip()  # Extract OTP from the result
        return otp
    except subprocess.CalledProcessError as e:
        print(f"Error generating OTP: {e}")
        return None


# Function to update OTP in ERP system
def update_otp_in_erp(docname, otp):
    """Update the OTP for a record in the ERP system."""
    update_url = f"{url}/{docname}"
    payload = {
        "data": {
            "otp": otp
        }
    }
    try:
        response = requests.put(update_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully updated OTP for {docname}")
    except requests.exceptions.RequestException as e:
        print(f"Error updating OTP for {docname}: {e}")


# Main process to generate OTPs and update ERP system
def main():
    for _, row in otp_df.iterrows():
        # Extract details from the row
        name = row['name']
        mac_id = row['mac_id']
        serial_no = row['serial_no']
        firmware_no = row['firmware_no']
        mode = row['mode']
        build_no = row['build_no']

        if mac_id and serial_no and firmware_no and mode and build_no:
            # Generate OTP using the Docker command
            otp = generate_otp_with_docker(mac_id, serial_no, firmware_no, mode, build_no)
            if otp:
                # Update the OTP in the ERP system
                update_otp_in_erp(name, otp)
            else:
                print(f"Failed to generate OTP for {name}")
        else:
            print(f"Incomplete data for {name}")


if __name__ == "__main__":
    main()
