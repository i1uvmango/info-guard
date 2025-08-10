"""
AI-Hub 데이터 전처리 시스템
"""

import json
import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import chardet

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIHubDataPreprocessor:
    """AI-Hub 데이터 전처리 클래스"""
    
    def __init__(self, validation_dir: str = "../../Validation"):
        self.validation_dir = Path(validation_dir)
        self.processed_data = {}
        
    def detect_encoding(self, file_path: str) -> str:
        """파일 인코딩 감지"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding']
        except Exception as e:
            logger.warning(f"인코딩 감지 실패: {e}")
            return 'utf-8'
    
    def fix_csv_encoding(self, file_path: str) -> Optional[pd.DataFrame]:
        """CSV 파일 인코딩 문제 해결"""
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"성공적으로 로드됨: {file_path} (인코딩: {encoding})")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"파일 로드 실패: {file_path}, 에러: {e}")
                continue
        
        logger.error(f"모든 인코딩 시도 실패: {file_path}")
        return None
    
    def load_json_data(self, data_dir: str) -> List[Dict]:
        """JSON 라벨링 데이터 로드"""
        json_data = []
        json_dir = Path(data_dir)
        
        if not json_dir.exists():
            logger.error(f"디렉토리가 존재하지 않음: {data_dir}")
            return json_data
        
        for json_file in json_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    json_data.append(data)
            except Exception as e:
                logger.error(f"JSON 파일 로드 실패: {json_file}, 에러: {e}")
        
        logger.info(f"로드된 JSON 파일 수: {len(json_data)}")
        return json_data
    
    def process_harmlessness_data(self) -> Dict:
        """무해성 데이터 처리"""
        harmlessness_dir = self.validation_dir / "02.라벨링데이터" / "VL_평가용_무해성"
        
        if not harmlessness_dir.exists():
            logger.error(f"무해성 데이터 디렉토리가 존재하지 않음: {harmlessness_dir}")
            return {}
        
        json_data = self.load_json_data(str(harmlessness_dir))
        
        # 전체 데이터 사용 (10% 제한 제거)
        logger.info(f"무해성 데이터 전체 사용: {len(json_data)}개")
        
        processed_data = {
            'texts': [],
            'labels': [],
            'categories': [],
            'subcategories': []
        }
        
        for item in json_data:
            # 질문과 답변들을 하나의 텍스트로 결합
            prompt = item.get('Prompt', '')
            answers = item.get('Candidate_answer', {})
            
            # 모든 답변을 하나의 텍스트로 결합
            all_answers = []
            for answer_key, answer_text in answers.items():
                if answer_text and isinstance(answer_text, str):
                    all_answers.append(answer_text)
            
            # 텍스트 결합
            combined_text = f"{prompt} {' '.join(all_answers)}"
            
            # 라벨 처리 (무해성: 0=유해, 1=무해)
            label = 1  # 기본값은 무해
            if 'harmless' in item:
                label = 1 if item['harmless'] else 0
            
            processed_data['texts'].append(combined_text)
            processed_data['labels'].append(label)
            processed_data['categories'].append('harmlessness')
            processed_data['subcategories'].append('evaluation')
        
        logger.info(f"무해성 데이터 처리 완료: {len(processed_data['texts'])}개")
        return processed_data
    
    def process_honesty_data(self) -> Dict:
        """정보정확성 데이터 처리"""
        honesty_dir = self.validation_dir / "02.라벨링데이터" / "VL_평가용_정보정확성"
        
        if not honesty_dir.exists():
            logger.error(f"정보정확성 데이터 디렉토리가 존재하지 않음: {honesty_dir}")
            return {}
        
        json_data = self.load_json_data(str(honesty_dir))
        
        # 전체 데이터 사용 (10% 제한 제거)
        logger.info(f"정보정확성 데이터 전체 사용: {len(json_data)}개")
        
        processed_data = {
            'texts': [],
            'labels': [],
            'categories': [],
            'subcategories': []
        }
        
        for item in json_data:
            # 질문과 답변들을 하나의 텍스트로 결합
            prompt = item.get('Prompt', '')
            answers = item.get('Candidate_answer', {})
            
            # 모든 답변을 하나의 텍스트로 결합
            all_answers = []
            for answer_key, answer_text in answers.items():
                if answer_text and isinstance(answer_text, str):
                    all_answers.append(answer_text)
            
            # 텍스트 결합
            combined_text = f"{prompt} {' '.join(all_answers)}"
            
            # 라벨 처리 (정보정확성: 0=부정확, 1=정확)
            label = 1  # 기본값은 정확
            if 'honest' in item:
                label = 1 if item['honest'] else 0
            
            processed_data['texts'].append(combined_text)
            processed_data['labels'].append(label)
            processed_data['categories'].append('honesty')
            processed_data['subcategories'].append('evaluation')
        
        logger.info(f"정보정확성 데이터 처리 완료: {len(processed_data['texts'])}개")
        return processed_data
    
    def process_helpfulness_data(self) -> Dict:
        """도움적정성 데이터 처리"""
        helpfulness_dir = self.validation_dir / "02.라벨링데이터" / "VL_평가용_도움적정성"
        
        if not helpfulness_dir.exists():
            logger.error(f"도움적정성 데이터 디렉토리가 존재하지 않음: {helpfulness_dir}")
            return {}
        
        json_data = self.load_json_data(str(helpfulness_dir))
        
        # 전체 데이터 사용 (10% 제한 제거)
        logger.info(f"도움적정성 데이터 전체 사용: {len(json_data)}개")
        
        processed_data = {
            'texts': [],
            'labels': [],
            'categories': [],
            'subcategories': []
        }
        
        for item in json_data:
            # 질문과 답변들을 하나의 텍스트로 결합
            prompt = item.get('Prompt', '')
            answers = item.get('Candidate_answer', {})
            
            # 모든 답변을 하나의 텍스트로 결합
            all_answers = []
            for answer_key, answer_text in answers.items():
                if answer_text and isinstance(answer_text, str):
                    all_answers.append(answer_text)
            
            # 텍스트 결합
            combined_text = f"{prompt} {' '.join(all_answers)}"
            
            # 라벨 처리 (도움적정성: 0=도움안됨, 1=도움됨)
            label = 1  # 기본값은 도움됨
            if 'helpful' in item:
                label = 1 if item['helpful'] else 0
            
            processed_data['texts'].append(combined_text)
            processed_data['labels'].append(label)
            processed_data['categories'].append('helpfulness')
            processed_data['subcategories'].append('evaluation')
        
        logger.info(f"도움적정성 데이터 처리 완료: {len(processed_data['texts'])}개")
        return processed_data
    
    def create_dataset_splits(self, data: Dict, train_ratio: float = 0.8, val_ratio: float = 0.1) -> Dict:
        """데이터셋 분할"""
        total_samples = len(data['texts'])
        train_size = int(total_samples * train_ratio)
        val_size = int(total_samples * val_ratio)
        
        # 인덱스 셔플
        indices = np.random.permutation(total_samples)
        
        train_indices = indices[:train_size]
        val_indices = indices[train_size:train_size + val_size]
        test_indices = indices[train_size + val_size:]
        
        # 데이터 분할
        train_data = {
            'texts': [data['texts'][i] for i in train_indices],
            'labels': [data['labels'][i] for i in train_indices],
            'categories': [data['categories'][i] for i in train_indices],
            'subcategories': [data['subcategories'][i] for i in train_indices]
        }
        
        val_data = {
            'texts': [data['texts'][i] for i in val_indices],
            'labels': [data['labels'][i] for i in val_indices],
            'categories': [data['categories'][i] for i in val_indices],
            'subcategories': [data['subcategories'][i] for i in val_indices]
        }
        
        test_data = {
            'texts': [data['texts'][i] for i in test_indices],
            'labels': [data['labels'][i] for i in test_indices],
            'categories': [data['categories'][i] for i in test_indices],
            'subcategories': [data['subcategories'][i] for i in test_indices]
        }
        
        logger.info(f"데이터 분할 완료: Train={len(train_data['texts'])}, Val={len(val_data['texts'])}, Test={len(test_data['texts'])}")
        
        return {
            'train': train_data,
            'val': val_data,
            'test': test_data
        }
    
    def save_processed_data(self, data: Dict, output_dir: str = "processed_data"):
        """전처리된 데이터 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for split_name, split_data in data.items():
            output_file = output_path / f"{split_name}_data.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(split_data, f, ensure_ascii=False, indent=2)
            logger.info(f"{split_name} 데이터 저장 완료: {output_file}")
    
    def process_all_data(self) -> Dict:
        """모든 데이터 처리"""
        logger.info("전체 AI-Hub 데이터 처리 시작")
        
        # 각 카테고리별 데이터 처리
        harmlessness_data = self.process_harmlessness_data()
        honesty_data = self.process_honesty_data()
        helpfulness_data = self.process_helpfulness_data()
        
        # 모든 데이터 결합
        all_texts = []
        all_labels = []
        all_categories = []
        all_subcategories = []
        
        for data in [harmlessness_data, honesty_data, helpfulness_data]:
            if data:
                all_texts.extend(data['texts'])
                all_labels.extend(data['labels'])
                all_categories.extend(data['categories'])
                all_subcategories.extend(data['subcategories'])
        
        combined_data = {
            'texts': all_texts,
            'labels': all_labels,
            'categories': all_categories,
            'subcategories': all_subcategories
        }
        
        logger.info(f"전체 데이터 결합 완료: {len(combined_data['texts'])}개")
        
        # 데이터셋 분할
        splits = self.create_dataset_splits(combined_data)
        
        # 데이터 저장
        self.save_processed_data(splits)
        
        return splits

def main():
    """메인 실행 함수"""
    logger.info("AI-Hub 데이터 전처리 시작")
    
    preprocessor = AIHubDataPreprocessor()
    processed_data = preprocessor.process_all_data()
    
    logger.info("데이터 전처리 완료!")
    logger.info(f"총 데이터 수: {len(processed_data['train']['texts']) + len(processed_data['val']['texts']) + len(processed_data['test']['texts'])}개")

if __name__ == "__main__":
    main() 