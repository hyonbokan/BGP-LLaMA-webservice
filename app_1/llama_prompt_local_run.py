DEFAULT_PROMPT = """
You are tasked with generating a Python script that performs basic BGP analysis using the pybgpstream library.
Please adhere to the following guidelines when writing the code:

- Correctly import required libraries:
from datetime import datetime, timezone
import pybgpstream
import os
import re
from collections import defaultdict, Counter
import statistics

- Directory containing BGP update files:
Replace {year} and {month} according to the timestamp
/home/hb/ris_bgp_updates/{year}/{month}/rrc00

- Parse the time window strings into datetime objects:
from_time = datetime.strptime(from_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
until_time = datetime.strptime(until_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

Here is your task:\n
"""


BASE_SETUP = """
You are tasked with generating a Python script that performs BGP data analysis using the pybgpstream library.
Please adhere to the following guidelines when writing the code. According the task below, you are allow to implement minor changes:

Correctly import required libraries:
from datetime import datetime, timezone
import pybgpstream
import os
import re
from collections import defaultdict, Counter
import statistics

Define Time Window and Target ASN:
from_time_str = "YYYY-MM-DD HH:MM:SS"
until_time_str = "YYYY-MM-DD HH:MM:SS"
target_asn = "{target ASN}"

Parse the time window strings into datetime objects:
from_time = datetime.strptime(from_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
until_time = datetime.strptime(until_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

Directory containing BGP update files:
Replace {year} and {month} according to the timestamp
/home/hb/ris_bgp_updates/{year}/{month}/rrc00


Define Regular Expression Pattern to Match Filenames:
pattern = r'^updates\.(\d{8})\.(\d{4})\.(bz2|gz)$'
"""
LOCAL_PREFIX_ANALYSYS = BASE_SETUP + """
Set up a set for unique prefixes and a dictionary for origin AS counts:
unique_prefixes = set()
origin_as_counts = defaultdict(set)
    
Iterate Over Files in the Directory:
for root, _, files in os.walk(directory):
    for file in files:

Filter Files Based on Time Window:
match = re.match(pattern, file)
if match:
    date_str = match.group(1)  # YYYYMMDD
    time_str = match.group(2)  # HHMM

    # Combine date and time strings
    file_timestamp_str = date_str + time_str  # 'YYYYMMDDHHMM'

    # Convert file timestamp to datetime object
    file_time = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)

    # Check if file time is within the desired time window
    if file_time < from_time or file_time > until_time:
        # Skip files outside the time window
        continue

    # Proceed to process the file
else:
    # If filename doesn't match pattern, skip it
    continue
    
Initialize BGPStream for Each File:
file_path = os.path.join(root, file)

# Initialize BGPStream for local file processing
stream = pybgpstream.BGPStream(data_interface="singlefile")
stream.set_data_interface_option("singlefile", "upd-file", file_path)

Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        # Processing logic goes here
        
Extract Element Information and Filter by Time Window:
elem_time = datetime.utcfromtimestamp(elem.time).replace(tzinfo=timezone.utc)

# Filter elements outside the time window
if elem_time < from_time or elem_time > until_time:
    continue

elem_type = elem.type
fields = elem.fields
prefix = fields.get("prefix")
if prefix is None:
    continue

Extract AS Path and Filter for Target ASN:
as_path_str = fields.get('as-path', "")
as_path = as_path_str.split()

# Filter for target ASN in the AS path
if target_asn not in as_path:
    continue

Process Announcements:
if elem_type == 'A':
    # Add prefix to the set of unique prefixes
    unique_prefixes.add(prefix)

    # Track changes in origin AS for each prefix
    origin_as = as_path[-1] if as_path else None
    if origin_as:
        origin_as_changes[prefix].add(origin_as)

Provide Summary:
print(f"Total unique prefixes: {len(unique_prefixes)}")
for prefix, origin_as_set in origin_as_changes.items():
    print(f"Prefix: {prefix}")
    print(f"  Origin AS count: {len(origin_as_set)}")
    if len(origin_as_set) > 1:
        print(f"  Changes in origin AS observed: {origin_as_set}")

Here is your task:\n
"""

