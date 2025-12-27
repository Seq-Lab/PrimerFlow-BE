# PrimerFlow


## 프로젝트 구조

```text
PrimerFlow-BE/
├─ api/
│  ├─ deps.py
│  └─ v1/
│     └─ endpoints/        # 엔드포인트 모음
├─ schemas/                # Pydantic 모델 모음
│  └─ schemas.py
├─ algorithms/             # 알고리즘 모음
├─ docs/                   # 협업 가이드 문서 모음
│  └─ prompts/
│  └─ strategy/
├─ main.py                 # FastAPI 앱 엔트리포인트 
├─ requirements.txt        # Python 패키지 목록
├─ README.md
└─ .gitignore
```


## 개발 환경 설정

### 1. 가상환경 생성 및 활성화

- Windows
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1    # PowerShell
    # 또는
    .\.venv\Scripts\activate.bat    # cmd
    ```
- macOS / Linux
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### 2. 의존성 설치

```powershell
pip install -r requirements.txt
```

### 3. 개발 서버 실행

```powershell
uvicorn main:app --reload
```

- 기본 엔드포인트: http://localhost:8000/
- OpenAPI 문서: http://localhost:8000/docs
- ReDoc 문서: http://localhost:8000/redoc



