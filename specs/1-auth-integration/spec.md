# Feature Specification: Auth Server 연동 및 로그인 기능 통합

**Feature Branch**: `1-auth-integration`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "@/home/ubuntu/auth-server/ 해당 프로젝트가 완료 되었어 그래서 인증을 맨 앞에 두어야 하는데 그 create by timestamp도 없어 그게 일단 전반적으로 있어야겠지? 전반적으로 로그인 기능을 연동해줘"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 로그인하여 대시보드 접근 (Priority: P1)

사용자가 Bitcoin-Auto-Trading 웹 애플리케이션에 접근하면 먼저 로그인 화면이 표시됩니다. 사용자는 이메일과 비밀번호를 입력하여 로그인하고, 성공하면 기존 대시보드 화면으로 이동합니다.

**Why this priority**: 로그인이 없으면 시스템 보안이 전혀 없으며, 모든 기능이 외부에 노출됩니다. 이것은 가장 기본적이고 필수적인 기능입니다.

**Independent Test**: 로그인 페이지에서 올바른 자격 증명을 입력하면 대시보드로 이동하고, 잘못된 자격 증명이면 오류 메시지가 표시됩니다.

**UI 결정사항**: 로그인 페이지는 심플한 디자인으로, 중앙 정렬된 로그인 폼만 있는 깔끔한 레이아웃 (사이드바 없음). '로그인 유지' 체크박스는 제외하고 항상 7일간 세션을 유지합니다.

**Acceptance Scenarios**:

1. **Given** 사용자가 로그인하지 않은 상태에서 웹 애플리케이션에 접근, **When** 어떤 페이지든 접근 시도, **Then** 로그인 페이지로 리다이렉트
2. **Given** 로그인 페이지, **When** 올바른 이메일과 비밀번호 입력 후 로그인 버튼 클릭, **Then** 대시보드 화면으로 이동하고 사용자 이름 표시
3. **Given** 로그인 페이지, **When** 잘못된 자격 증명 입력, **Then** "이메일 또는 비밀번호가 올바르지 않습니다" 오류 메시지 표시
4. **Given** 계정이 잠긴 상태 (5회 연속 로그인 실패), **When** 로그인 시도, **Then** "계정이 일시적으로 잠겼습니다. 잠시 후 다시 시도해주세요" 메시지 표시

---

### User Story 2 - 로그인 상태 유지 및 자동 토큰 갱신 (Priority: P2)

로그인한 사용자가 애플리케이션을 사용하는 동안 세션이 자동으로 유지됩니다. 액세스 토큰이 만료되기 전에 자동으로 갱신되어 사용자가 불편함 없이 계속 사용할 수 있습니다.

**Why this priority**: 로그인 후 지속적인 사용 경험을 위해 필수적입니다. 토큰 갱신이 없으면 15분마다 재로그인해야 합니다.

**Independent Test**: 로그인 후 15분 이상 경과해도 재로그인 없이 정상적으로 API 호출이 가능합니다.

**Acceptance Scenarios**:

1. **Given** 로그인된 사용자, **When** 액세스 토큰 만료 시점 도래 (만료 1분 전), **Then** 자동으로 토큰 갱신 수행
2. **Given** 로그인된 사용자, **When** 리프레시 토큰이 유효한 동안, **Then** 페이지 새로고침 후에도 로그인 상태 유지
3. **Given** 리프레시 토큰 만료 (7일 경과), **When** 어떤 API 호출 시도, **Then** 로그인 페이지로 리다이렉트

---

### User Story 3 - 로그아웃 (Priority: P2)

사용자가 로그아웃 버튼을 클릭하면 현재 세션이 종료되고 로그인 페이지로 이동합니다. 이후 해당 토큰으로는 더 이상 접근할 수 없습니다.

**Why this priority**: 공용 컴퓨터 사용 등의 상황에서 보안을 위해 반드시 필요한 기능입니다.

