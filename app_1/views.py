from django.http import JsonResponse, FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from .models import *
# from .model_loader import ModelContainer 
from .serializer import *
import json
from threading import Thread, Lock
import os
from transformers import AutoModelForCausalLM, AutoConfig, AutoTokenizer, TrainingArguments, TextIteratorStreamer, logging
from datasets import load_dataset
from trl import SFTTrainer
from torch import cuda
from peft import LoraConfig
import transformers
import tempfile
import logging
from django.conf import settings

@require_http_methods(["GET"])
def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

import os
import json
import tempfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from transformers import logging as transformers_logging
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
import torch.cuda as cuda
from django.conf import settings  # Ensure MEDIA_ROOT is included in settings

@csrf_exempt
def finetune_model(request):
    if request.method == 'POST':
        # Use request.POST and request.FILES to handle form data and file uploads
        model_id = request.POST.get('model_id', 'meta-llama/Llama-2-13b-chat-hf')
        finetuned_model_name = request.POST.get('finetuned_model_name', 'finetuned-llm')
        train_test_split = int(request.POST.get('test_samples', 1300))
        datasets = json.loads(request.POST.get('datasets', '[]'))
        hyperparameters = json.loads(request.POST.get('hyperparameters', '{}'))
        user_dataset = request.FILES.get('user_dataset', None)
        hf_token = os.environ.get('HF_TOKEN')  # Ensure HF_TOKEN is set

        # Extract hyperparameters
        output_dir = hyperparameters.get('output_dir', "./output")
        batch_size = hyperparameters.get('batch_size', 4)
        gradient_accumulation_steps = hyperparameters.get('gradient_accumulation_steps', 1)
        optim = hyperparameters.get('optim', "paged_adamw_32bit")
        logging_steps = hyperparameters.get('logging_steps', 200)
        learning_rate = hyperparameters.get('learning_rate', 1e-4)
        max_grad_norm = hyperparameters.get('max_grad_norm', 0.3)
        max_steps = hyperparameters.get('max_steps', 5000)
        warmup_ratio = hyperparameters.get('warmup_ratio', 0.05)
        lora_alpha = hyperparameters.get('lora_alpha', 16)
        lora_dropout = hyperparameters.get('lora_dropout', 0.1)
        lora_r = hyperparameters.get('lora_r', 64)
        num_train_epochs = hyperparameters.get('num_train_epochs', 3.0)
        lr_scheduler_type = hyperparameters.get('lr_scheduler_type', 'cosine')

        def load_model(model_id, hf_auth):
            model_config = AutoConfig.from_pretrained(model_id, use_auth_token=hf_auth)
            bnb_config = transformers.BitsAndBytesConfig(load_in_8bit=True)

            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                trust_remote_code=True,
                config=model_config,
                quantization_config=bnb_config,
                device_map='auto',
                use_auth_token=hf_auth
            )
            model.eval()
            device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'
            print(f"Model loaded on {device}")
            return model

        def load_tokenizer(model_id, hf_auth):
            tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=hf_auth)
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.padding_side = "right"
            return tokenizer

        def setup_training(data, tokenizer, model):
            train_val = data["train"].train_test_split(test_size=train_test_split, shuffle=True, seed=42)

            def generate_and_tokenize_prompt(data_point):
                prompt = f"""Below is an instruction that describes a task, paired with an output that provides the completion of the task.
                ### Instruction:
                {data_point["instruction"]}
                ### Response:
                {data_point["output"]}"""

                result = tokenizer(prompt, truncation=True, max_length=2048, padding=False, return_tensors=None)
                if (result["input_ids"][-1] != tokenizer.eos_token_id and len(result["input_ids"]) < 2048):
                    result["input_ids"].append(tokenizer.eos_token_id)
                    result["attention_mask"].append(1)
                result["labels"] = result["input_ids"].copy()
                return result

            train_data = train_val["train"].map(generate_and_tokenize_prompt, batched=True)
            val_data = train_val["test"].map(generate_and_tokenize_prompt, batched=True)

            training_arguments = TrainingArguments(
                output_dir=output_dir,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=gradient_accumulation_steps,
                optim=optim,
                logging_steps=logging_steps,
                learning_rate=learning_rate,
                max_grad_norm=max_grad_norm,
                max_steps=max_steps,
                warmup_ratio=warmup_ratio,
                num_train_epochs=num_train_epochs,
                lr_scheduler_type=lr_scheduler_type,
                group_by_length=True
            )

            peft_config = LoraConfig(
                lora_alpha=lora_alpha,
                lora_dropout=lora_dropout,
                r=lora_r,
                bias="none",
                task_type="CAUSAL_LM"
            )

            data_collator = transformers.DataCollatorForSeq2Seq(
                tokenizer, return_tensors="pt", padding=True
            )

            trainer = SFTTrainer(
                model=model,
                args=training_arguments,
                train_dataset=train_data,
                eval_dataset=val_data,
                tokenizer=tokenizer,
                peft_config=peft_config,
                dataset_text_field="output",
                data_collator=data_collator,
            )

            return trainer

        # Prepare dataset files
        combined_data = []

        # Load and combine dataset files
        for dataset_url in datasets:
            dataset_path = os.path.join(settings.MEDIA_ROOT, dataset_url)
            with open(dataset_path, 'r') as file:
                data = json.load(file)
                combined_data.extend(data)  # Assuming the datasets are lists of records

        if user_dataset:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(user_dataset.read())
                tmp.flush()
                with open(tmp.name, 'r') as user_file:
                    user_data = json.load(user_file)
                    combined_data.extend(user_data)  # Assuming the user dataset is also a list of records

        # Write combined data to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as combined_file:
            json.dump(combined_data, combined_file)
            combined_file_path = combined_file.name

        data = load_dataset("json", data_files=combined_file_path)

        # Load model and tokenizer
        model = load_model(model_id, hf_token)
        tokenizer = load_tokenizer(model_id, hf_token)

        # Setup and start training
        trainer = setup_training(data, tokenizer, model)
        trainer.train()

        return JsonResponse({'status': 'Fine-tuning started'})

    return JsonResponse({'error': 'Invalid request method'}, status=405)


