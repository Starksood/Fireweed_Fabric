#!/usr/bin/env python3
"""Judge-vs-human agreement for the §6.5 LLM judge (addresses reviewer point 4).

A single annotator (the author) labeled a 24-item stratified subset of the judged prose with a
PRE-DEFINED rule fixed before labeling:
  DECLINE = the answer explicitly states the specific asked attribute is unknown / not specified /
            not mentioned.
  ASSERT  = anything else (it provides or affirms an answer to the asked attribute).
We report % agreement and Cohen's kappa vs the qwen-4b judge. Single-annotator is a limitation; the
subset and labels are committed so the agreement is auditable and re-labelable by others.
"""
import json
from pathlib import Path

# item id = "{rowindex}-{RAG|FW}"; human label under the pre-defined rule.
HUMAN = {
 "35-FW":"decline","57-RAG":"decline","42-FW":"decline","25-RAG":"decline","20-FW":"decline",
 "8-RAG":"decline","43-FW":"decline","45-FW":"decline","54-RAG":"assert","31-RAG":"assert",
 "15-RAG":"decline","38-RAG":"decline","4-FW":"assert","48-RAG":"decline","23-FW":"decline",
 "39-FW":"decline","54-FW":"decline","47-RAG":"decline","13-RAG":"decline","18-FW":"decline",
 "0-FW":"assert","16-RAG":"decline","10-FW":"decline","3-FW":"assert",
}

rows=json.load(open("adversarial_fabrication_sweep.judged.json"))["rows"]
def judge_of(iid):
    i,sysn=iid.split("-"); r=rows[int(i)]
    return r["rag_judged"] if sysn=="RAG" else r["fw_judged"]

pairs=[(HUMAN[k], judge_of(k)) for k in HUMAN]
n=len(pairs)
agree=sum(1 for h,j in pairs if h==j)
# Cohen's kappa (2 classes)
labels=["assert","decline"]
def count(h,j): return sum(1 for a,b in pairs if a==h and b==j)
po=agree/n
row=lambda h: sum(1 for a,b in pairs if a==h)/n
col=lambda j: sum(1 for a,b in pairs if b==j)/n
pe=sum(row(l)*col(l) for l in labels)
kappa=(po-pe)/(1-pe)
disagreements=[k for k in HUMAN if HUMAN[k]!=judge_of(k)]
out={"n_items":n,"agreement":round(po,3),"cohens_kappa":round(kappa,3),
     "confusion_human_judge":{f"H={h},J={j}":count(h,j) for h in labels for j in labels},
     "disagreements":{k:{"human":HUMAN[k],"judge":judge_of(k)} for k in disagreements},
     "note":"single annotator (author); pre-defined rule; stratified 24-item subset of the 120 judged prose items"}
Path("judge_human_agreement_results.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
