"""
콘텐츠 분류 모델 테스트 스크립트
"""

import sys
import time
import logging
import numpy as np
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from models.content_classifier.classifier import ContentClassifier
from models.content_classifier.preprocessor import ContentPreprocessor
from models.content_classifier.trainer import ContentClassifierTrainer

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

def test_classifier():
    """분류기 테스트"""
    try:
        logger.info("분류기 테스트 시작...")
        
        # 사전훈련 모델 사용
        classifier = ContentClassifier(use_pretrained=True)
        
        if not classifier.is_loaded:
            logger.error("모델 로드 실패")
            return False
        
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
                "title": "엔터테인먼트: 아이돌 그룹 컴백",
                "description": "인기 아이돌 그룹이 새 앨범으로 컴백합니다.",
                "tags": ["아이돌", "컴백", "앨범", "엔터테인먼트"]
            }
        ]
        
        results = []
        
        for i, content in enumerate(test_contents):
            logger.info(f"콘텐츠 {i+1} 분류 중: {content['title']}")
            
            start_time = time.time()
            
            result = classifier.classify(
                content['title'],
                content['description'],
                content['tags']
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"  분류 결과: {result['prediction']['category_name']} (신뢰도: {result['prediction']['confidence']:.2f})")
            logger.info(f"  처리 시간: {processing_time:.3f}초")
            
            results.append({
                'content': content,
                'result': result,
                'processing_time': processing_time
            })
        
        # 배치 분류 테스트
        logger.info("배치 분류 테스트...")
        batch_results = classifier.batch_classify(test_contents)
        
        for i, result in enumerate(batch_results):
            logger.info(f"  배치 결과 {i+1}: {result['prediction']['category_name']} (신뢰도: {result['prediction']['confidence']:.2f})")
        
        logger.info("분류기 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"분류기 테스트 실패: {e}")
        return False

def test_trainer():
    """학습기 테스트"""
    try:
        logger.info("학습기 테스트 시작...")
        
        trainer = ContentClassifierTrainer()
        
        # 모델 설정
        trainer.setup_model()
        
        if not trainer.model or not trainer.tokenizer:
            logger.error("모델 또는 토크나이저 설정 실패")
            return False
        
        logger.info("모델 설정 완료")
        logger.info(f"  모델: {type(trainer.model).__name__}")
        logger.info(f"  토크나이저: {type(trainer.tokenizer).__name__}")
        
        # 샘플 데이터로 데이터셋 생성 테스트 (각 카테고리당 2개씩)
        sample_data = [
            # 정치 카테고리 (0)
            {
                "title": "정치 뉴스입니다.",
                "description": "정치 관련 뉴스 내용입니다.",
                "tags": ["정치", "뉴스"],
                "category": 0
            },
            {
                "title": "대통령 정책 발표",
                "description": "새로운 정책이 발표되었습니다.",
                "tags": ["정치", "대통령", "정책"],
                "category": 0
            },
            # 경제 카테고리 (1)
            {
                "title": "경제 뉴스입니다.",
                "description": "경제 관련 뉴스 내용입니다.",
                "tags": ["경제", "뉴스"],
                "category": 1
            },
            {
                "title": "주식 시장 동향",
                "description": "오늘 주식 시장 상황을 분석합니다.",
                "tags": ["경제", "주식", "시장"],
                "category": 1
            },
            # 시사 카테고리 (2)
            {
                "title": "시사 뉴스입니다.",
                "description": "시사 관련 뉴스 내용입니다.",
                "tags": ["시사", "뉴스"],
                "category": 2
            },
            {
                "title": "교통사고 발생",
                "description": "오늘 발생한 교통사고 소식을 전합니다.",
                "tags": ["시사", "교통사고", "안전"],
                "category": 2
            },
            # 엔터테인먼트 카테고리 (3)
            {
                "title": "엔터테인먼트 뉴스입니다.",
                "description": "엔터테인먼트 관련 뉴스 내용입니다.",
                "tags": ["엔터테인먼트", "뉴스"],
                "category": 3
            },
            {
                "title": "새 영화 개봉",
                "description": "이번 주 개봉하는 영화들을 소개합니다.",
                "tags": ["엔터테인먼트", "영화", "개봉"],
                "category": 3
            }
        ]
        
        # 간단한 데이터셋 생성 테스트 (전처리만)
        processed_texts = []
        labels = []
        
        for item in sample_data:
            try:
                preprocessed = trainer.preprocessor.preprocess_text(
                    title=item['title'],
                    description=item.get('description', ''),
                    tags=item.get('tags', [])
                )
                processed_texts.append(preprocessed['processed']['combined'])
                labels.append(item['category'])
            except Exception as e:
                logger.warning(f"데이터 전처리 실패: {e}")
                continue
        
        logger.info(f"  전처리 완료: {len(processed_texts)}개 샘플")
        logger.info(f"  카테고리 분포: {dict(zip(*np.unique(labels, return_counts=True)))}")
        
        logger.info("학습기 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"학습기 테스트 실패: {e}")
        return False

def test_performance():
    """성능 테스트"""
    try:
        logger.info("성능 테스트 시작...")
        
        classifier = ContentClassifier(use_pretrained=True)
        
        if not classifier.is_loaded:
            logger.error("모델 로드 실패")
            return False
        
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
        results = classifier.batch_classify(test_contents)
        total_time = time.time() - start_time
        
        logger.info(f"  총 처리 시간: {total_time:.2f}초")
        logger.info(f"  평균 처리 시간: {total_time/len(test_contents):.3f}초/개")
        logger.info(f"  처리 속도: {len(test_contents)/total_time:.1f}개/초")
        
        # 정확도 계산
        correct = 0
        for i, result in enumerate(results):
            expected_category = i % 4
            if result['prediction']['category_id'] == expected_category:
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
    logger.info("=== 콘텐츠 분류 모델 테스트 시작 ===")
    
    tests = [
        ("전처리기", test_preprocessor),
        ("분류기", test_classifier),
        ("학습기", test_trainer),
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