LOCAL_AS_PATH_ANALYSYS = BASE_SETUP + """
Set up dictionaries for AS paths and path length statistics:
as_paths_per_prefix = defaultdict(list)
as_path_changes = defaultdict(int)

Iterate Over Files in the Directory:
for root, _, files in os.walk(directory):
    for file in files:

Filter Files Based on Time Window:
match = re.match(pattern, file)
if match:
    date_str = match.group(1)  # YYYYMMDD
    time_str = match.group(2)  # HHMM

    # Combine date and time strings
    file_timestamp_str = date_str + time_str  # 'YYYYMMDDHHMM'

    # Convert file timestamp to datetime object
    file_time = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)

    # Check if file time is within the desired time window
    if file_time < from_time or file_time > until_time:
        # Skip files outside the time window
        continue

    # Proceed to process the file
else:
    # If filename doesn't match pattern, skip it
    continue
    
Initialize BGPStream for Each File:
file_path = os.path.join(root, file)

# Initialize BGPStream for local file processing
stream = pybgpstream.BGPStream(data_interface="singlefile")
stream.set_data_interface_option("singlefile", "upd-file", file_path)

Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        # Processing logic goes here
        
Extract Element Information and Filter by Time Window:
elem_time = datetime.utcfromtimestamp(elem.time).replace(tzinfo=timezone.utc)

# Filter elements outside the time window
if elem_time < from_time or elem_time > until_time:
    continue

elem_type = elem.type
fields = elem.fields
prefix = fields.get("prefix")
if prefix is None:
    continue

Extract AS Path and Filter for Target ASN:
as_path_str = fields.get('as-path', "")
as_path = as_path_str.split()

# Filter for target ASN in the AS path
if target_asn not in as_path:
    continue

Append AS path length to the list:
as_paths_per_prefix[prefix].append(len(as_path))

Detect changes in AS paths:
last_as_path = as_paths_per_prefix[prefix][-2] if len(as_paths_per_prefix[prefix]) > 1 else None
if last_as_path and as_path != last_as_path:
    as_path_changes[prefix] += 1

Provide Summary:
Calculate and output statistics:
for prefix, lengths in as_paths_per_prefix.items():
    min_length = min(lengths)
    max_length = max(lengths)
    median_length = statistics.median(lengths)
    print(f"Prefix: {prefix}")
    print(f"  Min AS path length: {min_length}")
    print(f"  Max AS path length: {max_length}")
    print(f"  Median AS path length: {median_length}")
    if as_path_changes[prefix]:
        print(f"  AS path changed {as_path_changes[prefix]} times")

Here is your task:\n
"""

LOCAL_MED_COMMUNITY_ANALYSYS = BASE_SETUP + """
Set up lists for MED values and a counter for community tags:
med_values = []
community_counts = Counter()

Iterate Over Files in the Directory:
for root, _, files in os.walk(directory):
    for file in files:

Filter Files Based on Time Window:
match = re.match(pattern, file)
if match:
    date_str = match.group(1)  # YYYYMMDD
    time_str = match.group(2)  # HHMM

    # Combine date and time strings
    file_timestamp_str = date_str + time_str  # 'YYYYMMDDHHMM'

    # Convert file timestamp to datetime object
    file_time = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)

    # Check if file time is within the desired time window
    if file_time < from_time or file_time > until_time:
        # Skip files outside the time window
        continue

    # Proceed to process the file
else:
    # If filename doesn't match pattern, skip it
    continue
    
Initialize BGPStream for Each File:
file_path = os.path.join(root, file)

# Initialize BGPStream for local file processing
stream = pybgpstream.BGPStream(data_interface="singlefile")
stream.set_data_interface_option("singlefile", "upd-file", file_path)

Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        # Processing logic goes here
        
Extract Element Information and Filter by Time Window:
elem_time = datetime.utcfromtimestamp(elem.time).replace(tzinfo=timezone.utc)

# Filter elements outside the time window
if elem_time < from_time or elem_time > until_time:
    continue

Extract MED and communities:
fields = elem.fields
elem_type = elem.type

Extract AS Path and Filter for Target ASN:
as_path_str = fields.get('as-path', "")
as_path = as_path_str.strip().split()

if target_asn not in as_path:
    continue

Extract MED Values:
med = fields.get('med')
if med is not None:
    try:
        med_values.append(int(med))
    except ValueError:
        pass  # Ignore invalid MED values

Get the Communities List:
communities = fields.get('communities', [])
for community in communities:
    community_str = f"{community[0]}:{community[1]}"
    community_counts[community_str] += 1

Calculate MED statistics:
if med_values:
    average_med = statistics.mean(med_values)
    min_med = min(med_values)
    max_med = max(med_values)
    print(f"Average MED Value: {average_med}")
    print(f"MED Value Range: {min_med} - {max_med}")
else:
    print("No MED values found.")
Output most common community tags:

if community_counts:
    most_common = community_counts.most_common(5)
    print("Most Common Community Tags:")
    for tag, count in most_common:
        print(f"  {tag}: {count} times")
else:
    print("No community tags found.")

Here is your task:\n
"""

