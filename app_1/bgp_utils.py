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
from collections import defaultdict, Counter
import ipaddress
from .preprocessing_data import process_bgp

def initialize_temp_counts():
    return {
        "num_announcements": 0,
        "num_withdrawals": 0,
        "num_new_routes": 0,
        "num_origin_changes": 0,
        "num_route_changes": 0,
        "prefixes_announced": {},
        "prefixes_withdrawn": {},
        "as_path_prepending": 0,
        "bogon_prefixes": 0,
        "total_communities": 0,
        "unique_communities": set()
    }
    
def extract_asn(query):
    match = re.search(r'\bAS(\d+)\b', query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def extract_target_prefixes(query):
    # IPv4 pattern matching IP addresses with CIDR notation
    ipv4_pattern = (
        r'\b'  # Word boundary
        r'(?:'
            r'(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.'  # First octet
            r'(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.'  # Second octet
            r'(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.'  # Third octet
            r'(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)'     # Fourth octet
        r')'
        r'/\d{1,2}'  # CIDR notation
        r'\b'
    )

    # Adjusted IPv6 pattern to avoid matching times
    ipv6_pattern = (
        r'\b'  # Word boundary
        r'(?:'
            r'(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}'            # Full IPv6 address
            r'|'
            r'(?:[A-Fa-f0-9]{1,4}:){1,7}:'                         # Addresses ending with ::
            r'|'
            r'::(?:[A-Fa-f0-9]{1,4}:){1,6}[A-Fa-f0-9]{1,4}'        # Addresses starting with ::
            r'|'
            r'(?:[A-Fa-f0-9]{1,4}:){1,6}:[A-Fa-f0-9]{1,4}'         # Addresses with a single ::
        r')'
        r'(?:/\d{1,3})?'  # Optional CIDR notation
        r'\b'
    )

    # Combine both IPv4 and IPv6 patterns
    combined_pattern = f'({ipv4_pattern})|({ipv6_pattern})'

    # Search the query for both IPv4 and IPv6 prefixes
    matches = re.findall(combined_pattern, query)

    # Extract non-empty matches and validate them
    prefixes = []
    for ipv4_match, ipv6_match in matches:
        prefix = ipv4_match or ipv6_match
        try:
            ipaddress.ip_network(prefix, strict=False)
            prefixes.append(prefix)
        except ValueError:
            continue  # Invalid IP prefix, ignore it

    return prefixes if prefixes else None

def extract_times(query):
    matches = re.findall(r'\b(\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2})\b', query)
    from_time = matches[0] if matches else None
    until_time = matches[1] if len(matches) > 1 else None
    return from_time, until_time

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

def build_routes_as(routes, target_asn):
    routes_as = {}
    for prefix in routes:
        for collector in routes[prefix]:
            for peer_asn in routes[prefix][collector]:
                path = routes[prefix][collector][peer_asn]
                if len(path) == 0:
                    continue
                if target_asn in path:
                    if target_asn not in routes_as:
                        routes_as[target_asn] = {}
                    routes_as[target_asn][prefix] = path
    return routes_as

def is_bogon_prefix(prefix):
    # List of bogon prefixes for IPv4
    bogon_ipv4_prefixes = [
        '0.0.0.0/8',
        '10.0.0.0/8',
        '100.64.0.0/10',
        '127.0.0.0/8',
        '169.254.0.0/16',
        '172.16.0.0/12',
        '192.0.0.0/24',
        '192.0.2.0/24',
        '192.168.0.0/16',
        '198.18.0.0/15',
        '198.51.100.0/24',
        '203.0.113.0/24',
        '224.0.0.0/4',
        '240.0.0.0/4'
    ]

    # List of bogon prefixes for IPv6
    bogon_ipv6_prefixes = [
        '::/128',           # Unspecified address
        '::1/128',          # Loopback address
        '::ffff:0:0/96',    # IPv4-mapped addresses
        '64:ff9b::/96',     # IPv4/IPv6 translation
        '100::/64',         # Discard prefix
        '2001:db8::/32',    # Documentation prefix
        'fc00::/7',         # Unique local addresses
        'fe80::/10',        # Link-local addresses
        'ff00::/8',         # Multicast addresses
        # Add more bogon IPv6 prefixes as needed
    ]

    try:
        network = ipaddress.ip_network(prefix, strict=False)
        if network.version == 4:
            for bogon in bogon_ipv4_prefixes:
                bogon_network = ipaddress.ip_network(bogon)
                if network.overlaps(bogon_network):
                    return True
        elif network.version == 6:
            for bogon in bogon_ipv6_prefixes:
                bogon_network = ipaddress.ip_network(bogon)
                if network.overlaps(bogon_network):
                    return True
        else:
            # Unknown IP version, consider as non-bogon
            return False
    except ValueError:
        # Invalid IP address format
        return False
    return False

def summarize_peer_updates(peer_updates):
    if not peer_updates:
        return {
            "Total Updates": 0,
            "Average Updates per Peer": 0,
            "Max Updates from a Single Peer": 0,
            "Min Updates from a Single Peer": 0,
            "Std Dev of Updates": 0
        }
    
    total_updates = sum(peer_updates.values())
    num_peers = len(peer_updates)
    avg_updates = total_updates / num_peers if num_peers else 0
    max_updates = max(peer_updates.values()) if peer_updates else 0
    min_updates = min(peer_updates.values()) if peer_updates else 0
    std_dev_updates = (sum((x - avg_updates) ** 2 for x in peer_updates.values()) / num_peers) ** 0.5 if num_peers else 0
    
    return {
        "Total Updates": total_updates,
        "Average Updates per Peer": avg_updates,
        "Max Updates from a Single Peer": max_updates,
        "Min Updates from a Single Peer": min_updates,
        "Std Dev of Updates": std_dev_updates
    }

def top_n_peer_updates(peer_updates, n=5):
    sorted_peers = sorted(peer_updates.items(), key=lambda item: item[1], reverse=True)
    top_peers = sorted_peers[:n]
    return {f"Top Peer {i+1} ASN": peer for i, (peer, _) in enumerate(top_peers)}

def summarize_prefix_announcements(prefix_announced):
    if not prefix_announced:
        return {
            "Total Prefixes Announced": 0,
            "Average Announcements per Prefix": 0,
            "Max Announcements for a Single Prefix": 0,
            "Min Announcements for a Single Prefix": 0,
            "Std Dev of Announcements": 0
        }
    
    total_announcements = sum(prefix_announced.values())
    num_prefixes = len(prefix_announced)
    avg_announcements = total_announcements / num_prefixes if num_prefixes else 0
    max_announcements = max(prefix_announced.values()) if prefix_announced else 0
    min_announcements = min(prefix_announced.values()) if prefix_announced else 0
    std_dev_announcements = (sum((x - avg_announcements) ** 2 for x in prefix_announced.values()) / num_prefixes) ** 0.5 if num_prefixes else 0
    
    return {
        "Total Prefixes Announced": num_prefixes,
        "Average Announcements per Prefix": avg_announcements,
        "Max Announcements for a Single Prefix": max_announcements,
        "Min Announcements for a Single Prefix": min_announcements,
        "Std Dev of Announcements": std_dev_announcements
    }

def top_n_prefix_announcements(prefix_announced, n=5):
    sorted_prefixes = sorted(prefix_announced.items(), key=lambda item: item[1], reverse=True)
    top_prefixes = sorted_prefixes[:n]
    return {f"Top Prefix {i+1}": prefix for i, (prefix, _) in enumerate(top_prefixes)}

def summarize_unexpected_asns(unexpected_asns):
    counter = Counter(unexpected_asns)
    top_unexpected = counter.most_common(3)  # Top 3 unexpected ASNs
    summary = {f"Unexpected ASN {i+1}": asn for i, (asn, _) in enumerate(top_unexpected)}
    return summary

def extract_features(index, routes, old_routes_as, target_asn, target_prefixes=None,
                    prefix_lengths=[], med_values=[], local_prefs=[], 
                    communities_per_prefix={}, peer_updates={}, anomaly_data={}, temp_counts=None):
    
    if temp_counts is None:
        temp_counts = initialize_temp_counts()
        
    features = {
        "Timestamp": None,
        "Autonomous System Number": target_asn,
        "Total Routes": 0,
        "New Routes": temp_counts.get("num_new_routes", 0),
        "Withdrawals": temp_counts.get("num_withdrawals", 0),
        "Origin Changes": temp_counts.get("num_origin_changes", 0),
        "Route Changes": temp_counts.get("num_route_changes", 0),
        "Maximum Path Length": 0,
        "Average Path Length": 0,
        "Maximum Edit Distance": 0,
        "Average Edit Distance": 0,
        "Announcements": temp_counts.get("num_announcements", 0),
        "Unique Prefixes Announced": 0,
        # New features
        "Average MED": 0,
        "Average Local Preference": 0,
        "Total Communities": temp_counts.get("total_communities", 0),
        "Unique Communities": len(temp_counts.get("unique_communities", set())),
        "Community Values": [],  # Added for policy analysis
        "Total Updates": 0,
        "Average Updates per Peer": 0,
        "Max Updates from a Single Peer": 0,
        "Min Updates from a Single Peer": 0,
        "Std Dev of Updates": 0,
        "Top Peer 1 ASN": None,
        "Top Peer 2 ASN": None,
        "Top Peer 3 ASN": None,
        "Top Peer 4 ASN": None,
        "Top Peer 5 ASN": None,
        "Total Prefixes Announced": 0,
        "Average Announcements per Prefix": 0,
        "Max Announcements for a Single Prefix": 0,
        "Min Announcements for a Single Prefix": 0,
        "Std Dev of Announcements": 0,
        "Top Prefix 1": None,
        "Top Prefix 2": None,
        "Top Prefix 3": None,
        "Top Prefix 4": None,
        "Top Prefix 5": None,
        "Count of Unexpected ASNs in Paths": 0,
        "Unexpected ASN 1": None,
        "Unexpected ASN 2": None,
        "Unexpected ASN 3": None,
        # Anomaly detection features
        "Target Prefixes Withdrawn": anomaly_data.get("target_prefixes_withdrawn", 0),
        "Target Prefixes Announced": anomaly_data.get("target_prefixes_announced", 0),
        "AS Path Changes": anomaly_data.get("as_path_changes", 0),
        # Policy-related feature
        "AS Path Prepending": temp_counts.get("as_path_prepending", 0),  # Added for policy analysis
    }

    routes_as = build_routes_as(routes, target_asn)

    if index >= 0:
        num_routes = len(routes_as.get(target_asn, {}))
        sum_path_length = 0
        sum_edit_distance = 0

        # Initialize counts
        new_routes = 0
        route_changes = 0
        origin_changes = 0

        for prefix in routes_as.get(target_asn, {}).keys():
            path = routes_as[target_asn][prefix]
            if target_asn in old_routes_as and prefix in old_routes_as[target_asn]:
                path_old = old_routes_as[target_asn][prefix]

                if path != path_old:
                    route_changes += 1
                    # Check for AS path changes involving target ASN
                    if target_asn in path or target_asn in path_old:
                        anomaly_data["as_path_changes"] += 1

                        # Detect unexpected ASNs in path to target prefixes
                        if target_prefixes and prefix in target_prefixes:
                            unexpected_asns = set(path) - set(path_old)
                            if unexpected_asns - {target_asn}:
                                anomaly_data["unexpected_asns_in_paths"].update(unexpected_asns)

                if path[-1] != path_old[-1]:
                    origin_changes += 1

                path_length = len(path)
                sum_path_length += path_length
                edist = editdistance.eval(path, path_old)
                sum_edit_distance += edist
                features["Maximum Path Length"] = max(features["Maximum Path Length"], path_length)
                features["Maximum Edit Distance"] = max(features["Maximum Edit Distance"], edist)
            else:
                new_routes += 1  # This is a new route
                path_length = len(path)
                sum_path_length += path_length
                # No edit distance to calculate for new routes
                features["Maximum Path Length"] = max(features["Maximum Path Length"], path_length)

        features["New Routes"] = new_routes
        features["Route Changes"] = route_changes
        features["Origin Changes"] = origin_changes

        num_routes_total = num_routes if num_routes else 1  # Avoid division by zero
        features["Total Routes"] = num_routes
        features["Average Path Length"] = sum_path_length / num_routes_total
        features["Average Edit Distance"] = sum_edit_distance / route_changes if route_changes else 0

        # Calculate average MED and Local Preference
        features["Average MED"] = sum(med_values) / len(med_values) if med_values else 0
        features["Average Local Preference"] = sum(local_prefs) / len(local_prefs) if local_prefs else 0

        # Calculate community metrics
        features["Total Communities"] = temp_counts["total_communities"]
        features["Unique Communities"] = len(temp_counts["unique_communities"])
        
        all_communities = set()
        for communities in communities_per_prefix.values():
            for community in communities:
                # Convert community tuple/list to a string representation
                if isinstance(community, (tuple, list)):
                    community_str = ':'.join(map(str, community))
                else:
                    community_str = str(community)
                all_communities.add(community_str)

        features["Community Values"] = list(all_communities)

        # Calculate prefix length statistics
        if prefix_lengths:
            features["Average Prefix Length"] = sum(prefix_lengths) / len(prefix_lengths)
            features["Max Prefix Length"] = max(prefix_lengths)
            features["Min Prefix Length"] = min(prefix_lengths)

        # Summarize and integrate peer updates
        peer_update_summary = summarize_peer_updates(peer_updates)
        features["Total Updates"] = peer_update_summary["Total Updates"]
        features["Average Updates per Peer"] = peer_update_summary["Average Updates per Peer"]
        features["Max Updates from a Single Peer"] = peer_update_summary["Max Updates from a Single Peer"]
        features["Min Updates from a Single Peer"] = peer_update_summary["Min Updates from a Single Peer"]
        features["Std Dev of Updates"] = peer_update_summary["Std Dev of Updates"]

        # Add Top 5 Peers
        top_peers = top_n_peer_updates(peer_updates, n=5)
        for key in top_peers:
            features[key] = top_peers[key]

        # Summarize and integrate prefix announcements
        prefix_announcement_summary = summarize_prefix_announcements(temp_counts["prefixes_announced"])
        features["Total Prefixes Announced"] = prefix_announcement_summary["Total Prefixes Announced"]
        features["Average Announcements per Prefix"] = prefix_announcement_summary["Average Announcements per Prefix"]
        features["Max Announcements for a Single Prefix"] = prefix_announcement_summary["Max Announcements for a Single Prefix"]
        features["Min Announcements for a Single Prefix"] = prefix_announcement_summary["Min Announcements for a Single Prefix"]
        features["Std Dev of Announcements"] = prefix_announcement_summary["Std Dev of Announcements"]

        # Add Top 5 Prefixes
        top_prefixes = top_n_prefix_announcements(temp_counts["prefixes_announced"], n=5)
        for key in top_prefixes:
            features[key] = top_prefixes[key]

        # Summarize unexpected ASNs in paths
        unexpected_asns = anomaly_data.get("unexpected_asns_in_paths", [])
        unexpected_asn_summary = summarize_unexpected_asns(unexpected_asns)
        features["Count of Unexpected ASNs in Paths"] = len(unexpected_asns)
        features.update(unexpected_asn_summary)

    features["Unique Prefixes Announced"] = len(routes_as.get(target_asn, {}))

    return features, routes_as


def extract_bgp_data(from_time, until_time, target_asn, target_prefixes=None, 
                     collectors=['rrc00', 'route-views2', 'route-views.sydney', 'route-views.wide']):
    # Convert target_asn to string for consistency
    target_asn = str(target_asn)

    # Generate a unique UUID for the dataset
    data_uuid = uuid.uuid4()
    
    # Define the output path in the media directory
    media_dir = os.path.join(settings.MEDIA_ROOT, 'rag_bgp_data', f'hist_AS{target_asn}_{data_uuid}')
    os.makedirs(media_dir, exist_ok=True)
    
    # Check if the directory exists
    if not os.path.exists(media_dir):
        raise OSError(f"Failed to create directory: {media_dir}")
    print(f"\nDirectory created: {media_dir}")

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

    # Initialize temporary counts and data collections
    temp_counts = initialize_temp_counts()
    temp_counts['as_path_prepending'] = 0
    prefix_lengths = []
    med_values = []
    local_prefs = []
    communities_per_prefix = {}
    peer_updates = defaultdict(int)
    anomaly_data = {
        "target_prefixes_withdrawn": 0,
        "target_prefixes_announced": 0,
        "as_path_changes": 0,
        "unexpected_asns_in_paths": set()
    }
    print(f"Starting BGP data extraction for ASN {target_asn} from {from_time} to {until_time}")

    record_count = 0
    element_count = 0

    for rec in stream.records():
        record_count += 1
        for elem in rec:
            element_count += 1
            update = elem.fields
            elem_time = datetime.utcfromtimestamp(elem.time)

            # If the time exceeds the 5-minute window, process the window and reset
            if elem_time >= current_window_start + timedelta(minutes=5):
                features, old_routes_as = extract_features(
                    index, routes, old_routes_as, target_asn, target_prefixes,
                    prefix_lengths, med_values, local_prefs, 
                    communities_per_prefix, peer_updates, anomaly_data, temp_counts
                )
                features['Timestamp'] = current_window_start.strftime("%Y-%m-%d %H:%M:%S")
                all_features.append(features)

                # Move to the next 5-minute window
                current_window_start += timedelta(minutes=5)
                routes = {}  # Reset the routes for the next window
                index += 1

                # Reset temporary counts and data collections
                temp_counts = initialize_temp_counts()
                prefix_lengths = []
                med_values = []
                local_prefs = []
                communities_per_prefix = {}
                peer_updates = defaultdict(int)
                anomaly_data = {
                    "target_prefixes_withdrawn": 0,
                    "target_prefixes_announced": 0,
                    "as_path_changes": 0,
                    "unexpected_asns_in_paths": set()
                }

            prefix = update.get("prefix")
            if prefix is None:
                continue

            # Initialize process_update flag
            process_update = False

            # Check if target ASN is in the AS path
            as_path_str = update.get('as-path', "")
            as_path = [asn for asn in as_path_str.split() if '{' not in asn and '(' not in asn]
            if target_asn in as_path:
                process_update = True

            # If target_prefixes are provided, check if the prefix is in target_prefixes
            if target_prefixes:
                if prefix in target_prefixes:
                    process_update = True
                else:
                    # Optionally, check if the prefix is a subprefix of any target_prefix
                    for tgt_prefix in target_prefixes:
                        try:
                            tgt_net = ipaddress.ip_network(tgt_prefix)
                            prefix_net = ipaddress.ip_network(prefix)
                            if prefix_net.subnet_of(tgt_net):
                                process_update = True
                                break
                        except ValueError:
                            continue  # Invalid prefix, skip
            else:
                # If target_prefixes is None, we don't filter by prefixes
                pass

            # If neither condition is met, skip this update
            if not process_update:
                continue

            # Collect prefix length
            try:
                network = ipaddress.ip_network(prefix, strict=False)
                prefix_length = network.prefixlen
            except ValueError:
                continue  # Skip this prefix if invalid
            prefix_lengths.append(prefix_length)

            # Check for bogon prefixes
            if is_bogon_prefix(prefix):
                temp_counts["bogon_prefixes"] += 1

            peer_asn = elem.peer_asn
            collector = rec.collector

            # Count updates per peer
            peer_updates[peer_asn] += 1

            # Processing Announcements (A) and Withdrawals (W)
            if elem.type == 'A':  # Announcement
                if as_path:
                    temp_counts["prefixes_announced"][prefix] = temp_counts["prefixes_announced"].get(prefix, 0) + 1
                    temp_counts["num_announcements"] += 1
                    # Initialize routes
                    if prefix not in routes:
                        routes[prefix] = {}
                    if collector not in routes[prefix]:
                        routes[prefix][collector] = {}

                    routes[prefix][collector][peer_asn] = as_path

                    # Collect MED and Local Preference
                    med = update.get('med')
                    if med is not None:
                        try:
                            med_values.append(int(med))
                        except ValueError:
                            pass  # Handle non-integer MED values
                    local_pref = update.get('local-pref')
                    if local_pref is not None:
                        try:
                            local_prefs.append(int(local_pref))
                        except ValueError:
                            pass  # Handle non-integer Local Preference values

                    # Collect Communities
                    communities = update.get('communities', [])
                    if communities:
                        temp_counts["total_communities"] += len(communities)
                        temp_counts["unique_communities"].update(tuple(c) for c in communities)
                        communities_per_prefix[prefix] = communities

                    # Check for AS Path Prepending
                    if len(set(as_path)) < len(as_path):
                        temp_counts["as_path_prepending"] += 1

                    # Anomaly detection for announcements
                    if isinstance(target_prefixes, (list, set)) and prefix in target_prefixes:
                        anomaly_data["target_prefixes_announced"] += 1
                        # Check for unexpected ASNs in path to target prefixes
                        if target_asn not in as_path:
                            anomaly_data["unexpected_asns_in_paths"].update(set(as_path))
            elif elem.type == 'W':  # Withdrawal
                if prefix in routes and collector in routes[prefix]:
                    if peer_asn in routes[prefix][collector]:
                        routes[prefix][collector].pop(peer_asn, None)
                        temp_counts["prefixes_withdrawn"][prefix] = temp_counts["prefixes_withdrawn"].get(prefix, 0) + 1
                        temp_counts["num_withdrawals"] += 1
                        
                        # Anomaly detection for withdrawals
                        if target_prefixes and prefix in target_prefixes:
                            anomaly_data["target_prefixes_withdrawn"] += 1

    print(f"Total records processed: {record_count}")
    print(f"Total elements processed: {element_count}")

    # Process the final 5-minute window
    features, old_routes_as = extract_features(
        index, routes, old_routes_as, target_asn, target_prefixes,
        prefix_lengths, med_values, local_prefs, 
        communities_per_prefix, peer_updates, anomaly_data, temp_counts
    )
    features['Timestamp'] = current_window_start.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Features at index {index}: {features}")
    all_features.append(features)
    
    # Convert collected features to a DataFrame
    df_features = pd.json_normalize(all_features, sep='_').fillna(0)
    print(df_features)
    df_features.to_csv(f"/home/hb/django_react/BGP-LLaMA-webservice/media/rag_bgp_data/knowledge/{target_asn}.csv")
    process_bgp(df=df_features, output_dir=media_dir)
    print(f"\nFinal data saved to {media_dir}\n")

    # Return the path to the output directory
    return media_dir

def collect_historical_data(from_time, target_asn, target_prefixes=None, until_time=None):
    if target_asn is None or from_time is None:
        print("ASn or start time not provided. Exiting historical data collection.")
        return
    
    if target_prefixes is None:
        print("\nTarget prefixes are not provided")
    else:
        print(f"Target prefixes: {target_prefixes}")
        
    if until_time is None:
        until_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return extract_bgp_data(from_time=from_time, until_time=until_time, target_asn=target_asn, target_prefixes=target_prefixes)

def convert_lists_to_tuples(df):
    for col in df.columns:
        # Check if any element in the column is a list
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(lambda x: tuple(x) if isinstance(x, list) else x)
    return df

def run_real_time_bgpstream(asn, collection_period, target_prefixes, return_dict):
    all_features = []
    stream = pybgpstream.BGPStream(
        project="ris-live",
        record_type="updates",
    )
    
    start_time = time.time()
    current_window_start = datetime.utcnow().replace(second=0, microsecond=0)
    index = 0
    old_routes_as = {}
    routes = {}
    
    # Initialize temp_counts with all required keys
    temp_counts = initialize_temp_counts()
    temp_counts['as_path_prepending'] = 0
    prefix_lengths = []
    med_values = []
    local_prefs = []
    communities_per_prefix = {}
    peer_updates = defaultdict(int)
    anomaly_data = {
        "target_prefixes_withdrawn": 0,
        "target_prefixes_announced": 0,
        "as_path_changes": 0,
        "unexpected_asns_in_paths": set()
    }
    
    try:
        for rec in stream.records():
            current_time = datetime.utcnow()

            # Check if the collection period has ended
            if time.time() - start_time >= collection_period.total_seconds():
                print("Collection period ended. Processing data...")
                break

            try:
                for elem in rec:
                    as_path_str = elem.fields.get('as-path', '')
                    as_path = [asn_str for asn_str in as_path_str.strip().split() if '{' not in asn_str and '(' not in asn_str]
                    prefix = elem.fields.get('prefix')
                    if not prefix:
                        continue

                    # Initialize process_update flag
                    process_update = False

                    # Check if target ASN is in the AS path
                    if asn in as_path:
                        process_update = True

                    # If target_prefixes are provided, check if the prefix is in target_prefixes
                    if target_prefixes:
                        if prefix in target_prefixes:
                            process_update = True
                        else:
                            # Check if the prefix is a subprefix of any target_prefix
                            for tgt_prefix in target_prefixes:
                                try:
                                    tgt_net = ipaddress.ip_network(tgt_prefix)
                                    prefix_net = ipaddress.ip_network(prefix)
                                    if prefix_net.subnet_of(tgt_net):
                                        process_update = True
                                        break
                                except ValueError:
                                    continue  # Invalid prefix, skip
                    else:
                        # If target_prefixes is None, we don't filter by prefixes
                        pass

                    # If neither condition is met, skip this update
                    if not process_update:
                        continue

                    collector = rec.collector
                    peer_asn = elem.peer_asn

                    if prefix not in routes:
                        routes[prefix] = {}
                    if collector not in routes[prefix]:
                        routes[prefix][collector] = {}

                    if elem.type == 'A':  # Announcement
                        path = as_path
                        # Increment announcement counts
                        temp_counts["prefixes_announced"][prefix] = temp_counts["prefixes_announced"].get(prefix, 0) + 1
                        temp_counts["num_announcements"] += 1
                        peer_updates[peer_asn] += 1

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
                        
                        # Anomaly detection for announcements
                        if isinstance(target_prefixes, (list, set)) and prefix in target_prefixes:
                            anomaly_data["target_prefixes_announced"] += 1
                            # Check for unexpected ASNs in path to target prefixes
                            if asn not in path:
                                anomaly_data["unexpected_asns_in_paths"].update(set(path))
                            
                        # Collect MED and Local Preference
                        med = elem.fields.get('med')
                        if med is not None:
                            try:
                                med_values.append(int(med))
                            except ValueError:
                                pass  # Handle non-integer MED values
                        local_pref = elem.fields.get('local-pref')
                        if local_pref is not None:
                            try:
                                local_prefs.append(int(local_pref))
                            except ValueError:
                                pass  # Handle non-integer Local Preference values

                        # Collect Communities
                        communities = elem.fields.get('communities', [])
                        if communities:
                            temp_counts["total_communities"] += len(communities)
                            temp_counts["unique_communities"].update(tuple(c) for c in communities)
                            communities_per_prefix[prefix] = communities

                        # Check for AS Path Prepending
                        if len(set(path)) < len(path):
                            temp_counts["as_path_prepending"] += 1

                    elif elem.type == 'W':  # Withdrawal
                        if prefix in routes and collector in routes[prefix]:
                            if peer_asn in routes[prefix][collector]:
                                routes[prefix][collector].pop(peer_asn, None)
                                temp_counts["prefixes_withdrawn"][prefix] = temp_counts["prefixes_withdrawn"].get(prefix, 0) + 1
                                temp_counts["num_withdrawals"] += 1
                                peer_updates[peer_asn] += 1
                                
                                # Anomaly detection for withdrawals
                                if target_prefixes and prefix in target_prefixes:
                                    anomaly_data["target_prefixes_withdrawn"] += 1

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
                    index, routes, old_routes_as, asn, target_prefixes,
                    prefix_lengths, med_values, local_prefs, 
                    communities_per_prefix, peer_updates, anomaly_data, temp_counts
                )
                # Check if features is non-empty
                if features:
                    features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"Features at index {index}: {features}")
                    
                    all_features.append(features)

                    # Create DataFrame with an explicit index only if features is non-empty
                    try:
                        features_df = pd.DataFrame([features]).dropna(axis=1, how='all')
                        # Update return_dict with the latest features
                        return_dict['features_df'] = features_df
                    except ValueError as ve:
                        print(f"ValueError creating DataFrame from features: {ve}. Skipping this window.")
                else:
                    print(f"No features extracted for this window. Skipping DataFrame creation.")

                current_window_start = current_time.replace(second=0, microsecond=0)
                routes = {}
                index += 1
                # Reset temp_counts for the next window
                temp_counts = initialize_temp_counts()
                temp_counts['as_path_prepending'] = 0
                prefix_lengths = []
                med_values = []
                local_prefs = []
                communities_per_prefix = {}
                peer_updates = defaultdict(int)
                anomaly_data = {
                    "target_prefixes_withdrawn": 0,
                    "target_prefixes_announced": 0,
                    "as_path_changes": 0,
                    "unexpected_asns_in_paths": set()
                }
                
        if routes:
            features, old_routes_as = extract_features(
                index, routes, old_routes_as, asn, target_prefixes,
                prefix_lengths, med_values, local_prefs, 
                communities_per_prefix, peer_updates, anomaly_data, temp_counts
            )
            if features:
                features['Timestamp'] = current_window_start.strftime('%Y-%m-%d %H:%M:%S')
                all_features.append(features)
                try:
                    final_features_df = pd.DataFrame(all_features).dropna(axis=1, how='all')
                    return_dict['features_df'] = final_features_df
                except ValueError as ve:
                    print(f"ValueError creating final DataFrame from all_features: {ve}.")
            else:
                print("No features extracted in the final aggregation window.")
                
    except Exception as e:
        error_message = f"An error occurred during real-time data collection for {asn}: {e}"
        print(error_message)
        return_dict['error'] = error_message
        if all_features:
            features_df = pd.DataFrame(all_features).dropna(axis=1, how='all')
            return_dict['features_df'] = features_df


