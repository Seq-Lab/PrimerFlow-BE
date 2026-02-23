import gzip
import os
import sqlite3

# ---------------------------------------------------------
# 1. 경로 및 설정
# ---------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

DB_PATH = os.path.join(BASE_DIR, "database", "annotations.db")
RAW_DATA_DIR = os.path.join(BASE_DIR, "database", "raw_data")

# 제한 효소 목록 (필요시 추가)
ENZYMES = {
    'EcoRI': 'GAATTC',
    'BamHI': 'GGATCC',
    'HindIII': 'AAGCTT',
    'NotI': 'GCGGCCGC'
}

def get_db_connection():
    # DB 파일이 위치할 디렉터리가 없으면 생성하여 연결 오류를 방지
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_schema(conn):
    cursor = conn.cursor()
    print("⚙️  스키마 재설정 중 (기존 데이터 삭제)...")
    
    # 기존 테이블 삭제 후 재생성 (Clean Build)
    cursor.executescript("""
        DROP TABLE IF EXISTS snp;
        DROP TABLE IF EXISTS restriction_site;
        DROP TABLE IF EXISTS exon;
        DROP TABLE IF EXISTS repeats;

        CREATE TABLE snp (id INTEGER PRIMARY KEY, chrom TEXT, pos INTEGER);
        CREATE TABLE restriction_site (id INTEGER PRIMARY KEY, chrom TEXT, name TEXT, start INTEGER, end INTEGER);
        CREATE TABLE exon (id INTEGER PRIMARY KEY, chrom TEXT, start INTEGER, end INTEGER, transcript_id TEXT);
        CREATE TABLE repeats (id INTEGER PRIMARY KEY, chrom TEXT, start INTEGER, end INTEGER);
        
        CREATE INDEX idx_snp ON snp(chrom, pos);
        CREATE INDEX idx_res ON restriction_site(chrom, start);
        CREATE INDEX idx_exon ON exon(chrom, start, end);
        CREATE INDEX idx_repeats ON repeats(chrom, start, end);
    """)
    print("✅ 스키마 준비 완료")

# ---------------------------------------------------------
# 제너레이터(Generator) 기반 파서: 메모리 OOM 방지
# ---------------------------------------------------------
def parse_gff3(filename):
    path = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"⚠️ Exon GFF3 파일이 존재하지 않아 파싱을 건너뜁니다: {path}")
        return
    print(f"📖 Exon 파싱 시작: {filename}")
    open_func = gzip.open if filename.endswith('.gz') else open
    try:
        with open_func(path, 'rt', encoding='utf-8') as f:
            for line in f:
                if line.startswith("#"): continue
                parts = line.strip().split('\t')
                if len(parts) < 9 or parts[2] != 'exon': continue
                chrom, start, end = parts[0], int(parts[3]), int(parts[4])
                attr = parts[8]
                tid = "unknown"
                if "Parent=" in attr:
                    tid = attr.split("Parent=")[1].split(";")[0].replace("transcript:", "")
                # 리스트에 담지 않고 바로바로 반환(yield)
                yield (chrom, start, end, tid)
    except Exception as e:
        print(f"❌ Exon 파싱 오류: {e}")

def parse_vcf(filename):
    path = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"⚠️ SNP VCF 파일을 찾을 수 없습니다: {path}")
        return
    print(f"📖 SNP 파싱 시작: {filename}")
    open_func = gzip.open if filename.endswith('.gz') else open
    try:
        with open_func(path, 'rt', encoding='utf-8') as f:
            for line in f:
                if line.startswith("#"): continue
                parts = line.strip().split('\t')
                if len(parts) < 2: continue
                yield (parts[0], int(parts[1]))
    except Exception as e:
        print(f"❌ SNP 파싱 오류: {e}")

