import pybgpstream
import re
import time
from datetime import datetime

def extract_asn(query):
    match = re.search(r'\bAS(\d+)\b', query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def extract_times(query):
    matches = re.findall(r'\b(\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2})\b', query)
    from_time = matches[0] if matches else None
    until_time = matches[1] if len(matches) > 1 else None
    return from_time, until_time

def collect_historical_data(asn, from_time_str, until_time_str):
    if asn is None or from_time_str is None:
        print("ASn or start time not provided. Exiting historical data collection.")
        return

    if until_time_str is None:
        until_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"Starting historical data collection for ASn: {asn} from {from_time_str} to {until_time_str}")
    

def collect_real_time_data(asn):
    if asn is None:
        print("ASn not provided. Exiting real-time collection.")
        return

    print(f"Starting real-time data collection for ASn: {asn}")

    # Create a BGPStream instance
    stream = pybgpstream.BGPStream(
        project="ris-live",
        record_type="updates",
    )

    # Record the start time
    start_time = time.time()
    collection_period = 60  # Example collection period in seconds

    # Start the live stream
    for rec in stream.records():
        # Check if the collection period has elapsed
        if collection_period < time.time() - start_time:
            print("Collection period ended. Processing data...")
            break

        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(rec.time))
        for elem in rec:
            print(f"Time: {current_time}, Element: {elem}")