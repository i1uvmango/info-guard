#!/usr/bin/env python3
"""
학습 스크립트 테스트를 위한 샘플 데이터 생성 스크립트
"""

import json
import csv
import random
from pathlib import Path

def create_sentiment_data():
    """감정 분석 테스트 데이터 생성"""
    data = []
    
    # 긍정적인 텍스트
    positive_texts = [
        "이 영상은 정말 유익하고 재미있어요!",
        "훌륭한 정보를 제공해주셔서 감사합니다.",
        "매우 도움이 되는 내용이었습니다.",
        "정말 좋은 영상이네요!",
        "이런 영상이 더 필요해요."
    ]
    
    # 중립적인 텍스트
    neutral_texts = [
        "이 영상은 보통 수준입니다.",
        "그럭저럭 괜찮은 내용이에요.",
        "평범한 영상이네요.",
        "특별한 점은 없지만 나쁘지 않아요.",
        "보통의 품질을 가지고 있습니다."
    ]
    
    # 부정적인 텍스트
    negative_texts = [
        "이 영상은 별로 도움이 안 되었어요.",
        "내용이 부족하고 실망스럽습니다.",
        "시간 낭비였어요.",
        "이런 영상은 필요 없어요.",
        "품질이 좋지 않습니다."
    ]
    
    # 데이터 생성
    for text in positive_texts:
        data.append({"text": text, "label": "positive"})
    
    for text in neutral_texts:
        data.append({"text": text, "label": "neutral"})
    
    for text in negative_texts:
        data.append({"text": text, "label": "negative"})
    
    # 데이터 섞기
    random.shuffle(data)
    
    # JSON 파일로 저장
    with open("test_sentiment_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # CSV 파일로도 저장
    with open("test_sentiment_data.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"감정 분석 테스트 데이터 생성 완료: {len(data)}개 샘플")

def create_bias_data():
    """편향 감지 테스트 데이터 생성"""
    data = []
    
    # 중립적인 텍스트
    neutral_texts = [
        "이 영상은 객관적인 사실을 바탕으로 제작되었습니다.",
        "여러 관점에서 균형있게 다루고 있습니다.",
        "사실에 근거한 정보를 제공합니다.",
        "객관적인 분석을 시도합니다.",
        "편향 없이 정보를 전달합니다."
    ]
    
    # 편향적인 텍스트
    biased_texts = [
        "이것은 확실히 잘못된 것입니다.",
        "절대적으로 옳은 방법입니다.",
        "이런 사람들은 모두 나쁩니다.",
        "이것만이 유일한 해결책입니다.",
        "다른 의견은 모두 틀렸습니다."
    ]
    
    # 데이터 생성
    for text in neutral_texts:
        data.append({"text": text, "bias_label": "neutral"})
    
    for text in biased_texts:
        data.append({"text": text, "bias_label": "biased"})
    
    # 데이터 섞기
    random.shuffle(data)
    
    # JSON 파일로 저장
    with open("test_bias_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # CSV 파일로도 저장
    with open("test_bias_data.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "bias_label"])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"편향 감지 테스트 데이터 생성 완료: {len(data)}개 샘플")

def create_credibility_data():
    """신뢰도 분석 테스트 데이터 생성"""
    data = []
    
    # 신뢰할 수 있는 텍스트
    reliable_texts = [
        "공식 통계에 따르면 2023년 경제 성장률은 2.6%입니다.",
        "의학 저널에 발표된 연구 결과입니다.",
        "전문가들의 합의된 의견입니다.",
        "공식 문서에 기록된 사실입니다.",
        "검증된 출처에서 제공된 정보입니다."
    ]
    
    # 부분적으로 신뢰할 수 있는 텍스트
    partially_reliable_texts = [
        "일부 전문가들이 주장하는 내용입니다.",
        "초기 연구 결과이므로 추가 검증이 필요합니다.",
        "개인적인 경험을 바탕으로 한 의견입니다.",
        "아직 검증되지 않은 가설입니다.",
        "제한된 데이터를 바탕으로 한 추정입니다."
    ]
    
    # 신뢰할 수 없는 텍스트
    unreliable_texts = [
        "익명의 소식통에 따르면...",
        "인터넷에서 본 글입니다.",
        "확인되지 않은 소문입니다.",
        "개인 블로그의 의견입니다.",
        "출처가 불분명한 정보입니다."
    ]
    
    # 데이터 생성
    for text in reliable_texts:
        data.append({"text": text, "credibility_label": "reliable"})
    
    for text in partially_reliable_texts:
        data.append({"text": text, "credibility_label": "partially_reliable"})
    
    for text in unreliable_texts:
        data.append({"text": text, "credibility_label": "unreliable"})
    
    # 데이터 섞기
    random.shuffle(data)
    
    # JSON 파일로 저장
    with open("test_credibility_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # CSV 파일로도 저장
    with open("test_credibility_data.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "credibility_label"])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"신뢰도 분석 테스트 데이터 생성 완료: {len(data)}개 샘플")

def create_content_classification_data():
    """콘텐츠 분류 테스트 데이터 생성"""
    data = []
    
    categories = {
        'news': [
            "오늘 주요 뉴스는 다음과 같습니다.",
            "정부에서 새로운 정책을 발표했습니다.",
            "국제 뉴스에서 중요한 소식이 전해졌습니다."
        ],
        'entertainment': [
            "새로운 영화가 개봉되었습니다.",
            "인기 연예인의 소식입니다.",
            "재미있는 예능 프로그램이 방영됩니다."
        ],
        'education': [
            "학습에 도움이 되는 팁을 알려드립니다.",
            "새로운 교육 방법에 대해 알아보겠습니다.",
            "지식 습득을 위한 방법을 제시합니다."
        ],
        'technology': [
            "최신 기술 동향을 살펴보겠습니다.",
            "새로운 소프트웨어가 출시되었습니다.",
            "기술 발전에 대한 분석입니다."
        ]
    }
    
    # 데이터 생성
    for category, texts in categories.items():
        for text in texts:
            data.append({"text": text, "category_label": category})
    
    # 데이터 섞기
    random.shuffle(data)
    
    # JSON 파일로 저장
    with open("test_content_classification_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # CSV 파일로도 저장
    with open("test_content_classification_data.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "category_label"])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"콘텐츠 분류 테스트 데이터 생성 완료: {len(data)}개 샘플")

def main():
    """메인 함수"""
    print("테스트 데이터 생성 시작...")
    
    # 랜덤 시드 설정
    random.seed(42)
    
    # 각 모델별 테스트 데이터 생성
    create_sentiment_data()
    create_bias_data()
    create_credibility_data()
    create_content_classification_data()
    
    print("\n모든 테스트 데이터 생성 완료!")
    print("생성된 파일들:")
    print("- test_sentiment_data.json/csv")
    print("- test_bias_data.json/csv")
    print("- test_credibility_data.json/csv")
    print("- test_content_classification_data.json/csv")

if __name__ == "__main__":
    main()
