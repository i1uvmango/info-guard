"""
사용자 피드백 서비스
사용자 피드백 수집 및 모델 개선을 위한 서비스
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from config.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class UserFeedback:
    """사용자 피드백 데이터 모델"""
    analysis_id: str
    session_id: str
    feedback_type: str  # "accurate", "inaccurate", "helpful", "not_helpful"
    user_id: Optional[str] = None
    feedback_score: Optional[int] = None  # 1-5 점수
    feedback_text: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

class FeedbackService:
    """
    사용자 피드백 서비스
    피드백 수집, 통계, 모델 정확도 계산
    """
    
    def __init__(self):
        self.feedback_storage: Dict[str, List[UserFeedback]] = {}
        self.model_accuracy: Dict[str, float] = {}
        self.logger = logger
    
    async def submit_feedback(self, feedback: UserFeedback) -> Dict[str, Any]:
        """피드백 제출"""
        try:
            # 피드백 저장
            if feedback.analysis_id not in self.feedback_storage:
                self.feedback_storage[feedback.analysis_id] = []
            
            self.feedback_storage[feedback.analysis_id].append(feedback)
            
            # 모델 정확도 업데이트
            await self._update_model_accuracy()
            
            self.logger.info(f"피드백 제출됨: {feedback.analysis_id}, 타입: {feedback.feedback_type}")
            
            return {
                "success": True,
                "message": "피드백이 성공적으로 제출되었습니다.",
                "feedback_id": f"{feedback.analysis_id}_{int(time.time())}",
                "timestamp": feedback.created_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"피드백 제출 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_feedback_stats(self) -> Dict[str, Any]:
        """피드백 통계 조회"""
        try:
            total_feedback = sum(len(feedbacks) for feedbacks in self.feedback_storage.values())
            
            # 피드백 타입별 통계
            type_stats = {}
            score_stats = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            
            for feedbacks in self.feedback_storage.values():
                for feedback in feedbacks:
                    # 타입별 통계
                    if feedback.feedback_type not in type_stats:
                        type_stats[feedback.feedback_type] = 0
                    type_stats[feedback.feedback_type] += 1
                    
                    # 점수별 통계
                    if feedback.feedback_score:
                        score_key = str(feedback.feedback_score)
                        if score_key in score_stats:
                            score_stats[score_key] += 1
            
            return {
                "total_feedback": total_feedback,
                "type_distribution": type_stats,
                "score_distribution": score_stats,
                "average_score": self._calculate_average_score(),
                "accuracy_rate": self._calculate_accuracy_rate()
            }
            
        except Exception as e:
            self.logger.error(f"피드백 통계 조회 실패: {e}")
            return {"error": str(e)}
    
    async def calculate_model_accuracy(self) -> Dict[str, Any]:
        """모델 정확도 계산"""
        try:
            accuracy_data = {}
            
            # 정확도 피드백 분석
            accurate_count = 0
            inaccurate_count = 0
            
            for feedbacks in self.feedback_storage.values():
                for feedback in feedbacks:
                    if feedback.feedback_type == "accurate":
                        accurate_count += 1
                    elif feedback.feedback_type == "inaccurate":
                        inaccurate_count += 1
            
            total_accuracy_feedback = accurate_count + inaccurate_count
            accuracy_rate = (accurate_count / total_accuracy_feedback * 100) if total_accuracy_feedback > 0 else 0
            
            # 유용성 피드백 분석
            helpful_count = 0
            not_helpful_count = 0
            
            for feedbacks in self.feedback_storage.values():
                for feedback in feedbacks:
                    if feedback.feedback_type == "helpful":
                        helpful_count += 1
                    elif feedback.feedback_type == "not_helpful":
                        not_helpful_count += 1
            
            total_helpfulness_feedback = helpful_count + not_helpful_count
            helpfulness_rate = (helpful_count / total_helpfulness_feedback * 100) if total_helpfulness_feedback > 0 else 0
            
            return {
                "accuracy_rate": accuracy_rate,
                "helpfulness_rate": helpfulness_rate,
                "total_accuracy_feedback": total_accuracy_feedback,
                "total_helpfulness_feedback": total_helpfulness_feedback,
                "accurate_count": accurate_count,
                "inaccurate_count": inaccurate_count,
                "helpful_count": helpful_count,
                "not_helpful_count": not_helpful_count
            }
            
        except Exception as e:
            self.logger.error(f"모델 정확도 계산 실패: {e}")
            return {"error": str(e)}
    
    async def get_feedback_by_analysis(self, analysis_id: str) -> List[Dict[str, Any]]:
        """특정 분석에 대한 피드백 조회"""
        try:
            if analysis_id not in self.feedback_storage:
                return []
            
            feedbacks = self.feedback_storage[analysis_id]
            return [feedback.to_dict() for feedback in feedbacks]
            
        except Exception as e:
            self.logger.error(f"피드백 조회 실패: {analysis_id}, 오류: {e}")
            return []
    
    async def get_recent_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 피드백 조회"""
        try:
            all_feedbacks = []
            for feedbacks in self.feedback_storage.values():
                all_feedbacks.extend(feedbacks)
            
            # 생성 시간순으로 정렬
            all_feedbacks.sort(key=lambda x: x.created_at, reverse=True)
            
            return [feedback.to_dict() for feedback in all_feedbacks[:limit]]
            
        except Exception as e:
            self.logger.error(f"최근 피드백 조회 실패: {e}")
            return []
    
    async def _update_model_accuracy(self):
        """모델 정확도 업데이트"""
        try:
            accuracy_data = await self.calculate_model_accuracy()
            if "error" not in accuracy_data:
                self.model_accuracy = accuracy_data
                self.logger.info(f"모델 정확도 업데이트: {accuracy_data}")
        except Exception as e:
            self.logger.error(f"모델 정확도 업데이트 실패: {e}")
    
    def _calculate_average_score(self) -> float:
        """평균 점수 계산"""
        try:
            total_score = 0
            total_count = 0
            
            for feedbacks in self.feedback_storage.values():
                for feedback in feedbacks:
                    if feedback.feedback_score:
                        total_score += feedback.feedback_score
                        total_count += 1
            
            return total_score / total_count if total_count > 0 else 0
            
        except Exception as e:
            self.logger.error(f"평균 점수 계산 실패: {e}")
            return 0
    
    def _calculate_accuracy_rate(self) -> float:
        """정확도 비율 계산"""
        try:
            accurate_count = 0
            total_count = 0
            
            for feedbacks in self.feedback_storage.values():
                for feedback in feedbacks:
                    if feedback.feedback_type in ["accurate", "inaccurate"]:
                        total_count += 1
                        if feedback.feedback_type == "accurate":
                            accurate_count += 1
            
            return (accurate_count / total_count * 100) if total_count > 0 else 0
            
        except Exception as e:
            self.logger.error(f"정확도 비율 계산 실패: {e}")
            return 0 