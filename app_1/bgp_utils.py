import pybgpstream
import re
import os
import time
from datetime import datetime, timedelta
import editdistance
import multiprocessing
import uuid
import pandas as pd
from django.conf import settings

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
        "Timestamp": None,
        "Autonomous System Number": target_asn,
        "Number of Routes": 0,
        "Number of New Routes": 0,
        "Number of Withdrawals": 0,
        "Number of Origin Changes": 0,
        "Number of Route Changes": 0,
        "Maximum Path Length": 0,
        "Average Path Length": 0,
        "Maximum Edit Distance": 0,
        "Average Edit Distance": 0,
        "Number of Announcements": temp_counts["Number of Announcements"],
        "Total Withdrawals": temp_counts["Total Withdrawals"],
        "Number of Unique Prefixes Announced": 0,
        "Paths": []
    }

    routes_as = build_routes_as(routes)

    if index > 0:
        if target_asn in routes_as:
            num_routes = len(routes_as[target_asn])
            sum_path_length = 0
            sum_edit_distance = 0

            for prefix in routes_as[target_asn].keys():
                path = routes_as[target_asn][prefix]

                # Convert the path list to a string and store it in the features list
                features["Paths"].append(f"{prefix}: {' '.join(path)}")

                if target_asn in old_routes_as and prefix in old_routes_as[target_asn]:
                    path_old = old_routes_as[target_asn][prefix]

                    if path != path_old:
                        features["Number of Route Changes"] += 1

                    if path[-1] != path_old[-1]:
                        features["Number of Origin Changes"] += 1

                    path_length = len(path)
                    path_old_length = len(path_old)

                    sum_path_length += path_length
                    if path_length > features["Maximum Path Length"]:
                        features["Maximum Path Length"] = path_length

                    edist = editdistance.eval(path, path_old)
                    sum_edit_distance += edist
                    if edist > features["Maximum Edit Distance"]:
                        features["Maximum Edit Distance"] = edist
                else:
                    features["Number of New Routes"] += 1

            features["Number of Routes"] = num_routes
            features["Average Path Length"] = sum_path_length / num_routes
            features["Average Edit Distance"] = sum_edit_distance / num_routes

        if target_asn in old_routes_as:
            for prefix in old_routes_as[target_asn].keys():
                if not (target_asn in routes_as and prefix in routes_as[target_asn]):
                    features["Total Withdrawals"] += 1

    features["Number of Unique Prefixes Announced"] = len(routes_as.get(target_asn, {}))

    return features, routes_as


# def extract_bgp_data(target_asn, from_time, until_time):
#     stream = pybgpstream.BGPStream(
#         from_time=from_time,
#         until_time=until_time,
#         record_type="updates",
#         collectors=['rrc00']
#     )

#     all_features = []
#     old_routes_as = {}
#     routes = {}
#     current_window_start = datetime.strptime(from_time, "%Y-%m-%d %H:%M:%S")
#     index = 0

#     temp_counts = {
#         "Number of Announcements": 0,
#         "Total Withdrawals": 0
#     }

#     record_count = 0
#     element_count = 0

#     print(f"Starting BGP data extraction for ASN {target_asn} from {from_time} to {until_time}")

#     for rec in stream.records():
#         record_count += 1
#         for elem in rec:
#             element_count += 1
#             update = elem.fields
#             elem_time = datetime.utcfromtimestamp(elem.time)

#             if elem_time >= current_window_start + timedelta(minutes=5):
#                 features, old_routes_as = extract_features(index, routes, old_routes_as, target_asn, temp_counts)
#                 features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
#                 all_features.append(features)

#                 current_window_start += timedelta(minutes=5)
#                 routes = {}
#                 index += 1
#                 temp_counts = {
#                     "Number of Announcements": 0,
#                     "Total Withdrawals": 0
#                 }

#             prefix = update.get("prefix")
#             if prefix is None:
#                 continue

#             peer_asn = update.get("peer_asn", "unknown")
#             collector = rec.collector

#             if prefix not in routes:
#                 routes[prefix] = {}
#             if collector not in routes[prefix]:
#                 routes[prefix][collector] = {}

#             if elem.type == 'A':
#                 as_path = update.get('as-path')
#                 if as_path:
#                     path = as_path.split()
#                     if path[-1] == target_asn:
#                         routes[prefix][collector][peer_asn] = path
#                         temp_counts["Number of Announcements"] += 1
#             elif elem.type == 'W':
#                 if prefix in routes and collector in routes[prefix]:
#                     if peer_asn in routes[prefix][collector]:
#                         if routes[prefix][collector][peer_asn][-1] == target_asn:
#                             routes[prefix][collector].pop(peer_asn, None)
#                             temp_counts["Total Withdrawals"] += 1

