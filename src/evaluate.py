import pandas as pd
import numpy as np
import re
import time
from src.model import YoModel
from tqdm import tqdm
from typing import List, Tuple
from src.utils import WORDS_REGEX
from dataclasses import dataclass, asdict
from sklearn.metrics import accuracy_score, precision_score, recall_score, \
    f1_score, roc_auc_score


@dataclass
class EvaluateResult:
    """Model evaluation result."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auroc: float
    wall_time: float
    cpu_time: float
    token_to_sec: float

    def __str__(self):
        return "\n".join([f"{m}: {v}" for m, v in asdict(self).items()])

def get_token_counts(text: str) -> int:
    """Calculate count of token in text"""
    return len(list(re.finditer(WORDS_REGEX, text)))


def get_substrings(text: str) -> List[Tuple[int]]:
    """Extracts ye (yo) word indexes from text"""
    res = []
    for re_match in re.finditer(WORDS_REGEX, text):
        if re.search(r'[ЕЁеё]', re_match.group()) is not None:
            res.append(re_match.span())
    return res


def substrings2onehot(text: str, positions: List[Tuple[int, int]]) -> np.ndarray[bool]:
    """Transforms substring positions to one hot vector"""
    words_pos = get_substrings(text)
    one_hot_index = np.zeros(len(words_pos), dtype=bool)
    for i, pos in enumerate(positions):
        if pos in words_pos:
            one_hot_index.put(i, True)

    return one_hot_index


def evaluate_model(model: YoModel, data: pd.DataFrame, verbose: bool = False) -> EvaluateResult:
    X = data['ye_text'].to_list()
    y_true = data["yo_words"].to_list()

    wall_time = time.time()
    cpu_time = time.process_time()
    y_pred = model.predict(X, verbose=verbose)
    wall_time = time.time() - wall_time
    cpu_time = time.process_time() - cpu_time
    
    y_true_onehot = []
    y_pred_onehot =[]

    if verbose:
        X = tqdm(X, desc="Index to onehot")

    for i, text in enumerate(X):
        y_true_onehot.extend(substrings2onehot(text, y_true[i]))
        y_pred_onehot.extend(substrings2onehot(text, y_pred[i]))

    count_tokens = data['ye_text'].apply(get_token_counts).sum()

    res = EvaluateResult(
        accuracy=accuracy_score(y_true_onehot, y_pred_onehot),
        precision=precision_score(y_true_onehot, y_pred_onehot),
        recall=recall_score(y_true_onehot, y_pred_onehot),
        f1_score=f1_score(y_true_onehot, y_pred_onehot),
        auroc=roc_auc_score(y_true_onehot, y_pred_onehot),
        wall_time=wall_time,
        cpu_time=cpu_time,
        token_to_sec=count_tokens/wall_time
    )
    
    if verbose:
        print("Metrics\n" + str(res))

    return res