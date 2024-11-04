from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig, TextIteratorStreamer
import logging
import sys
import torch
import os
from django.conf import settings
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from llama_index.core import PromptTemplate
from threading import Lock

# Logging configuration
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

# model_lock = Lock()
# index_cache = {}
# index_lock = Lock()

# # LLM models
LLAMA3_8B_INSTRUCT = "meta-llama/Meta-Llama-3.1-8B-Instruct"
CUSTOM_MODEL = "hyonbokan/BGPStream13-10k-cutoff-1024-max-2048"

# # Embed models
# BGE_SMALL = "BAAI/bge-small-en-v1.5"
# BGE_ICL = "BAAI/bge-en-icl"
# BGE_M3 = "BAAI/bge-m3"

# SYSTEM_PROMPT = """
# You are an AI BGP analysist assistant that answers questions in a friendly manner, based on the given BGP data. Here are some rules you always follow:
# - Generate only the requested output, don't include any other language before or after the requested output.
# - Your answers should be clear, including relevant timestamps and values when analyzing BGP data features.
# - If the prompt includes the word 'collect' related to BGP data, just state that data has been collected and ask the user to input query.
# - Never say thank you, that you are happy to help, that you are an AI agent, and additional suggestions.
# - Never include file paths, refer to the data content instead
# """

# # Prompt template
# query_wrapper_prompt = PromptTemplate(
#     "<s>[INST] " + SYSTEM_PROMPT + "\n\n{query_str} [/INST]</s>"
# )

# def initialize_models():
#     with model_lock:
#          if not hasattr(settings, 'llm') or not hasattr(settings, 'embed_model'):
#             try:
#                 llm = HuggingFaceLLM(
#                 context_window=4096,
#                 max_new_tokens=756,
#                 generate_kwargs={
#                     "temperature": 0.7,
#                     "do_sample": True,
#                     "repetition_penalty": 1.1
#                 },
#                 query_wrapper_prompt=query_wrapper_prompt,
#                 tokenizer_name=LLAMA3_8B_INSTRUCT,
#                 model_name=LLAMA3_8B_INSTRUCT,
#                 device_map="auto",
#                 model_kwargs={"torch_dtype": torch.float32,
#                               "load_in_8bit": False},
#                 )

#                 embed_model = HuggingFaceEmbedding(model_name=BGE_SMALL)

#                 settings.llm = llm
#                 settings.embed_model = embed_model
                
#                 logger.info("Models loaded and set globally.")
#             except Exception as e:
#                 logger.error(f"Error initializing models: {str(e)}")
#                 raise e
# # Load documents from directory
# def load_documents(directory_path):
#     reader = SimpleDirectoryReader(directory_path)
#     documents = reader.load_data()
#     return documents

# # Create vector store index
# def create_index(documents):
#     service_context = ServiceContext.from_defaults(llm=settings.llm, embed_model=settings.embed_model)
#     index = VectorStoreIndex.from_documents(documents, service_context=service_context)
#     return index

# def stream_bgp_query(query, directory_path=None):
#     try:
#         global index_cache
#         # Ensure models are initialized only if they haven't been set already
#         with model_lock:
#             if not hasattr(settings, "llm") or not hasattr(settings, "embed_model"):
#                 logger.info("Models not found in Settings. Initializing...")
#                 initialize_models()
        
#         index = None

#         # Determine the directory path to use
#         if directory_path:
#             if os.path.exists(directory_path):
#                 directory_to_use = directory_path
#             else:
#                 logger.warning(f"Directory {directory_path} does not exist. Using default directory instead.")
#                 directory_to_use = "/home/hb/django_react/BGP-LLaMA-webservice/media/rag_bgp_data/default"
#                 # directory_to_use = "/home/hb/django_react/BGP-LLaMA-webservice/media/rag_bgp_data/csv"
#         else:
#             # Use default directory path if none provided
#             directory_to_use = "/home/hb/django_react/BGP-LLaMA-webservice/media/rag_bgp_data/default"
#             # directory_to_use = "/home/hb/django_react/BGP-LLaMA-webservice/media/rag_bgp_data/csv"

