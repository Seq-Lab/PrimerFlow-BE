# DB 구축 및 알고리즘 연동 가이드

## 1. 배경 및 목적

- **배경**: 프라이머 디자인 알고리즘(`PrimerDesigner`)에서 열역학적 계산(Tm) 외에 생물학적 필터링(Off-target, SNP, 제한효소 등)을 수행하기 위해 로컬 데이터베이스가 필수적임.
- **목적**:
    1. `PrimerDesigner` 파이썬 코드 실행에 필요한 `annotations.db`의 스키마(Schema)를 설계.
    2. SQL이나 DB를 모르는 초보자도 따라 할 수 있도록 원시 데이터(Raw Data) 다운로드부터 SQLite DB 구축까지의 전 과정을 자동화.
    3. 구축된 DB와 알고리즘을 연동하여 실제 유전체 분석 환경(WSL)에서 동작을 검증.

## 2. 핵심 프롬프트 (User Input)

프로젝트 진행 과정에서 발생한 기술적 난관을 해결하고, 결과물의 신뢰성을 확보하기 위해 사용된 주요 프롬프트입니다.

### [Phase 1] DB 아키텍처 설계 요청 (Architecture Design)
```
# (PrimerDesigner 클래스 코드 제공...)
이 코드 실행을 위해서 DB를 구축하려고 해.
어떤 DB가 필요한 지, 하나도 빠짐없이 다 구축하고,
구축하려는 DB는 SQL lite DB나 라이브러리를 통해 구축하려고 해.
필요한 DB들의 구축방법을 DB를 하나도 모르는 나같은 초보자도 알 수 있게 아주 상세하게 설명해줘.
```


### [Phase 2] 시스템 의존성 및 환경 충돌 해결 (System Troubleshooting)
```Plaintext
현재 WSL(Ubuntu 24.04) 환경에서 `pip install pysam` 실행 시 `externally-managed-environment` 에러가 발생하고 있습니다.
가상환경(venv) 설정 또는 시스템 패키지 관리자(apt)를 우회하여, 프로젝트에 필요한 `pysam`, `numpy` 라이브러리를 강제로 설치하고 구동할 수 있는 해결책을 제시해 주세요.
추가로, `gzip`으로 압축된 게놈 파일이 인덱싱되지 않는 문제(`[E::fai_build_core]`)에 대한 데이터 전처리 방안도 알려주세요.
```
### [Phase 3] 알고리즘 로직 검증을 위한 모니터링 (White-box Testing)
```
프라이머 디자인 과정에서 결과값만 출력되는 것이 아니라, 알고리즘의 중간 처리 과정을 모니터링하고 싶습니다.
`generate_candidates` 메서드에서 생성된 초기 후보군 리스트와, `local_db_filter`를 거치며 SNP 또는 제한효소(Restriction Enzyme)로 인해 탈락하는 후보들을 로그 형태로 출력하는 `show_candidates.py` 스크립트를 작성해 주세요.
이를 통해 필터링 로직이 DB와 연동되어 정상 작동하는지 눈으로 확인하고 싶습니다.
```
### [Phase 4] DB 데이터 정합성 검증 (Data Integrity Verification)
```
구축된 `annotations.db` 파일의 무결성을 검증하려고 합니다.
단순히 파일 생성 여부만 확인하는 것이 아니라, 실제 SQL 쿼리를 수행하여 `exon`, `repeats`, `restriction_site`, `snp` 각 테이블에 적재된 데이터의 총 개수(Count)를 조회하고 싶습니다.
테이블 구조를 분석하여, 전체 데이터 적재 현황을 한 번에 파악할 수 있는 최적화된 집계 쿼리(Aggregation Query)를 제공해 주세요.
```
## 3. AI 응답 요약 (AI Output)

사용자의 요청에 따라 데이터베이스 설계부터 환경 최적화, 그리고 검증 도구까지 단계별 엔지니어링 솔루션을 제공함.

