# 프라이머 디자인 알고리즘 최적화 및 좌표 보정

## 1. 배경 및 목적

- 사용자가 입력한 템플릿 서열(Local 좌표)과 게놈 DB(Genomic 절대 좌표) 간의 좌표 불일치 문제 해결
- 1-based 기준인 생물학적 데이터를 0-based 파이썬 인덱스로 처리하며 발생하는 오차 수정
- 전수 게놈 스캔 시 발생하는 심각한 I/O 병목 현상을 해결하여 발표 시연이 가능한 수준으로 성능 개선

## 2. 프라이머 (User Input)

```text
(좌표계 문제 제기)
이 코드를 보면 primer design 알고리즘을 설계한 것을 알 수 있어. 문제는 여기서 UI에서 입력값으로 fasta 파일이나 txt 파일을 넣을거야. 이때, template sequence가 해당 organism species의 genome을 읽어들여서 template sequence의 genome 상에서의 좌표를 파악해서 아래 코파일럿이 제기한 문제를 해결할려고 해. 기존 BLAST designer 등에서 사용하는 방법들을 사용해서 로직 코드를 보완해줘.
-제기된 문제: PrimerDesigner.py는 게놈 좌표/DB 좌표 기반으로 동작하는 전제인데, 현재 입력(템플릿 서열/검색 범위)이 템플릿 좌표로 들어오면 필터가 어긋납니다.

(성능 문제 제기)
근데 genome 상 좌표를 그렇게 찾으면 시간이 너무 오래 걸릴 거 같은데? 로직 자체를 효율적으로 수정해줬으면 해. API한테 전달 받는 것도, 전달 하는 것도 변함은 없어야 해.

```

## 3. AI 응답 요약 (AI Output)

* **좌표계 동기화**: `locate_template_in_genome` 메서드를 추가하여 템플릿의 게놈 내 위치를 찾고, 모든 로컬 좌표를 1-based 게놈 절대 좌표로 매핑하는 로직 구현.
* **I/O 최적화 (Batch Scan)**: 기존에 프라이머마다 염색체 파일을 반복 호출하던 방식에서, 염색체를 한 번 로드할 때 모든 프라이머 후보를 일괄 검사하는 루프 역전(Loop Inversion) 기법 적용.
* **정밀도 향상**: SNP, Exon 필터링 시 3' 말단(Inclusive range) 처리를 1-based 기준으로 정확히 계산하도록 수정.

## 4. 결과 및 적용 (Result)

* **적용 사항**: `app/algorithms/PrimerDesigner.py` 내 `generate_candidates`, `local_db_filter`, `pair_primers` 등 핵심 로직 전면 수정.
* **성능 변화**: 수백 개의 후보군에 대한 특이성 검사 시간이 디스크 I/O 최적화를 통해 획기적으로 단축됨.
* **영향**: API 엔드포인트의 구조 변경 없이 알고리즘 내부 수정만으로 요구사항을 충족하여 프론트엔드/API 파트와의 정합성 유지.