#         # Check if index is already cached
#         with index_lock:
#             if directory_to_use in index_cache:
#                 logger.info(f"Using cached index for directory: {directory_to_use}")
#                 index = index_cache[directory_to_use]
#             else:
#                 logger.info(f"Loading documents from {directory_to_use} for RAG.")
#                 documents = load_documents(directory_to_use)
#                 if documents:
#                     index = create_index(documents)
#                     index_cache[directory_to_use] = index
#                     logger.info(f"Index created and cached for directory: {directory_to_use}")
#                 else:
#                     logger.warning(f"No documents found in directory: {directory_to_use}. Proceeding with LLM response without augmentation.")
#                     index = None  # Handle as per your requirements

#         if index is None:
#             logger.warning("No index available. Proceeding with LLM response without augmentation.")
#             # Implement logic to handle queries without an index, if needed
#             return

#         logger.info(f"\nUser query: {query}\n")
        
#         # Create the query engine
#         query_engine = index.as_query_engine(streaming=True)

#         # Perform the query and yield response tokens
#         response = query_engine.query(query)
        
#         stop_tokens = ["<s>", "[INST]", "</s>", "[/INST]"]

#         # Stream the generated response tokens
#         generated_text = ""
#         for token in response.response_gen:
#             generated_text += token
#             # Check if any of the stop tokens are in the token
#             if any(stop_token in token for stop_token in stop_tokens):
#                 logger.info(f"Stop token encountered. Stopping generation.")
#                 break
#             yield token

#         logger.info("Query completed.")
#     except Exception as e:
#         logger.error(f"Error in stream_bgp_query: {str(e)}")
#         yield f"Error: {str(e)}"


model = None
tokenizer = None
streamer = None
model_lock = Lock()

def load_model():
    global model, tokenizer, streamer
    with model_lock:
        if model is None or tokenizer is None or streamer is None:
            try:
                model_id = LLAMA3_8B_INSTRUCT
                hf_auth = os.environ.get('hf_token')

                model_config = AutoConfig.from_pretrained(
                    model_id,
                    use_auth_token=hf_auth
                )
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    config=model_config,
                    device_map='auto',
                    use_auth_token=hf_auth
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    use_auth_token=hf_auth
                )
                
                # Set padding token
                if tokenizer.pad_token is None:
                    tokenizer.add_special_tokens({'pad_token': '[PAD]'})

                tokenizer.padding_side = "right"

                # Resize model embeddings if new tokens are added
                model.resize_token_embeddings(len(tokenizer))

                streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
                # transformers.logging.set_verbosity(transformers.logging.CRITICAL)

                logging.info("Model loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load the model: {str(e)}")
                raise

    return model, tokenizer, streamer

LLAMA_SYSTEM_PROMPT = """
You are tasked with generating Python scripts that perform various BGP analysis tasks using the pybgpstream library. Please adhere to the following guidelines when writing the code:
- Key Processing Guidelines:
* Time Format: Define the time range as strings in the following format: from_time = "YYYY-MM-DD HH:MM:SS"
until_time = "YYYY-MM-DD HH:MM:SS"

- Stream Initialization: Use these time parameters during BGPStream initialization:
    stream = pybgpstream.BGPStream(
        from_time=from_time,
        until_time=until_time,
        record_type="updates",
        collectors=["rrc00", "route-views.amsix"]
    )
- Iterating Over Records and Elements:
for rec in stream.records(): for elem in rec: Processing logic goes here

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
Here is your task:\n
"""