LOCAL_PREFIX_STABILITY = """
"""
LOCAL_OUTAGE = BASE_SETUP + """
Prepare data structures to store counts and detected anomalies:
announcements = defaultdict(int)
withdrawals = defaultdict(int)

outage_events = defaultdict(int)
flapping_events = defaultdict(int)
route_leaks = defaultdict(int)


If including other anomalies, initialize them as well
outage_events = defaultdict(int)
flapping_events = defaultdict(int)
route_leaks = defaultdict(int)

Iterate Over Files in the Directory:
for root, _, files in os.walk(directory):
    for file in files:

Filter Files Based on Time Window:
match = re.match(pattern, file)
if match:
    date_str = match.group(1)  # YYYYMMDD
    time_str = match.group(2)  # HHMM

    # Combine date and time strings
    file_timestamp_str = date_str + time_str  # 'YYYYMMDDHHMM'

    # Convert file timestamp to datetime object
    file_time = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)

    # Check if file time is within the desired time window
    if file_time < from_time or file_time > until_time:
        continue

    # Proceed to process the file
else:
    continue
    
Initialize BGPStream for Each File:
file_path = os.path.join(root, file)

# Initialize BGPStream for local file processing
stream = pybgpstream.BGPStream(data_interface="singlefile")
stream.set_data_interface_option("singlefile", "upd-file", file_path)

Process BGP records and elements:
            for rec in stream.records():
                for elem in rec:
                    fields = elem.fields
                    prefix = fields.get("prefix")
                    as_path_str = fields.get('as-path', "")
                    as_path = as_path_str.split()

                    # Count Announcements and Withdrawals
                    if elem.type == 'A':
                        announcements[prefix] += 1
                    elif elem.type == 'W':
                        withdrawals[prefix] += 1

                    # Detect Anomalies
                    # Outage Detection: Check for absence of updates for known prefixes
                    if prefix in known_prefixes and target_asn not in as_path:
                        outage_events[prefix] += 1

                    # Flapping Detection: Detect frequent changes in announcements/withdrawals
                    if announcements[prefix] > FLAPPING_THRESHOLD:
                        flapping_events[prefix] += 1

                    # Route Leak Detection: Detect unexpected AS path patterns
                    if detect_route_leak(as_path):
                        route_leaks[prefix] += 1
def detect_route_leak(as_path_list):
    Define criteria for route leak detection
    Example: Unexpected presence of certain ASNs in the AS path
    suspicious_asns = {"ASN_X", "ASN_Y"}  # Replace with relevant ASNs
    leak_detected = any(asn in suspicious_asns for asn in as_path_list)

    if leak_detected:
        print(f"Route leak detected in AS path: {' '.join(as_path_list)}")

    return leak_detected
    

Summarize the results
results = []
for prefix in known_prefixes:
    results.append({
        'prefix': prefix,
        'announcements': announcements.get(prefix, 0),
        'withdrawals': withdrawals.get(prefix, 0),
        'outage_events': outage_events.get(prefix, 0),
        'flapping_events': flapping_events.get(prefix, 0),
        'route_leaks': route_leaks.get(prefix, 0)
    })

# Convert to DataFrame for better readability
df_results = pd.DataFrame(results)

# Display the results
if not df_results.empty:
    print(f"\nDetected BGP Outage Incidents for ASN {asn}:\n")
    for index, row in df_results.iterrows():
        print(f"Incident {index + 1}:")
        print(f"  Prefix: {row['prefix']}")
        print(f"  Announcements: {row['announcements']}")
        print(f"  Withdrawals: {row['withdrawals']}")
        print(f"  Outage Events: {row['outage_events']}")
        print(f"  Flapping Events: {row['flapping_events']}")
        print(f"  Route Leaks: {row['route_leaks']}\n")
else:
    print(f"\nNo BGP outage incidents detected for ASN {asn} in the given time period.")
"""

