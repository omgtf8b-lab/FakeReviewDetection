"""Fine-tune DistilBERT; genuine curves/metrics generated only after successful training."""
import argparse
import json
import random
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
from ml.bert_adapter import BertAdapter

ROOT=Path(__file__).resolve().parents[1]


class Reviews(Dataset):
    def __init__(self, frame, tokenizer):
        self.tokens=tokenizer(frame.text.tolist(),truncation=True,max_length=128,padding='max_length')
        self.labels=frame.target.astype(int).tolist()
    def __len__(self):return len(self.labels)
    def __getitem__(self,i):
        return {**{k:torch.tensor(v[i]) for k,v in self.tokens.items()},'labels':torch.tensor(self.labels[i])}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data',default=str(ROOT/'ml/models/dataset_split.csv'))
    p.add_argument('--output',default=str(ROOT/'ml/models/distilbert.joblib'))
    p.add_argument('--epochs',type=int,default=3)
    p.add_argument('--batch-size',type=int,default=8)
    p.add_argument('--learning-rate',type=float,default=2e-5)
    p.add_argument('--limit',type=int,default=0,help='Smoke-test only. Nonzero must not be reported as full training.')
    args=p.parse_args()
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    torch.set_num_threads(4)
    df=pd.read_csv(args.data)
    train=df[df.split=='train']; test=df[df.split=='test']
    if args.limit:
        train=train.groupby('target',group_keys=False).sample(n=max(args.limit//2,4),random_state=42)
        test=test.groupby('target',group_keys=False).sample(n=max(args.limit//8,2),random_state=42)
    train,val=train_test_split(train,test_size=.1,stratify=train.target,random_state=42)
    base='distilbert/distilbert-base-uncased'
    from huggingface_hub import model_info
    revision=model_info(base).sha
    tokenizer=AutoTokenizer.from_pretrained(base,revision=revision)
    model=AutoModelForSequenceClassification.from_pretrained(base,revision=revision,num_labels=2)
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device);model.gradient_checkpointing_enable()
    loaders={name:DataLoader(Reviews(frame,tokenizer),batch_size=args.batch_size,shuffle=name=='train') for name,frame in [('train',train),('validation',val),('test',test)]}
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.learning_rate,weight_decay=.01)
    output=Path(args.output);checkpoint=output.with_suffix('');checkpoint.mkdir(parents=True,exist_ok=True)
    best=float('inf');history=[];start=time.monotonic()
    for epoch in range(args.epochs):
        metrics={'epoch':epoch+1}
        for phase in ('train','validation'):
            model.train(phase=='train');loss_sum=0;correct=0;total=0
            for batch in loaders[phase]:
                batch={k:v.to(device) for k,v in batch.items()}
                with torch.set_grad_enabled(phase=='train'):
                    result=model(**batch)
                    if phase=='train':
                        optimizer.zero_grad();result.loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
                n=len(batch['labels']);loss_sum+=result.loss.item()*n
                correct+=(result.logits.argmax(1)==batch['labels']).sum().item();total+=n
            metrics[phase+'_loss']=loss_sum/total;metrics[phase+'_accuracy']=correct/total
        history.append(metrics);print(json.dumps(metrics),flush=True)
        if metrics['validation_loss']<best:
            best=metrics['validation_loss'];model.save_pretrained(checkpoint);tokenizer.save_pretrained(checkpoint)
        output.with_name(output.stem+'_history.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
    model=AutoModelForSequenceClassification.from_pretrained(checkpoint,local_files_only=True).to(device).eval()
    truth=[];probs=[]
    with torch.inference_mode():
        for batch in loaders['test']:
            truth.extend(batch['labels'].tolist());batch={k:v.to(device) for k,v in batch.items()}
            probs.extend(torch.softmax(model(**batch).logits,dim=1)[:,1].cpu().tolist())
    pred=(np.array(probs)>=.5).astype(int)
    metrics={'model_name':'distilbert_finetuned','version':str(int(time.time())), 'base_model':base,'revision':revision,
        'language':'en','task':'original vs computer generated reviews','smoke_test':bool(args.limit),
        'learning_rate':args.learning_rate,'batch_size':args.batch_size,'epochs':args.epochs,'loss_function':'CrossEntropyLoss',
        'max_length':128,'optimizer':'AdamW','weight_decay':.01,'random_state':42,'train_size':len(train),'validation_size':len(val),'test_size':len(test),
        'device':str(device),'elapsed_seconds':time.monotonic()-start,'accuracy':accuracy_score(truth,pred),
        'roc_auc':roc_auc_score(truth,probs),'classification_report':classification_report(truth,pred,output_dict=True),
        'confusion_matrix':confusion_matrix(truth,pred).tolist(),'history':history}
    output.with_suffix('.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    joblib.dump(BertAdapter(checkpoint.resolve()),output)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for phase in ('train','validation'):
        axes[0].plot([x['epoch'] for x in history],[x[phase+'_loss'] for x in history],label=phase)
        axes[1].plot([x['epoch'] for x in history],[x[phase+'_accuracy'] for x in history],label=phase)
    axes[0].set_title('Loss');axes[1].set_title('Accuracy')
    for ax in axes:ax.set_xlabel('Epoch');ax.legend()
    fig.tight_layout();fig.savefig(output.with_name(output.stem+'_curves.png'),dpi=150)
    baseline=json.loads((ROOT/'ml/models/fake_review_model.json').read_text(encoding='utf-8'))
    comparison=pd.DataFrame([{'model':'SVM calibrated','test_size':baseline['test_size'],'accuracy':baseline['accuracy'],'f1_macro':baseline['classification_report']['macro avg']['f1-score']},
        {'model':'DistilBERT'+(' SMOKE ONLY' if args.limit else ''),'test_size':len(test),'accuracy':metrics['accuracy'],'f1_macro':metrics['classification_report']['macro avg']['f1-score']}])
    comparison.to_csv(output.with_name(output.stem+'_comparison.csv'),index=False)
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':main()
