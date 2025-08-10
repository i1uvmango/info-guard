"""
Info-Guard AI 모델 테스트
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import json

from models.credibility_analyzer import CredibilityAnalyzer
from models.bias_detector import BiasDetector
from models.fact_checker import FactChecker
from models.source_validator import SourceValidator
from models.sentiment_analyzer import SentimentAnalyzer

class TestCredibilityAnalyzer:
    """신뢰도 분석기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.analyzer = CredibilityAnalyzer()
    
    def test_extract_features(self):
        """특징 추출 테스트"""
        text = "This is a factual news report with verified sources and official data."
        metadata = {
            "title": "Factual News Report",
            "description": "Based on verified sources and official data."
        }
        
        features = self.analyzer.extract_features(text, metadata)
        
        assert "text_length" in features
        assert "avg_sentence_length" in features
        assert "vocabulary_diversity" in features
        assert "sentiment_neutral" in features
        assert "sentiment_compound" in features
        assert "technical_terms" in features
        assert "citation_count" in features
        assert "reference_count" in features
        assert "claim_fact_ratio" in features
    
    def test_analyze_credibility(self):
        """신뢰도 분석 테스트"""
        text = "This is a factual news report with verified sources and official data."
        metadata = {
            "title": "Factual News Report",
            "description": "Based on verified sources and official data."
        }
        
        result = self.analyzer.analyze_credibility(text, metadata)
        
        assert "score" in result
        assert "grade" in result
        assert "breakdown" in result
        assert "explanation" in result
        assert "confidence" in result
        
        assert 0 <= result["score"] <= 100
        assert result["grade"] in ["A", "B", "C", "D", "F"]
        assert result["confidence"] >= 0
    
    def test_high_credibility_content(self):
        """높은 신뢰도 콘텐츠 테스트"""
        text = """
        According to official government data released on March 15, 2024, 
        the economic growth rate was 2.8% in the first quarter. 
        This figure is based on verified statistics from the Bureau of Economic Analysis 
        and has been confirmed by multiple independent sources.
        """
        
        result = self.analyzer.analyze_credibility(text)
        
        # 높은 신뢰도 콘텐츠는 높은 점수를 받아야 함
        assert result["score"] > 70
        assert result["grade"] in ["A", "B"]
    
    def test_low_credibility_content(self):
        """낮은 신뢰도 콘텐츠 테스트"""
        text = """
        I heard from my friend that the government is hiding the real numbers. 
        Everyone knows the economy is actually terrible and they're just lying to us. 
        Don't trust the official data!
        """
        
        result = self.analyzer.analyze_credibility(text)
        
        # 낮은 신뢰도 콘텐츠는 낮은 점수를 받아야 함
        assert result["score"] < 50
        assert result["grade"] in ["D", "F"]

class TestBiasDetector:
    """편향 감지기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.detector = BiasDetector()
    
    def test_detect_bias(self):
        """편향 감지 테스트"""
        text = "This is a neutral text without any obvious bias."
        
        result = self.detector.detect(text)
        
        assert "total_bias_score" in result
        assert "bias_types" in result
        assert "emotional" in result["bias_types"]
        assert "political" in result["bias_types"]
        assert "economic" in result["bias_types"]
        assert "cultural" in result["bias_types"]
        
        assert 0 <= result["total_bias_score"] <= 100
    
    def test_political_bias_detection(self):
        """정치적 편향 감지 테스트"""
        text = "The liberal media is always lying to us and spreading fake news."
        
        result = self.detector.detect(text)
        
        # 정치적 편향이 감지되어야 함
        assert result["bias_types"]["political"] > 30
    
    def test_emotional_bias_detection(self):
        """감정적 편향 감지 테스트"""
        text = "This is absolutely terrible and disgusting! I can't believe how awful this is!"
        
        result = self.detector.detect(text)
        
        # 감정적 편향이 감지되어야 함
        assert result["bias_types"]["emotional"] > 40

class TestFactChecker:
    """팩트 체커 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.checker = FactChecker()
    
    def test_extract_claims(self):
        """주장 추출 테스트"""
        text = "The population of Seoul is 10 million people according to official statistics."
        
        claims = self.checker.extract_claims(text)
        
        assert len(claims) > 0
        assert "Seoul" in str(claims)
        assert "10 million" in str(claims)
    
    def test_verify_facts(self):
        """사실 검증 테스트"""
        text = "The Earth is round and orbits around the Sun."
        
        result = self.checker.verify(text)
        
        assert "score" in result
        assert "verified_claims" in result
        assert "fact_check_results" in result
        
        assert 0 <= result["score"] <= 100
    
    def test_high_fact_check_score(self):
        """높은 팩트 체크 점수 테스트"""
        text = "Water boils at 100 degrees Celsius at sea level."
        
        result = self.checker.verify(text)
        
        # 검증 가능한 사실은 높은 점수를 받아야 함
        assert result["score"] > 80

