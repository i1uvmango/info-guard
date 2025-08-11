# Info-Guard Chrome Extension 이미지 폴더

이 폴더는 Chrome Extension에서 사용하는 이미지 파일들을 저장합니다.

## 필요한 이미지 파일들

### 1. 로고 이미지
- `logo.png` - Info-Guard 로고 (권장 크기: 200x200)
- `logo-dark.png` - 다크 테마용 로고 (권장 크기: 200x200)

### 2. UI 요소 이미지
- `credibility-badge.png` - 신뢰도 배지 이미지
- `analysis-icon.png` - 분석 아이콘
- `settings-icon.png` - 설정 아이콘

### 3. 상태 표시 이미지
- `loading.gif` - 로딩 애니메이션
- `success-icon.png` - 성공 상태 아이콘
- `error-icon.png` - 에러 상태 아이콘
- `warning-icon.png` - 경고 상태 아이콘

## 이미지 가이드라인

- **형식**: PNG, SVG (투명도 지원)
- **크기**: 아이콘은 16x16, 32x32, 48x48, 128x128
- **스타일**: Info-Guard 브랜딩에 맞는 일관된 디자인
- **최적화**: 웹 사용을 위한 적절한 압축

## 사용법

이미지 파일들은 HTML과 CSS에서 다음과 같이 참조할 수 있습니다:

```html
<img src="../assets/images/logo.png" alt="Info-Guard">
```

```css
.background {
    background-image: url('../assets/images/credibility-badge.png');
}
```
