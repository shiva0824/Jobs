import os
import json
import boto3
import torch
import spacy
from transformers import AutoTokenizer, AutoModelForTokenClassification

# --- S3 Setup ---
s3 = boto3.client("s3")
BUCKET_NAME = "job-skill-extractor"

# --- Local cache paths ---
LOCAL_MODEL_DIR = os.path.join("models", "bert-base-cased")
os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)

DICT_FILE = "dictionaries/lookup_phrases.json"
dict_local_path = os.path.join("dictionaries", "lookup_phrases.json")
os.makedirs(os.path.dirname(dict_local_path), exist_ok=True)

# --- Download dictionary if not already cached ---
if not os.path.exists(dict_local_path):
    s3.download_file(BUCKET_NAME, DICT_FILE, dict_local_path)

with open(dict_local_path, "r", encoding="utf-8") as f:
    lookup_phrases = json.load(f)

# --- Download model files if missing ---
MODEL_PREFIX = "models/bert-base-cased/"
def download_model_from_s3():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=MODEL_PREFIX)
    if "Contents" not in response:
        raise RuntimeError(f"No objects found in S3 at {MODEL_PREFIX}")

    for obj in response["Contents"]:
        key = obj["Key"]
        if key.endswith("/"):  # skip folders
            continue
        local_path = os.path.join(LOCAL_MODEL_DIR, os.path.basename(key))
        if not os.path.exists(local_path):
            s3.download_file(BUCKET_NAME, key, local_path)

#download_model_from_s3()

# --- Load model & tokenizer once ---
tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_DIR)
model = AutoModelForTokenClassification.from_pretrained(LOCAL_MODEL_DIR)
model.eval()

# --- Load label mappings ---
label_map_path = os.path.join(LOCAL_MODEL_DIR, "label_mappings.json")
with open(label_map_path, "r", encoding="utf-8") as f:
    mappings = json.load(f)
id2tag = {int(k): v for k, v in mappings["id2tag"].items()}

# --- Precompile dictionary lookups ---
technical_groups = ["SKILL_PHRASES", "TOOL_PHRASES", "LANG_PHRASES", "FIELD_PHRASES"]
technical_dict = set(sum([lookup_phrases.get(g, []) for g in technical_groups], []))
soft_dict = set(lookup_phrases.get("SOFT_SKILL_PHRASES", []))

# --- Global sets ---
STOPWORDS = {
    "and","or","to","for","of","the","an","a","with","in","on","at","by","from",
    "up","about","into","through","during","before","after","above","below",
    "between","among","again","further","then","once"
}

PROTECTED_TERMS = {
    "AI","ML","BI","UI","UX","DB","OS","JS","CSS","SQL","AWS","GCP","API","SDK",
    "CLI","IDE","JWT","SSL","TLS","TCP","UDP","DNS","CDN","VPN","SSH","FTP",
    "HTTP","HTTPS","JSON","XML","CSV","PDF","PNG","JPG","GIF","SVG","AR","VR",
    "IoT","NLP","GPU","CPU","RAM","SSD","HDD","QA","QC","CI","CD","OOP","MVC",
    "MVP","SPA","PWA","DevOps","MLOps"
}

COMMON_SUFFIXES = {
    "ing","ed","er","est","ly","tion","sion","ness","ment","ful","less","able",
    "ible","ous","ive","al","ic","ical","ary","ory","ent","ant","ure","ade","age",
    "ism","ist","ite","ize","ise","ate","ify","en","ward","wise","like","ship",
    "hood","dom","craft","ware"
}

MEANINGLESS_SHORT = {
    "is","it","be","to","do","go","we","me","my","he","his","her","you","your",
    "our","they","them","this","that","these","those","what","when","where","why",
    "how","all","any","can","had","has","have","will","would","could","should",
    "may","might","must","shall","am","are","was","were","been","being","get",
    "got","make","made","take","took","come","came","give","gave","find","found",
    "think","thought","know","knew","see","saw","look","use","used","work","works",
    "need","needs","want","wants","try","tried","ask","asked","seem","seems",
    "feel","felt","leave","left","put","set","run","ran","move","moved","play",
    "played","turn","turned","start","started","show","showed","help","helped",
    "change","changed","end","ended"
}