GPT_REAL_TIME_SYSTEM_PROMPT = """
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
Clean up resources, close streams, and terminate processes properly.

- Main Loop Processing
Do not use any filter attributes like stream.add_filter() or set filter parameters when initializing BGPStream.
All filtering and processing should occur within the main loop where you iterate over records and elements.
for rec in stream.records():
    for elem in rec:
        Processing logic goes here

Handling Potential Blocking in Data Streams:
Be aware that data streams may block if no new data is received.
Implement mechanisms to periodically check stop conditions even when data is not being received.
Consider using timeouts, non-blocking iterators, or running data collection in a separate thread or process.

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

Outages:
Monitor for sustained withdrawals of prefixes without re-announcements.
Keep track of withdrawn prefixes and their timestamps.
Example:

from datetime import datetime, timedelta

withdrawals_timestamps = {}

if elem_type == 'W':
    withdrawals_timestamps[prefix] = datetime.utcnow()
elif elem_type == 'A' and prefix in withdrawals_timestamps:
    del withdrawals_timestamps[prefix]

outage_threshold = timedelta(minutes=30)
current_time = datetime.utcnow()
for prefix, withdrawal_time in list(withdrawals_timestamps.items()):
    if current_time - withdrawal_time > outage_threshold:
        # Outage detected
        print(f"Outage detected for {prefix} since {withdrawal_time}")
        del withdrawals_timestamps[prefix]


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

GPT_HIST_SYSTEM_PROMPT = """
You are tasked with generating Python scripts that perform various BGP analysis tasks using the pybgpstream library.
Do not provide any additional suggestions.
Please adhere to the following guidelines when writing the code:

- Main Loop Processing:
Do not use any filter attributes like stream.add_filter() or set filter parameters when initializing BGPStream.
All filtering and processing should occur within the main loop where you iterate over records and elements.

- Script Structure:
Start by importing necessary libraries, including pybgpstream and any others required for the task (e.g., datetime, collections).
Define a main function or functions that encapsulate the core logic.
Include a __main__ block or a usage example to demonstrate how to run the script.

- Key Processing Guidelines:
* Time Format: Define the time range as strings in the following format: from_time = "YYYY-MM-DD HH:MM:SS"
until_time = "YYYY-MM-DD HH:MM:SS"

* Stream Initialization: Use these time parameters during BGPStream initialization:
stream = pybgpstream.BGPStream(
    from_time=from_time,
    until_time=until_time,
    record_type="updates",
    collectors=collectors
)

* Iterating Over Records and Elements:
for rec in stream.records(): for elem in rec: Processing logic goes here

* Accessing Element Attributes:
Timestamp: elem_time = datetime.utcfromtimestamp(elem.time)

Element Type (Announcement or Withdrawal): elem_type = elem.type 'A' for announcements, 'W' for withdrawals

Fields Dictionary: fields = elem.fields

Prefix: prefix = fields.get("prefix") if prefix is None: continue

AS Path: as_path_str = fields.get('as-path', "") as_path = as_path_str.split()

Peer ASN and Collector: peer_asn = elem.peer_asn collector = rec.collector

Communities: communities = fields.get('communities', [])

* Filtering Logic Within the Loop:
Filtering for a Specific ASN in AS Path: target_asn = '64500' if target_asn not in as_path: continue

Filtering for Specific Prefixes: target_prefixes = ['192.0.2.0/24', '198.51.100.0/24'] if prefix not in target_prefixes: continue

* Processing Key Values and Attributes:
Counting Announcements and Withdrawals: if elem_type == 'A': announcements[prefix] += 1 elif elem_type == 'W': withdrawals[prefix] += 1

Detecting AS Path Changes: if prefix in prefix_as_paths: if as_path != prefix_as_paths[prefix]: # AS path has changed prefix_as_paths[prefix] = as_path else: prefix_as_paths[prefix] = as_path

Analyzing Community Attributes: for community in communities: community_str = f"{community[0]}:{community[1]}" community_counts[community_str] += 1

Calculating Statistics (e.g., Average MED): med = fields.get('med') if med is not None: try: med_values.append(int(med)) except ValueError: pass

* Detecting Hijacks: Compare the observed origin AS with the expected origin AS for target prefixes:
expected_origins = {'192.0.2.0/24': '64500', '198.51.100.0/24': '64501'}
if prefix in expected_origins:
    observed_origin = as_path[-1] if as_path else None
    expected_origin = expected_origins[prefix]
    if observed_origin != expected_origin:
        # Potential hijack detected
        print(f"Possible hijack detected for {prefix}: expected {expected_origin}, observed {observed_origin}")

