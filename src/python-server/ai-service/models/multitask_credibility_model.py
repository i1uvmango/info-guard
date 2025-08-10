"""
AI-Hub 데이터 기반 멀티태스크 신뢰도 분석 모델
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MultiTaskCredibilityModel(nn.Module):
    """멀티태스크 신뢰도 분석 모델"""
    
    def __init__(self, model_name: str = "klue/roberta-base", num_classes: int = 2):
        super(MultiTaskCredibilityModel, self).__init__()
        
        # GPU 사용 가능 여부 확인
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # BERT 모델 로드
        self.bert = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # 모델 크기
        self.hidden_size = self.bert.config.hidden_size
        
        # 멀티태스크 헤드
        self.harmlessness_head = nn.Linear(self.hidden_size, num_classes)  # 무해성
        self.honesty_head = nn.Linear(self.hidden_size, num_classes)       # 정보정확성
        self.helpfulness_head = nn.Linear(self.hidden_size, num_classes)   # 도움적정성
        
        # 드롭아웃
        self.dropout = nn.Dropout(0.1)
        
        # GPU 메모리 최적화
        if torch.cuda.is_available():
            # GPU 메모리 사용량 설정
            torch.cuda.set_per_process_memory_fraction(0.8)  # 80% 사용
            logger.info(f"GPU 메모리 설정: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB 중 80% 사용")
        
        # 모델을 GPU로 이동
        self.to(self.device)
        
    def forward(self, input_ids, attention_mask, task_type: str = "harmlessness"):
        """순전파"""
        # BERT 인코딩
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        
        # 드롭아웃 적용
        pooled_output = self.dropout(pooled_output)
        
        # 태스크별 헤드 적용
        if task_type == "harmlessness":
            logits = self.harmlessness_head(pooled_output)
        elif task_type == "honesty":
            logits = self.honesty_head(pooled_output)
        elif task_type == "helpfulness":
            logits = self.helpfulness_head(pooled_output)
        else:
            # 기본값은 무해성
            logits = self.harmlessness_head(pooled_output)
        
        return logits
    
    def predict_credibility(self, text: str, task_type: str = "harmlessness") -> Dict:
        """신뢰도 예측"""
        # 텍스트 토크나이징
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # GPU로 이동
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        # 예측
        with torch.no_grad():
            logits = self.forward(input_ids, attention_mask, task_type)
            probabilities = F.softmax(logits, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1)
            
            # 신뢰도 점수 계산 (0-100)
            confidence_score = probabilities[0][predicted_class].item() * 100
            
            # 무해성 점수 (높을수록 안전)
            if task_type == "harmlessness":
                safety_score = confidence_score
            else:
                safety_score = 50.0  # 기본값
            
            return {
                'text': text,
                'task_type': task_type,
                'predicted_class': predicted_class.item(),
                'confidence_score': confidence_score,
                'safety_score': safety_score,
                'probabilities': probabilities[0].cpu().numpy().tolist()
            }
    
    def predict_multiple_tasks(self, text: str) -> Dict:
        """여러 태스크에 대한 예측"""
        results = {}
        
        for task_type in ["harmlessness", "honesty", "helpfulness"]:
            result = self.predict_credibility(text, task_type)
            results[task_type] = result
        
        # 종합 신뢰도 점수 계산
        overall_score = (results['harmlessness']['safety_score'] + 
                        results['honesty']['confidence_score'] + 
                        results['helpfulness']['confidence_score']) / 3
        
        results['overall'] = {
            'credibility_score': overall_score,
            'analysis': {
                'harmlessness': results['harmlessness']['safety_score'],
                'honesty': results['honesty']['confidence_score'],
                'helpfulness': results['helpfulness']['confidence_score']
            }
        }
        
        return results

class AIHubDataset(torch.utils.data.Dataset):
    """AI-Hub 데이터셋"""
    
    def __init__(self, data_path: str, task_type: str = "harmlessness", max_length: int = 512):
        self.task_type = task_type
        self.max_length = max_length
        
        # 데이터 로드
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # 토크나이저
        self.tokenizer = AutoTokenizer.from_pretrained("klue/roberta-base")
        
        logger.info(f"데이터셋 로드 완료: {len(self.data['texts'])}개 샘플")
    
    def __len__(self):
        return len(self.data['texts'])
    
    def __getitem__(self, idx):
        text = self.data['texts'][idx]
        label = self.data['labels'][idx]
        
        # 토크나이징
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def train_multitask_model(model, train_dataloader, val_dataloader, epochs: int = 5, task_type: str = "harmlessness"):
    """멀티태스크 모델 학습"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    # 손실 함수와 옵티마이저
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    
    # Mixed Precision 설정 (최신 API 사용)
    scaler = torch.amp.GradScaler('cuda')
    
    # 학습 루프
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch in train_dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            # Mixed Precision 순전파 (최신 API 사용)
            with torch.amp.autocast('cuda'):
                logits = model(input_ids, attention_mask, task_type)
                loss = criterion(logits, labels)
            
            # 역전파
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            total_loss += loss.item()
            
            # 정확도 계산
            _, predicted = torch.max(logits.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
        
        # 검증
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for batch in val_dataloader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                logits = model(input_ids, attention_mask, task_type)
                loss = criterion(logits, labels)
                
                val_loss += loss.item()
                
                _, predicted = torch.max(logits.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        train_acc = 100 * correct / total
        val_acc = 100 * val_correct / val_total
        
        logger.info(f"Epoch {epoch+1}/{epochs}: "
                   f"Train Loss: {total_loss/len(train_dataloader):.4f}, "
                   f"Train Acc: {train_acc:.2f}%, "
                   f"Val Loss: {val_loss/len(val_dataloader):.4f}, "
                   f"Val Acc: {val_acc:.2f}%")
    
    return model

def main():
    """메인 실행 함수"""
    logger.info("멀티태스크 모델 학습 시작 (GPU 최적화 모드)")
    
    # GPU 메모리 확인
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"GPU 메모리: {gpu_memory:.1f}GB")
    
    # 모델 초기화
    model = MultiTaskCredibilityModel()
    
    # 데이터 로더 생성
    train_dataset = AIHubDataset("processed_data/train_data.json", "harmlessness")
    val_dataset = AIHubDataset("processed_data/val_data.json", "harmlessness")
    
    # 배치 크기 증가 (GPU 최적화)
    train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_dataloader = torch.utils.data.DataLoader(val_dataset, batch_size=16, shuffle=False)
    
    # 에포크 수 증가
    trained_model = train_multitask_model(model, train_dataloader, val_dataloader, epochs=5)
    
    # 모델 저장
    torch.save(trained_model.state_dict(), "multitask_credibility_model_optimized.pth")
    logger.info("모델 저장 완료: multitask_credibility_model_optimized.pth")
    
    # 테스트 예측
    test_text = "이 영상은 과학적 사실을 바탕으로 제작되었습니다."
    result = trained_model.predict_multiple_tasks(test_text)
    
    logger.info(f"테스트 예측 결과: {result}")
    
    return trained_model

if __name__ == "__main__":
    main() 