import re
import string
from typing import List, Dict, Any
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk

class TextProcessor:
    """
    텍스트 전처리 및 분석 유틸리티
    """
    
    def __init__(self):
        # NLTK 데이터 다운로드
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
        
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
    
    def preprocess_text(self, text: str) -> str:
        """
        텍스트를 전처리합니다.
        """
        if not text:
            return ""
        
        # 소문자 변환
        text = text.lower()
        
        # 특수 문자 제거 (단, 문장 구분자와 기본 문장 부호는 유지)
        text = re.sub(r'[^\w\s\.\!\?\,\;\:]', '', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def clean_text(self, text: str) -> str:
        """
        텍스트를 깨끗하게 정리합니다.
        """
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # URL 제거
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 이메일 제거
        text = re.sub(r'\S+@\S+', '', text)
        
        # 특수 문자 제거 (문장 부호는 유지)
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize_words(self, text: str) -> List[str]:
        """
        텍스트를 단어로 토큰화합니다.
        """
        if not text:
            return []
        
        # 문장 부호 제거
        text = re.sub(r'[^\w\s]', '', text)
        
        # 단어 토큰화
        tokens = word_tokenize(text.lower())
        
        # 불용어 제거
        tokens = [token for token in tokens if token not in self.stop_words]
        
        # 숫자 제거
        tokens = [token for token in tokens if not token.isdigit()]
        
        # 길이가 1인 토큰 제거
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        텍스트를 문장으로 토큰화합니다.
        """
        if not text:
            return []
        
        sentences = sent_tokenize(text)
        
        # 빈 문장 제거
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def lemmatize_words(self, words: List[str]) -> List[str]:
        """
        단어들을 원형으로 변환합니다.
        """
        return [self.lemmatizer.lemmatize(word) for word in words]
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        텍스트에서 키워드를 추출합니다.
        """
        if not text:
            return []
        
        # 단어 토큰화
        words = self.tokenize_words(text)
        
        # 단어 빈도 계산
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 N개 키워드 반환
        keywords = []
        for word, freq in sorted_words[:top_n]:
            keywords.append({
                'word': word,
                'frequency': freq,
                'percentage': round(freq / len(words) * 100, 2)
            })
        
        return keywords
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        텍스트에서 개체명을 추출합니다.
        """
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'numbers': []
        }
        
        # 사람 이름 패턴 (대문자로 시작하는 2-3단어)
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b'
        persons = re.findall(person_pattern, text)
        entities['persons'] = list(set(persons))
        
        # 조직명 패턴
        org_pattern = r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)* (?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University|College)\b'
        organizations = re.findall(org_pattern, text)
        entities['organizations'] = list(set(organizations))
        
        # 지역명 패턴
        location_pattern = r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)* (?:City|State|Country|Province|Region)\b'
        locations = re.findall(location_pattern, text)
        entities['locations'] = list(set(locations))
        
        # 날짜 패턴
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b'
        dates = re.findall(date_pattern, text)
        entities['dates'] = list(set(dates))
        
        # 숫자 패턴
        number_pattern = r'\b\d+(?:\.\d+)?(?:%|원|달러|개|명|년|월|일)?\b'
        numbers = re.findall(number_pattern, text)
        entities['numbers'] = list(set(numbers))
        
        return entities
    
    def calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        텍스트 통계를 계산합니다.
        """
        if not text:
            return {
                'character_count': 0,
                'word_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'avg_word_length': 0,
                'avg_sentence_length': 0,
                'unique_word_ratio': 0
            }
        
        # 기본 통계
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(self.tokenize_sentences(text))
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # 평균 단어 길이
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # 평균 문장 길이
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # 고유 단어 비율
        unique_words = set(self.tokenize_words(text))
        unique_word_ratio = len(unique_words) / word_count if word_count > 0 else 0
        
        return {
            'character_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_word_length': round(avg_word_length, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'unique_word_ratio': round(unique_word_ratio, 3)
        }
    
    def detect_language_patterns(self, text: str) -> Dict[str, Any]:
        """
        텍스트의 언어 패턴을 감지합니다.
        """
        patterns = {
            'has_technical_terms': False,
            'has_emotional_words': False,
            'has_absolute_claims': False,
            'has_conditional_claims': False,
            'has_citations': False,
            'has_questions': False,
            'has_exclamations': False
        }
        
        text_lower = text.lower()
        
        # 전문 용어
        technical_terms = [
            'research', 'study', 'analysis', 'data', 'evidence',
            'statistics', 'survey', 'experiment', 'methodology',
            'peer-reviewed', 'scientific', 'academic'
        ]
        patterns['has_technical_terms'] = any(term in text_lower for term in technical_terms)
        
        # 감정적 단어
        emotional_words = [
            'amazing', 'incredible', 'shocking', 'terrible', 'horrible',
            'wonderful', 'fantastic', 'awful', 'disgusting', 'beautiful'
        ]
        patterns['has_emotional_words'] = any(word in text_lower for word in emotional_words)
        
        # 절대적 주장
        absolute_claims = [
            'always', 'never', 'everyone', 'nobody', 'completely',
            'absolutely', 'totally', 'definitely', 'certainly'
        ]
        patterns['has_absolute_claims'] = any(claim in text_lower for claim in absolute_claims)
        
        # 조건부 주장
        conditional_claims = [
            'might', 'could', 'possibly', 'perhaps', 'maybe',
            'suggest', 'indicate', 'seem', 'appear'
        ]
        patterns['has_conditional_claims'] = any(claim in text_lower for claim in conditional_claims)
        
        # 인용
        citation_patterns = [
            r'\([^)]*\d{4}[^)]*\)',  # (Author, 2023)
            r'\[[^\]]*\d{4}[^\]]*\]',  # [Author, 2023]
            r'http[s]?://[^\s]+'  # URL
        ]
        patterns['has_citations'] = any(re.search(pattern, text) for pattern in citation_patterns)
        
        # 질문
        patterns['has_questions'] = '?' in text
        
        # 감탄
        patterns['has_exclamations'] = '!' in text
        
        return patterns
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트에서 주장을 추출합니다.
        """
        claims = []
        sentences = self.tokenize_sentences(text)
        
        claim_indicators = [
            'research shows', 'study found', 'data indicates',
            'evidence suggests', 'statistics show', 'proven',
            'according to', 'says', 'claims', 'states',
            'reports', 'finds', 'shows', 'demonstrates'
        ]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # 주장 지시어 확인
            has_claim_indicator = any(indicator in sentence_lower for indicator in claim_indicators)
            
            # 구체적 정보 확인 (숫자, 이름, 날짜)
            has_specific_info = bool(re.search(r'\d+|[A-Z][a-z]+ [A-Z][a-z]+|\d{4}', sentence))
            
            if has_claim_indicator or has_specific_info:
                claim = {
                    'text': sentence.strip(),
                    'confidence': self._calculate_claim_confidence(sentence),
                    'type': self._classify_claim_type(sentence),
                    'indicators': [indicator for indicator in claim_indicators if indicator in sentence_lower]
                }
                claims.append(claim)
        
        return claims
    
    def _calculate_claim_confidence(self, sentence: str) -> float:
        """
        주장의 신뢰도를 계산합니다.
        """
        confidence = 0.0
        
        # 구체적 정보 점수
        if re.search(r'\d+', sentence):
            confidence += 0.3
        
        if re.search(r'\d{4}', sentence):  # 연도
            confidence += 0.2
        
        # 출처 언급 점수
        source_indicators = ['according to', 'study by', 'research by', 'reported by']
        if any(indicator in sentence.lower() for indicator in source_indicators):
            confidence += 0.3
        
        # 전문 용어 점수
        technical_terms = ['research', 'study', 'data', 'evidence', 'statistics']
        if any(term in sentence.lower() for term in technical_terms):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _classify_claim_type(self, sentence: str) -> str:
        """
        주장 유형을 분류합니다.
        """
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['research', 'study', 'survey']):
            return 'research_claim'
        elif any(word in sentence_lower for word in ['statistics', 'data', 'numbers']):
            return 'statistical_claim'
        elif any(word in sentence_lower for word in ['expert', 'specialist', 'professor']):
            return 'expert_claim'
        elif any(word in sentence_lower for word in ['government', 'official']):
            return 'official_claim'
        elif any(word in sentence_lower for word in ['evidence', 'proof']):
            return 'evidence_claim'
        else:
            return 'general_claim' 