# --- SpaCy for lemmatization ---
nlp = spacy.load("en_core_web_sm")

# -------------------------------
# Core helpers
# -------------------------------

def is_fragment(skill, existing):
    """General fragment detection logic"""
    skill_lower = skill.lower()
    existing_lower = existing.lower()

    # Case 1: prefix fragment
    if (len(skill) <= 3 and existing_lower.startswith(skill_lower)
        and skill.upper() not in PROTECTED_TERMS and len(existing) > len(skill) * 2):
        return True

    # Case 2: word overlap fragment
    skill_words = skill_lower.split()
    existing_words = existing_lower.split()
    if len(skill_words) >= 2 and len(existing_words) >= 2:
        if (len(skill_words) < len(existing_words)
            and len(set(skill_words) & set(existing_words)) >= len(skill_words) - 1):
            return True
        if (skill_words[-1] == existing_words[-1]
            and len(skill_words) == len(existing_words)
            and len(skill) < len(existing)):
            if (len(skill_words[0]) < len(existing_words[0])
                and (existing_words[0].endswith(skill_words[0])
                     or existing_words[0].startswith(skill_words[0]))):
                return True

    # Case 3: direct substring
    if skill_lower in existing_lower and len(skill) < len(existing):
        if len(skill) <= len(existing) * 0.6:
            return True

    # Case 4: single word fragment inside phrase
    if skill_lower in existing_words and len(skill) < len(existing):
        return True

    # Case 5: plural/singular variation
    if (skill_lower + "s" == existing_lower or
        skill_lower + "es" == existing_lower or
        skill_lower[:-1] + "ies" == existing_lower or
        existing_lower + "s" == skill_lower):
        return True

    return False

def deduplicate_and_remove_fragments(skills):
    if not skills:
        return []
    sorted_skills = sorted(set(skills), key=len, reverse=True)
    result = []
    for skill in sorted_skills:
        skill = skill.strip()
        if not skill:
            continue
        skip = False
        for existing in result:
            if skill.lower() == existing.lower():
                skip = True
                break
            if is_fragment(skill, existing):
                skip = True
                break
        if not skip:
            result.append(skill)
    return sorted(result)

def deduplicate_skills(skills):
    if not skills:
        return []
    groups = {}
    for skill in skills:
        key = skill.lower()
        groups.setdefault(key, []).append(skill)
    result = []
    for variants in groups.values():
        best = variants[0]
        for v in variants:
            if v.istitle() and not best.istitle():
                best = v
            elif not v.islower() and best.islower():
                best = v
            elif len(v) > len(best):
                best = v
            elif len(v) <= 3 and v.isupper() and not best.isupper():
                best = v
        result.append(best)
    return sorted(result)

def is_valid_final_entity(entity):
    entity = entity.strip()
    if not entity or len(entity) == 1:
        return False
    if not any(c.isalpha() for c in entity):
        return False
    if len(entity) <= 2 and entity.upper() not in PROTECTED_TERMS:
        return False
    if entity.lower() in COMMON_SUFFIXES:
        return False
    if entity.lower() in STOPWORDS:
        return False
    if entity.lower() in MEANINGLESS_SHORT:
        return False
    return True