class TestSourceValidator:
    """소스 검증기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.validator = SourceValidator()
    
    def test_validate_source(self):
        """소스 검증 테스트"""
        source_info = {
            "domain": "reuters.com",
            "author": "John Smith",
            "publication_date": "2024-01-15",
            "citations": 5
        }
        
        result = self.validator.validate(source_info)
        
        assert "score" in result
        assert "reliability" in result
        assert "authority" in result
        assert "recency" in result
        
        assert 0 <= result["score"] <= 100
    
    def test_trusted_source(self):
        """신뢰할 수 있는 소스 테스트"""
        source_info = {
            "domain": "reuters.com",
            "author": "Professional Journalist",
            "publication_date": "2024-01-15",
            "citations": 10
        }
        
        result = self.validator.validate(source_info)
        
        # 신뢰할 수 있는 소스는 높은 점수를 받아야 함
        assert result["score"] > 70
    
    def test_untrusted_source(self):
        """신뢰할 수 없는 소스 테스트"""
        source_info = {
            "domain": "conspiracy-blog.com",
            "author": "Anonymous",
            "publication_date": "2024-01-15",
            "citations": 0
        }
        
        result = self.validator.validate(source_info)
        
        # 신뢰할 수 없는 소스는 낮은 점수를 받아야 함
        assert result["score"] < 50

class TestSentimentAnalyzer:
    """감정 분석기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.analyzer = SentimentAnalyzer()
    
    def test_analyze_sentiment(self):
        """감정 분석 테스트"""
        text = "This is a neutral text without strong emotions."
        
        result = self.analyzer.analyze(text)
        
        assert "score" in result
        assert "sentiment" in result
        assert "confidence" in result
        
        assert -1 <= result["score"] <= 1
        assert result["sentiment"] in ["positive", "negative", "neutral"]
        assert 0 <= result["confidence"] <= 1
    
    def test_positive_sentiment(self):
        """긍정적 감정 테스트"""
        text = "This is wonderful and amazing! I love it!"
        
        result = self.analyzer.analyze(text)
        
        assert result["sentiment"] == "positive"
        assert result["score"] > 0.3
    
    def test_negative_sentiment(self):
        """부정적 감정 테스트"""
        text = "This is terrible and awful! I hate it!"
        
        result = self.analyzer.analyze(text)
        
        assert result["sentiment"] == "negative"
        assert result["score"] < -0.3
    
    def test_neutral_sentiment(self):
        """중립적 감정 테스트"""
        text = "This is a factual statement without emotional content."
        
        result = self.analyzer.analyze(text)
        
        assert result["sentiment"] == "neutral"
        assert abs(result["score"]) < 0.3

class TestModelIntegration:
    """모델 통합 테스트"""
    
    def test_full_analysis_pipeline(self):
        """전체 분석 파이프라인 테스트"""
        # 모든 모델 초기화
        credibility_analyzer = CredibilityAnalyzer()
        bias_detector = BiasDetector()
        fact_checker = FactChecker()
        source_validator = SourceValidator()
        sentiment_analyzer = SentimentAnalyzer()
        
        # 테스트 텍스트
        text = "According to official government data, the economic growth was 2.8% in Q1 2024."
        metadata = {
            "title": "Economic Report",
            "source": "reuters.com"
        }
        
        # 각 모델로 분석
        credibility_result = credibility_analyzer.analyze_credibility(text, metadata)
        bias_result = bias_detector.detect(text)
        fact_result = fact_checker.verify(text)
        source_result = source_validator.validate({"domain": "reuters.com"})
        sentiment_result = sentiment_analyzer.analyze(text)
        
        # 결과 검증
        assert credibility_result["score"] > 0
        assert bias_result["total_bias_score"] >= 0
        assert fact_result["score"] > 0
        assert source_result["score"] > 0
        assert sentiment_result["score"] >= -1 and sentiment_result["score"] <= 1

if __name__ == "__main__":
    pytest.main([__file__]) 