import sqlite3
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np
import pysam

############################################
# Thermodynamics & Alignment Utilities
############################################
RC_MAP = str.maketrans("ATCG", "TAGC")

def reverse_complement(seq: str) -> str:
    return seq.translate(RC_MAP)[::-1]

NN_PARAMS = {
    "AA": (-7.9, -22.2),
    "TT": (-7.9, -22.2),
    "AT": (-7.2, -20.4),
    "TA": (-7.2, -21.3),
    "CA": (-8.5, -22.7),
    "TG": (-8.5, -22.7),
    "GT": (-8.4, -22.4),
    "AC": (-8.4, -22.4),
    "CT": (-7.8, -21.0),
    "AG": (-7.8, -21.0),
    "GA": (-8.2, -22.2),
    "TC": (-8.2, -22.2),
    "CG": (-10.6, -27.2),
    "GC": (-9.8, -24.4),
    "GG": (-8.0, -19.9),
    "CC": (-8.0, -19.9),
}

def calc_tm_nn(seq: str, dna_nM=50.0, salt_mM=50.0) -> float:
    dh, ds = 0.0, 0.0
    for i in range(len(seq) - 1):
        h, s = NN_PARAMS.get(seq[i : i + 2], (0, 0))
        dh += h
        ds += s
    ds_corrected = ds + 0.368 * (len(seq) - 1) * np.log(salt_mM / 1000.0)
    R = 1.987
    c = dna_nM * 1e-9
    denominator = ds_corrected + R * np.log(c / 4)
    if denominator == 0:
        return 0.0
    return ((dh * 1000) / denominator) - 273.15


def needleman_wunsch_mismatch(seq1: str, seq2: str) -> int:
    n, m = len(seq1), len(seq2)
    score_matrix = np.zeros((n + 1, m + 1))
    for i in range(n + 1):
        score_matrix[i][0] = -i
    for j in range(m + 1):
        score_matrix[0][j] = -j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            match = 1 if seq1[i - 1] == seq2[j - 1] else -1
            score_matrix[i][j] = max(
                score_matrix[i - 1][j - 1] + match,
                score_matrix[i - 1][j] - 1,
                score_matrix[i][j - 1] - 1,
            )
    return max(len(seq1), len(seq2)) - int(score_matrix[n][m])


