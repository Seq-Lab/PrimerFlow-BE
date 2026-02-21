import os
import sqlite3

# 1. DB 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "annotations.db")

def check_table(cursor, table_name):
    print(f"\n🔎 [Table: {table_name}] 검사 중...")
    
    try:
        # 1. 전체 데이터 개수 확인 (Count)
        cursor.execute(f"SELECT count(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   📊 총 데이터 개수: {count:,} 개")
        
        if count == 0:
            print("   ⚠️  데이터가 없습니다.")
            return

        # 2. 상위 5개 데이터 미리보기 (Limit)
        print("   👀 상위 5개 데이터 미리보기:")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        
        # 컬럼 이름 가져오기
        col_names = [description[0] for description in cursor.description]
        print(f"      Columns: {col_names}")
        
        for row in rows:
            print(f"      Row: {row}")
            
    except sqlite3.OperationalError:
        print(f"   ❌ 테이블이 존재하지 않습니다: {table_name}")
    except Exception as e:
        print(f"   ❌ 오류 발생: {e}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB 파일이 없습니다: {DB_PATH}")
        return

    print("============== DB 정밀 진단 시작 ==============")
    print(f"📂 파일 경로: {DB_PATH}")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 검사할 테이블 목록
            tables = ['exon', 'snp', 'repeats', 'restriction_site']
            
            for table in tables:
                check_table(cursor, table)
    except Exception as e:
        print(f"❌ DB 연결 오류: {e}")
        
    print("\n============== DB 진단 종료 ==============")

if __name__ == "__main__":
    main()
