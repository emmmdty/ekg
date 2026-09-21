import argparse
import json
import os
import logging
import random

import time

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
from model import DMBert, RawBert
from data import EFDDataset


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_data", type=str, default="train.jsonl")
    parser.add_argument("--test_data", type=str, default="test.jsonl")
    # PATCH(ekg): dev split for epoch selection; upstream selects on --test_data.
    parser.add_argument("--dev_data", type=str, default=None)
    parser.add_argument("--report_out", type=str, default=None)
    parser.add_argument("--model_dir", type=str, default="models")
    parser.add_argument("--log_dir", type=str, default="logs")
    parser.add_argument("--model_name", type=str, default="roberta-large")
    parser.add_argument("--ckpt", type=str, default="/data/MODELS/flan-t5-base")
    parser.add_argument("--model", type=str, default="DMBert")
    parser.add_argument("--pooling_type", type=str, default="cls")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--max_length", type=int, default=160)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--add_relation", action="store_true")
    parser.add_argument("--add_argument", action="store_true")
    return parser.parse_args()


def evaluate(preds, labels, mode):
    gold_label = {"CT+": 0, "CT-": 1, "PS+": 2, "PS-": 3, "Uu": 4}
    gold_label_pair = {"CT": [0, 1], "PS": [2, 3], "p": [0, 2], "n": [1, 3]}

    if mode in gold_label:
        tp = sum([1 for p, l in zip(preds, labels) if p == gold_label[mode] and l == gold_label[mode]])
        fp = sum([1 for p, l in zip(preds, labels) if p == gold_label[mode] and l != gold_label[mode]])
        fn = sum([1 for p, l in zip(preds, labels) if p != gold_label[mode] and l == gold_label[mode]]) 
    elif mode in gold_label_pair:
        tp = sum([1 for p, l in zip(preds, labels) if p in gold_label_pair[mode] and l in gold_label_pair[mode]])
        fp = sum([1 for p, l in zip(preds, labels) if p in gold_label_pair[mode] and l not in gold_label_pair[mode]])
        fn = sum([1 for p, l in zip(preds, labels) if p not in gold_label_pair[mode] and l in gold_label_pair[mode]])
    else:
        raise ValueError("Invalid evaluation mode")

    precision = tp / (tp + fp) if tp + fp != 0 else 0
    recall = tp / (tp + fn) if tp + fn != 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall != 0 else 0
    return precision, recall, f1


# PATCH(ekg): the upstream epoch loop inlines this; a shared helper lets the same
# forward pass score a dev split without duplicating it.
def _infer(model, dataloader, device, args, desc):
    preds_all = []
    labels_all = []
    with torch.no_grad():
        for data in tqdm(dataloader, desc=desc):
            input_ids = data['input_ids'].to(device)
            attention_mask = data['attention_mask'].to(device)
            labels = data['labels'].to(device)
            maskL = data['maskL'].to(device)
            maskR = data['maskR'].to(device)
            if args.add_relation:
                cause_ids = data['cause_ids'].to(device)
                precondition_ids = data['precondition_ids'].to(device)
                cause_mask = data['cause_mask'].to(device)
                precondition_mask = data['precondition_mask'].to(device)
            else:
                cause_ids = None
                precondition_ids = None
                cause_mask = None
                precondition_mask = None
            if args.add_argument:
                arg_ids = data['arg_ids'].to(device)
                arg_mask = data['arg_mask'].to(device)
            else:
                arg_ids = None
                arg_mask = None
            logits = model(input_ids=input_ids, attention_mask=attention_mask, maskL=maskL, maskR=maskR, arg_ids=arg_ids, arg_mask=arg_mask, cause_ids=cause_ids, cause_mask=cause_mask, precondition_ids=precondition_ids, precondition_mask=precondition_mask)
            preds_all.extend(torch.argmax(logits, dim=1).cpu().numpy())
            labels_all.extend(labels.cpu().numpy())
    return np.array(preds_all), np.array(labels_all)


def _report(preds, labels):
    out = {}
    for mode in ("CT+", "CT-", "PS+", "PS-", "Uu"):
        precision, recall, f1 = evaluate(preds, labels, mode=mode)
        out[mode] = {"precision": precision, "recall": recall, "f1": f1}
    out["macro_f1"] = float(f1_score(labels, preds, average="macro"))
    out["micro_f1"] = float(f1_score(labels, preds, average="micro"))
    out["accuracy"] = float(accuracy_score(labels, preds))
    return out


