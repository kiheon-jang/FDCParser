# FDC NEO Parser Application

**버전**: v1.0

---

## ⚡ 빠른 시작

```bash
# 1. 가상 환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 2. 라이브러리 설치
pip install -r requirements.txt

# 3. 애플리케이션 실행
streamlit run fdc_neo_app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 접속 가능합니다.

---

## 📦 포함된 파일

```
fdc_neo_converter.py     - 파일 변환 모듈
fdc_neo_app.py           - Streamlit UI 애플리케이션
requirements.txt         - 필요한 라이브러리
FDC_NEO_APP_가이드.md    - 이 파일
```

---

## 🚀 설치 및 실행

### 1. 가상 환경 생성 (권장)

macOS/Linux 환경에서는 가상 환경 사용을 권장합니다:

```bash
# 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 2. 필수 라이브러리 설치

```bash
pip install -r requirements.txt
```

**설치되는 패키지**:
- streamlit (>=1.28.0)
- matplotlib (>=3.7.0)
- numpy (>=1.24.0)
- pandas (>=2.0.0)

### 3. 애플리케이션 실행

```bash
streamlit run fdc_neo_app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 접속 가능합니다.

### 4. 가상 환경 종료

작업이 끝나면 가상 환경을 비활성화할 수 있습니다:

```bash
deactivate
```

### ⚠️ 주의사항

- **macOS**: 시스템 Python이 외부 관리 환경으로 설정되어 있어 가상 환경 사용이 필수입니다.
- **Windows**: 가상 환경 없이도 실행 가능하지만, 가상 환경 사용을 권장합니다.
- 가상 환경을 활성화하지 않으면 `pip install` 시 오류가 발생할 수 있습니다.

---

## 💡 주요 기능

### 1. 🔄 파일 변환

**특징**:
- 파일 타입 자동 감지 (온라인/오프라인)
- 타임스탬프 검증 완화로 모든 레코드 추출
- 데이터 손실 없이 전체 레코드 포함

**온라인 → 오프라인**:
```
입력: GT_N24987L02_260107_091837.txt (1 KB)
       ↓
처리: Hex-String → Binary 변환
      ConfigDone 헤더 추가
      GSP/WBVF 식별자 추가
      256KB/512KB로 패딩
       ↓
출력: Fault_GT_N24987L02.txt (512 KB)
```

**오프라인 → 온라인**:
```
입력: Fault_GT_N23261L01.txt (512 KB)
       ↓
처리: 헤더 제거
      전체 레코드 추출 (타임스탬프 검증 완화)
      Binary → Hex-String 변환
       ↓
출력: GT_FULL_N23261L01_260120_153045.txt (가변 크기)
      - 모든 레코드 포함 (크기 제한 없음)
```

---

### 2. 🔗 파일 병합

**특징**:
- 파일 타입 자동 감지 및 처리
- 타임스탬프 검증 완화로 모든 레코드 추출
- 병합 결과는 모든 레코드 포함 (크기 제한 없음)

**기능**:
- 온라인 + 오프라인 파일 병합
- 타임스탬프 기준 중복 제거
- 온라인 또는 오프라인 형식으로 출력

**프로세스**:
```
1. 두 파일에서 레코드 추출
   - 파일 타입 자동 감지 (온라인/오프라인)
   - 타임스탬프 검증 완화 (유효하지 않아도 포함)
   - 전체 레코드 추출 (데이터 손실 없음)
2. 타임스탬프 기준 정렬
3. 중복 레코드 제거
   - 타임스탬프가 있는 레코드: 타임스탬프 기준 중복 제거
   - 타임스탬프가 없는 레코드: 모두 포함 (중복 제거 안 함)
4. 선택한 형식으로 출력
```

**사용 예시**:
```
온라인: GT_N24987L02.txt (5개 레코드)
오프라인: Fault_GT_N23261L01.txt (903개 레코드)
       ↓ 병합 + 중복 제거
결과: Merged_Online.txt (296개 레코드)
      - 타임스탬프 기준 중복 제거 완료
      - 모든 레코드 포함 (크기 제한 없음)
      또는
      Merged_Offline.txt (296개 레코드)
      - 모든 레코드 포함
      - 256KB 또는 512KB로 패딩
```

**주의사항**:
- 파일 타입 자동 감지: 잘못된 파일이 업로드되어도 자동으로 감지하여 처리
- 타임스탬프 검증 완화: 유효하지 않은 타임스탬프도 레코드는 포함됨
- 중복 제거: 타임스탬프가 있는 레코드만 중복 제거, 없는 레코드는 모두 포함

---

## 🎯 사용 시나리오

### 시나리오 1: 온라인 파일을 오프라인으로 변환

```
1. "🔄 파일 변환" 메뉴 선택
2. "온라인 → 오프라인" 탭 선택
3. GT_N24987L02_260107_091837.txt 업로드
4. 출력 파일명 입력 (자동 생성됨)
5. "변환 시작" 클릭
6. 변환 완료 후 다운로드
7. 결과: Fault_GT_N24987L02.txt (512 KB)
```

### 시나리오 2: 파일 병합으로 데이터 통합

```
1. "🔗 파일 병합" 메뉴 선택
2. 온라인 파일 업로드: GT_N24987L02.txt
3. 오프라인 파일 업로드: Fault_GT_N23261L01.txt
4. 출력 형식 선택: "오프라인 형식"
5. "병합 시작" 클릭
6. 결과 확인:
   - 중복 제거 완료
   - 통합 레코드 수 표시