**Independent Test**: 로그아웃 클릭 후 로그인 페이지로 이동하고, 브라우저 뒤로가기로 대시보드 접근 시 다시 로그인 페이지로 리다이렉트됩니다.

**UI 결정사항**: 로그아웃 버튼은 사이드바 하단에 사용자 정보와 함께 배치됩니다.

**Acceptance Scenarios**:

1. **Given** 로그인된 사용자가 사이드바 하단에서 로그아웃 버튼 확인, **When** 로그아웃 버튼 클릭, **Then** 로그인 페이지로 이동
2. **Given** 로그아웃 완료 후, **When** 이전 토큰으로 API 호출 시도, **Then** 401 Unauthorized 응답

---

### User Story 4 - 비로그인 상태에서 보호된 API 접근 차단 (Priority: P1)

백엔드 API는 인증되지 않은 요청을 거부합니다. 유효한 토큰 없이 대시보드, 주문, 신호 등의 데이터를 조회할 수 없습니다.

**Why this priority**: 인증 없이 백엔드 API에 직접 접근하면 보안 문제가 발생합니다. 로그인 UI와 함께 백엔드 보호가 필수입니다.

**Independent Test**: 토큰 없이 `/api/v1/dashboard/market` 호출 시 401 응답을 받습니다.

**Acceptance Scenarios**:

1. **Given** 인증 토큰 없음, **When** 보호된 API 엔드포인트 호출, **Then** 401 Unauthorized 응답
2. **Given** 만료된 액세스 토큰, **When** 보호된 API 엔드포인트 호출, **Then** 401 Unauthorized 응답
3. **Given** 유효한 액세스 토큰, **When** 보호된 API 엔드포인트 호출, **Then** 정상 응답 (200 OK)

---

### User Story 5 - 로그인 사용자 정보 표시 (Priority: P3)

로그인한 사용자의 이름이 애플리케이션 UI에 표시됩니다. 사용자는 자신이 누구로 로그인했는지 확인할 수 있습니다.

**Why this priority**: 기능적으로 필수는 아니지만, 사용자 경험과 명확성을 위해 필요합니다.

**Independent Test**: 로그인 후 사이드바 또는 헤더에서 사용자 이름과 이메일을 확인할 수 있습니다.

**Acceptance Scenarios**:

1. **Given** 로그인 성공, **When** 대시보드 페이지 로드, **Then** UI에 사용자 이름 표시
2. **Given** 로그인된 상태, **When** 페이지 새로고침, **Then** 사용자 정보 유지 및 표시

---

### Edge Cases

- 네트워크 오류로 Auth Server에 연결할 수 없을 때 어떻게 처리할 것인가? → 사용자에게 "인증 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요" 메시지 표시
- 토큰 갱신 중 네트워크 오류 발생 시? → 기존 토큰으로 재시도 후 실패하면 로그인 페이지로 리다이렉트
- 브라우저 탭 여러 개에서 동시에 사용 중 한 탭에서 로그아웃 시? → 다른 탭에서 API 호출 시 401 응답 받고 로그인 페이지로 이동
- Auth Server가 다운된 경우? → 백엔드에서 Auth Server 연결 실패 시 503 응답, 프론트엔드에서 "서비스 일시 중단" 메시지 표시

---

## Requirements *(mandatory)*

### Functional Requirements

**백엔드 (Bitcoin-Auto-Trading Backend)**

- **FR-001**: 시스템은 Auth Server의 토큰 검증 API를 통해 모든 보호된 API 요청을 인증해야 합니다
- **FR-002**: 시스템은 Authorization 헤더의 Bearer 토큰을 추출하여 Auth Server에 검증을 요청해야 합니다
- **FR-003**: 시스템은 토큰 검증 실패 시 401 Unauthorized 응답을 반환해야 합니다
- **FR-004**: 시스템은 Auth Server 연결 실패 시 503 Service Unavailable 응답을 반환해야 합니다
- **FR-005**: 시스템은 헬스체크 API (`/api/v1/health`)는 인증 없이 접근 가능해야 합니다

