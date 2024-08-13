import pybgpstream
import re
import time
from datetime import datetime, timedelta
import editdistance
import pandas as pd

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

def build_routes_as(routes):
    routes_as = {}
    for prefix in routes:
        for collector in routes[prefix]:
            for peer_asn in routes[prefix][collector]:
                path = routes[prefix][collector][peer_asn]
                if len(path) == 0:
                    continue
                asn = path[-1]
                if asn not in routes_as:
                    routes_as[asn] = {}
                routes_as[asn][prefix] = path
    return routes_as

def extract_features(index, routes, old_routes_as, target_asn, temp_counts):
    features = {
        "timestamp": None,
        "asn": target_asn,
        "num_routes": 0,
        "num_new_routes": 0,
        "num_withdrawals": 0,
        "num_origin_changes": 0,
        "num_route_changes": 0,
        "max_path_length": 0,
        "avg_path_length": 0,
        "max_edit_distance": 0,
        "avg_edit_distance": 0,
        "num_announcements": temp_counts["num_announcements"],
        "num_withdrawals": temp_counts["num_withdrawals"],
        "num_unique_prefixes_announced": 0
    }

    routes_as = build_routes_as(routes)

    if index > 0:
        if target_asn in routes_as:
            num_routes = len(routes_as[target_asn])
            sum_path_length = 0
            sum_edit_distance = 0

            for prefix in routes_as[target_asn].keys():
                if target_asn in old_routes_as and prefix in old_routes_as[target_asn]:
                    path = routes_as[target_asn][prefix]
                    path_old = old_routes_as[target_asn][prefix]

                    if path != path_old:
                        features["num_route_changes"] += 1

                    if path[-1] != path_old[-1]:
                        features["num_origin_changes"] += 1

                    path_length = len(path)
                    path_old_length = len(path_old)

                    sum_path_length += path_length
                    if path_length > features["max_path_length"]:
                        features["max_path_length"] = path_length

                    edist = editdistance.eval(path, path_old)
                    sum_edit_distance += edist
                    if edist > features["max_edit_distance"]:
                        features["max_edit_distance"] = edist
                else:
                    features["num_new_routes"] += 1

            features["num_routes"] = num_routes
            features["avg_path_length"] = sum_path_length / num_routes
            features["avg_edit_distance"] = sum_edit_distance / num_routes

        if target_asn in old_routes_as:
            for prefix in old_routes_as[target_asn].keys():
                if not (target_asn in routes_as and prefix in routes_as[target_asn]):
                    features["num_withdrawals"] += 1

    features["num_unique_prefixes_announced"] = len(routes_as.get(target_asn, {}))

    return features, routes_as

def extract_bgp_data(target_asn, from_time, until_time, collectors=['rrc00']):
    stream = pybgpstream.BGPStream(
        from_time=from_time,
        until_time=until_time,
        record_type="updates",
        collectors=collectors
    )

    all_features = []
    old_routes_as = {}
    routes = {}
    current_window_start = datetime.strptime(from_time, "%Y-%m-%d %H:%M:%S")
    index = 0

    temp_counts = {
        "num_announcements": 0,
        "num_withdrawals": 0
    }

    record_count = 0
    element_count = 0

    for rec in stream.records():
        record_count += 1
        for elem in rec:
            element_count += 1
            update = elem.fields
            elem_time = datetime.utcfromtimestamp(elem.time)

            if elem_time >= current_window_start + timedelta(minutes=5):
                features, old_routes_as = extract_features(index, routes, old_routes_as, target_asn, temp_counts)
                features['timestamp'] = current_window_start
                all_features.append(features)

                current_window_start += timedelta(minutes=5)
                routes = {}
                index += 1
                temp_counts = {
                    "num_announcements": 0,
                    "num_withdrawals": 0
                }

            prefix = update.get("prefix")
            if prefix is None:
                continue

            peer_asn = update.get("peer_asn", "unknown")
            collector = rec.collector

            if prefix not in routes:
                routes[prefix] = {}
            if collector not in routes[prefix]:
                routes[prefix][collector] = {}

            if elem.type == 'A':
                path = update['as-path'].split()
                if path[-1] == target_asn:
                    routes[prefix][collector][peer_asn] = path
                    temp_counts["num_announcements"] += 1
            elif elem.type == 'W':
                if prefix in routes and collector in routes[prefix]:
                    if peer_asn in routes[prefix][collector]:
                        if routes[prefix][collector][peer_asn][-1] == target_asn:
                            routes[prefix][collector].pop(peer_asn, None)
                            temp_counts["num_withdrawals"] += 1

    # print(f"Total records processed: {record_count}")
    # print(f"Total elements processed: {element_count}")

    features, old_routes_as = extract_features(index, routes, old_routes_as, target_asn, temp_counts)
    features['timestamp'] = current_window_start
    all_features.append(features)

    df_features = pd.json_normalize(all_features, sep='_').fillna(0)
    print(df_features)

    return df_features

def collect_historical_data(asn, from_time_str, until_time_str=None):
    # Collect and analyze data for AS8342 from 2022-03-28 13:00:00 to 2022-03-28 14:00:00
    if asn is None or from_time_str is None:
        print("ASn or start time not provided. Exiting historical data collection.")
        return

    if until_time_str is None:
        until_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"Starting historical data collection for ASn: {asn} from {from_time_str} to {until_time_str}")
    return extract_bgp_data(asn, from_time_str, until_time_str)

def collect_real_time_data(asn):
    # Collect real-time data for AS12345
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
            
            
def split_dataframe(df, split_size=10):
    """
    Split a DataFrame into smaller DataFrames with a specified number of rows.

    Parameters:
    df (pd.DataFrame): The original DataFrame to split.
    split_size (int): The number of rows in each chunk. Default is 10.

    Returns:
    list of pd.DataFrame: A list containing the smaller DataFrames.
    """
    num_chunks = len(df) // split_size + (1 if len(df) % split_size > 0 else 0)
    data_list = [df.iloc[i*split_size:(i+1)*split_size].reset_index(drop=True) for i in range(num_chunks)]
    return data_list


def preprocess_data(data):
    """
    Convert a DataFrame chunk into the specified JSON format for LLM training.

    Parameters:
    data (pd.DataFrame): The DataFrame chunk to convert.

    Returns:
    dict: A dictionary in the specified JSON format.
    """
    input_seg = "[TLE] The section is related to a specific time period of BGP monitoring. Perform BGP analysis with the given data. [TAB] col: | " + " | ".join(data.columns) + " |"
    
    for idx, row in data.iterrows():
        input_seg += " row {}: | ".format(idx+1) + " | ".join([str(x) for x in row.values]) + " | [SEP]"
    
    return input_seg