LOCAL_HIJACKING = """
You are tasked with generating a Python script that performs BGP data analysis using the pybgpstream library for anomaly detection.
The script should process BGP update files locally, filter data within a specified time window for a specific ASN
Please adhere to the following guidelines when writing the code:

Correctly import required libraries:
import os
import re
import pybgpstream
import pandas as pd
from datetime import datetime, timezone
from collections import defaultdict, Counter

Define Time Window and Target ASN:
asn = "ASN_NUMBER" Replace with the target ASN (e.g., "16509")
start_time = "YYYY-MM-DD HH:MM:SS"  # UTC
end_time = "YYYY-MM-DD HH:MM:SS"    # UTC

Replace known prefixes: 
known_prefixes = set([
    "177.93.174.0/23",
    "138.59.238.0/23",
    "177.93.168.0/23",
])

Parse the time window strings into datetime objects:
from_time = datetime.strptime(from_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
until_time = datetime.strptime(until_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

This is a directory containing BGP update files:
/home/hb/ris_bgp_updates/{year}}/{month}}/rrc00 Replace year and month accordingly

Define Regular Expression Pattern to Match Filenames:
pattern = r'^updates\.(\d{8})\.(\d{4})\.(bz2|gz)$'

Prepare data structures to store counts and detected anomalies:
hijack_attempts = {}

If including other anomalies, initialize them as well
outage_events = defaultdict(int)
flapping_events = defaultdict(int)
route_leaks = defaultdict(int)

Iterate Over Files in the Directory:
for root, _, files in os.walk(directory):
    for file in files:

Filter Files Based on Time Window:
match = re.match(pattern, file)
if match:
    date_str = match.group(1)  # YYYYMMDD
    time_str = match.group(2)  # HHMM

    # Combine date and time strings
    file_timestamp_str = date_str + time_str  # 'YYYYMMDDHHMM'

    # Convert file timestamp to datetime object
    file_time = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)

    # Check if file time is within the desired time window
    if file_time < from_time or file_time > until_time:
        continue

    # Proceed to process the file
else:
    continue
    
Initialize BGPStream for Each File:
file_path = os.path.join(root, file)

# Initialize BGPStream for local file processing
stream = pybgpstream.BGPStream(data_interface="singlefile")
stream.set_data_interface_option("singlefile", "upd-file", file_path)

Process BGP records and elements:
for rec in stream.records():
    for elem in rec:
        if elem.type == 'A':
            prefix = elem.fields.get('prefix')
            as_path = elem.fields.get('as-path', '')
            as_path_list = as_path.strip().split()
            origin_asn = as_path_list[-1] if as_path_list else None

            Check if the prefix is known and the origin ASN is not the target ASN
            if prefix in known_prefixes and origin_asn != asn:
                if prefix not in hijack_attempts:
                    hijack_attempts[prefix] = {'unauthorized_asns': set(), 'count': 0}
                hijack_attempts[prefix]['unauthorized_asns'].add(origin_asn)
                hijack_attempts[prefix]['count'] += 1

Summarize the results
results = []
for prefix, data in hijack_attempts.items():
    results.append({
        'prefix': prefix,
        'unauthorized_asns': list(data['unauthorized_asns']),
        'frequency_of_suspected_hijacks': data['count']
    })

df_hijacks = pd.DataFrame(results)

if not df_hijacks.empty:
    print(f"\nSuspected BGP Hijacking Incidents Involving ASN {asn}:\n")
    for index, row in df_hijacks.iterrows():
        print(f"Incident {index + 1}:")
        print(f"  Prefix: {row['prefix']}")
        print(f"  Unauthorized ASNs: {row['unauthorized_asns']}")
        print(f"  Frequency of Suspected Hijacks: {row['frequency_of_suspected_hijacks']}\n")
else:
    print(f"\nNo suspected hijacking incidents detected for ASN {asn} in the given time period.")
"""