def merge_subword_tokens(tokens, predictions, confidences):
    """Merges subwords into entities (merge first, clean later)"""
    entities = []
    current_entity, current_confidences, current_tag = "", [], "O"
    i = 0
    while i < len(tokens):
        token = tokens[i]
        pred_id = predictions[i]
        conf = confidences[i]
        tag = id2tag.get(pred_id, "O")

        # skip special tokens only
        if token in ["[CLS]","[SEP]","[PAD]","[UNK]","[MASK]"]:
            i += 1
            continue

        if tag == "O":
            if current_entity and current_tag != "O":
                cleaned = current_entity.strip()
                if is_valid_final_entity(cleaned):
                    avg_conf = sum(current_confidences)/len(current_confidences)
                    entities.append((cleaned, avg_conf, False))
            current_entity, current_confidences, current_tag = "", [], "O"
        else:
            if tag.startswith("B-") or (tag.startswith("I-") and current_tag == "O"):
                if current_entity and current_tag != "O":
                    cleaned = current_entity.strip()
                    if is_valid_final_entity(cleaned):
                        avg_conf = sum(current_confidences)/len(current_confidences)
                        entities.append((cleaned, avg_conf, False))
                current_entity = token[2:] if token.startswith("##") else token
                current_confidences, current_tag = [conf], tag
            elif tag.startswith("I-") and current_tag != "O" and current_tag.split("-")[-1] == tag.split("-")[-1]:
                current_entity += token[2:] if token.startswith("##") else " " + token
                current_confidences.append(conf)
            else:
                if current_entity and current_tag != "O":
                    cleaned = current_entity.strip()
                    if is_valid_final_entity(cleaned):
                        avg_conf = sum(current_confidences)/len(current_confidences)
                        entities.append((cleaned, avg_conf, False))
                current_entity = token[2:] if token.startswith("##") else token
                current_confidences, current_tag = [conf], tag
        i += 1

    if current_entity and current_tag != "O":
        cleaned = current_entity.strip()
        if is_valid_final_entity(cleaned):
            avg_conf = sum(current_confidences)/len(current_confidences)
            entities.append((cleaned, avg_conf, False))
    return entities

def postprocess_entities(entities, dictionary, conf_threshold=0.85):
    final = []
    for e, conf, from_dict in entities:
        e = e.strip()
        if not e:
            continue
        if from_dict or e in dictionary:
            if len(e) > 1 and e.lower() not in STOPWORDS:
                final.append(e)
            continue
        if conf < conf_threshold:
            continue
        if not is_valid_final_entity(e):
            continue
        if len(e) < 3:
            continue
        alpha_count = sum(1 for c in e if c.isalnum())
        if alpha_count < max(2, len(e) * 0.6):
            continue
        if "/" in e:
            parts = [p.strip() for p in e.split("/") if p.strip()]
            final.extend([p for p in parts if is_valid_final_entity(p)])
            continue
        final.append(e)

    cleaned = []
    final_set = set(final)
    for e in final:
        skip = False
        for other in final_set:
            if e != other and is_fragment(e, other):
                skip = True
                break
        if not skip:
            cleaned.append(e)
    return deduplicate_skills(cleaned)

# -------------------------------
# Main extraction
# -------------------------------
def extract_skills(text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    confidences, predictions = torch.max(probs, dim=2)
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    confidences, predictions = confidences[0].tolist(), predictions[0].tolist()

    model_entities = merge_subword_tokens(tokens, predictions, confidences)

    text_lower = text.lower()
    raw_dict_matches = [p for g in technical_groups for p in lookup_phrases.get(g, []) if p.lower() in text_lower]
    technical_matches = []
    for p in raw_dict_matches:
        if "/" in p:
            technical_matches.extend([part.strip() for part in p.split("/") if part.strip()])
        else:
            technical_matches.append(p)
    soft_matches = [p for p in soft_dict if p.lower() in text_lower]

    clean_model = postprocess_entities(model_entities, technical_dict, conf_threshold=0.92)
    all_technical = clean_model + technical_matches
    clean_technical = deduplicate_and_remove_fragments(all_technical)
    clean_soft = postprocess_entities([(s, 1.0, True) for s in soft_matches], soft_dict)

    already_found = set([s.lower() for s in clean_technical + clean_soft])
    suggested_entities = [e for e in model_entities if e[0].lower() not in already_found
                          and e[0] not in technical_dict and e[0] not in soft_dict]
    suggested = postprocess_entities(suggested_entities, set(), conf_threshold=0.95)

    clean_technical = [t for t in clean_technical if t.lower() not in [s.lower() for s in clean_soft] and is_valid_final_entity(t)]
    clean_soft = [s for s in clean_soft if is_valid_final_entity(s)]
    suggested = [s for s in suggested if is_valid_final_entity(s)]

    return {
        "technical_skills": clean_technical,
        "soft_skills": clean_soft,
        "suggested": suggested
    }