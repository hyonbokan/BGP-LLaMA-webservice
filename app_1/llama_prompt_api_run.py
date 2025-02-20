LLAMA_DEFAULT_PROMPT = """
You are tasked with generating a Python script that performs basic BGP analysis using the pybgpstream library.
Please adhere to the following guidelines when writing the code:

Import Required Libraries:
Correctly import datetime and pybgpstream:
from datetime import datetime
import pybgpstream

Define the time range as strings in the following format:
from_time = "YYYY-MM-DD HH:MM:SS"
until_time = "YYYY-MM-DD HH:MM:SS"

collectors = ["rrc00"]
Initialize BGPStream with these parameters:
stream = pybgpstream.BGPStream(
    from_time=from_time,
    until_time=until_time,
    record_type="updates",
    collectors=collectors
)

Initialize Counters:
total_announcements = 0
total_withdrawals = 0

Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        # Processing logic goes here
        
Accessing and Validating Element Attributes:
Extract element type and fields:
elem_type = elem.type
fields = elem.fields

Increment counters based on element type:
if elem_type == 'A':
    total_announcements += 1
elif elem_type == 'W':
    total_withdrawals += 1

Provide Summary:
After processing, output the total counts:
print(f"Total announcements: {total_announcements}")
print(f"Total withdrawals: {total_withdrawals}")

Here is your task:\n
"""

LLAMA_PREFIX_ANALYSYS = """
You are tasked with generating a Python script that performs prefix analysis using the pybgpstream library.
Please adhere to the following guidelines when writing the code:

Correctly import datetime, pybgpstream, and defaultdict:
from datetime import datetime
import pybgpstream
from collections import defaultdict

Define Time Range and Collectors:
from_time = "YYYY-MM-DD HH:MM:SS"
until_time = "YYYY-MM-DD HH:MM:SS"
collectors = ["rrc00"]

Initialize BGPStream:
stream = pybgpstream.BGPStream(
    from_time=from_time,
    until_time=until_time,
    record_type="updates",
    collectors=collectors
)

target_asn = 'target asn' ('4766')

Set up a set for unique prefixes and a dictionary for origin AS counts:
unique_prefixes = set()
origin_as_counts = defaultdict(set)

Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        # Processing logic goes here

Extract Element Information:
elem_time = datetime.utcfromtimestamp(elem.time)
elem_type = elem.type
fields = elem.fields
prefix = fields.get("prefix")
if prefix is None:
    continue

Extract AS Path and Filter for target asn:
as_path_str = fields.get('as-path', "")
as_path = as_path_str.split()
if 'target asn' not in as_path:
    continue

Process Announcements:
if elem_type == 'A':

Add prefix to the set:
unique_prefixes.add(prefix)

Track Changes in Origin AS for Each Prefix:
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

LLAMA_AS_PATH_OPERATIONS = """
You are tasked with generating a Python script that performs AS path analysis using the pybgpstream library.
Please adhere to the following guidelines when writing the code:

Import Required Libraries:
from datetime import datetime
import pybgpstream
from collections import defaultdict
import statistics

Define Time Range and Collectors:
from_time = "YYYY-MM-DD HH:MM:SS"
until_time = "YYYY-MM-DD HH:MM:SS"
collectors = ["rrc00"]

Initialize BGPStream:
stream = pybgpstream.BGPStream(
    from_time=from_time,
    until_time=until_time,
    record_type="updates",
    collectors=collectors
)
target_asn = 'target asn' ('4766')

Set up dictionaries for AS paths and path length statistics:
as_paths_per_prefix = defaultdict(list)
as_path_changes = defaultdict(int)

Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        # Processing logic goes here

Extract prefix and AS path:
fields = elem.fields
prefix = fields.get("prefix")
if prefix is None:
    continue

as_path_str = fields.get('as-path', "")
as_path = as_path_str.split()
if target_asn not as_path:
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

LLAMA_MED_COMMUNITY = """
You are tasked with generating Python scripts that analyze MED values and community tags using the pybgpstream library.
Please adhere to the following guidelines when writing the code:

Import Required Libraries:
from datetime import datetime
import pybgpstream
from collections import defaultdict, Counter
import statistics

Define Time Range and Collectors:
from_time = "YYYY-MM-DD HH:MM:SS"
until_time = "YYYY-MM-DD HH:MM:SS"
collectors = ["rrc00"]

Initialize BGPStream:
stream = pybgpstream.BGPStream(
    from_time=from_time,
    until_time=until_time,
    record_type="updates",
    collectors=collectors
)

target_asn = 'target asn' ('4766')

Set up lists for MED values and a counter for community tags:
med_values = []
community_counts = Counter()

Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        # Processing logic goes here

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

LLAMA_SYSTEM_PROMPT = """
You are tasked with generating Python scripts that perform various BGP analysis tasks using the pybgpstream library.
Please adhere to the following guidelines when writing the code:
- Import Required Libraries:
Correctly import `datetime` for handling timestamp conversions:
from datetime import datetime

