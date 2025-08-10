"""
콘텐츠 분류 모델 간단 테스트 스크립트 (규칙 기반)
"""

import sys
import time
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from models.content_classifier.preprocessor import ContentPreprocessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_preprocessor():
    """전처리기 테스트"""
    try:
        logger.info("전처리기 테스트 시작...")
        
        preprocessor = ContentPreprocessor()
        
        # 테스트 데이터
        test_cases = [
            {
                "title": "정치 뉴스: 대통령, 경제 정책 발표",
                "description": "오늘 대통령이 새로운 경제 정책을 발표했습니다.",
                "tags": ["정치", "경제", "대통령", "정책"]
            },
            {
                "title": "엔터테인먼트: 최신 영화 리뷰",
                "description": "이번 주 개봉한 영화들의 리뷰를 소개합니다.",
                "tags": ["영화", "리뷰", "엔터테인먼트"]
            },
            {
                "title": "경제: 주식 시장 동향 분석",
                "description": "오늘 주식 시장의 주요 동향을 분석해드립니다.",
                "tags": ["주식", "경제", "시장", "분석"]
            }
        ]
        
        for i, case in enumerate(test_cases):
            logger.info(f"테스트 케이스 {i+1}: {case['title']}")
            
            result = preprocessor.preprocess_text(
                case['title'], 
                case['description'], 
                case['tags']
            )
            
            logger.info(f"  원본 텍스트 길이: {result['metadata']['title_length']}")
            logger.info(f"  전처리된 텍스트: {result['processed']['combined'][:100]}...")
            
        logger.info("전처리기 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"전처리기 테스트 실패: {e}")
        return False

def test_rule_based_classification():
    """규칙 기반 분류 테스트"""
    try:
        logger.info("규칙 기반 분류 테스트 시작...")
        
        # 간단한 규칙 기반 분류 함수
        def simple_classify(text):
            text_lower = text.lower()
            
            # 정치 관련 키워드
            political_keywords = [
                '정치', '대통령', '국회', '의원', '정부', '여당', '야당', '선거', '투표',
                '민주주의', '자유주의', '보수', '진보', '정책', '법안', '헌법', '외교',
                '국방', '행정', '사법', '입법', '지방자치', '정당', '여론조사'
            ]
            
            # 경제 관련 키워드
            economic_keywords = [
                '경제', '주식', '부동산', '금리', '인플레이션', 'GDP', '수출', '수입',
                '기업', '주식시장', '환율', '원화', '달러', '투자', '재정', '은행',
                '금융', '보험', '세금', '예산', '무역', '산업', '고용', '실업률'
            ]
            
            # 시사 관련 키워드
            news_keywords = [
                '뉴스', '사건', '사고', '범죄', '재난', '사고', '사망', '부상',
                '화재', '교통사고', '자연재해', '테러', '전쟁', '평화', '사회',
                '교육', '의료', '환경', '기후', '에너지', '교통', '건설', '농업'
            ]
            
            # 엔터테인먼트 관련 키워드 (우선순위 높임)
            entertainment_keywords = [
                '엔터테인먼트', '영화', '드라마', '예능', '음악', '가수', '아이돌',
                '배우', '연예인', '콘서트', '공연', '게임', '스포츠', '축구',
                '야구', '농구', '골프', '테니스', '유튜브', '스트리밍', '방송',
                '채널', '구독자', '뷰', '좋아요', '댓글', '트렌드', '인기'
            ]
            
            # 키워드 매칭 (엔터테인먼트 우선)
            entertainment_score = sum(2 for keyword in entertainment_keywords if keyword in text_lower)  # 가중치 2배
            political_score = sum(1 for keyword in political_keywords if keyword in text_lower)
            economic_score = sum(1 for keyword in economic_keywords if keyword in text_lower)
            news_score = sum(1 for keyword in news_keywords if keyword in text_lower)
            
            # 디버깅: 각 카테고리별 점수 출력
            logger.info(f"    점수 - 정치: {political_score}, 경제: {economic_score}, 시사: {news_score}, 엔터테인먼트: {entertainment_score}")
            
            # 가장 높은 점수의 카테고리 선택
            scores = [political_score, economic_score, news_score, entertainment_score]
            max_score = max(scores)
            category_id = scores.index(max_score)
            
            categories = ["정치", "경제", "시사", "엔터테인먼트"]
            return category_id, categories[category_id], max_score
        
        # 테스트 데이터
        test_contents = [
            {
                "title": "정치 뉴스: 국회에서 예산안 통과",
                "description": "오늘 국회에서 내년도 예산안이 통과되었습니다.",
                "tags": ["정치", "국회", "예산", "통과"]
            },
            {
                "title": "경제: 부동산 시장 전망",
                "description": "전문가들이 내년 부동산 시장 전망을 분석했습니다.",
                "tags": ["경제", "부동산", "시장", "전망"]
            },
            {
                "title": "시사: 교통사고 증가 추세",
                "description": "최근 교통사고가 증가하고 있어 주의가 필요합니다.",
                "tags": ["시사", "교통사고", "안전", "주의"]
            },
            {
                "title": "아이돌 그룹 컴백 소식",
                "description": "인기 아이돌 그룹이 새 앨범으로 컴백합니다.",
                "tags": ["아이돌", "컴백", "앨범", "음악", "가수"]
            }
        ]
        
        results = []
        
        for i, content in enumerate(test_contents):
            logger.info(f"콘텐츠 {i+1} 분류 중: {content['title']}")
            
            # 텍스트 결합
            combined_text = f"{content['title']} {content['description']} {' '.join(content['tags'])}"
            logger.info(f"  결합된 텍스트: {combined_text}")
            
            start_time = time.time()
            
            category_id, category_name, score = simple_classify(combined_text)
            
            processing_time = time.time() - start_time
            
            logger.info(f"  분류 결과: {category_name} (점수: {score}, 신뢰도: {min(score/3, 0.9):.2f})")
            logger.info(f"  처리 시간: {processing_time:.3f}초")
            
            results.append({
                'content': content,
                'result': {
                    'category_id': category_id,
                    'category_name': category_name,
                    'score': score,
                    'confidence': min(score/3, 0.9)
                },
                'processing_time': processing_time
            })
        
        logger.info("규칙 기반 분류 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"규칙 기반 분류 테스트 실패: {e}")
        return False

def test_performance():
    """성능 테스트"""
    try:
        logger.info("성능 테스트 시작...")
        
        # 간단한 분류 함수
        def simple_classify(text):
            text_lower = text.lower()
            
            political_keywords = ['정치', '대통령', '국회', '의원', '정부', '여당', '야당', '선거', '투표']
            economic_keywords = ['경제', '주식', '부동산', '금리', '인플레이션', 'GDP', '수출', '수입']
            news_keywords = ['뉴스', '사건', '사고', '범죄', '재난', '사고', '사망', '부상']
            
            political_score = sum(1 for keyword in political_keywords if keyword in text_lower)
            economic_score = sum(1 for keyword in economic_keywords if keyword in text_lower)
            news_score = sum(1 for keyword in news_keywords if keyword in text_lower)
            
            scores = [political_score, economic_score, news_score, 0]
            return scores.index(max(scores))
        
        # 대량의 테스트 데이터
        test_contents = []
        categories = ["정치", "경제", "시사", "기타"]
        
        for i in range(100):
            category = categories[i % 4]
            test_contents.append({
                "title": f"{category} 관련 제목 {i+1}",
                "description": f"{category}에 대한 설명 {i+1}입니다.",
                "tags": [category, f"태그{i+1}"]
            })
        
        # 배치 분류 성능 테스트
        start_time = time.time()
        results = []
        
        for content in test_contents:
            combined_text = f"{content['title']} {content['description']} {' '.join(content['tags'])}"
            category_id = simple_classify(combined_text)
            results.append(category_id)
        
        total_time = time.time() - start_time
        
        logger.info(f"  총 처리 시간: {total_time:.2f}초")
        logger.info(f"  평균 처리 시간: {total_time/len(test_contents):.3f}초/개")
        logger.info(f"  처리 속도: {len(test_contents)/total_time:.1f}개/초")
        
        # 정확도 계산
        correct = 0
        for i, result in enumerate(results):
            expected_category = i % 4
            if result == expected_category:
                correct += 1
        
        accuracy = correct / len(results) * 100
        logger.info(f"  정확도: {accuracy:.1f}%")
        
        logger.info("성능 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"성능 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("=== 콘텐츠 분류 모델 간단 테스트 시작 ===")
    
    tests = [
        ("전처리기", test_preprocessor),
        ("규칙 기반 분류", test_rule_based_classification),
        ("성능", test_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} 테스트 ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"{test_name} 테스트에서 예외 발생: {e}")
            results[test_name] = False
    
    # 결과 요약
    logger.info("\n=== 테스트 결과 요약 ===")
    for test_name, result in results.items():
        status = "성공" if result else "실패"
        logger.info(f"{test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    logger.info(f"\n전체 테스트: {success_count}/{total_count} 성공")
    
    if success_count == total_count:
        logger.info("🎉 모든 테스트가 성공했습니다!")
    else:
        logger.warning("⚠️ 일부 테스트가 실패했습니다.")

if __name__ == "__main__":
    main()
