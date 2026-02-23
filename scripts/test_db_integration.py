import os
import sys

# ---------------------------------------------------------
# 1. 프로젝트 루트 경로 설정 (모듈 Import를 위해 필수)
# ---------------------------------------------------------
# 현재 스크립트(scripts/)의 부모 폴더(PrimerFlow-BE/)를 찾습니다.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(BASE_DIR)

# DB 및 Dummy FASTA 경로 설정
DB_PATH = os.path.join(BASE_DIR, "database", "annotations.db")
FAKE_FASTA_PATH = os.path.join(BASE_DIR, "database", "raw_data", "test_genome.fa")

def create_fake_fasta():
    """PrimerDesigner 초기화를 위해 최소한의 가짜 FASTA 파일을 생성합니다."""
    if not os.path.exists(os.path.dirname(FAKE_FASTA_PATH)):
        os.makedirs(os.path.dirname(FAKE_FASTA_PATH))
    
    # 윈도우 환경 등에서 pysam 에러 방지를 위해 파일은 만들어둡니다.
    with open(FAKE_FASTA_PATH, "w") as f:
        f.write(">chr1\nATGCATGCATGCATGCATGC\n")

    # pysam.FastaFile 초기화 시 .fai 인덱스가 필요할 수 있으므로,
    # 가능하다면 여기서 인덱스를 생성해 둡니다.
    try:
        import pysam
        pysam.faidx(FAKE_FASTA_PATH)
    except ImportError:
        # 윈도우 등 pysam 미설치 환경에서는 인덱스 생성 없이 DB 연동만 테스트합니다.
        pass
    except Exception:
        # 인덱스 생성 실패는 통합 테스트 전체를 막지 않도록 무시합니다.
        pass
def main():
    print("🔬 [통합 테스트] 기존 PrimerDesigner 코드와 DB 연동 확인")
    print(f"📂 프로젝트 경로: {BASE_DIR}")
    print(f"📂 DB 파일 경로: {DB_PATH}")

    # 1. 가짜 FASTA 생성
    create_fake_fasta()

    # 2. 모듈 불러오기 (Import)
    try:
        from app.algorithms.PrimerDesigner import PrimerDesigner
        print("✅ 모듈 Import 성공: app.algorithms.PrimerDesigner")
    except ImportError as e:
        print(f"❌ 모듈 Import 실패: {e}")
        print("   -> app/algorithms/PrimerDesigner.py 파일이 있는지 확인해주세요.")
        return
    except Exception as e:
        print(f"⚠️ 모듈 로드 중 오류 발생: {e}")
        if "pysam" in str(e):
            print("\n[🚨 Windows 환경 Pysam 오류 감지]")
            print("윈도우에서는 'pysam' 라이브러리가 설치되지 않아 에러가 날 수 있습니다.")
            print("DB 테스트만 하려면, PrimerDesigner.py 파일에서 'import pysam' 줄을 잠시 주석 처리(#) 해주세요.")
        return

    # 3. 클래스 초기화
    try:
        # pysam이 없으면 __init__에서 터질 수 있으므로 예외처리
        pd = PrimerDesigner(FAKE_FASTA_PATH, DB_PATH)
        print("✅ PrimerDesigner 클래스 초기화(DB 연결) 성공")
    except Exception as e:
        print(f"❌ 클래스 초기화 실패: {e}")
        print("   -> PrimerDesigner.py의 __init__ 메서드에서 pysam 관련 코드를 확인해주세요.")
        return

    # 4. DB 연동 테스트 (local_db_filter)
    print("\n🧪 [Test Case] 제한효소(EcoRI) 필터링 테스트")
    
    # DB에서 EcoRI 위치 하나를 조회해봅니다.
    pd.cur.execute("SELECT chrom, start, end FROM restriction_site WHERE name='EcoRI' LIMIT 1")
    row = pd.cur.fetchone()
    
    if row:
        chrom, r_start, r_end = row
        print(f"   ℹ️ DB 데이터 확인: {chrom}의 {r_start}~{r_end} 구간에 EcoRI 존재")
        
        # EcoRI 구간을 포함하는 가상의 프라이머 생성
        test_primer = {
            "seq": "TEST_SEQ",
            "start": r_start - 5,
            "end": r_end + 5,
            "strand": "+"
        }

        # 필터링 함수 실행
        # (restriction_enzymes 리스트에 'EcoRI'를 넣어서 감지하는지 확인)
        is_valid = pd.local_db_filter(
            chrom=chrom,
            primer=test_primer,
            restriction_enzymes=["EcoRI"]
        )

        if is_valid is False:
            print("✅ PASS: DB와 연동하여 제한효소 포함 프라이머를 성공적으로 걸러냈습니다!")
        else:
            print("❌ FAIL: 제한효소를 감지하지 못했습니다. (필터링 로직 확인 필요)")
            
    else:
        print("⚠️ SKIP: DB에 EcoRI 데이터가 없습니다. (구축 스크립트를 다시 확인해주세요)")

    # 종료
    pd.cur.close()
    pd.db.close()
    print("\n🎉 모든 테스트 종료")

if __name__ == "__main__":
    main()