### [Solution 1] 관계형 데이터베이스 스키마 설계 (Schema Design)
알고리즘의 요구사항을 분석하여, 데이터 중복을 최소화하고 조회 성능을 높일 수 있는 **정규화된 4개의 테이블 스키마**를 정의함.
- **`exon`**: 유전자(Gene) 영역과 전사체 정보를 저장하여 구조적 필터링 지원.
- **`snp`**: dbSNP 등에서 추출한 변이 정보를 인덱싱하여 오프타겟(Off-target) 방지.
- **`repeats`**: RepeatMasker 데이터를 저장하여 비특이적 결합 방지.
- **`restriction_site`**: 실험에 방해가 되는 제한효소 절단 부위 정보 저장.

### [Solution 2] 자동화된 ETL 스키마 및 스크립트 제공
복잡한 Raw Data(BED, GFF, VCF 등)를 파싱(Parsing)하여 SQLite DB로 변환하는 **자동화된 ETL(Extract, Transform, Load) 파이프라인 스크립트**(`build_db.py`)를 제공.
- 대용량 텍스트 파일 처리를 위한 메모리 효율적인 코딩 기법 적용.

### [Solution 3] 리눅스 기반 바이오 분석 환경 표준화
Windows 환경에서의 호환성 문제를 근본적으로 해결하기 위해 **WSL 2(Ubuntu 24.04)** 기반의 개발 환경을 제안하고 구축을 가이드함.
- **Dependency 해결**: `--break-system-packages` 옵션을 통해 최신 리눅스 보안 정책(PEP 668) 하에서도 `pysam` 등 필수 라이브러리 설치를 완료.
- **I/O 최적화**: `gzip` 압축 파일의 Random Access 불가 문제를 해결하기 위해 `gunzip` 전처리 및 파일 경로 재설정 가이드 제공.

### [Solution 4] 데이터 및 로직 검증 도구 (Verification Tools)
단순 구현을 넘어 결과의 신뢰성을 보장하기 위한 **검증용 쿼리와 스크립트**를 제공.
- **Data QA**: 테이블별 레코드 수를 교차 검증할 수 있는 `UNION ALL` 기반의 집계 SQL 쿼리.
- **Logic QA**: 알고리즘 내부의 필터링 판단 로직(Pass/Fail)을 추적할 수 있는 모니터링 스크립트(`test_db_integration.py`).

## 4. 결과 및 검증 (Result)

### ✅ 개발 환경 구축 결과 (Environment Setup)
- **OS 마이그레이션**: Windows에서 **WSL 2 (Ubuntu 24.04)**로 성공적으로 전환하여, 바이오인포매틱스 표준 라이브러리(`htslib`, `pysam`)의 네이티브 구동 환경을 확보함.
- **성능**: `pysam`을 통한 게놈 서열 추출(Fetching) 지연 시간이 획기적으로 단축됨(ms 단위).

### ✅ DB 데이터 정합성 검증 (Data Integrity)
구축된 `annotations.db`에 대해 SQL 검증 쿼리를 수행한 결과, **총 1,570만 여 건**의 데이터가 누락 없이 적재되었음을 확인함.

| 테이블명 (Table) | 레코드 수 (Count) | 데이터 역할 (Role) |
| :--- | :--- | :--- |
| **Exon** | 3,673,949 | 전사체 엑손 영역 정의 (Gene Coverage 100%) |
| **Repeats** | 5,683,690 | 반복 서열 필터링 (Mispriming 방지) |
| **Restriction Sites** | 2,091,546 | 주요 제한효소(EcoRI, BamHI 등) 위치 정보 |
| **SNP** | 4,283,874 | 고빈도 변이(Common Variants) 정보 |

### 📝 최종 산출물 (Deliverables)
- **DB 파일**: `database/annotations.db` (약 760 MB / SQLite3 Format)
- **소스 코드**: 
    - `build_db.py` (DB 구축)
    - `check_db_detail.py` (대용량 DB Summary 확인)
    - `test_db_integration.py` (DB 연동 및 필터링 테스트)