- Define Time Range and Collectors:
The time range as strings in the following format: 
from_time = "YYYY-MM-DD HH:MM:SS"
until_time = "YYYY-MM-DD HH:MM:SS"

Specify the BGP collectors list and initialize BGPStream with these parameters:
stream = pybgpstream.BGPStream(
        from_time=from_time,
        until_time=until_time,
        record_type="updates",
        collectors=["rrc00"]
    )

- Initialize Counters and Data Structures:
Set up counters and dictionaries for announcements, withdrawals, AS paths, community counts, and MED values:
from collections import defaultdict
announcements = defaultdict(int)
withdrawals = defaultdict(int)
prefix_as_paths = {}
community_counts = defaultdict(int)
med_values = []

- Iterate Over Records and Elements:
for rec in stream.records():
    for elem in rec:
        Processing logic goes here

- Accessing and Validating Element Attributes:
Extract basic element information such as timestamps, element type, and fields:
from datetime import datetime

elem_time = datetime.utcfromtimestamp(elem.time)
elem_type = elem.type 'A' for announcements, 'W' for withdrawals
fields = elem.fields

Retrieve prefix, validate it, and continue if it's absent:
prefix = fields.get("prefix")
if prefix is None:
    continue

Extract AS Path and filter based on the target ASN:
as_path_str = fields.get('as-path', "")
as_path = as_path_str.split()
target_asn = '3356'
if target_asn not in as_path:
    continue

Access additional attributes like Peer ASN, Collector, and Communities:
peer_asn = elem.peer_asn
collector = rec.collector
communities = fields.get('communities', [])

- Filtering and Counting Announcements and Withdrawals:
* Count announcements and withdrawals based on element type:
if elem_type == 'A':
    announcements[prefix] += 1
elif elem_type == 'W':
    withdrawals[prefix] += 1

- Detecting AS Path Changes:
* Track changes in AS paths for each prefix:
if prefix in prefix_as_paths:
    if as_path != prefix_as_paths[prefix]:  # AS path has changed
        # Update the AS path
        prefix_as_paths[prefix] = as_path
else:
    prefix_as_paths[prefix] = as_path

- Analyzing Community Attributes:
Count occurrences of each community string in the communities list:
for community in communities:
    community_str = f"{community[0]}:{community[1]}"
    community_counts[community_str] += 1

- Calculating Statistics (e.g., Average MED):
Retrieve the MED field, add it to a list, and calculate the average:
med = fields.get('med')
if med is not None:
    try:
        med_values.append(int(med))
    except ValueError:
        pass  Ignore invalid MED values

Calculate average MED if values exist
if med_values:
    average_med = sum(med_values) / len(med_values)


- Anomaly Detection Tasks
Implement functions or logic within the main loop to detect:
Hijacks:
Compare the observed origin AS with the expected origin AS for target prefixes.
Example:

expected_origins = {'192.0.2.0/24': '64500', '198.51.100.0/24': '64501'}
observed_origin = as_path[-1] if as_path else None
expected_origin = expected_origins.get(prefix)
if expected_origin and observed_origin != expected_origin:
    print(f"Possible hijack detected for {prefix}: expected {expected_origin}, observed {observed_origin}")

MOAS (Multiple Origin AS) Conflicts:
Monitor prefixes announced by multiple origin ASNs.
Example:
prefix_origins = defaultdict(set)

origin_asn = as_path[-1] if as_path else None
if origin_asn:
    prefix_origins[prefix].add(origin_asn)
    if len(prefix_origins[prefix]) > 1:
        origins = ', '.join(prefix_origins[prefix])
        print(f"MOAS conflict for {prefix}: announced by ASNs {origins}")

AS Path Prepending:
Detect AS path prepending by identifying consecutive repeated ASNs in the AS path.
Example:
prepending_counts = defaultdict(int)
last_asn = None
consecutive_count = 1

for asn in as_path:
    if asn == last_asn:
        consecutive_count += 1
    else:
        if consecutive_count > 1:
            prepending_counts[last_asn] += consecutive_count - 1
        consecutive_count = 1
    last_asn = asn

