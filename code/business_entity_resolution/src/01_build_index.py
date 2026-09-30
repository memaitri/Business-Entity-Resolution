"""
Build a disk-backed SQLite blocking index from Source-2 and Source-3.

Same blocking key as v1 (country | sorted, suffix-stripped name tokens), but
now ALSO stores a compact address-token string per record. v1 only stored
zip, which is why v1 had no fallback signal when a bucket had no usable zip.

Usage:
    python3 01_build_index.py <source2.tsv> <source3.tsv> <db_path>

Example (test set):
    python3 01_build_index.py /path/to/test_source2.tsv /path/to/test_source3.tsv /work/test_index.db
"""
import csv, sqlite3, time, os, sys, resource

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import normalize_text, norm_name_key, extract_zip, addr_tokens

csv.field_size_limit(sys.maxsize)


def mem_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def build(files, db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA synchronous=OFF')
    conn.execute('PRAGMA journal_mode=OFF')
    conn.execute('PRAGMA temp_store=MEMORY')
    conn.execute('CREATE TABLE records (key TEXT, zip TEXT, addr TEXT, id TEXT)')

    total = 0
    for path in files:
        t0 = time.time()
        n = 0
        batch = []
        with open(path, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader)
            idx = {c: i for i, c in enumerate(header)}
            for row in reader:
                entity_id = row[idx['entity_id']]
                name = row[idx['business_name']]
                addr = row[idx['business_address']]
                country = row[idx['country']]
                key = normalize_text(country) + '|' + norm_name_key(name)
                z = extract_zip(addr)
                at = ' '.join(sorted(addr_tokens(addr)))
                batch.append((key, z, at, entity_id))
                n += 1
                if len(batch) >= 50000:
                    conn.executemany('INSERT INTO records VALUES (?,?,?,?)', batch)
                    batch = []
                    if n % 1000000 == 0:
                        print(f'  {os.path.basename(path)}: {n} rows, {time.time()-t0:.1f}s, mem={mem_mb():.0f}MB', flush=True)
        if batch:
            conn.executemany('INSERT INTO records VALUES (?,?,?,?)', batch)
        conn.commit()
        print(f'  {os.path.basename(path)}: DONE {n} rows in {time.time()-t0:.1f}s, mem={mem_mb():.0f}MB', flush=True)
        total += n

    print('=== creating SQL index on key ===', flush=True)
    t0 = time.time()
    conn.execute('CREATE INDEX idx_key ON records(key)')
    conn.commit()
    print(f'index created in {time.time()-t0:.1f}s, mem={mem_mb():.0f}MB', flush=True)
    print('total records indexed:', total, flush=True)
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    source2, source3, db_path = sys.argv[1], sys.argv[2], sys.argv[3]
    build([source2, source3], db_path)
