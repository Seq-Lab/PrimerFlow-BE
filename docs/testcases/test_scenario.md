**작성자** : 강두하 <br>
**작성일** : 2026-01-11 <br>

# Equivalence Partitioning(EP) 토대의 테스트 시나리오 목록
| TC ID | 구분 | 테스트 항목 | 입력 | 기대 결과(Expected Result) | 결과(Pass/Fail) | 비고 |
|:---:|:---:|:---|:---|:---|:---:|:---|
| TC-001 | 정상 | DNA 서열 파일 유효성 확인 | TC-001.fna<br>-Target Organism: Homo Sapiens<br>-Specificity check enable: O<br> | 유사 유전자(RPS4Y1) 회피 설계 능력 확인 | - | 문자열이 1개만 차이가 나는 매우 유사한 유전자(paralog)가 있어서 이를 off-target으로 감지하고 1bp 불일치도 감지해야 함. |
| TC-002 | 정상 | DNA 서열 파일 유효성 확인 | TC-002.fna<br>-Target Organism: Homo Sapiens<br> | TC-001과 동일 | - | TC-001.fna의 서열만 있고, 헤더는 없음 |
| TC-003 | 예외 | DNA 서열 파일 유효성 확인 | TC-003.fna<br>-Target Organism: Homo Sapiens<br> | "허용되지 않는 문자가 포함되어 있습니다" 에러 메시지 출력 | - | A/T/G/C/N 이외의 다른 문자열이 서열에 포함됨 |
| TC-004 | 예외 | DNA 서열 파일 유효성 확인 | TC-004.txt<br>-Target Organism: Homo Sapiens<br> | "서열이 비어 있습니다" 에러 메시지 출력| - | 헤더와 서열 모두 없음 |
| TC-005 | 예외 | DNA 서열 파일 유효성 확인 | TC-005.fna<br>-Target Organism: Homo Sapiens<br> | 파싱 실패 및 에러 메시지 | - | TC-001.fna의 헤더만 있음 |
| TC-006 | 예외 | 파일 업로드 포맷 검증 | TC-006.png<br>-Target Organism: Homo Sapiens<br> | 에러 메시지 | - | fasta나 txt 외 다른 확장자 파일을 입력으로 받음. |
| TC-007 | 정상 | 특정 variant 증폭 가능 여부 확인 | TC-007.fna<br>-Target Organism: Homo Sapiens<br>-**Splice Variant Handling**: OFF<br>-**Exon Junction Span** : "spanning"<br>  | ZNF419 Var5 타겟팅 확인 | - | 포유류 속 일부 유전자는 발현하는 유전자 정보를 잘라서 선택적으로 조합 후 발현할 수 있다. 입력받는 파일은 이 유전자 변이체들 중 하나이다. 즉, 입력받은 서열만 특이적으로 증폭할 수 있는 프라이머를 설계할 수 있어야 한다. |
| TC-008 | 정상 | Intron Inclusion 고려 여부 확인| TC-008.fna<br>-Target Organism: Mus musculus<br>-Intron Inclusion: ON | Primer 후보군 쌍들이 gDNA(원본), mRNA(변이체)를 증폭하느냐에 따라 PCR 결과물의 크기가 다르게 나옴 | - | Intron은 원본 유전자 서열(gDNA=Exons+Introns)에서 정보가 없는 부분이다. 이 부분은 유전자 발현 시 mRNA에서 잘라내어 정보를 담는 exon만 남는다.(mRNA=Exons)<br>Primer 설계 시에 이를 고려하여, intron도 포함된 원본 유전자 서열을 결과물로 만들어 낼 수도 있다. |

# Boundary Value Analysis(BVA) 토대의 테스트 시나리오 목록
| TC ID | 구분 | 테스트 항목 | 사전 조건(Pre-condition) | 기대 결과(Expected Result) | 결과(Pass/Fail) | 비고 |
|:---:|:---:|:---|:---|:---|:---:|:---|


# Cause-Effect Graphing(CE) 토대의 테스트 시나리오 목록
| TC ID | 구분 | 테스트 항목 | 사전 조건(Pre-condition) | 기대 결과(Expected Result) | 결과(Pass/Fail) | 비고 |
|:---:|:---:|:---|:---|:---|:---:|:---|