7. 병합된 파일 다운로드
```

---

## 🔧 CLI 사용법 (고급)

> **참고**: CLI 사용 시에도 가상 환경이 활성화되어 있어야 합니다.
> ```bash
> source venv/bin/activate  # 가상 환경 활성화
> ```

### 변환만 하기

```python
from fdc_neo_converter import FDCNEOConverter

converter = FDCNEOConverter()

# 온라인 → 오프라인
result = converter.online_to_offline(
    'GT_N24987L02.txt', 
    'Fault_GT_converted.txt'
)

print(result.message)
```

### 병합만 하기

```python
from fdc_neo_converter import FDCNEOConverter

converter = FDCNEOConverter()

# 온라인 형식으로 병합
result = converter.merge_to_online(
    'GT_online.txt',
    'Fault_GT_offline.txt',
    'merged_output.txt'
)

print(f"{result.record_count}개 레코드 병합 완료")
```

---

## 📁 출력 파일 형식

### 변환 결과

**온라인 → 오프라인**:
```
입력: GT_N24987L02_260107_091837.txt
출력: Fault_GT_N24987L02.txt

형식:
  - Binary 파일
  - 512 KB (GT) 또는 256 KB (WBVF)
  - ConfigDone 헤더 포함
  - GSP/WBVF 식별자 포함
```

**오프라인 → 온라인**:
```
입력: Fault_GT_N23261L01.txt
출력: GT_FULL_N23261L01_260120_153045.txt

형식:
  - Hex-String 텍스트
  - 가변 크기 (레코드 수에 따라)
  - 전체 레코드 포함 (크기 제한 없음)
  - 타임스탬프 검증 완화로 모든 레코드 추출
```

### 병합 결과

**온라인 형식**:
```
출력: Merged_Online_260120_153045.txt

특징:
  - Hex-String 텍스트
  - 가변 크기 (레코드 수에 따라)
  - 모든 레코드 포함 (크기 제한 없음)
  - 타임스탬프 기준 중복 제거됨
  - 타임스탬프가 없는 레코드도 모두 포함
```

**오프라인 형식**:
```
출력: Merged_Offline_260120_153045.txt

특징:
  - Binary 파일
  - 256 KB / 512 KB
  - 모든 레코드 포함
  - 중복 제거됨
  - ConfigDone 헤더 포함
```

---

## ⚙️ 설정 및 커스터마이징

### 병합 시 레코드 수 조정

`fdc_neo_converter.py` 파일에서:

```python
# 온라인 출력 시 최대 레코드 수
def _save_as_online(self, records, output_file):
    for ts, data in records[:20]:  # ← 20을 원하는 숫자로 변경
        record_data += data
```

---

## 🐛 문제 해결

### 문제 0: 설치 오류 (externally-managed-environment)

**증상**: `pip install` 시 "externally-managed-environment" 오류 발생

**해결**:
```bash
# 가상 환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows

# 가상 환경에서 설치
pip install -r requirements.txt
```

**원인**: macOS의 시스템 Python은 외부 패키지 설치를 제한합니다. 가상 환경을 사용하면 이 제한을 우회할 수 있습니다.

### 문제 1: 변환 실패

**증상**: "변환 실패" 오류 메시지

**해결**:
```
1. 입력 파일 타입 확인
   - 온라인 파일인지 오프라인 파일인지
   - 파일 타입 자동 감지 기능이 있지만, 올바른 파일 업로드 권장
   
2. Hex-String 검증 (온라인 파일)
   - 0-9, A-F만 포함되어야 함
   - Binary 파일이 온라인 파일 슬롯에 업로드되면 자동 감지됨
   
3. 권한 확인
   - 출력 디렉토리 쓰기 권한
```

### 문제 2: 병합 시 레코드 수가 예상보다 적음

**증상**: 병합 결과 레코드 수가 입력 파일 레코드 합보다 적음

**원인 및 해결**:
```
1. 타임스탬프 기준 중복 제거
   - 같은 타임스탬프를 가진 레코드는 하나만 유지
   - 정상적인 동작입니다
   
2. 타임스탬프가 없는 레코드
   - 타임스탬프가 없는 레코드는 모두 포함됨
   - 중복 제거 대상이 아님
   
3. 레코드 추출 개선
   - 타임스탬프 검증 완화로 더 많은 레코드 추출
   - 데이터 손실 없이 전체 레코드 포함
```

---

## 📊 성능 정보

### 처리 속도

| 작업 | 파일 크기 | 예상 시간 |
|------|----------|----------|
| 변환 | 모든 크기 | ~0.1초 |
| 병합 | 두 파일 | ~1.5초 |

### 메모리 사용

| 작업 | 예상 메모리 |
|------|-----------|
| 변환 1개 파일 | ~5 MB |
| 병합 2개 파일 | ~10 MB |

---

## 🎓 추가 정보

### 지원되는 마커

```
E4 (228): WBVF 구형
E5 (229): WBVF 구형
E6 (230): WBVF 주력
E7 (231): GT 주력
E8 (232): GT 보조
E9 (233): GT/WB 온라인
EA (234): GT 온라인 최신
EB (235): WB 온라인 최신
```

### 타임스탬프 형식

```
6 bytes: [YY] [MM] [DD] [HH] [MI] [SS]

예시: 26 01 07 09 07 38
     → 2026-01-07 09:07:56

범위:
  YY: 00-99 (2000-2099)
  MM: 01-12
  DD: 01-31
  HH: 00-23
  MI: 00-59
  SS: 00-59
```



- 기술 문서: 파서_기능_요약.md
- 파일 구조: 온라인_오프라인_구조_최종.md


