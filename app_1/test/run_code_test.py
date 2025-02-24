import io
import traceback
from contextlib import redirect_stdout
from datetime import datetime
import pybgpstream
import re

# Define the code as a string
output = """
Below is a Python script that uses the `pybgpstream` library to list BGP messages for AS3356 from the collector `rrc00` between the specified time range of October 28, 2024, from 13:00 to 13:10 PM UTC.
```python
import pybgpstream
from datetime import datetime

def list_bgp_messages(target_asn, collector, from_time, until_time):
    # Initialize the BGPStream
    stream = pybgpstream.BGPStream(
        from_time=from_time,
        until_time=until_time,
        record_type="updates",
        collectors=[collector]
    )

    # Iterate over records and elements
    for rec in stream.records():
        for elem in rec:
            elem_time = datetime.utcfromtimestamp(elem.time)
            elem_type = elem.type  # 'A' for announcements, 'W' for withdrawals
            fields = elem.fields
            prefix = fields.get("prefix")

            if prefix is None:
                continue  # Skip if prefix is not available
            
            # Get the AS path and check for target ASN
            as_path_str = fields.get('as-path', "")
            as_path = as_path_str.split()
            peer_asn = elem.peer_asn

            # Check if the target ASN is in the AS path
            if target_asn in as_path:
                print(f"Time: {elem_time}, Type: {elem_type}, Prefix: {prefix}, AS Path: {as_path}, Peer ASN: {peer_asn}")

# Define parameters and run the function
target_asn = '3356'
collector = 'rrc00'
from_time = "2024-10-28 13:00:00"
until_time = "2024-10-28 13:01:00"
list_bgp_messages(target_asn, collector, from_time, until_time)
```

### Instructions to Run the Script
 1. Make sure you have the `pybgpstream` library installed. You can install it using pip if you haven't done so:
    ```bash
    pip install pybgpstream
    ```
 2. Save the script to a Python file (e.g., `bgp_messages.py`).
 3. Run the script using Python:
    ```bash
    python bgp_messages.py
    ```
 This script will output the BGP messages for AS3356 from the collector `rrc00` within the specified time range. Each message will include the timestamp, message type (announcement or withdrawal), prefix, AS path, and peer ASN.
"""

def extract_code_from_reply(assistant_reply_content):
    code_pattern = r"```python\s*\n(.*?)```"
    match = re.search(code_pattern, assistant_reply_content, re.DOTALL)
    if match:
        code = match.group(1)
        return code
    else:
        # No code block found
        return None

code = extract_code_from_reply(output)
# Initialize a string to capture outputs
output_capture = io.StringIO()

# Run the code and capture outputs
try:
    # Redirect stdout to capture print statements
    with redirect_stdout(output_capture):
        # Prepare a local namespace for exec
        safe_globals = {
            "__builtins__": __builtins__,
            "pybgpstream": pybgpstream,
            "datetime": datetime,
        }
        exec(code, safe_globals)
except Exception as e:
    # Capture the traceback if an error occurs
    error_output = traceback.format_exc()
    output_capture.write("\nError while executing the code:\n")
    output_capture.write(error_output)

# Get the captured output
code_output = output_capture.getvalue()
print("Captured Output:\n", code_output)