**프론트엔드 (Bitcoin-Auto-Trading Frontend)**

- **FR-101**: 시스템은 로그인 페이지를 제공하여 이메일/비밀번호 입력을 받아야 합니다
- **FR-102**: 시스템은 로그인 성공 시 액세스 토큰과 리프레시 토큰을 안전하게 저장해야 합니다
- **FR-103**: 시스템은 모든 API 요청에 Authorization 헤더를 자동으로 추가해야 합니다
- **FR-104**: 시스템은 액세스 토큰 만료 1분 전에 자동으로 토큰을 갱신해야 합니다
- **FR-105**: 시스템은 401 응답 수신 시 로그인 페이지로 리다이렉트해야 합니다
- **FR-106**: 시스템은 비로그인 상태에서 보호된 페이지 접근 시 로그인 페이지로 리다이렉트해야 합니다
- **FR-107**: 시스템은 로그아웃 기능을 제공하여 토큰을 삭제하고 로그인 페이지로 이동해야 합니다
- **FR-108**: 시스템은 로그인한 사용자 정보 (이름, 이메일)를 UI에 표시해야 합니다

### Key Entities

- **User (사용자)**: Auth Server에서 관리되는 사용자 정보 (id, email, name, role)
- **Access Token**: 15분 유효의 JWT 토큰, API 인증에 사용
- **Refresh Token**: 7일 유효의 토큰, 액세스 토큰 갱신에 사용
- **Auth State**: 프론트엔드에서 관리하는 인증 상태 (토큰, 사용자 정보, 로그인 여부)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 로그인 성공률 99% 이상 (올바른 자격 증명 입력 시)
- **SC-002**: 로그인 완료 시간 3초 이내 (네트워크 지연 제외)
- **SC-003**: 토큰 자동 갱신 성공률 99% 이상 (리프레시 토큰 유효 기간 내)
- **SC-004**: 비인증 API 요청 100% 차단 (401 응답)
- **SC-005**: 세션 유지 기간 최대 7일 (리프레시 토큰 유효 기간)
- **SC-006**: 사용자가 로그인 없이 대시보드, 주문, 신호 페이지에 접근 불가
- **SC-007**: Auth Server 장애 시 적절한 오류 메시지 표시 및 복구 후 정상 동작

---

## Assumptions

- Auth Server는 `http://localhost:8001` (개발) 또는 환경 변수로 지정된 URL에서 운영됩니다
- Auth Server의 API 명세 (SPEC.md에 정의됨)가 변경되지 않습니다
- 사용자 계정은 Auth Server에서 관리자가 사전에 생성합니다 (셀프 회원가입 없음)
- 토큰 저장은 localStorage를 사용합니다 (브라우저 탭 간 공유)
- Auth Server와 Bitcoin-Auto-Trading 백엔드 간 통신은 내부 네트워크로 신뢰할 수 있습니다

---

## Dependencies

- **Auth Server**: `/home/ubuntu/auth-server/` 프로젝트가 완료되어 운영 가능 상태여야 합니다
- **Auth Server API**:
  - `POST /api/v1/auth/login` - 로그인
  - `POST /api/v1/auth/refresh` - 토큰 갱신
  - `POST /api/v1/auth/logout` - 로그아웃
  - `GET /api/v1/auth/verify` - 토큰 검증 (백엔드에서 사용)
  - `GET /api/v1/auth/me` - 현재 사용자 정보

---

## Out of Scope

- 사용자 회원가입 기능 (Auth Server 관리자가 직접 생성)
- 비밀번호 찾기/재설정 기능
- OAuth 소셜 로그인 (Google, GitHub 등)
- 2FA (이중 인증)
- 사용자 관리 UI (Auth Server 직접 관리)
- 역할 기반 접근 제어 (모든 인증된 사용자는 동일한 권한)
