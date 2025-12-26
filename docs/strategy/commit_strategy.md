# Commit Strategy

이 문서는 협업 시 일관된 커밋 메시지와 브랜치/PR 정책을 정의합니다. <br>팀 전체의 가독성과 릴리즈 관리를 개선하기 위해 아래 규칙을 따르세요.

## 커밋 메시지 포맷

```bash
<type>(<scope>): <short summary>
<BLANK LINE>
<body>
```

- `type` 예시:
  - `feat`: 새로운 기능
  - `fix`: 버그 수정
  - `docs`: 문서 변경
  - `style`: 포매팅/스타일 (기능 변경 없음)
  - `refactor`: 리팩터링
  - `test`: 테스트 관련
  - `build`: 빌드 관련
  - `ci`: CI 설정 변경
  - `perf`: 성능 개선
  - `chore`: 기타 잡일 (자잘한 수정)

- `short summary`는 20자 이내로 간결하게 작성합니다.
- `body`에는 변경 이유와 중요한 구현 세부사항을 기술합니다. (필요 시)

### 예시
- `feat(auth): 구글 OAuth2 로그인 추가`
- `fix(api): 사용자 서비스 널 포인터 처리`
- `docs: 배포 관련 README 업데이트`
