import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    allDatasets: [
            {
                title: 'Self-Instruct Generated Dataset',
                id: 'self-instruct-generated-dataset',
                datasets: [
                    {
                        id: 'bgp-knowledge',
                        title:'BGP Knowledge',
                        fileUrl: 'finetuning-dataset/self-instruct-generated-dataset/bgp-knowledge.json',
                        fileCount: 20000,
                        size: '18.1 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {
                            "instruction": "Discuss the challenges of debugging BGP issues and the best practices for troubleshooting BGP sessions.",
                            "input": "Our service provider reported a communication issue between two BGP routers.",
                            "output": "Debugging BGP issues can be complex and time-consuming due to configuration complexity, state issues, and the distributed nature of BGP. It is important to understand the best practices for troubleshooting BGP sessions. It is best to start by verifying the basic connectivity and ICMP echo responses, followed by examining route health scores and dampened routes. Next, verify that BGP peers are established and peering correctly by analyzing BGP updates, routes, and timers. Finally, focus on stabilizing the BGP session to prevent routing instabilities. A combination of BGP debugging tools, such as TCPdump, show ip bgp, and show ip route, can prove invaluable in this process."
                        },
                    },
                    {   
                        id: 'pybgpstream-base',
                        title:'PyBGPStream Base',
                        fileUrl: '/finetuning-dataset/self-instruct-generated-dataset/pybgpstream-base.json',
                        fileCount: 8609,
                        size: '27.5 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {                           
                            "instruction": "Identify the MOASes that announce AS 2497 and determine the path inflation.",
                            "input": "ASN: 2497\nFilter: path \"_2497_\"",
                            "output": "import pybgpstream\nfrom collections import Counter\n\nstream = pybgpstream.BGPStream(\n    from_time=\"2020-10-01 00:00:00\",\n    until_time=\"2020-10-31 00:00:00\",\n    collectors=[\"route-views2\", \"route-views3\", \"route-views4\", \"ris-ripe\"],\n    record_type=\"updates\",\n    filter=\"path \\\"_2497_\\\"\"\n)\n\nas_paths = []\n\nfor rec in stream.records():\n    for elem in rec:\n      if elem.type == \"A\":\n        as_paths.append(elem.fields[\"as-path\"].split()[0])\n\nmoases = Counter(as_paths).most_common()\n\n# Calculate path inflation\npath_inflation = 0\nfor moas in moases:\n    path_inflation += (moas[1] - 1)\n\nprint(f\"MOASes: {moases}\")\nprint(f\"Path inflation for AS 2497: {path_inflation}\")",
                        },
                    },
                    {   
                        id: 'pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        fileUrl: '/finetuning-dataset/self-instruct-generated-dataset/pybgpstream-real-time.json',
                        fileCount: 1501,
                        size: '4.5 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {
                            "instruction": "Access live RPKI information from RIPE NCC for the Autonomous System (AS 2856).",
                            "input": "AS Number: 2856",
                            "output": "import pybgpstream\nasn=\"AS2856\"\nstream = pybgpstream.BGPStream(\n    project=\"rpki\",\n    record_type=\"roas\",\n    filter=\"type rpki and registered 'false' and asn '{}'\".format(asn)\n)\nfor rec in stream.records():\n    elem = rec.get_next_elem()\n    while elem:\n        print(elem.fields['prefix'])\n        elem = rec.get_next_elem()",
                        },
                    },
                ],
            },
            {
                title: 'Manual Seed Tasks',
                id: 'manual-seed-dataset',
                datasets: [
                    {
                        id: 'bgp-knowledge-1',
                        title:'BGP Knowledge I',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-knowledge-1.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_knowledge.txt',
                        fileCount: 121,
                        size: '115 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {"id": "seed_task_5", "name": "BGP Message Formats and Communication", "instruction": "Can you describe the various message formats that BGP uses for communication between routers?","instances": [    {        "input": "<noinput>",        "output": "BGP (Border Gateway Protocol) uses various message formats for effective communication between routers. These formats include the Open Message, which initiates connections and shares essential parameters. The Update Message conveys route changes, additions, or updates. Notification Messages signal errors, while Keepalive Messages maintain connections. These formats ensure routers establish, maintain, and update routing information, enabling reliable and efficient data forwarding across networks. BGP's message formats facilitate informed routing decisions and adaptability to network changes, contributing to stable and efficient internet routing."}],"is_classification": false},
                    },
                    {
                        id: 'bgp-knowledge-2',
                        title:'BGP Knowledge II',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-knowledge-2.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_knowledge.txt',
                        fileCount: 36,
                        size: '49 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {"id": "seed_task_11", "name": "BGP Confederations and Scalability", "instruction": "Describe the concept of BGP Confederations, how they address BGP scalability issues in large networks, and their advantages over traditional route reflection.", "instances": [{"input": "Consider a large ISP with multiple internal BGP (iBGP) routers and the challenges of maintaining full-mesh peering.", "output": "BGP Confederations are a mechanism designed to address the scalability challenges associated with maintaining full-mesh iBGP peering in large networks. In a full-mesh iBGP setup, every router needs to establish peering with every other router, leading to a quadratic increase in the number of peering sessions as the network grows. Confederations address this by dividing an autonomous system (AS) into multiple sub-ASes or confederation members. These sub-ASes then peer among themselves using eBGP, while still appearing as a single AS to external peers. This approach significantly reduces the number of required peering sessions. Compared to traditional route reflection, confederations offer a more granular and flexible approach to BGP scalability. While route reflectors simplify iBGP topology by reducing the number of peering sessions, they can introduce suboptimal routing. Confederations, on the other hand, provide a more hierarchical structure, allowing for better path selection and more efficient routing decisions. In essence, BGP Confederations offer a scalable and efficient solution to the challenges of managing BGP in large, complex networks."}], "is_classification": false},
                    },
                    {
                        id: 'bgp-pybgpstream-base',
                        title:'PyBGPStream Base',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-pybgpstream-base.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_pybgpstream.txt',
                        fileCount: 54,
                        size: '90 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {"id": "seed_task_2", "name": "Investigating BGP Community Local Preference Variations", "instruction": "Investigate variations in local preference values associated with BGP communities using data from collector rrc03 on July 15, 2021, between 10:00 and 11:00.", "instances": [{"input": "Investigating BGP community local preference variations using data from collector rrc03 on July 15, 2021, between 10:00 and 11:00.", "output": "import pybgpstream\nfrom collections import defaultdict\n\n# Initialize BGP Stream\nstream = pybgpstream.BGPStream(\n    from_time=\"2021-07-15 10:00:00\", until_time=\"2021-07-15 11:00:00\",\n    project=\"ris\",\n    collectors=\"rrc03\",\n    record_type=\"updates\",\n    filter=\"ipversion 4\"\n)\n\n# Map of communities to local preference values\ncommunity_to_local_pref = defaultdict(list)\n\n# Loop through the stream records\nfor rec in stream.records():\n    for elem in rec:\n        if elem.type == \"A\":\n            communities = elem.fields.get('communities', None)\n            local_pref = elem.fields.get('local_pref', None)\n\n            if communities and local_pref:\n                for community in communities.split(\",\"):\n                    community_to_local_pref[community].append(int(local_pref))\n\n# Calculate average local preference for each community\nprint(\"Average Local Preference Values for Communities:\")\nfor community, local_prefs in community_to_local_pref.items():\n    avg_local_pref = sum(local_prefs) / len(local_prefs)\n    print(f\"{community}: {avg_local_pref}\")"}], "is_classification": false},
                    },
                    {
                        id: 'bgp-pybgpstream-real-case',
                        title:'PyBGPStream Real Cases',
                        fileUrl: '',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_pybgpstream.txt',
                        fileCount: 25,
                        size: '61 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {"id": "seed_task_0", "name": "Google May 2005 Outage", "instruction": "Visualize the BGP update timeline for the prefix 64.233.161.0/24 during the time window from May 7, 2005, 00:00:00 to May 7, 2005, 23:59:00. Use data from multiple RouteViews collectors, including route-views2, route-views3, route-views4, ris-ripe, bview, and rib, and collect BGP update records of type 'A' (Announcements) for this prefix. Plot the timeline to show how different Autonomous Systems (ASes) contributed to the announcements over time.", "instances": [{"input": "Time window: May 7, 2005, 00:00:00 to May 7, 2005, 23:59:00\nCollectors: route-views2, route-views3, route-views4, ris-ripe, bview, rib\nRecord Type: updates (Announcements)\nPrefix of Interest: 64.233.161.0/24", "output": "import pybgpstream\nimport matplotlib.pyplot as plt\nfrom datetime import datetime\n\n# Define the time window around the TTNet incident\nstart_time = \"2005-05-07 00:00:00\"\nend_time = \"2005-05-07 23:59:00\"\n\n# Initialize the BGPStream to use multiple RouteViews collectors\nstream = pybgpstream.BGPStream(\n    from_time=start_time,\n    until_time=end_time,\n    collectors=[\"route-views2\", \"route-views3\", \"route-views4\", \"ris-ripe\", \"bview\", \"rib\"],\n    record_type=\"updates\",\n)\n\nas_path_data = {}\ntimeline_data = {}\n\nfor elem in stream:\n    if elem.type == \"A\" and elem.fields[\"prefix\"] == \"64.233.161.0/24\":\n   as_path = elem.fields[\"as-path\"].split(\" \")\n   originating_as = as_path[-1]\n   timestamp = datetime.utcfromtimestamp(elem.time).strftime('%Y-%m-%d %H:%M:%S')\n\n   if originating_as not in as_path_data:\n  as_path_data[originating_as] = 1\n  timeline_data[originating_as] = [timestamp]\n   else:\n  as_path_data[originating_as] += 1\n  timeline_data[originating_as].append(timestamp)\n\n# Plotting the BGP Update Timeline\nplt.figure(figsize=(12, 6))\nfor as_num, timestamps in timeline_data.items():\n    plt.plot(timestamps, [as_num] * len(timestamps), marker='o', label=f\"AS{as_num}\")\n\nplt.xlabel('Timestamp')\nplt.ylabel('Autonomous System (AS)')\nplt.title('BGP Update Timeline for Prefix 64.233.161.0/24')\nplt.legend()\nplt.xticks(rotation=45)\nplt.tight_layout()\nplt.grid(axis='x')\nplt.show()"}], "is_classification": false},
                    },
                    {
                        id: 'bgp-pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-pybgpstream-real-time.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt-pybgpstream-realtime.txt',
                        fileCount: 4,
                        size: '12 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        jsonSnapshot: {"id": "seed_task_0", "name": "AS18298 Real-Time BGP Data Analysis", "instruction": "Collect BGP update data for AS18298 over a specific collection period. Record prefix announcements and withdrawals during this period. Aggregate and visualize the collected data.", "instances": [{"input": "Collection Period: 72000 seconds\nTarget AS: 18298", "output": "import pybgpstream\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport time\n\ncollection_period = 72000\ntarget_as = \"18298\"\n\nprefix_announcements_df = pd.DataFrame(columns=['Time', 'Prefix', 'Count'])\nwithdrawals_df = pd.DataFrame(columns=['Time', 'Prefix', 'Count'])\n\nstream = pybgpstream.BGPStream(\n    project=\"ris-live\",\n    record_type=\"updates\",\n)\n\nstart_time = time.time()\n\nfor rec in stream.records():\n    if collection_period < time.time() - start_time:\n        print(\"Collection period ended. Processing data...\")\n        break\n\n    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(rec.time))\n    for elem in rec:\n        as_path = elem.fields.get('as-path', '').split()\n        prefix = elem.fields['prefix']\n\n        if target_as in as_path:\n            if elem.type == 'A':\n                if prefix in prefix_announcements_df['Prefix'].values:\n                    prefix_announcements_df.loc[prefix_announcements_df['Prefix'] == prefix, 'Count'] += 1\n                else:\n                    new_row = pd.DataFrame({'Time': [current_time], 'Prefix': [elem.fields['prefix']], 'Count': [1]})\n                    prefix_announcements_df = pd.concat([prefix_announcements_df, new_row], ignore_index=True)\n            elif elem.type == 'W':\n                if prefix in withdrawals_df['Prefix'].values:\n                    withdrawals_df.loc[withdrawals_df['Prefix'] == prefix, 'Count'] += 1\n                else:\n                    new_row = pd.DataFrame({'Time': [current_time], 'Prefix': [elem.fields['prefix']], 'Count': [1]})\n                    withdrawals_df = pd.concat([withdrawals_df, new_row], ignore_index=True)\n\nprefix_announcements_df = prefix_announcements_df.groupby(['Prefix']).size().reset_index(name='Counts')\nwithdrawals_df = withdrawals_df.groupby(['Prefix']).size().reset_index(name='Counts')\n\ndef plot_data(df, title):\n    if not df.empty:\n        plt.figure(figsize=(10, 5))\n        plt.bar(df['Prefix'], df['Counts'], align='center')\n        plt.xticks(rotation=90)\n        plt.title(title)\n        plt.show()\n    else:\n        print(f\"No data to display for {title}\")\n\nplot_data(prefix_announcements_df, f\"Prefix Announcements for AS{target_as} (Collected Data)\")\nplot_data(withdrawals_df, f\"Withdrawals for AS{target_as} (Collected Data)\")"}], "is_classification": false},
                    },             
                ]
            },
            // other sections
    ],
    loading: false,
    error: null
};

const datasetsSlice = createSlice({
    name: 'datasets',
    initialState,
    reducers: {
        addDatasetToSection: (state, action) => {
            const { sectionTitle, newDataset } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                section.datasets.push(newDataset);
            }
        },        
        removeDatasetFromSection: (state, action) => {
            const { sectionTitle, datasetId } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                section.datasets = section.datasets.filter(dataset => dataset.id !== datasetId);
            }
        },        
        updateDatasetInSection: (state, action) => {
            const { sectionTitle, updatedDataset } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                const index = section.datasets.findIndex(dataset => dataset.id === updatedDataset.id);
                if (index !== -1) {
                    section.datasets[index] = updatedDataset;
                }
            }
        },        
        // Additional reducers for adding, removing, or updating whole sections could be added here
    }
});

export const { addDatasetToSection, removeDatasetFromSection, updateDatasetInSection } = datasetsSlice.actions;
export default datasetsSlice.reducer;

// Initial State: Defined starting state for the slice.
// Reducers: Functions defining how state changes in response to actions. These update the state based on the type of action and the payload provided.
// Action Creators: Automatically generated functions (addDataset, removeDataset, updateDataset) that you can call to create action objects to dispatch to the store.