* Detecting Outages:
* Monitor for withdrawals of prefixes without re-announcements:
Keep track of withdrawn prefixes and their timestamps
if elem_type == 'W':
    withdrawals[prefix] = elem_time
elif elem_type == 'A':
    # Remove from withdrawals if re-announced
    if prefix in withdrawals:
        del withdrawals[prefix]
Check if prefix remains withdrawn for a certain period (e.g., 30 minutes)
for prefix, withdrawal_time in list(withdrawals.items()):
    if elem_time - withdrawal_time > timedelta(minutes=30):
        # Outage detected for prefix
        print(f"Outage detected for {prefix} starting at {withdrawal_time}")
        del withdrawals[prefix]

* Detecting MOAS (Multiple Origin AS) Conflicts: Monitor prefixes announced by multiple origin ASNs
origin_asn = as_path[-1] if as_path else None
if origin_asn:
    if prefix not in prefix_origins:
        prefix_origins[prefix] = set()
    prefix_origins[prefix].add(origin_asn)
    if len(prefix_origins[prefix]) > 1:
        # MOAS conflict detected
        origins = ', '.join(prefix_origins[prefix])
        print(f"MOAS conflict for {prefix}: announced by ASNs {origins}")

* Analyzing AS Path Prepending: Detect AS path prepending by identifying consecutive repeated ASNs in the AS path:
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
Check for prepending at the end of the path
if consecutive_count > 1 and last_asn:
    prepending_counts[last_asn] += consecutive_count - 1
    
* Handling IP Addresses and Prefixes:
Validating and Parsing IP Prefixes: import ipaddress try: network = ipaddress.ip_network(prefix) except ValueError: continue

Here is your tasks:\n
"""

# @csrf_exempt
# def finetune_model(request):
#     if request.method == 'POST':
#         # Use request.POST and request.FILES to handle form data and file uploads
#         model_id = request.POST.get('model_id', 'meta-llama/Llama-2-13b-chat-hf')
#         finetuned_model_name = request.POST.get('finetuned_model_name', 'finetuned-llm')
#         train_test_split = int(request.POST.get('test_samples', 1300))
#         datasets = json.loads(request.POST.get('datasets', '[]'))
#         hyperparameters = json.loads(request.POST.get('hyperparameters', '{}'))
#         user_dataset = request.FILES.get('user_dataset', None)
#         hf_token = os.environ.get('HF_TOKEN')  # Ensure HF_TOKEN is set

#         # Extract hyperparameters
#         output_dir = hyperparameters.get('output_dir', "./output")
#         batch_size = hyperparameters.get('batch_size', 4)
#         gradient_accumulation_steps = hyperparameters.get('gradient_accumulation_steps', 1)
#         optim = hyperparameters.get('optim', "paged_adamw_32bit")
#         logging_steps = hyperparameters.get('logging_steps', 200)
#         learning_rate = hyperparameters.get('learning_rate', 1e-4)
#         max_grad_norm = hyperparameters.get('max_grad_norm', 0.3)
#         max_steps = hyperparameters.get('max_steps', 5000)
#         warmup_ratio = hyperparameters.get('warmup_ratio', 0.05)
#         lora_alpha = hyperparameters.get('lora_alpha', 16)
#         lora_dropout = hyperparameters.get('lora_dropout', 0.1)
#         lora_r = hyperparameters.get('lora_r', 64)
#         num_train_epochs = hyperparameters.get('num_train_epochs', 3.0)
#         lr_scheduler_type = hyperparameters.get('lr_scheduler_type', 'cosine')

#         def load_model(model_id, hf_auth):
#             model_config = AutoConfig.from_pretrained(model_id, use_auth_token=hf_auth)
#             bnb_config = transformers.BitsAndBytesConfig(load_in_8bit=True)

#             model = AutoModelForCausalLM.from_pretrained(
#                 model_id,
#                 trust_remote_code=True,
#                 config=model_config,
#                 quantization_config=bnb_config,
#                 device_map='auto',
#                 use_auth_token=hf_auth
#             )
#             model.eval()
#             device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'
#             print(f"Model loaded on {device}")
#             return model

#         def load_tokenizer(model_id, hf_auth):
#             tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=hf_auth)
#             tokenizer.pad_token = tokenizer.eos_token
#             tokenizer.padding_side = "right"
#             return tokenizer

#         def setup_training(data, tokenizer, model):
#             train_val = data["train"].train_test_split(test_size=train_test_split, shuffle=True, seed=42)

#             def generate_and_tokenize_prompt(data_point):
#                 prompt = f"""Below is an instruction that describes a task, paired with an output that provides the completion of the task.
#                 ### Instruction:
#                 {data_point["instruction"]}
#                 ### Response:
#                 {data_point["output"]}"""

