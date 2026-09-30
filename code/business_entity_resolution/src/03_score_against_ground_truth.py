"""
Score a matching_results.tsv-style file against a ground-truth file using
the challenge's own macro F0.5 formula. Used throughout development to
verify every methodology change against real numbers instead of assumptions
-- every score quoted in METHODOLOGY.md was produced by this
script.

IDs are encoded as ints (source-prefix bit-packed with the numeric suffix)
rather than kept as strings, and the ground-truth file is the only thing
held fully in memory -- this keeps peak memory low enough to score the full
~2.2M-row training set inside a ~3.9GB-RAM environment. The scorer built
into this script also handles a prediction file that only covers a *subset*
of ground-truth IDs (e.g. a fast sample run) without incorrectly penalizing
the score for entities that were never predicted on -- see --sample-mode.

Usage:
    python3 03_score_against_ground_truth.py <predictions.tsv> <ground_truth.tsv> [--sample-mode]
"""
import sys, csv, argparse


def encode_ids(s):
    # "S2-123456" -> (2<<48)|123456 ; "S3-123456" -> (3<<48)|123456
    # (int encoding instead of raw strings roughly halves memory vs a
    # dict-of-string-sets for a ground-truth file this large)
    out = []
    if not s:
        return frozenset()
    for tok in s.split(','):
        if not tok:
            continue
        src = tok[1]
        num = int(tok[3:])
        out.append((int(src) << 48) | num)
    return frozenset(out)


def load_truth(path):
    m = {}
    with open(path, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)
        for row in reader:
            if not row or not row[0]:
                continue
            sid = row[0]
            ids = row[1] if len(row) > 1 else ''
            m[sid] = encode_ids(ids)
    return m


def f_beta(precision, recall, beta=0.5):
    if precision == 0 and recall == 0:
        return 0.0
    b2 = beta * beta
    denom = b2 * precision + recall
    return 0.0 if denom == 0 else (1 + b2) * precision * recall / denom


def score(pred_path, truth_path, sample_mode):
    print('loading ground truth...', flush=True)
    truth = load_truth(truth_path)
    print(f'  {len(truth)} truth entries loaded', flush=True)

    total = 0.0
    n = 0
    n_matched_nonempty = 0
    seen_pred_ids = set()

    with open(pred_path, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)
        for row in reader:
            if not row or not row[0]:
                continue
            sid = row[0]
            seen_pred_ids.add(sid)
            pred = encode_ids(row[1] if len(row) > 1 else '')
            gt = truth.get(sid, frozenset())
            if not pred and not gt:
                total += 1.0
            elif not pred and gt:
                total += 0.0
            else:
                tp = len(pred & gt)
                precision = tp / len(pred) if pred else 0.0
                recall = tp / len(gt) if gt else 0.0
                total += f_beta(precision, recall, 0.5)
            if pred:
                n_matched_nonempty += 1
            n += 1

    if not sample_mode:
        # any ground-truth id with no row at all in the prediction file is a
        # missing prediction, not something to silently ignore. Skip this
        # (--sample-mode) when scoring a prediction file that only covers a
        # deliberate subset of Source-1 (e.g. a fast dev sample), or every
        # non-sampled entity gets counted as an empty prediction and the
        # score becomes meaningless.
        missing = set(truth.keys()) - seen_pred_ids
        for sid in missing:
            gt = truth[sid]
            if not gt:
                total += 1.0
            n += 1

    print(f'entities scored: {n}  matched(non-empty pred): {n_matched_nonempty} '
          f'({n_matched_nonempty / n * 100:.1f}%)')
    print(f'macro F0.5 = {total / n:.4f}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('predictions')
    ap.add_argument('ground_truth')
    ap.add_argument('--sample-mode', action='store_true',
                     help='predictions file only covers a subset of ground_truth IDs '
                          '(e.g. a fast dev sample) -- do not penalize for ids outside it')
    a = ap.parse_args()
    score(a.predictions, a.ground_truth, a.sample_mode)