def main():
    args = parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("CUDA available: ", torch.cuda.is_available())


    model_save_path = os.path.join(args.model_dir, args.model_name)
    os.makedirs(model_save_path, exist_ok=True)
    log_save_path = os.path.join(args.log_dir, args.model_name)
    os.makedirs(log_save_path, exist_ok=True)



    logger = logging.getLogger("EFD")
    log_file_name = f'log_{args.model}_bs{args.batch_size}_ml{args.max_length}_lr{args.lr}'
    if args.add_relation:
        log_file_name += "_relation"
    if args.add_argument:
        log_file_name += "_argument"
    log_file_name += ".log"
    handler = logging.FileHandler(os.path.join(log_save_path, log_file_name))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    seed = args.seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    tokenizer = AutoTokenizer.from_pretrained(args.ckpt)
    tokenizer.add_special_tokens({'additional_special_tokens': ['<e>', '</e>', '<p>', '</p>', '<c>', '</c>']})

    if args.model == "RawBert":
        model = RawBert(args.ckpt, dropout=args.dropout, tokenizer_size=len(tokenizer), num_labels=5).to(device)
    else:
        model = DMBert(args.ckpt, args.max_length, args.dropout, len(tokenizer), args.add_argument, args.add_relation, pooling_type=args.pooling_type).to(device)



    train_dataset = EFDDataset(data_dir=args.train_data, tokenizer=tokenizer, max_length=args.max_length, add_argument=args.add_argument, add_relation=args.add_relation)
    train_dataloader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)

    test_dataset = EFDDataset(data_dir=args.test_data, tokenizer=tokenizer, max_length=args.max_length, add_argument=args.add_argument, add_relation=args.add_relation)
    test_dataloader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    # PATCH(ekg): dev split, used only to pick the epoch.
    if args.dev_data is None:
        raise ValueError("--dev_data is required: this fork selects the epoch on dev, not on test")
    dev_dataset = EFDDataset(data_dir=args.dev_data, tokenizer=tokenizer, max_length=args.max_length, add_argument=args.add_argument, add_relation=args.add_relation)
    dev_dataloader = DataLoader(dev_dataset, batch_size=args.batch_size, shuffle=False)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    loss_fn = torch.nn.CrossEntropyLoss()
    # PATCH(ekg): dev-selected result plus upstream's epoch-max test number.
    best_dev_macro_f1 = -1.0
    epoch_max_test_macro_f1 = 0.0
    selected = None

    model.train()

    for epoch in range(args.epochs):
        start_time = time.time()
        for data in tqdm(train_dataloader, desc=f"Epoch {epoch} training: "):
            input_ids = data['input_ids'].to(device)
            attention_mask = data['attention_mask'].to(device)
            labels = data['labels'].to(device)
            maskL = data['maskL'].to(device)
            maskR = data['maskR'].to(device)


            optimizer.zero_grad()
            if args.add_relation:
                cause_ids = data['cause_ids'].to(device)
                precondition_ids = data['precondition_ids'].to(device)
                cause_mask = data['cause_mask'].to(device)
                precondition_mask = data['precondition_mask'].to(device)
            else:
                cause_ids = None
                precondition_ids = None
                cause_mask = None
                precondition_mask = None
            if args.add_argument:
                arg_ids = data['arg_ids'].to(device)
                arg_mask = data['arg_mask'].to(device)
            else:
                arg_ids = None
                arg_mask = None
            logits = model(input_ids=input_ids, attention_mask=attention_mask, maskL=maskL, maskR=maskR, arg_ids=arg_ids, arg_mask=arg_mask, cause_ids=cause_ids, cause_mask=cause_mask, precondition_ids=precondition_ids, precondition_mask=precondition_mask)
            
            loss = loss_fn(logits, labels)
            loss.backward()
            optimizer.step()

        end_time = time.time()
        logger.info(f"Epoch {epoch} training time: {end_time - start_time}")

        model.eval()
        # PATCH(ekg): score dev and test with the same helper. The epoch is chosen
        # on dev; upstream instead reported max-over-epochs of the test macro-F1
        # (its checkpoint-saving line is commented out), which is selection on the
        # evaluation set. Both numbers are kept so the difference is visible.
        dev_preds, dev_labels = _infer(model, dev_dataloader, device, args, f"Epoch {epoch} dev: ")
        test_preds, test_labels = _infer(model, test_dataloader, device, args, f"Epoch {epoch} test: ")
        dev_metrics = _report(dev_preds, dev_labels)
        test_metrics = _report(test_preds, test_labels)
        logger.info(f"Epoch {epoch} dev macro F1: {dev_metrics['macro_f1']}")
        logger.info(f"Epoch {epoch} test macro F1: {test_metrics['macro_f1']}")
        epoch_max_test_macro_f1 = max(epoch_max_test_macro_f1, test_metrics["macro_f1"])
        if dev_metrics["macro_f1"] > best_dev_macro_f1:
            best_dev_macro_f1 = dev_metrics["macro_f1"]
            selected = {
                "selected_epoch": epoch,
                "dev": dev_metrics,
                "test": test_metrics,
                "test_predictions": [int(value) for value in test_preds],
                "test_labels": [int(value) for value in test_labels],
            }
            logger.info(f"Best dev model at epoch {epoch}")

        model.train()

    # PATCH(ekg): publish both numbers instead of only logging them.
    if selected is None:
        raise ValueError("no epoch produced a dev score")
    selected["epoch_max_test_macro_f1_upstream_rule"] = epoch_max_test_macro_f1
    selected["selection"] = "dev macro-F1 (upstream selected on test)"
    if args.report_out is not None:
        if os.path.exists(args.report_out):
            raise FileExistsError(args.report_out)
        with open(args.report_out, "w", encoding="utf-8") as handle:
            json.dump(selected, handle, indent=2, sort_keys=True)
            handle.write("\n")
    logger.info(f"dev-selected test macro F1: {selected['test']['macro_f1']}")
    logger.info(f"upstream-rule epoch-max test macro F1: {epoch_max_test_macro_f1}")


if __name__ == "__main__":
    main()