#                 result = tokenizer(prompt, truncation=True, max_length=2048, padding=False, return_tensors=None)
#                 if (result["input_ids"][-1] != tokenizer.eos_token_id and len(result["input_ids"]) < 2048):
#                     result["input_ids"].append(tokenizer.eos_token_id)
#                     result["attention_mask"].append(1)
#                 result["labels"] = result["input_ids"].copy()
#                 return result

#             train_data = train_val["train"].map(generate_and_tokenize_prompt, batched=True)
#             val_data = train_val["test"].map(generate_and_tokenize_prompt, batched=True)

#             training_arguments = TrainingArguments(
#                 output_dir=output_dir,
#                 per_device_train_batch_size=batch_size,
#                 gradient_accumulation_steps=gradient_accumulation_steps,
#                 optim=optim,
#                 logging_steps=logging_steps,
#                 learning_rate=learning_rate,
#                 max_grad_norm=max_grad_norm,
#                 max_steps=max_steps,
#                 warmup_ratio=warmup_ratio,
#                 num_train_epochs=num_train_epochs,
#                 lr_scheduler_type=lr_scheduler_type,
#                 group_by_length=True
#             )

#             peft_config = LoraConfig(
#                 lora_alpha=lora_alpha,
#                 lora_dropout=lora_dropout,
#                 r=lora_r,
#                 bias="none",
#                 task_type="CAUSAL_LM"
#             )

#             data_collator = transformers.DataCollatorForSeq2Seq(
#                 tokenizer, return_tensors="pt", padding=True
#             )

#             trainer = SFTTrainer(
#                 model=model,
#                 args=training_arguments,
#                 train_dataset=train_data,
#                 eval_dataset=val_data,
#                 tokenizer=tokenizer,
#                 peft_config=peft_config,
#                 dataset_text_field="output",
#                 data_collator=data_collator,
#             )

#             return trainer

#         # Prepare dataset files
#         combined_data = []

#         # Load and combine dataset files
#         for dataset_url in datasets:
#             dataset_path = os.path.join(settings.MEDIA_ROOT, dataset_url)
#             with open(dataset_path, 'r') as file:
#                 data = json.load(file)
#                 combined_data.extend(data)  # Assuming the datasets are lists of records

#         if user_dataset:
#             with tempfile.NamedTemporaryFile(delete=False) as tmp:
#                 tmp.write(user_dataset.read())
#                 tmp.flush()
#                 with open(tmp.name, 'r') as user_file:
#                     user_data = json.load(user_file)
#                     combined_data.extend(user_data)  # Assuming the user dataset is also a list of records

#         # Write combined data to a temporary file
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as combined_file:
#             json.dump(combined_data, combined_file)
#             combined_file_path = combined_file.name

#         data = load_dataset("json", data_files=combined_file_path)

#         # Load model and tokenizer
#         model = load_model(model_id, hf_token)
#         tokenizer = load_tokenizer(model_id, hf_token)

#         # Setup and start training
#         trainer = setup_training(data, tokenizer, model)
#         trainer.train()

#         return JsonResponse({'status': 'Fine-tuning started'})

#     return JsonResponse({'error': 'Invalid request method'}, status=405)