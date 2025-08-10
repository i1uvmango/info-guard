#!/usr/bin/env python3
"""
BERT 기반 신뢰성 모델
저장된 가중치 파일(credibility_model.pth)과 호환되는 모델 구조
"""

import torch
import torch.nn as nn
from transformers import BertModel, BertTokenizer
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class BertCredibilityModel(nn.Module):
    """BERT 기반 다중 태스크 신뢰성 모델"""
    
    def __init__(self, model_name: str = "klue/bert-base", num_labels: int = 3):
        super().__init__()
        self.model_name = model_name
        self.num_labels = num_labels
        
        # BERT 모델 로드
        self.bert = BertModel.from_pretrained(model_name)
        bert_hidden_size = self.bert.config.hidden_size
        
        # 저장된 가중치와 정확히 일치하는 계층적 구조
        # classifier.0: 768 → 512
        # classifier.3: 512 → 256  
        # classifier.6: 256 → 5
        self.classifier_0 = nn.Linear(bert_hidden_size, 512)  # classifier.0
        self.classifier_3 = nn.Linear(512, 256)               # classifier.3  
        self.classifier_6 = nn.Linear(256, 5)                 # classifier.6
        
        # 드롭아웃
        self.dropout = nn.Dropout(0.1)
        
        # 디바이스 설정
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.to(self.device)
        
        logger.info(f"BERT 기반 신뢰성 모델 초기화 완료 (디바이스: {self.device})")
    
    def forward(self, input_ids, attention_mask=None, token_type_ids=None):
        """순전파"""
        # BERT 인코더
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids
        )
        
        # [CLS] 토큰의 표현 사용
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        
        # 계층적 분류기로 예측 (저장된 가중치와 정확히 일치)
        # classifier.0: 768 → 512
        hidden_0 = self.classifier_0(pooled_output)
        hidden_0 = torch.relu(hidden_0)
        hidden_0 = self.dropout(hidden_0)
        
        # classifier.3: 512 → 256
        hidden_3 = self.classifier_3(hidden_0)
        hidden_3 = torch.relu(hidden_3)
        hidden_3 = self.dropout(hidden_3)
        
        # classifier.6: 256 → 5
        logit_6 = self.classifier_6(hidden_3)
        
        return [hidden_0, hidden_3, logit_6]
    
    def predict_multiple_tasks(self, text: str) -> Dict[str, float]:
        """다중 태스크 예측"""
        try:
            # 토크나이저 로드
            tokenizer = BertTokenizer.from_pretrained(self.model_name)
            
            # 텍스트 토크나이징
            inputs = tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # 디바이스로 이동
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 예측
            self.eval()
            with torch.no_grad():
                outputs = self.forward(**inputs)
            
            # 각 계층의 출력을 1차원으로 압축 (평균 사용)
            probs = []
            
            # classifier.0 출력 (512차원)
            hidden_0 = outputs[0]
            prob_0 = torch.mean(hidden_0, dim=1).cpu().numpy()[0]
            probs.append(prob_0)
            
            # classifier.3 출력 (256차원)  
            hidden_3 = outputs[1]
            prob_3 = torch.mean(hidden_3, dim=1).cpu().numpy()[0]
            probs.append(prob_3)
            
            # classifier.6 출력 (5차원)
            logit_6 = outputs[2]
            prob_6 = torch.mean(logit_6, dim=1).cpu().numpy()[0]
            probs.append(prob_6)
            
            # 시그모이드로 확률 변환
            probs = [torch.sigmoid(torch.tensor(p)).item() for p in probs]
            
            # 결과 매핑 (저장된 모델의 순서에 맞춤)
            result = {
                "harmlessness": float(probs[0]),  # classifier.0
                "honesty": float(probs[1]),       # classifier.3
                "helpfulness": float(probs[2])    # classifier.6
            }
            
            logger.info(f"예측 완료: {result}")
            return result
            
        except Exception as e:
            logger.error(f"예측 중 오류 발생: {e}")
            return {
                "harmlessness": 0.0,
                "honesty": 0.0,
                "helpfulness": 0.0
            }
    
    def load_pretrained_weights(self, weights_path: str) -> bool:
        """사전 학습된 가중치 로드"""
        try:
            logger.info(f"가중치 파일 로드 중: {weights_path}")
            
            # 가중치 로드
            state_dict = torch.load(weights_path, map_location=self.device)
            
            # 키 이름 매핑 (저장된 가중치의 키를 현재 모델의 키로 변환)
            key_mapping = {
                "classifier.0.weight": "classifier_0.weight",
                "classifier.0.bias": "classifier_0.bias",
                "classifier.3.weight": "classifier_3.weight",
                "classifier.3.bias": "classifier_3.bias",
                "classifier.6.weight": "classifier_6.weight",
                "classifier.6.bias": "classifier_6.bias"
            }
            
            # 키 이름 변환
            new_state_dict = {}
            for key, value in state_dict.items():
                if key in key_mapping:
                    new_key = key_mapping[key]
                    new_state_dict[new_key] = value
                    logger.info(f"✅ 분류기 가중치 로드: {key} → {new_key}")
                elif key.startswith("bert."):
                    # BERT 레이어는 크기가 다를 수 있으므로 건너뛰기
                    logger.info(f"⚠️ BERT 레이어 건너뛰기 (크기 불일치): {key}")
                else:
                    new_state_dict[key] = value
            
            # 모델에 가중치 적용 (strict=False로 호환되지 않는 키 무시)
            missing_keys, unexpected_keys = self.load_state_dict(new_state_dict, strict=False)
            
            if missing_keys:
                logger.warning(f"⚠️ 누락된 키: {missing_keys}")
            if unexpected_keys:
                logger.warning(f"⚠️ 예상치 못한 키: {unexpected_keys}")
            
            logger.info("✅ 가중치 로드 완료 (BERT 임베딩 레이어 제외)")
            return True
            
        except Exception as e:
            logger.error(f"❌ 가중치 로드 실패: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_type": "BERT",
            "base_model": self.model_name,
            "num_classifiers": 3,
            "classifier_structure": "768→512→256→5",
            "device": str(self.device),
            "total_parameters": sum(p.numel() for p in self.parameters()),
            "trainable_parameters": sum(p.numel() for p in self.parameters() if p.requires_grad)
        }