############################################
# Main Designer
############################################
class PrimerDesigner:
    def __init__(self, genome_fasta: str, annotation_db: str):
        self.genome = pysam.FastaFile(genome_fasta)
        self.db = sqlite3.connect(annotation_db)
        self.cur = self.db.cursor()
    def generate_candidates(
        self,
        template: str,
        k_min=18,
        k_max=25,
        tm_range=(57, 63),
        gc_range=(0.4, 0.6),
        max_poly_x=4,
        gc_clamp=True,
    ) -> List[Dict]:
        """Stage 2.1: 물성 기반 후보군 생성 (1-based 반영)"""
        candidates = []
        for k in range(k_min, k_max + 1):
            for i in range(len(template) - k + 1):
                seq = template[i : i + k]
                for strand, s in [("+", seq), ("-", reverse_complement(seq))]:
                    tm = calc_tm_nn(s)
                    if not (tm_range[0] <= tm <= tm_range[1]):
                        continue
                    
                    # 1. Poly-X 필터
                    if any(base * max_poly_x in s for base in "ATCG"):
                        continue

                    # 2. GC Content 필터
                    gc_content = (s.count("G") + s.count("C")) / len(s)
                    if not (gc_range[0] <= gc_content <= gc_range[1]):
                        continue
                        
                    # 3. 3' 말단 안정성 및 GC Clamp
                    dg3 = sum(NN_PARAMS.get(s[-5:][j : j + 2], (0, 0))[0] for j in range(4))
                    if dg3 <= -10.0:
                        continue
                    if gc_clamp and s[-1] not in "GC":
                        continue
                    if s[-5:].count("G") + s[-5:].count("C") > 4:
                        continue
                        
                    candidates.append(
                        {
                            "seq": s,
                            "start": i + 1,  # [수정] 1-based 시작점
                            "end": i + k,    # [수정] 1-based 종료점 (inclusive)
                            "strand": strand,
                            "tm": tm,
                            "dg3": dg3,
                        }
                    )
        return candidates

    # ==========================================
    # 좌표 변환 및 매핑 유틸리티 추가
    # ==========================================
    def locate_template_in_genome(self, template_seq: str) -> Optional[Dict]:
        """Stage 1: 입력된 템플릿 서열의 1-based 게놈 좌표 탐색"""
        for ref in self.genome.references:
            full_seq = self.genome.fetch(ref)
            pos = full_seq.find(template_seq)
            if pos != -1:
                return {
                    "chrom": ref,
                    "genomic_start": pos + 1,  # 1-based 변환
                    "strand": "+",
                    "template_length": len(template_seq)
                }
            rev_seq = reverse_complement(template_seq)
            pos = full_seq.find(rev_seq)
            if pos != -1:
                return {
                    "chrom": ref,
                    "genomic_start": pos + 1,  # 1-based 변환
                    "strand": "-",
                    "template_length": len(template_seq)
                }
        return None

    def map_to_genomic_coords(self, primer: Dict, template_info: Dict) -> Dict:
        """Stage 1.5: 1-based 로컬 좌표를 1-based 게놈 절대 좌표로 변환"""
        p_start = primer["start"]
        p_end = primer["end"]
        
        if template_info["strand"] == "+":
            primer["genomic_start"] = template_info["genomic_start"] + p_start - 1
            primer["genomic_end"] = template_info["genomic_start"] + p_end - 1
            primer["genomic_strand"] = primer["strand"]
        else:
            t_len = template_info["template_length"]
            primer["genomic_start"] = template_info["genomic_start"] + (t_len - p_end)
            primer["genomic_end"] = template_info["genomic_start"] + (t_len - p_start)
            primer["genomic_strand"] = "-" if primer["strand"] == "+" else "+"
            
        primer["chrom"] = template_info["chrom"]
        return primer

    def local_db_filter(
        self,
        chrom: str,
        primer: Dict,
        junction_mode: Literal["none", "flanking", "spanning"] = "none",
        restriction_enzymes: List[str] = [],
        intron_inclusion: bool = True,
        intron_size_range: Optional[Tuple[int, int]] = None,
    ) -> bool:
        """Stage 2.2: 위치 및 구조 기반 필터링 (게놈 절대 좌표 사용)"""
        g_start = primer["genomic_start"]
        g_end = primer["genomic_end"]
        g_strand = primer["genomic_strand"]

        # 1. SNP 필터링 (3' end strictness, inclusive search 적용)
        s_pos, e_pos = (g_end - 4, g_end) if g_strand == "+" else (g_start, g_start + 4)
        self.cur.execute(
            "SELECT COUNT(*) FROM snp WHERE chrom=? AND pos BETWEEN ? AND ?",
            (chrom, s_pos, e_pos),
        )
        if self.cur.fetchone()[0] > 0:
            return False

        # 2. 제한효소 필터링
        if restriction_enzymes:
            placeholders = ",".join(["?"] * len(restriction_enzymes))
            query = f"SELECT COUNT(*) FROM restriction_site WHERE chrom=? AND name IN ({placeholders}) AND NOT (end < ? OR start > ?)"
            self.cur.execute(query, (chrom, *restriction_enzymes, g_start, g_end))
            if self.cur.fetchone()[0] > 0:
                return False

        # 3. Exon/Intron 구조 필터링
        self.cur.execute("SELECT start, end FROM exon WHERE chrom=? ORDER BY start", (chrom,))
        exons = self.cur.fetchall()
        
        # Intron Inclusion 로직
        is_in_intron = any(
            g_start > exons[i][1] and g_end < exons[i + 1][0]
            for i in range(len(exons) - 1)
        )
        if not intron_inclusion and is_in_intron:
            return False

        # Intron Size 제한 확인
        if is_in_intron and intron_size_range:
            for i in range(len(exons) - 1):
                if g_start > exons[i][1] and g_end < exons[i + 1][0]:
                    i_size = exons[i + 1][0] - exons[i][1]
                    if not (intron_size_range[0] <= i_size <= intron_size_range[1]):
                        return False
                        
        # Exon Junction Spanning 로직
        if junction_mode == "spanning":
            is_on_junction = any(
                g_start < e[1] and g_end > exons[idx + 1][0]
                for idx, e in enumerate(exons[:-1])
            )
            if not is_on_junction:
                return False

        return True

    def filter_specific_primers(
        self,
        primers: List[Dict],
        target_chrom: str,
        target_start: int,
        target_end: int,
        mispriming_library: bool = False,
        snp_exclusion: bool = False,
        splice_variant_handling: bool = False,
        max_hits=50,
        mismatch_cutoff=2,
    ) -> List[Dict]:
        """
        Stage 2.3: 게놈 전체 특이성 일괄 검사 (I/O 병목 극적 최적화)
        기존 specificity_check를 대체하며, 후보군 전체(List)를 받아 염색체 호출을 24회로 최소화합니다.
        """
        valid_primers = []

        # 1. Mispriming Library (반복 서열) 필터링 - SQLite 쿼리 사전 수행
        if mispriming_library:
            for p in primers:
                self.cur.execute(
                    "SELECT COUNT(*) FROM repeats WHERE chrom=? AND NOT (end < ? OR start > ?)",
                    (p["chrom"], p["genomic_start"], p["genomic_end"]),
                )
                if self.cur.fetchone()[0] == 0:
                    valid_primers.append(p)
        else:
            valid_primers = primers.copy()

        # 2. 상태 추적용 딕셔너리 구성
        primer_pool = {p["seq"]: p for p in valid_primers}
        hit_counts = {p["seq"]: 0 for p in valid_primers}

        # 3. 루프 역전: 염색체를 한 번만 불러오고, 메모리 상에서 남은 모든 프라이머 스캔
        for ref in self.genome.references:
            if not primer_pool:
                break  # 모든 프라이머가 탈락했다면 스캔 즉시 종료

            full_seq = self.genome.fetch(ref)

            for p_seq in list(primer_pool.keys()):
                for search_seq in [p_seq, reverse_complement(p_seq)]:
                    pos = full_seq.find(search_seq)
                    
                    while pos != -1:
                        pos_1based = pos + 1
                        end_1based = pos + len(search_seq)

                        # 의도된 타겟 구간 무시
                        if ref == target_chrom and target_start <= pos_1based <= target_end:
                            pos = full_seq.find(search_seq, pos + 1)
                            continue

                        # DB 변이체 필터링 (일치 타겟 발견 시에만)
                        if splice_variant_handling:
                            self.cur.execute(
                                "SELECT transcript_id FROM exon WHERE chrom=? AND start <= ? AND end >= ?",
                                (ref, pos_1based, end_1based),
                            )
                            if self.cur.fetchone():
                                pos = full_seq.find(search_seq, pos + 1)
                                continue

                        if snp_exclusion:
                            self.cur.execute(
                                "SELECT COUNT(*) FROM snp WHERE chrom=? AND pos BETWEEN ? AND ?",
                                (ref, pos_1based, end_1based),
                            )
                            if self.cur.fetchone()[0] > 0:
                                pos = full_seq.find(search_seq, pos + 1)
                                continue

                        # 3' 말단 미스매치 정밀 검사
                        off_target = full_seq[pos : pos + len(p_seq)]
                        mm = needleman_wunsch_mismatch(p_seq[-10:], off_target[-10:])
                        
                        if mm < mismatch_cutoff:
                            # 치명적 Off-target 발견 시 즉시 탈락
                            del primer_pool[p_seq]
                            break 
                            
                        hit_counts[p_seq] += 1
                        if hit_counts[p_seq] > max_hits:
                            del primer_pool[p_seq]
                            break

                        pos = full_seq.find(search_seq, pos + 1)

                    # 현재 프라이머가 탈락했다면, Reverse Complement 검사 등 내부 루프 완전히 중단
                    if p_seq not in primer_pool:
                        break

        # 안전성이 검증된 프라이머들만 반환
        return list(primer_pool.values())

    def pair_primers(
        self,
        primers: List[Dict],
        product_range=(100, 300),
        max_tm_diff=3.0,
        opt_tm=60.0,
    ) -> List[Dict]:
        """Stage 2.4: 최종 페어링 및 Penalty 스코어링"""
        fwd = [p for p in primers if p["strand"] == "+"]
        rev = [p for p in primers if p["strand"] == "-"]
        pairs = []
        for f in fwd:
            for r in rev:
                # [수정] 생물학적으로 올바른 Product Size 계산 (1-based 기준)
                size = r["end"] - f["start"] + 1
                if not (product_range[0] <= size <= product_range[1]):
                    continue

                # Tm 차이 및 페널티 계산 (UI 설정값 opt_tm 반영)
                tm_diff = abs(f["tm"] - r["tm"])
                if tm_diff > max_tm_diff:
                    continue
                penalty = (
                    abs(f["tm"] - opt_tm)
                    + abs(r["tm"] - opt_tm)
                    + abs(f["dg3"] + 8.0)
                    + abs(r["dg3"] + 8.0)
                    + (tm_diff * 2)
                )
                pairs.append(
                    {
                        "fwd": f,
                        "rev": r,
                        "product_size": size,
                        "penalty": penalty,
                    }
                )
        return sorted(pairs, key=lambda x: x["penalty"])