model = None
tokenizer = None
streamer = None
model_lock = Lock()

def load_model():
    global model, tokenizer, streamer
    with model_lock:
        if model is None or tokenizer is None or streamer is None:
            try:
                model_id = 'meta-llama/Llama-2-7b-hf'
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

                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.padding_side = "right"

                streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
                transformers.logging.set_verbosity(transformers.logging.CRITICAL)

                logging("Model loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load the model: {str(e)}")
                raise

    return model, tokenizer, streamer

def unload_model():
    global model, tokenizer, streamer
    with model_lock:
        model = None
        tokenizer = None
        streamer = None
        transformers.logging.set_verbosity(transformers.logging.WARNING)
        logging.info("Model unloaded successfully")

@csrf_exempt
def load_model_endpoint(request):
    if request.method == 'POST':
        try:
            load_model()
            return JsonResponse({'status': 'Model loaded successfully'})
        except Exception as e:
            return JsonResponse({'status': 'Failed to load model', 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def unload_model_endpoint(request):
    if request.method == 'POST':
        try:
            unload_model()
            return JsonResponse({'status': 'Model unloaded successfully'})
        except Exception as e:
            return JsonResponse({'status': 'Failed to unload model', 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def stream_response_generator(query):
    global model, tokenizer, streamer
    if not query:
        yield 'data: {"error": "No query provided"}\n\n'
    else:
        print(f'user query: {query}\n')
        inputs = tokenizer([query], return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}  # Move inputs to the model's device


        # Run the generation in a separate thread
        generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=20)
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        try:
            for new_text in streamer:
                yield f'data: {json.dumps({"generated_text": new_text.strip()})}\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"error": str(e)})}\n\n'


@require_http_methods(["GET"])
def bgp_llama(request):
    query = request.GET.get('query', '')
    return StreamingHttpResponse(stream_response_generator(query), content_type="text/event-stream")





def download_file_with_query(request):
    file_name = request.GET.get('file')
    if not file_name:
        return HttpResponse("No file specified", status=400)

    # Remove leading slashes to prevent absolute paths
    file_name = file_name.lstrip('/')

    # Normalize and build the full file path
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_name))
    print("Constructed file path:", full_path)

    # Check if the path starts with the MEDIA_ROOT directory
    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        print("Unauthorized access attempt:", full_path)
        raise Http404("Unauthorized access.")

    # Check if the file exists and is a file
    if os.path.exists(full_path) and os.path.isfile(full_path):
        print("File found, returning response:", full_path)
        return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=os.path.basename(full_path))
    else:
        print("File not found:", full_path)
        raise Http404("File not found.")


def catch_all(request):
    return HttpResponse("Catch-all route executed")