def parse_repeats_rmsk(filename):
    path = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"⚠️  파일 없음: {filename} (Repeats 건너뜀)")
        return
    print(f"📖 Repeats 파싱 시작: {filename}")
    open_func = gzip.open if filename.endswith('.gz') else open
    try:
        with open_func(path, 'rt', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 8: continue
                chrom = parts[5]
                start = int(parts[6]) + 1
                end = int(parts[7])
                yield (chrom, start, end)
    except Exception as e:
        print(f"❌ Repeats 파싱 오류: {e}")

# ---------------------------------------------------------
# Rolling Window 기반 FASTA 스캐너: 대용량 염색체 OOM 방지
# ---------------------------------------------------------
def scan_restriction_sites(fasta_filename, chunk_size=1000000):
    path = os.path.join(RAW_DATA_DIR, fasta_filename)
    if not os.path.exists(path):
        print(f"⚠️  파일 없음: {fasta_filename} (제한효소 스캔 건너뜀)")
        return

    print(f"🕵️ 제한효소 스캔 시작 (FASTA 읽는 중... 시간 소요 예상): {fasta_filename}")
    open_func = gzip.open if fasta_filename.endswith('.gz') else open
    
    # 모티프가 청크 경계에 걸치는 것을 방지하기 위한 오버랩 길이 설정
    overlap_len = max(len(m) for m in ENZYMES.values()) - 1 if ENZYMES else 0

    try:
        with open_func(path, 'rt', encoding='utf-8') as f:
            buffer = ""
            global_pos = 0
            current_chrom = None
            
            def process_buffer(buf, g_pos, is_last=False):
                buf_up = buf.upper()
                # 마지막 청크가 아니면 오버랩 영역에서 시작하는 모티프는 다음 청크로 넘김 (중복 방지)
                limit = len(buf) if is_last else len(buf) - overlap_len
                for name, motif in ENZYMES.items():
                    pos = buf_up.find(motif)
                    while pos != -1 and pos < limit:
                        yield (current_chrom, name, g_pos + pos + 1, g_pos + pos + len(motif))
                        pos = buf_up.find(motif, pos + 1)

            for line in f:
                line = line.strip()
                if not line: continue
                if line.startswith(">"):
                    if current_chrom and buffer:
                        yield from process_buffer(buffer, global_pos, is_last=True)
                        print(f"   -> {current_chrom} 스캔 완료")
                    current_chrom = line[1:].split()[0]
                    buffer = ""
                    global_pos = 0
                else:
                    buffer += line
                    # 버퍼가 chunk_size 이상 커지면 스캔 후 털어냄 (Rolling Window)
                    if len(buffer) >= chunk_size:
                        yield from process_buffer(buffer, global_pos, is_last=False)
                        advance = len(buffer) - overlap_len
                        global_pos += advance
                        buffer = buffer[-overlap_len:]
            
            # 마지막 염색체의 남은 버퍼 처리
            if current_chrom and buffer:
                yield from process_buffer(buffer, global_pos, is_last=True)
                print(f"   -> {current_chrom} 스캔 완료")

    except Exception as e:
        print(f"❌ 제한효소 스캔 오류: {e}")

# ---------------------------------------------------------
# Batch Insert Helper: DB 적재 시 메모리/트랜잭션 최적화
# ---------------------------------------------------------
def insert_in_batches(cursor, conn, query, generator, batch_size=100000):
    batch = []
    count = 0
    for record in generator:
        batch.append(record)
        if len(batch) >= batch_size:
            cursor.executemany(query, batch)
            conn.commit()
            count += len(batch)
            batch = []
    if batch:
        cursor.executemany(query, batch)
        conn.commit()
        count += len(batch)
    return count

def main():
    conn = get_db_connection()
    init_schema(conn)
    cursor = conn.cursor()

    # 1. Exon
    exons_gen = parse_gff3("gencode.v49.annotation.gff3.gz") 
    if exons_gen:
        print("💾 Exon 데이터 스트리밍 저장 시작...")
        count = insert_in_batches(cursor, conn, "INSERT INTO exon (chrom, start, end, transcript_id) VALUES (?, ?, ?, ?)", exons_gen)
        print(f"   -> ✅ Exon {count:,}개 저장 완료")

    # 2. SNP
    snps_gen = parse_vcf("clinvar.vcf.gz")
    if snps_gen:
        print("💾 SNP 데이터 스트리밍 저장 시작...")
        count = insert_in_batches(cursor, conn, "INSERT INTO snp (chrom, pos) VALUES (?, ?)", snps_gen)
        print(f"   -> ✅ SNP {count:,}개 저장 완료")

    # 3. Repeats
    repeats_gen = parse_repeats_rmsk("rmsk.txt.gz")
    if repeats_gen:
        print("💾 Repeats 데이터 스트리밍 저장 시작...")
        count = insert_in_batches(cursor, conn, "INSERT INTO repeats (chrom, start, end) VALUES (?, ?, ?)", repeats_gen)
        print(f"   -> ✅ Repeats {count:,}개 저장 완료")

    # 4. Restriction Sites
    res_sites_gen = scan_restriction_sites("GRCh38.primary_assembly.genome.fa.gz")
    if res_sites_gen:
        print("💾 Restriction Site 데이터 스트리밍 저장 시작...")
        count = insert_in_batches(cursor, conn, "INSERT INTO restriction_site (chrom, name, start, end) VALUES (?, ?, ?, ?)", res_sites_gen)
        print(f"   -> ✅ Restriction Site {count:,}개 저장 완료")

    conn.close()
    print(f"\n🎉 최종 DB 구축 완료! 파일 위치: {DB_PATH}")

if __name__ == "__main__":
    main()
