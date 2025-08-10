
import os
import logging
from datasets import load_dataset, Dataset
from transformers import MarianMTModel, MarianTokenizer, Seq2SeqTrainer, Seq2SeqTrainingArguments, DataCollatorForSeq2Seq

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fine_tune_marianmt")

model_name = "Helsinki-NLP/opus-mt-en-tl"
try:
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    logger.info(f"Loaded base model and tokenizer: {model_name}")
except Exception as e:
    logger.error(f"Error loading model/tokenizer: {e}")
    raise

# Load and validate parallel corpus
corpus_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/translation/corpus.csv'))
logger.info(f"Loading corpus from: {corpus_path}")
dataset = load_dataset('csv', data_files={'train': corpus_path}, split='train')

# Filter out rows with missing/invalid data
def is_valid(row):
    return bool(row.get('english')) and bool(row.get('tagalog')) and isinstance(row['english'], str) and isinstance(row['tagalog'], str)

valid_rows = [row for row in dataset if is_valid(row)]
logger.info(f"Loaded {len(dataset)} rows, {len(valid_rows)} valid rows for training.")
if len(valid_rows) == 0:
    logger.error("No valid training samples found in corpus. Check column names and data format.")
    raise ValueError("No valid training samples found.")

# Convert valid rows to a new dataset
dataset = Dataset.from_list(valid_rows)

def preprocess(examples):
    inputs = [str(x) for x in examples['english'] if x is not None]
    targets = [str(x) for x in examples['tagalog'] if x is not None]
    
    # Skip empty batches
    if not inputs or not targets or len(inputs) != len(targets):
        return {}
    
    model_inputs = tokenizer(inputs, max_length=128, truncation=True, padding=True)
    labels = tokenizer(targets, max_length=128, truncation=True, padding=True)
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

tokenized_dataset = dataset.map(preprocess, batched=True)

# Output directory (absolute path)
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/translation/en-tl-marianmt'))
os.makedirs(output_dir, exist_ok=True)

training_args = Seq2SeqTrainingArguments(
    output_dir=output_dir,
    num_train_epochs=3,
    per_device_train_batch_size=8,
    save_strategy="epoch",
    eval_strategy="no",
    logging_dir=os.path.join(output_dir, "logs"),
    predict_with_generate=True,
    fp16=False  # Disabled for CPU or non-compatible GPU
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=DataCollatorForSeq2Seq(tokenizer, model=model)
)

try:
    logger.info("Starting training...")
    trainer.train()
    logger.info("Training complete. Saving model...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.info(f"Model and tokenizer saved to: {output_dir}")
except Exception as e:
    logger.error(f"Error during training or saving: {e}")
    raise