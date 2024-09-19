from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig, TextIteratorStreamer
import logging
import sys
import torch
import os
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core import PromptTemplate
from threading import Lock

# Logging configuration
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

LLAMA3_8B_INSTRUCT = "meta-llama/Meta-Llama-3.1-8B-Instruct"
CUSTOM_MODEL = "hyonbokan/bgp-llama-knowledge-5k"
model_lock = Lock()


# System prompt
SYSTEM_PROMPT = """
You are an AI assistant that answers questions in a friendly manner, based on the given source BGP data. Here are some rules you always follow:
- Generate only the requested output, don't include any other language before or after the requested output.
- Your answers should be direct and include relevant timestamps and values when analyzing BGP data features.
- Be clear without repeating yourself.
- Never say thank you, that you are happy to help, that you are an AI agent, and additional suggestions.
"""

# Prompt template
query_wrapper_prompt = PromptTemplate("[INST]<>\n" + SYSTEM_PROMPT + "<>\n\n{query_str}[/INST] ")


def initialize_models():
    with model_lock:
            llm = HuggingFaceLLM(
                context_window=4096,
                max_new_tokens=512,
                generate_kwargs={"temperature": 0.0, "do_sample": False},
                query_wrapper_prompt=query_wrapper_prompt,
                tokenizer_name=LLAMA3_8B_INSTRUCT,
                model_name=LLAMA3_8B_INSTRUCT,
                device_map="auto",
                model_kwargs={"torch_dtype": torch.float16, "load_in_8bit": False},
            )

            embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

            Settings.llm = llm
            Settings.embed_model = embed_model

            logger.info("Models loaded and set globally.")

# Load documents from directory
def load_documents(directory_path):
    reader = SimpleDirectoryReader(directory_path)
    documents = reader.load_data()
    return documents

# Create vector store index
def create_index(documents):
    index = VectorStoreIndex.from_documents(documents)
    return index

# Query the engine with streaming support
def stream_bgp_query(query, directory_path=None):
    # Ensure models are initialized only if they haven't been set already
    with model_lock:
        if not hasattr(Settings, "llm") or not hasattr(Settings, "embed_model"):
            logger.info("Models not found in Settings. Initializing...")
            initialize_models()
    
    index = None
    
    # If a directory path is provided, load documents from that directory
    if directory_path:
        logger.info(f"Loading documents from {directory_path} for RAG.")
        documents = load_documents(directory_path)
        index = create_index(documents)

    # If no directory path is provided, try using default documents
    if index is None and not directory_path:
        logger.info("\nNo specific BGP data provided. Loading default documents for regular query.")
        default_directory_path = "/home/hb/django_react/BGP-LLaMA-webservice/media/rag_bgp_data/knowledge"
        documents = load_documents(default_directory_path)
        if documents:
            index = create_index(documents)
        else:
            logger.warning(f"No default documents found in directory: {default_directory_path}. Proceeding with LLM response without augmentation.")
    
    logger.info(f"\nuser query: {query}\n")
    
    # Create the query engine
    query_engine = index.as_query_engine(streaming=True)

    # Perform the query and yield response tokens
    response = query_engine.query(query)
    # Set stopping condition to stop at [/INST]
    stop_token = "[/INST]"

    # Stream the generated response tokens
    generated_text = ""
    for token in response.response_gen:
        generated_text += token
        yield token
        
        # Check if stop token is encountered, and stop the generation
        if stop_token in generated_text:
            logger.info(f"Stop token {stop_token} encountered. Stopping generation.")
            break

    logger.info("Query completed.")

# model = None
# tokenizer = None
# streamer = None

# def load_model():
#     global model, tokenizer, streamer
#     with model_lock:
#         if model is None or tokenizer is None or streamer is None:
#             try:
#                 model_id = 'meta-llama/Llama-2-7b-chat-hf'
#                 # model_id = 'hyonbokan/bgp-llama-knowledge-5k'
#                 hf_auth = os.environ.get('hf_token')

#                 model_config = AutoConfig.from_pretrained(
#                     model_id,
#                     use_auth_token=hf_auth
#                 )
#                 model = AutoModelForCausalLM.from_pretrained(
#                     model_id,
#                     trust_remote_code=True,
#                     config=model_config,
#                     device_map='auto',
#                     use_auth_token=hf_auth
#                 )
#                 tokenizer = AutoTokenizer.from_pretrained(
#                     model_id,
#                     use_auth_token=hf_auth
#                 )

#                 tokenizer.pad_token = tokenizer.eos_token
#                 tokenizer.pad_token_id = tokenizer.eos_token_id
#                 tokenizer.padding_side = "right"

#                 streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
#                 # transformers.logging.set_verbosity(transformers.logging.CRITICAL)

#                 logging.info("Model loaded successfully")
#             except Exception as e:
#                 logging.error(f"Failed to load the model: {str(e)}")
#                 raise

#     return model, tokenizer, streamer


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