Handle the last ASN in the path
if consecutive_count > 1 and last_asn:
    prepending_counts[last_asn] += consecutive_count - 1

Report ASes performing prepending
for asn, count in prepending_counts.items():
    print(f"ASN {asn} prepended {count} times")

Here is your task:
"""

LLAMA_REAL_TIME_SYSTEM_PROMPT = """
You are tasked with generating Python scripts that perform real-time BGP analysis using the pybgpstream library. Please adhere to the following guidelines when writing the code:

- Script Structure
Include a __main__ block or a usage example to demonstrate how to run the script.
Implement time-based stop triggers to gracefully stop data collection and processing after a specified duration.
Use Separate Time Variables for Collection Duration and Metrics Interval
Collection Duration Tracking:
Use collection_start_time to track the total duration of data collection.
Metrics Interval Tracking:
Use a separate interval_start_time to track intervals for periodic tasks like printing metrics.
Do not reset collection_start_time inside loops, as it affects the stop condition.

- Key Processing Guidelines
Initialize BGPStream Without Filters:
stream = pybgpstream.BGPStream(
    project="ris-live",
    record_type="updates",
)
Implement Time-Based Stop Triggers:
import time

collection_start_time = time.time()
interval_start_time = collection_start_time
COLLECTION_DURATION = 300

- Initialize Counters and Tracking Variables:
At the start of the script, initialize all necessary counters and tracking variables:
announcements = defaultdict(int), withdrawals = defaultdict(int)
prefix_as_paths = {}
community_counts = defaultdict(int)
med_values = []

Checking for Stop Conditions Within the Loop:
while True:
    # Check if the total collection duration has been exceeded
    if time.time() - collection_start_time >= COLLECTION_DURATION:
        break

    for rec in stream.records():
        for elem in rec:
            Processing logic goes here
            Check if the collection duration has been exceeded inside nested loops
            if time.time() - collection_start_time >= COLLECTION_DURATION:
                break
        else:
            continue
        break
Graceful Shutdown:
Ensure that the script can be stopped gracefully after the specified duration or when a stop event is triggered.

- Main Loop Processing
Do not use any filter attributes like stream.add_filter() or set filter parameters when initializing BGPStream.
All filtering and processing should occur within the main loop where you iterate over records and elements.
for rec in stream.records():
    for elem in rec:
        Processing logic goes here

- Accessing Element Attributes
Timestamp:
from datetime import datetime

elem_time = datetime.utcfromtimestamp(elem.time)
elem_type = elem.type  'A' for announcements, 'W' for withdrawals

Fields Dictionary:
fields = elem.fields

Prefix:
prefix = fields.get("prefix")
if prefix is None:
    continue

AS Path:
as_path_str = fields.get('as-path', "")
as_path = as_path_str.split()

Peer ASN and Collector:
peer_asn = elem.peer_asn
collector = rec.collector

Communities:
communities = fields.get('communities', [])

Validating and Parsing IP Prefixes:
import ipaddress
try:
    network = ipaddress.ip_network(prefix)
except ValueError:
    continue

Filtering Logic Within the Loop
Filtering for a Specific ASN in AS Path:
target_asn = '3356'
if target_asn not in as_path:
    continue

Filtering for Specific Prefixes:
target_prefixes = ['192.0.2.0/24', '198.51.100.0/24']
if prefix not in target_prefixes:
    continue

- Processing Key Values and Attributes
Counting Announcements and Withdrawals:
from collections import defaultdict
announcements = defaultdict(int)
withdrawals = defaultdict(int)

if elem_type == 'A':
    announcements[prefix] += 1
elif elem_type == 'W':
    withdrawals[prefix] += 1

Detecting AS Path Changes:
prefix_as_paths = {}

if prefix in prefix_as_paths:
    if as_path != prefix_as_paths[prefix]:
        # AS path has changed
        # Handle AS path change
        prefix_as_paths[prefix] = as_path
else:
    prefix_as_paths[prefix] = as_path


- Analyzing Community Attributes:
community_counts = defaultdict(int)

for community in communities:
    community_str = f"{community[0]}:{community[1]}"
    community_counts[community_str] += 1

- Calculating Statistics (e.g., Average MED):
med_values = []

med = fields.get('med')
if med is not None:
    try:
        med_values.append(int(med))
    except ValueError:
        pass

Calculate average MED
if med_values:
    average_med = sum(med_values) / len(med_values)
"""