# LOCAL_DEFAULT = """
# You are tasked with generating a Python script that performs BGP data analysis using the pybgpstream library.
# Please adhere to the following guidelines when writing the code:

# Correctly import required libraries:
# from datetime import datetime, timezone
# import pybgpstream
# from collections import defaultdict

# Define Time Window and Target ASN:
# from_time_str = "YYYY-MM-DD HH:MM:SS"
# until_time_str = "YYYY-MM-DD HH:MM:SS"
# target_asn = "{target ASN}"

# Parse the time window strings into datetime objects:
# from_time = datetime.strptime(from_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
# until_time = datetime.strptime(until_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

# The directory containing BGP update files:
# /home/hb/ris_bgp_updates/{year}}/{month}}/rrc00

# Define Regular Expression Pattern to Match Filenames:
# pattern = r'^updates\.(\d{8})\.(\d{4})\.(bz2|gz)$'

# Initialize Counters:
# total_announcements = 0
# total_withdrawals = 0
# update_counts = []


# Iterate Over Files in the Directory:
# for root, _, files in os.walk(directory):
#     for file in files:
#         match = re.match(pattern, file)
#         if match:
#             date_str = match.group(1)  # YYYYMMDD
#             time_str = match.group(2)  # HHMM
#             file_timestamp_str = date_str + time_str
#             file_time = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
#             if file_time < from_time or file_time > until_time:
#                 continue
#             file_path = os.path.join(root, file)
            
#             # Initialize BGPStream for file
#             stream = pybgpstream.BGPStream(data_interface="singlefile")
#             stream.set_data_interface_option("singlefile", "upd-file", file_path)
            
#             # Process records in the file
#             for rec in stream.records():
#                 for elem in rec:
#                     elem_time = datetime.utcfromtimestamp(elem.time)
#                     elem_type = elem.type  # 'A' for announcements, 'W' for withdrawals
#                     fields = elem.fields
#                     prefix = fields.get("prefix")
#                     as_path_str = fields.get('as-path', "")
#                     as_path = as_path_str.split()
#                     peer_asn = elem.peer_asn

#                     # Filter for AS4766
#                     if '4766' not in as_path:
#                         continue

#                     # Count announcements and withdrawals
#                     if elem_type == 'A':
#                         total_announcements += 1
#                     elif elem_type == 'W': total_withdrawals += 1

#                     # Track updates for statistical analysis
#                     update_counts.append(1 if elem_type == 'A' else 0)
#                     update_counts.append(-1 if elem_type == 'W' else 0)

#     Calculate total updates
#     total_updates = total_announcements + total_withdrawals
    
#     Calculate statistics
#     min_updates = min(update_counts) if update_counts else 0
#     max_updates = max(update_counts) if update_counts else 0
#     median_updates = statistics.median(update_counts) if update_counts else 0
    
#     Print results
#     print(f"Total BGP updates for AS4766 from {from_time} to {until_time}: {total_updates}")
#     print(f"Minimum updates observed: {min_updates}")
#     print(f"Maximum updates observed: {max_updates}")
#     print(f"Median updates observed: {median_updates}")
# Here is your task:\n
# """

