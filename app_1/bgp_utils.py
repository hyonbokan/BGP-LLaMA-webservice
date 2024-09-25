import pybgpstream
import re
import os
import time
from datetime import datetime, timedelta
import editdistance
import multiprocessing
import uuid
import pandas as pd
import networkx as nx
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

import re
from datetime import timedelta

def extract_real_time_span(query):
    patterns = {
        'minutes': r'((?:\d+|a|an))\s*(?:minute|minutes)\b',
        'hours': r'((?:\d+|a|an))\s*(?:hour|hours)\b',
        'days': r'((?:\d+|a|an))\s*(?:day|days)\b',
        'weeks': r'((?:\d+|a|an))\s*(?:week|weeks)\b'
    }
    
    total_minutes = total_hours = total_days = total_weeks = 0
    
    for unit, pattern in patterns.items():
        matches = re.findall(pattern, query, re.IGNORECASE)
        for match in matches:
            match_lower = match.lower()
            if match_lower in ('a', 'an'):
                value = 1
            else:
                value = int(match)
            if unit == 'minutes':
                total_minutes += value
            elif unit == 'hours':
                total_hours += value
            elif unit == 'days':
                total_days += value
            elif unit == 'weeks':
                total_weeks += value

    # Calculate the total collection period
    total_seconds = (
        (total_minutes * 60) +
        (total_hours * 3600) +
        (total_days * 86400) +
        (total_weeks * 604800)
    )
    
    # If no time span is specified, default to 5 minutes (300 seconds)
    if total_seconds == 0:
        total_seconds = 300
    
    collection_period = timedelta(seconds=total_seconds)
    print(f"\nParsed time span for real-time collection: {collection_period} (total seconds: {total_seconds})")
    return collection_period

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
        "Total Routes": 0,
        "New Routes": temp_counts["num_new_routes"],
        "Withdrawals": temp_counts["num_withdrawals"],
        "Origin Changes": temp_counts["num_origin_changes"],
        "Route Changes": temp_counts["num_route_changes"],
        "Maximum Path Length": 0,
        "Average Path Length": 0,
        "Maximum Edit Distance": 0,
        "Average Edit Distance": 0,
        "Announcements": temp_counts["num_announcements"],
        "Unique Prefixes Announced": 0,
        "Graph Average Degree": 0,
        "Graph Betweenness Centrality": 0,
        "Graph Closeness Centrality": 0,
        "Graph Eigenvector Centrality": 0
    }

    routes_as = build_routes_as(routes)

    if index > 0 and target_asn in routes_as:
        num_routes = len(routes_as[target_asn])
        sum_path_length = 0
        sum_edit_distance = 0

        # Build the graph for the current ASN
        G = nx.Graph()
        for prefix, path in routes_as[target_asn].items():
            for i in range(len(path) - 1):
                G.add_edge(path[i], path[i + 1])

        # Calculate graph features if the graph has nodes
        if G.number_of_nodes() > 0:
            features["Graph Average Degree"] = sum(dict(G.degree).values()) / G.number_of_nodes()
            features["Graph Betweenness Centrality"] = sum(nx.betweenness_centrality(G).values()) / G.number_of_nodes()
            features["Graph Closeness Centrality"] = sum(nx.closeness_centrality(G).values()) / G.number_of_nodes()
            features["Graph Eigenvector Centrality"] = sum(nx.eigenvector_centrality(G).values()) / G.number_of_nodes()

        for prefix in routes_as[target_asn].keys():
            path = routes_as[target_asn][prefix]
            if target_asn in old_routes_as and prefix in old_routes_as[target_asn]:
                path_old = old_routes_as[target_asn][prefix]

                if path != path_old:
                    features["Route Changes"] += 1  # Already counted in temp_counts
                if path[-1] != path_old[-1]:
                    features["Origin Changes"] += 1  # Already counted in temp_counts

                path_length = len(path)
                sum_path_length += path_length
                edist = editdistance.eval(path, path_old)
                sum_edit_distance += edist
                features["Maximum Path Length"] = max(features["Maximum Path Length"], path_length)
                features["Maximum Edit Distance"] = max(features["Maximum Edit Distance"], edist)

        features["Total Routes"] = num_routes
        features["Average Path Length"] = sum_path_length / num_routes if num_routes else 0
        features["Average Edit Distance"] = sum_edit_distance / num_routes if num_routes else 0

    features["Unique Prefixes Announced"] = len(routes_as.get(target_asn, {}))

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
    os.makedirs(media_dir, exist_ok=True)
    
    # Check if the directory exists
    if not os.path.exists(media_dir):
        raise OSError(f"Failed to create directory: {media_dir}")
    print(f"\nDirectory created: {media_dir}")

    # Define the file name and path inside the new directory
    file_name = f"bgp_data_{data_uuid}.csv"
    file_path = os.path.join(media_dir, file_name)
    print(f"\nFile will be saved to: {file_path}")

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

    # Update temp_counts to match extract_features
    temp_counts = {
        "num_announcements": 0,
        "num_withdrawals": 0,
        "num_new_routes": 0,
        "num_origin_changes": 0,
        "num_route_changes": 0
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

            # If the time exceeds the 5-minute window, process the window and reset
            if elem_time >= current_window_start + timedelta(minutes=5):
                features, old_routes_as = extract_features(
                    index, routes, old_routes_as, target_asn, temp_counts
                )
                features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
                all_features.append(features)

                # Move to the next 5-minute window
                current_window_start += timedelta(minutes=5)
                routes = {}  # Reset the routes for the next window
                index += 1
                temp_counts = {
                    "num_announcements": 0,
                    "num_withdrawals": 0,
                    "num_new_routes": 0,
                    "num_origin_changes": 0,
                    "num_route_changes": 0
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

            # Processing Announcements (A) and Withdrawals (W)
            if elem.type == 'A':
                as_path = update.get('as-path')
                if as_path:
                    path = as_path.split()
                    if path[-1] == target_asn:
                        # Check if it's a new route
                        if prefix not in routes or collector not in routes[prefix] or peer_asn not in routes[prefix][collector]:
                            temp_counts["num_new_routes"] += 1

                        # Compare with old routes for changes
                        if target_asn in old_routes_as and prefix in old_routes_as.get(target_asn, {}):
                            old_path = old_routes_as[target_asn][prefix]
                            if path != old_path:
                                temp_counts["num_route_changes"] += 1
                            if path[-1] != old_path[-1]:
                                temp_counts["num_origin_changes"] += 1

                        # Update the route
                        routes[prefix][collector][peer_asn] = path
                        temp_counts["num_announcements"] += 1
            elif elem.type == 'W':
                if prefix in routes and collector in routes[prefix]:
                    if peer_asn in routes[prefix][collector]:
                        if routes[prefix][collector][peer_asn][-1] == target_asn:
                            routes[prefix][collector].pop(peer_asn, None)
                            temp_counts["num_withdrawals"] += 1

        # Handle time windows where no new data comes in
        while elem_time >= current_window_start + timedelta(minutes=5):
            features, old_routes_as = extract_features(
                index, routes, old_routes_as, target_asn, temp_counts
            )
            features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
            all_features.append(features)

            current_window_start += timedelta(minutes=5)
            routes = {}
            index += 1
            temp_counts = {
                "num_announcements": 0,
                "num_withdrawals": 0,
                "num_new_routes": 0,
                "num_origin_changes": 0,
                "num_route_changes": 0
            }

    print(f"Total records processed: {record_count}")
    print(f"Total elements processed: {element_count}")

    # Capture any remaining features after the final time window
    features, old_routes_as = extract_features(
        index, routes, old_routes_as, target_asn, temp_counts
    )
    features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
    all_features.append(features)

    # Convert collected features to a DataFrame
    df_features = pd.json_normalize(all_features, sep='_').fillna(0)
    print(df_features.columns)
    print(df_features)

    try:
        df_features.to_csv(file_path, index=False)
        print(f"Data saved to {file_path} in {media_dir}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")

    return media_dir

def collect_historical_data(asn, from_time_str, until_time_str=None):
    if asn is None or from_time_str is None:
        print("ASn or start time not provided. Exiting historical data collection.")
        return

    if until_time_str is None:
        until_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return extract_bgp_data(asn, from_time_str, until_time_str)

def convert_lists_to_tuples(df):
    # Identify columns that contain list values
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(tuple)
    return df

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
        "num_announcements": 0,
        "num_withdrawals": 0,
        "num_new_routes": 0,
        "num_origin_changes": 0,
        "num_route_changes": 0
    }
    
    try:
        for rec in stream.records():
            current_time = datetime.utcnow()

            if time.time() - start_time >= collection_period.total_seconds():
                print("Collection period ended. Processing data...")
                break

            try:
                for elem in rec:
                    as_path = elem.fields.get('as-path', '').split()
                    prefix = elem.fields.get('prefix')
                    if not prefix:
                        continue
                    
                    if asn in as_path:
                        collector = rec.collector
                        peer_asn = elem.peer_asn

                        if prefix not in routes:
                            routes[prefix] = {}
                        if collector not in routes[prefix]:
                            routes[prefix][collector] = {}

                        if elem.type == 'A':
                            path = as_path
                            # Check if it's a new route
                            if peer_asn not in routes[prefix][collector]:
                                temp_counts["num_new_routes"] += 1

                            # Compare with old routes for changes
                            if asn in old_routes_as and prefix in old_routes_as.get(asn, {}):
                                old_path = old_routes_as[asn][prefix]
                                if path != old_path:
                                    temp_counts["num_route_changes"] += 1
                                if path[-1] != old_path[-1]:
                                    temp_counts["num_origin_changes"] += 1

                            routes[prefix][collector][peer_asn] = path
                            temp_counts["num_announcements"] += 1
                            
                        elif elem.type == 'W':
                            if peer_asn in routes[prefix][collector]:
                                if routes[prefix][collector][peer_asn][-1] == asn:
                                    del routes[prefix][collector][peer_asn]
                                    temp_counts["num_withdrawals"] += 1

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
                features, old_routes_as = extract_features(
                    index, routes, old_routes_as, asn, temp_counts
                )
                features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
                all_features.append(features)

                # Update return_dict with real-time data
                return_dict['features_df'] = pd.DataFrame(all_features).dropna(axis=1, how='all')

                current_window_start = current_window_start + timedelta(minutes=1)
                routes = {}
                index += 1
                # Reset temp_counts for the next window
                temp_counts = {
                    "num_announcements": 0,
                    "num_withdrawals": 0,
                    "num_new_routes": 0,
                    "num_origin_changes": 0,
                    "num_route_changes": 0
                }
                
        if routes:
            features, old_routes_as = extract_features(
                index, routes, old_routes_as, asn, temp_counts
            )
            features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
            all_features.append(features)
            return_dict['features_df'] = pd.DataFrame(all_features).dropna(axis=1, how='all')

    except Exception as e:
        error_message = f"An error occurred during real-time data collection for {asn}: {e}"
        print(error_message)
        return_dict['error'] = error_message
        if all_features:
            return_dict['features_df'] = pd.DataFrame(all_features).dropna(axis=1, how='all')

def collect_real_time_data(asn, collection_period=300):
    all_collected_data = []  # List to store all collected DataFrames
    features_df = pd.DataFrame()

    # Generate a unique UUID for the real-time data session
    data_uuid = uuid.uuid4()

    media_dir = os.path.join(settings.MEDIA_ROOT, 'rag_bgp_data', str(data_uuid))
    os.makedirs(media_dir, exist_ok=True)  # Ensure the directory exists
    file_name = f"bgp_real_time_data_{data_uuid}.csv"
    file_path = os.path.join(media_dir, file_name)

    print(f"\nCollecting data for ASN {asn} for {collection_period//60} minutes...")

    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p = multiprocessing.Process(target=run_real_time_bgpstream, args=(asn, collection_period, return_dict))
    p.start()

    start_time = time.time()
    last_features_df = pd.DataFrame()

    while time.time() - start_time < collection_period.total_seconds() + 5:
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
                remaining_time = collection_period.total_seconds() - (time.time() - start_time)
                if remaining_time <= 0:
                    print("No remaining time left for data collection. Exiting.")
                    break

                # Restart the process with the remaining collection period
                p.terminate()
                p.join()
                p = multiprocessing.Process(target=run_real_time_bgpstream, args=(asn, timedelta(seconds=remaining_time), return_dict))
                p.start()

            # Update last_features_df to the current state for the next check
            last_features_df = features_df.copy()

        time.sleep(63)

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

    # Save the final DataFrame to a CSV file
    final_features_df.to_csv(file_path, index=False)
    print(f"\nFinal data saved to {file_path}\n")
    
    return media_dir


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
        row_description = f"At {row['Timestamp']}, AS{row['Autonomous System Number']} observed {row['Announcements']} announcements"
        
        if 'Withdrawals' in df.columns and row['Withdrawals'] > 0:
            row_description += f" and {row['Withdrawals']} withdrawals"
        
        if 'New Routes' in df.columns and row['New Routes'] > 0:
            row_description += f". There were {row['New Routes']} new routes added"
        
        if 'Origin Changes' in df.columns and row['Origin Changes'] > 0:
            row_description += f", with {row['Origin Changes']} origin changes"
        
        if 'Route Changes' in df.columns and row['Route Changes'] > 0:
            row_description += f" and {row['Route Changes']} route changes"
        
        if 'Total Routes' in df.columns:
            row_description += f". A total of {row['Total Routes']} routes were active"

        if 'Maximum Path Length' in df.columns:
            row_description += f", with a maximum path length of {row['Maximum Path Length']}"
        
        if 'Average Path Length' in df.columns:
            row_description += f" and an average path length of {row['Average Path Length']}"
        
        if 'Maximum Edit Distance' in df.columns:
            row_description += f". The maximum edit distance observed was {row['Maximum Edit Distance']}"
        
        if 'Average Edit Distance' in df.columns:
            row_description += f" with an average edit distance of {row['Average Edit Distance']}"
        
        if 'Unique Prefixes Announced' in df.columns:
            row_description += f". There were {row['Unique Prefixes Announced']} unique prefixes announced"

        # Add graph-related features if available
        if 'Graph Average Degree' in df.columns:
            row_description += f". The graph's average degree was {row['Graph Average Degree']}"
        
        if 'Graph Betweenness Centrality' in df.columns:
            row_description += f", betweenness centrality was {row['Graph Betweenness Centrality']}"
        
        if 'Graph Closeness Centrality' in df.columns:
            row_description += f", closeness centrality was {row['Graph Closeness Centrality']}"
        
        if 'Graph Eigenvector Centrality' in df.columns:
            row_description += f", and eigenvector centrality was {row['Graph Eigenvector Centrality']}"
        
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