#     print(f"Total records processed: {record_count}")
#     print(f"Total elements processed: {element_count}")

#     features, old_routes_as = extract_features(index, routes, old_routes_as, target_asn, temp_counts)
#     features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
#     all_features.append(features)

#     df_features = pd.json_normalize(all_features, sep='_').fillna(0)
#     print(df_features.columns)
#     print(df_features)
#     return df_features

def extract_bgp_data(target_asn, from_time, until_time):
    # Generate a unique UUID for the dataset
    data_uuid = uuid.uuid4()

    # Define the output path in the media directory
    media_dir = os.path.join(settings.MEDIA_ROOT, 'rag_bgp_data', str(data_uuid))
    os.makedirs(media_dir, exist_ok=True)  # Ensure the directory exists

    # Define the file name and path inside the new directory
    file_name = f"bgp_data_{data_uuid}.csv"
    file_path = os.path.join(media_dir, file_name)

    stream = pybgpstream.BGPStream(
        from_time=from_time,
        until_time=until_time,
        record_type="updates",
        collectors=['rrc00']
    )

    all_features = []
    old_routes_as = {}
    routes = {}
    current_window_start = datetime.strptime(from_time, "%Y-%m-%d %H:%M:%S")
    index = 0

    temp_counts = {
        "Number of Announcements": 0,
        "Total Withdrawals": 0
    }

    record_count = 0
    element_count = 0

    print(f"Starting BGP data extraction for ASN {target_asn} from {from_time} to {until_time}")

    for rec in stream.records():
        record_count += 1
        for elem in rec:
            element_count += 1
            update = elem.fields
            elem_time = datetime.utcfromtimestamp(elem.time)

            if elem_time >= current_window_start + timedelta(minutes=5):
                features, old_routes_as = extract_features(index, routes, old_routes_as, target_asn, temp_counts)
                features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
                all_features.append(features)

                current_window_start += timedelta(minutes=5)
                routes = {}
                index += 1
                temp_counts = {
                    "Number of Announcements": 0,
                    "Total Withdrawals": 0
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
                as_path = update.get('as-path')
                if as_path:
                    path = as_path.split()
                    if path[-1] == target_asn:
                        routes[prefix][collector][peer_asn] = path
                        temp_counts["Number of Announcements"] += 1
            elif elem.type == 'W':
                if prefix in routes and collector in routes[prefix]:
                    if peer_asn in routes[prefix][collector]:
                        if routes[prefix][collector][peer_asn][-1] == target_asn:
                            routes[prefix][collector].pop(peer_asn, None)
                            temp_counts["Total Withdrawals"] += 1

    print(f"Total records processed: {record_count}")
    print(f"Total elements processed: {element_count}")

    # Capture any remaining features after the final time window
    features, old_routes_as = extract_features(index, routes, old_routes_as, target_asn, temp_counts)
    features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
    all_features.append(features)

    # Convert collected features to a DataFrame
    df_features = pd.json_normalize(all_features, sep='_').fillna(0)
    print(df_features.columns)
    print(df_features)

    # Save the DataFrame to a CSV file inside the newly created directory
    df_features.to_csv(file_path, index=False)
    print(f"Data saved to {file_path} in {media_dir}")

    # Return the directory path (not the file path)
    return media_dir

def collect_historical_data(asn, from_time_str, until_time_str=None):
    if asn is None or from_time_str is None:
        print("ASn or start time not provided. Exiting historical data collection.")
        return

    if until_time_str is None:
        until_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return extract_bgp_data(asn, from_time_str, until_time_str)

def run_real_time_bgpstream(asn, collection_period, return_dict):
    all_features = []
    stream = pybgpstream.BGPStream(
        project="ris-live",
        record_type="updates",
    )

    start_time = time.time()
    current_window_start = datetime.utcnow()
    index = 0
    old_routes_as = {}
    routes = {}
    temp_counts = {
        "Number of Announcements": 0,
        "Total Withdrawals": 0
    }
    
    try:
        for rec in stream.records():
            current_time = datetime.utcnow()

            if time.time() - start_time >= collection_period:
                print("Collection period ended. Processing data...")
                break

            try:
                for elem in rec:
                    as_path = elem.fields.get('as-path', '').split()
                    prefix = elem.fields.get('prefix')

                    # Process announcements and withdrawals involving the target ASN
                    if asn in as_path:
                        if elem.type == 'A':  # Announcement
                            if prefix not in routes:
                                routes[prefix] = {}
                            if rec.collector not in routes[prefix]:
                                routes[prefix][rec.collector] = {}
                            routes[prefix][rec.collector][elem.peer_asn] = as_path
                            temp_counts["Number of Announcements"] += 1

                        elif elem.type == 'W':  # Withdrawal
                            if prefix in routes:
                                if rec.collector in routes[prefix]:
                                    if elem.peer_asn in routes[prefix][rec.collector]:
                                        del routes[prefix][rec.collector][elem.peer_asn]
                                        temp_counts["Total Withdrawals"] += 1

            except KeyError as ke:
                print(f"KeyError processing record: {ke}. Continuing with the next record.")
                continue
            
            except ValueError as ve:
                print(f"ValueError processing record: {ve}. Continuing with the next record.")
                continue

            except Exception as e:
                print(f"Unexpected error processing record: {e}. Continuing with the next record.")
                continue

            # Time window check: aggregate and reset every 1 minute
            if current_time >= current_window_start + timedelta(minutes=1):
                print(f"Reached time window: {current_window_start} to {current_time}")

                # Extract features, including paths
                features, old_routes_as = extract_features(index, routes, old_routes_as, asn, temp_counts)
                features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
                all_features.append(features)

                # Update return_dict with real-time data
                return_dict['features_df'] = pd.DataFrame(all_features).dropna(axis=1, how='all')

                # Log update and prepare for the next minute
                next_window_start = current_window_start + timedelta(minutes=1)
                print(f"\n\nUpdate from {current_window_start} to {next_window_start}: {all_features[-1]}\n\n")

                current_window_start = next_window_start
                routes = {}
                index += 1
                temp_counts = {
                    "Number of Announcements": 0,
                    "Total Withdrawals": 0
                }

        # Final extraction for any remaining data after the collection period ends
        if routes:
            features, old_routes_as = extract_features(index, routes, old_routes_as, asn, temp_counts)
            features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
            all_features.append(features)
            return_dict['features_df'] = pd.DataFrame(all_features).dropna(axis=1, how='all')

    except Exception as e:
        error_message = f"An error occurred during real-time data collection for {asn}: {e}"
        print(error_message)
        return_dict['error'] = error_message
        if all_features:
            return_dict['features_df'] = pd.DataFrame(all_features).dropna(axis=1, how='all')



def convert_lists_to_tuples(df):
    # Identify columns that contain list values
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            # Convert the list values to tuples (hashable type)
            df[col] = df[col].apply(tuple)
    return df

def collect_real_time_data(asn, collection_period=300):
    all_collected_data = []  # List to store all collected DataFrames
    features_df = pd.DataFrame()

    print(f"\nCollecting data for ASN {asn} for {collection_period//60} minutes...")

    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p = multiprocessing.Process(target=run_real_time_bgpstream, args=(asn, collection_period, return_dict))
    p.start()

    start_time = time.time()
    last_features_df = pd.DataFrame()  # Initialize with an empty DataFrame

    while time.time() - start_time < collection_period + 5:
        if 'error' in return_dict:
            print(f"Real-time data collection encountered an error: {return_dict['error']}")
            features_df = return_dict.get('features_df', pd.DataFrame())
            break

        features_df = return_dict.get('features_df', pd.DataFrame())

        if not features_df.empty:
            print(f"\nUpdated features_df at {datetime.utcnow()}:\n{features_df.tail(1)}\n")

            # Save the current features_df to the list
            all_collected_data.append(features_df.copy())

            # Check if the DataFrame hasn't changed in the last n seconds
            if not last_features_df.empty and features_df.equals(last_features_df):
                print("No changes in data for the last few seconds. Restarting data collection...")

                # Calculate remaining time for the collection
                remaining_time = collection_period - (time.time() - start_time)
                if remaining_time <= 0:
                    print("No remaining time left for data collection. Exiting.")
                    break

                # Restart the process with the remaining collection period
                p.terminate()
                p.join()
                p = multiprocessing.Process(target=run_real_time_bgpstream, args=(asn, remaining_time, return_dict))
                p.start()

            # Update last_features_df to the current state for the next check
            last_features_df = features_df.copy()

        time.sleep(63)  # Check for updates every n seconds

    if p.is_alive():
        print("BGPStream collection timed out. Terminating process...")
        p.terminate()
        p.join()

    # Concatenate all collected DataFrames into one final DataFrame
    if all_collected_data:
        final_features_df = pd.concat(all_collected_data, ignore_index=True)
    else:
        final_features_df = features_df

    # Convert list columns to tuples before removing duplicates
    final_features_df = convert_lists_to_tuples(final_features_df)

    # Remove duplicates from the final DataFrame
    final_features_df = final_features_df.drop_duplicates()

    print(f"\nFinal features df: {final_features_df}\n")
    return final_features_df


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


def dataframe_to_tab(data):
    """
    Convert a DataFrame chunk into the specified JSON format for LLM training.

    Parameters:
    data (pd.DataFrame): The DataFrame chunk to convert.

    Returns:
    dict: A dictionary in the specified JSON format.
    """
    input_seg = "[TLE] The context is about BGP update message for analysis. The section is related to a specific time period of BGP monitoring. [TAB] col: | " + " | ".join(data.columns) + " |"
    
    for idx, row in data.iterrows():
        input_seg += "row {}: | ".format(idx+1) + " | ".join([str(x) for x in row.values]) + " | [SEP]"
    
    return input_seg

def split_dataframe(df, split_size):
    """
    Split DataFrame into smaller DataFrames of specified size.

    Parameters:
    df (pd.DataFrame): The DataFrame to split.
    split_size (int): The number of rows per split.

    Returns:
    list: A list of DataFrames.
    """
    return [df.iloc[i:i + split_size] for i in range(0, len(df), split_size)]

def dataframe_to_string(data):
    """
    Convert a DataFrame into a formatted string with tab-separated values.

    Parameters:
    data (pd.DataFrame): The DataFrame to convert.

    Returns:
    str: A string representation of the DataFrame.
    """
    # Create a list to hold the lines of the formatted string
    lines = []

    # Add the header line
    header = "\t".join(data.columns)
    lines.append(header)

    # Add each row
    for _, row in data.iterrows():
        row_str = "\t".join([str(item) for item in row])
        lines.append(row_str)

    # Join all lines into a single string with newline separators
    df_string = "\n".join(lines)
    
    return df_string

def dataframe_to_tabular_string(df):
    """
    Convert a pandas DataFrame into a simple tabular string representation.

    Parameters:
    df (pd.DataFrame): The DataFrame to convert.

    Returns:
    str: A string representing the DataFrame in a tabular format.
    """

    # Create the header row
    header = " | ".join(df.columns)

    # Create the separator row
    separator = " | ".join(["-" * len(col) for col in df.columns])

    # Create the data rows
    data_rows = []
    for idx, row in df.iterrows():
        row_string = " | ".join([str(val) for val in row.values])
        data_rows.append(row_string)

    # Combine all parts into the final string
    tabular_string = f"{header}\n{separator}\n" + "\n".join(data_rows)

    return tabular_string


def df_to_plain_text_description(df):
    """
    Convert a DataFrame into a plain text description.

    Parameters:
    df (pd.DataFrame): The DataFrame to convert.

    Returns:
    str: A plain text description of the DataFrame content.
    """
    description = ""

    for index, row in df.iterrows():
        row_description = f"At {row['Timestamp']}, AS{row['Autonomous System Number']} observed {row['Number of Announcements']} announcements"
        
        if 'Number of Withdrawals' in df.columns:
            row_description += f" and {row['Number of Withdrawals']} withdrawals"

        if 'Number of Origin Changes' in df.columns and row['Number of Origin Changes'] > 0:
            row_description += f". There were {row['Number of Origin Changes']} origin changes"
        
        if 'Number of Route Changes' in df.columns and row['Number of Route Changes'] > 0:
            row_description += f" and {row['Number of Route Changes']} route changes"
        
        if 'Maximum Path Length' in df.columns:
            row_description += f". The maximum path length was {row['Maximum Path Length']}"
        
        if 'Average Path Length' in df.columns:
            row_description += f" with an average path length of {row['Average Path Length']}"
        
        if 'Maximum Edit Distance' in df.columns:
            row_description += f". The maximum edit distance observed was {row['Maximum Edit Distance']}"
        
        if 'Average Edit Distance' in df.columns:
            row_description += f" with an average edit distance of {row['Average Edit Distance']}"
        
        if 'Number of Unique Prefixes Announced' in df.columns:
            row_description += f". There were {row['Number of Unique Prefixes Announced']} unique prefixes announced"

        row_description += "."
        description += row_description + "\n"
    
    return description.strip()

def process_dataframe(df):
    """
    Process a DataFrame by splitting it into chunks and converting each chunk to a string.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.

    Returns:
    list: A list of strings, each representing a chunk of the DataFrame.
    """
    chunks = split_dataframe(df, split_size=20)
    processed_data = []
    for chunk in chunks:
        processed_data.append(dataframe_to_tab(chunk))
    return processed_data