LOCAL_DEFAULT = BASE_SETUP + """
Initialize Counters and Data Structures for Various Analysis Tasks:

Basic Update Counts (Announcements, Withdrawals)
Prefix Analysis (track unique prefixes and occurrences)
MED Analysis (store MED values)
Community Analysis (count frequency of community tags)
AS Path Analysis (track AS path lengths and changes)
Origin AS Analysis (track origin ASNs for prefixes, detect MOAS)

Iterate Over Files in the Directory and Filter by Time Window:
for root, _, files in os.walk(directory):
    for file in files:
        match = re.match(pattern, file)
        if match:
            date_str = match.group(1)  # YYYYMMDD
            time_str = match.group(2)  # HHMM
            file_timestamp_str = date_str + time_str
            file_time = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
            if file_time < from_time or file_time > until_time:
                continue

            file_path = os.path.join(root, file)

            # Initialize BGPStream for local file processing
            stream = pybgpstream.BGPStream(data_interface="singlefile")
            stream.set_data_interface_option("singlefile", "upd-file", file_path)

            # Process records and elements
            for rec in stream.records():
                for elem in rec:
                    elem_time = datetime.utcfromtimestamp(elem.time).replace(tzinfo=timezone.utc)

                    # Filter elements outside the time window (if needed)
                    if elem_time < from_time or elem_time > until_time:
                        continue

                    elem_type = elem.type  # 'A' for announcements, 'W' for withdrawals
                    fields = elem.fields
                    prefix = fields.get("prefix")
                    if prefix is None:
                        continue

                    as_path_str = fields.get('as-path', "")
                    as_path = as_path_str.split()
                    med = fields.get('med')
                    communities = fields.get('communities', [])
                    peer_asn = elem.peer_asn

                    # Filter for target ASN in AS path (if required)
                    if target_asn not in as_path:
                        continue

                    # Basic Update Counting
                    if elem_type == 'A':
                        total_announcements += 1
                        update_counts.append(1)
                    elif elem_type == 'W':
                        total_withdrawals += 1
                        update_counts.append(-1)

                    # Prefix Analysis
                    prefix_counts[prefix] += 1
                    unique_prefixes.add(prefix)

                    # MED Analysis
                    if med is not None:
                        try:
                            med_values.append(int(med))
                        except ValueError:
                            pass

                    # Community Analysis
                    for comm in communities:
                        community_str = f"{comm[0]}:{comm[1]}"
                        community_counts[community_str] += 1

                    # AS Path Analysis
                    # Track AS path lengths and detect changes
                    current_path_length = len(as_path)
                    if prefix in as_paths_per_prefix:
                        last_path = as_paths_per_prefix[prefix][-1] if as_paths_per_prefix[prefix] else None
                        if last_path is not None and as_path != last_path:
                            as_path_changes[prefix] += 1
                        as_paths_per_prefix[prefix].append(as_path)
                    else:
                        as_paths_per_prefix[prefix].append(as_path)

                    # Origin AS Analysis (MOAS detection)
                    origin_asn = as_path[-1] if as_path else None
                    if origin_asn:
                        origin_as_counts[prefix].add(origin_asn)
                        
After Processing All Files, Compute Statistics:
total_updates = total_announcements + total_withdrawals

min_updates = min(update_counts) if update_counts else 0
max_updates = max(update_counts) if update_counts else 0
median_updates = statistics.median(update_counts) if update_counts else 0

if med_values:
    min_med = min(med_values)
    max_med = max(med_values)
    median_med = statistics.median(med_values)
else:
    min_med = max_med = median_med = 0

as_path_lengths = [len(path) for paths in as_paths_per_prefix.values() for path in paths]
if as_path_lengths:
    min_path_len = min(as_path_lengths)
    max_path_len = max(as_path_lengths)
    median_path_len = statistics.median(as_path_lengths)
else:
    min_path_len = max_path_len = median_path_len = 0

Output Results in a Human-Readable Format:

Print total updates, announcements, withdrawals
Print prefix analysis results
Print MED stats if any
Print top communities if any
Print AS path length stats and changes
Print MOAS conflicts

Here is your task:\n
"""