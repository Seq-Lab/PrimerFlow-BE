# Branch Strategy

이 문서는 브랜치 네이밍과 워크플로우(브랜치 유형, PR/리뷰 규칙, 보호 정책)를 정의합니다. <br>팀의 일관된 개발 흐름을 위해 아래 규칙을 따라주세요.

## 브랜치 종류 및 네이밍
- `main`: 배포 가능한 코드만 존재 (프로덕션)
- `develop`: 다음 릴리즈 통합 브랜치
- 기능 브랜치: `feature/<short-description>` (예: `feature/login-oauth`)
- 버그 수정 브랜치: `fix/<short-description>` (예: `fix/null-pointer-user`)
- 리팩토링 브랜치: `refactor/<short-description>`
- 의존성 업데이트: `chore/deps-<pkg>`

브랜치 이름 규칙
- 소문자 및 `-`로 구분, 공백 금지

## 브랜치 생성/병합 흐름
- 모든 작업은 `feature`/`fix` 브랜치에서 진행 후 `develop`으로 PR 생성
- 관리자는 주마다 정기적으로 `develop` → `main`으로 릴리즈 머지

## Pull Request 규칙
- **PR 제목은 한 줄 요약**
- PR 본문에 변경 목적, 주요 변경 사항, 테스트 방법 명시
- 최소 1명 이상의 리뷰어 승인 필요 (팀 규모에 따라 2명 권장)
- PR 리뷰 기한: 작성 후 24시간
- **단순 승인만 하지 말고, 최소 1개의 구체적 코멘트 남기기**



## 📌 작업 흐름 예시

### 0. 초기 설정
```bash
# 조직 저장소 별칭(upstream) 등록
git remote add upstream [조직 레포지토리 URL]

# 연결 확인
git remote -v
```

### 1. 최신화 (Sync)
작업 시작 전, 내 로컬의 `develop`을 조직 저장소(Upstream)와 똑같이 맞춥니다.
```bash
# 로컬 develop 브랜치로 이동
git checkout develop

# 조직 저장소(upstream)의 내용을 당겨와서 동기화
git pull upstream develop
```

### 2. 브랜치 생성 (Branch)
develop에서 바로 작업하지 않고, 작업 전용 브랜치를 새로 만듭니다.

```bash
# 형식: git checkout -b [기능명]
# 예시: 로그인 페이지 작업 시
git checkout -b feature/login-page
```

### 3. 작업 및 커밋 (Commit)
코드를 작성하고 저장합니다.

```bash
# 변경된 파일 전체 스테이징
git add .

# 커밋 메시지 작성 (예: feat, fix 등 말머리 사용 권장)
git commit -m "feat: 로그인 페이지 UI 구현 완료"
```

### 4. 푸시 (Push)
작업한 브랜치를 내 원격 저장소(Origin)에 업로드합니다.

```bash
# 형식: git push origin [작업한 브랜치명]
git push origin feature/login-page
```

### 5. PR 요청 (Pull Request)
GitHub 웹사이트에서 내 포크 저장소의 브랜치를 조직 저장소로 합쳐달라고 요청합니다.

1. GitHub 본인 저장소(Fork) 페이지 접속
2. `'Compare & pull request'` 버튼 클릭
3. 방향(Direction) 확인:
    - base repository: 조직 저장소 / `base: develop` ⬅ (여기로 보냄)
    - head repository: 내 저장소 / `compare: PR보낼 내 저장소 브랜치`
4. 내용 작성 후 Create Pull Request