def collect_real_time_data(asn, target_prefixes, collection_period=timedelta(minutes=5)):
    all_collected_data = []  # List to store all collected DataFrames
    features_df = pd.DataFrame()

    # Generate a unique UUID for the real-time data session
    data_uuid = uuid.uuid4()

    media_dir = os.path.join(settings.MEDIA_ROOT, 'rag_bgp_data', f'realtime_AS{asn}_{data_uuid}')
    os.makedirs(media_dir, exist_ok=True)  # Ensure the directory exists
    print(f"\nDirectory created: {media_dir}")

    print(f"\nCollecting data for ASN {asn} for {collection_period.total_seconds() // 60} minutes...")

    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    
    p = multiprocessing.Process(
        target=run_real_time_bgpstream, 
        args=(asn, collection_period, target_prefixes, return_dict)
    )
    p.start()

    start_time = time.time()
    end_time = start_time + collection_period.total_seconds()
    last_features_df = pd.DataFrame()

    no_change_counter = 0
    max_no_change_iterations = 2  # Adjust as needed

    while time.time() < end_time + 5:
        if 'error' in return_dict:
            print(f"Real-time data collection encountered an error: {return_dict['error']}")
            features_df = return_dict.get('features_df', pd.DataFrame())
            break

        features_df = return_dict.get('features_df', pd.DataFrame())

        if not features_df.empty:
            print(f"\nUpdated features_df at {datetime.utcnow()}:\n{features_df.tail(1)}\n")

            # Save the current features_df to the list
            all_collected_data.append(features_df.copy())

            if not last_features_df.empty and features_df.equals(last_features_df):
                no_change_counter += 1
                if no_change_counter >= max_no_change_iterations:
                    print(f"No changes in data for the last {no_change_counter} intervals. Restarting data collection...")
                    # Calculate remaining time for the collection
                    elapsed_time = timedelta(seconds=time.time() - start_time)
                    remaining_time = collection_period - elapsed_time
                    if remaining_time.total_seconds() <= 0:
                        print("No remaining time left for data collection. Exiting.")
                        break

                    # Restart the process with the remaining collection period
                    p.terminate()
                    p.join()
                    
                    print(f"Restarting data collection for the remaining {int(remaining_time.total_seconds())} seconds...")
                    p = multiprocessing.Process(
                        target=run_real_time_bgpstream, 
                        args=(asn, remaining_time, target_prefixes, return_dict)
                    )
                    p.start()
                    no_change_counter = 0  # Reset counter after restarting
            else:
                no_change_counter = 0  # Reset counter if data has changed

            last_features_df = features_df.copy()

        time.sleep(60)  # Sleep for 60 seconds to align with aggregation window
        
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
    print(final_features_df[['Top Peer 1 ASN', 'Top Peer 2 ASN', 'Top Prefix 1', 'Top Prefix 2']].head())
    final_features_df.to_csv(f"/home/hb/django_react/BGP-LLaMA-webservice/media/rag_bgp_data/knowledge/{asn}.csv")
    # Save the final DataFrame to a CSV file
    process_bgp(df=final_features_df, output_dir=media_dir)
    print(f"\nFinal data saved to {media_dir}\n")
    
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

