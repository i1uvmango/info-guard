"""
고급 리포트 서비스
상세한 분석 리포트 생성 및 통계 제공
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from config.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class AnalysisReport:
    """분석 리포트 데이터 모델"""
    report_id: str
    video_id: str
    channel_id: str
    analysis_data: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]
    risk_level: str  # "low", "medium", "high", "critical"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class TrendReport:
    """트렌드 리포트 데이터 모델"""
    report_id: str
    channel_id: str
    period_days: int
    trend_data: Dict[str, Any]
    insights: List[str]
    predictions: Dict[str, Any]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

class ReportService:
    """
    고급 리포트 서비스
    상세한 분석 리포트 생성 및 통계 제공
    """
    
    def __init__(self):
        self.analysis_reports: Dict[str, AnalysisReport] = {}
        self.trend_reports: Dict[str, TrendReport] = {}
        self.logger = logger
    
    async def generate_analysis_report(self, video_id: str, channel_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """분석 리포트 생성"""
        try:
            # 종합 점수 계산
            overall_score = self._calculate_overall_score(analysis_data)
            
            # 위험도 평가
            risk_level = self._assess_risk_level(analysis_data)
            
            # 요약 생성
            summary = self._generate_summary(analysis_data, overall_score)
            
            # 권장사항 생성
            recommendations = self._generate_recommendations(analysis_data, risk_level)
            
            # 리포트 생성
            report_id = f"report_{video_id}_{int(time.time())}"
            report = AnalysisReport(
                report_id=report_id,
                video_id=video_id,
                channel_id=channel_id,
                analysis_data=analysis_data,
                summary=summary,
                recommendations=recommendations,
                risk_level=risk_level
            )
            
            self.analysis_reports[report_id] = report
            
            self.logger.info(f"분석 리포트 생성: {report_id}")
            
            return {
                "success": True,
                "report_id": report_id,
                "report": report.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"분석 리포트 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_trend_report(self, channel_id: str, period_days: int = 30, video_analyses: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """트렌드 리포트 생성"""
        try:
            if not video_analyses:
                return {"error": "분석 데이터가 없습니다."}
            
            # 트렌드 데이터 분석
            trend_data = self._analyze_trends(video_analyses, period_days)
            
            # 인사이트 생성
            insights = self._generate_insights(trend_data)
            
            # 예측 생성
            predictions = self._generate_predictions(trend_data)
            
            # 리포트 생성
            report_id = f"trend_{channel_id}_{int(time.time())}"
            report = TrendReport(
                report_id=report_id,
                channel_id=channel_id,
                period_days=period_days,
                trend_data=trend_data,
                insights=insights,
                predictions=predictions
            )
            
            self.trend_reports[report_id] = report
            
            self.logger.info(f"트렌드 리포트 생성: {report_id}")
            
            return {
                "success": True,
                "report_id": report_id,
                "report": report.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"트렌드 리포트 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_analysis_report(self, report_id: str) -> Dict[str, Any]:
        """분석 리포트 조회"""
        try:
            if report_id not in self.analysis_reports:
                return {"error": "리포트를 찾을 수 없습니다."}
            
            return self.analysis_reports[report_id].to_dict()
            
        except Exception as e:
            self.logger.error(f"분석 리포트 조회 실패: {report_id}, 오류: {e}")
            return {"error": str(e)}
    
    async def get_trend_report(self, report_id: str) -> Dict[str, Any]:
        """트렌드 리포트 조회"""
        try:
            if report_id not in self.trend_reports:
                return {"error": "리포트를 찾을 수 없습니다."}
            
            return self.trend_reports[report_id].to_dict()
            
        except Exception as e:
            self.logger.error(f"트렌드 리포트 조회 실패: {report_id}, 오류: {e}")
            return {"error": str(e)}
    
    async def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 리포트 조회"""
        try:
            all_reports = []
            
            # 분석 리포트
            for report in self.analysis_reports.values():
                all_reports.append({
                    "type": "analysis",
                    "report": report.to_dict()
                })
            
            # 트렌드 리포트
            for report in self.trend_reports.values():
                all_reports.append({
                    "type": "trend",
                    "report": report.to_dict()
                })
            
            # 생성 시간순으로 정렬
            all_reports.sort(key=lambda x: x["report"]["created_at"], reverse=True)
            
            return all_reports[:limit]
            
        except Exception as e:
            self.logger.error(f"최근 리포트 조회 실패: {e}")
            return []
    
    def _calculate_overall_score(self, analysis_data: Dict[str, Any]) -> float:
        """종합 점수 계산"""
        try:
            scores = []
            
            if "credibility_score" in analysis_data:
                scores.append(analysis_data["credibility_score"])
            if "fact_check_score" in analysis_data:
                scores.append(analysis_data["fact_check_score"])
            if "bias_score" in analysis_data:
                # 편향 점수를 신뢰도로 변환 (100 - bias_score)
                scores.append(100 - analysis_data["bias_score"])
            if "source_validation_score" in analysis_data:
                scores.append(analysis_data["source_validation_score"])
            
            return sum(scores) / len(scores) if scores else 0
            
        except Exception as e:
            self.logger.error(f"종합 점수 계산 실패: {e}")
            return 0
    
    def _assess_risk_level(self, analysis_data: Dict[str, Any]) -> str:
        """위험도 평가"""
        try:
            overall_score = self._calculate_overall_score(analysis_data)
            
            if overall_score >= 80:
                return "low"
            elif overall_score >= 60:
                return "medium"
            elif overall_score >= 40:
                return "high"
            else:
                return "critical"
                
        except Exception as e:
            self.logger.error(f"위험도 평가 실패: {e}")
            return "medium"
    
    def _generate_summary(self, analysis_data: Dict[str, Any], overall_score: float) -> Dict[str, Any]:
        """요약 생성"""
        try:
            summary = {
                "overall_score": overall_score,
                "key_findings": [],
                "strengths": [],
                "weaknesses": []
            }
            
            # 주요 발견사항
            if "credibility_score" in analysis_data:
                score = analysis_data["credibility_score"]
                if score >= 80:
                    summary["key_findings"].append("높은 신뢰도를 보입니다.")
                    summary["strengths"].append("신뢰할 수 있는 정보 제공")
                elif score < 50:
                    summary["key_findings"].append("낮은 신뢰도를 보입니다.")
                    summary["weaknesses"].append("신뢰성 부족")
            
            if "bias_score" in analysis_data:
                score = analysis_data["bias_score"]
                if score > 70:
                    summary["key_findings"].append("강한 편향성을 보입니다.")
                    summary["weaknesses"].append("편향된 관점")
                elif score < 30:
                    summary["key_findings"].append("객관적인 관점을 보입니다.")
                    summary["strengths"].append("객관적 분석")
            
            if "fact_check_score" in analysis_data:
                score = analysis_data["fact_check_score"]
                if score >= 80:
                    summary["key_findings"].append("사실 확인이 잘 되어 있습니다.")
                    summary["strengths"].append("정확한 사실 제시")
                elif score < 50:
                    summary["key_findings"].append("사실 확인이 부족합니다.")
                    summary["weaknesses"].append("사실 확인 부족")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"요약 생성 실패: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, analysis_data: Dict[str, Any], risk_level: str) -> List[str]:
        """권장사항 생성"""
        try:
            recommendations = []
            
            if risk_level == "critical":
                recommendations.append("이 콘텐츠는 신뢰할 수 없습니다. 다른 출처를 확인하세요.")
                recommendations.append("사실 확인이 필요합니다.")
            
            elif risk_level == "high":
                recommendations.append("주의해서 시청하시기 바랍니다.")
                recommendations.append("추가적인 사실 확인을 권장합니다.")
            
            elif risk_level == "medium":
                recommendations.append("일반적인 수준의 신뢰도를 보입니다.")
                recommendations.append("중요한 정보는 추가 확인이 필요합니다.")
            
            else:  # low
                recommendations.append("높은 신뢰도를 보입니다.")
                recommendations.append("일반적으로 신뢰할 수 있는 콘텐츠입니다.")
            
            # 구체적인 권장사항
            if "bias_score" in analysis_data and analysis_data["bias_score"] > 60:
                recommendations.append("편향된 관점이 포함되어 있으니 다양한 시각을 고려하세요.")
            
            if "fact_check_score" in analysis_data and analysis_data["fact_check_score"] < 70:
                recommendations.append("사실 확인이 부족하니 추가 검증이 필요합니다.")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"권장사항 생성 실패: {e}")
            return ["분석 중 오류가 발생했습니다."]
    
    def _analyze_trends(self, video_analyses: List[Dict[str, Any]], period_days: int) -> Dict[str, Any]:
        """트렌드 분석"""
        try:
            if not video_analyses:
                return {"error": "분석 데이터가 없습니다."}
            
            # 시간별 점수 추이
            time_series = []
            credibility_scores = []
            bias_scores = []
            
            for analysis in video_analyses:
                if "created_at" in analysis and "analysis_data" in analysis:
                    time_series.append(analysis["created_at"])
                    
                    analysis_data = analysis["analysis_data"]
                    if "credibility_score" in analysis_data:
                        credibility_scores.append(analysis_data["credibility_score"])
                    if "bias_score" in analysis_data:
                        bias_scores.append(analysis_data["bias_score"])
            
            # 평균 및 표준편차 계산
            avg_credibility = sum(credibility_scores) / len(credibility_scores) if credibility_scores else 0
            avg_bias = sum(bias_scores) / len(bias_scores) if bias_scores else 0
            
            return {
                "period_days": period_days,
                "total_videos": len(video_analyses),
                "average_credibility": avg_credibility,
                "average_bias": avg_bias,
                "trend_direction": self._calculate_trend_direction(credibility_scores),
                "consistency_score": self._calculate_consistency(credibility_scores)
            }
            
        except Exception as e:
            self.logger.error(f"트렌드 분석 실패: {e}")
            return {"error": str(e)}
    
    def _generate_insights(self, trend_data: Dict[str, Any]) -> List[str]:
        """인사이트 생성"""
        try:
            insights = []
            
            if "error" in trend_data:
                return ["분석 데이터가 부족합니다."]
            
            avg_credibility = trend_data.get("average_credibility", 0)
            avg_bias = trend_data.get("average_bias", 0)
            trend_direction = trend_data.get("trend_direction", "stable")
            consistency_score = trend_data.get("consistency_score", 0)
            
            # 신뢰도 관련 인사이트
            if avg_credibility >= 80:
                insights.append("전반적으로 높은 신뢰도를 유지하고 있습니다.")
            elif avg_credibility < 50:
                insights.append("신뢰도가 낮은 콘텐츠가 많습니다.")
            
            # 편향성 관련 인사이트
            if avg_bias > 70:
                insights.append("강한 편향성을 보이는 콘텐츠가 많습니다.")
            elif avg_bias < 30:
                insights.append("객관적인 관점을 유지하고 있습니다.")
            
            # 트렌드 관련 인사이트
            if trend_direction == "improving":
                insights.append("신뢰도가 점진적으로 개선되고 있습니다.")
            elif trend_direction == "declining":
                insights.append("신뢰도가 감소하는 추세입니다.")
            
            # 일관성 관련 인사이트
            if consistency_score >= 80:
                insights.append("일관된 품질을 유지하고 있습니다.")
            elif consistency_score < 50:
                insights.append("콘텐츠 품질의 편차가 큽니다.")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"인사이트 생성 실패: {e}")
            return ["분석 중 오류가 발생했습니다."]
    
    def _generate_predictions(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """예측 생성"""
        try:
            if "error" in trend_data:
                return {"error": "예측을 위한 데이터가 부족합니다."}
            
            avg_credibility = trend_data.get("average_credibility", 0)
            trend_direction = trend_data.get("trend_direction", "stable")
            
            # 간단한 예측 로직
            if trend_direction == "improving":
                predicted_score = min(100, avg_credibility + 5)
                prediction = "신뢰도가 계속 개선될 것으로 예상됩니다."
            elif trend_direction == "declining":
                predicted_score = max(0, avg_credibility - 5)
                prediction = "신뢰도가 감소할 것으로 예상됩니다."
            else:
                predicted_score = avg_credibility
                prediction = "현재 수준을 유지할 것으로 예상됩니다."
            
            return {
                "predicted_credibility": predicted_score,
                "prediction": prediction,
                "confidence": 0.7,  # 예측 신뢰도
                "timeframe": "30일"
            }
            
        except Exception as e:
            self.logger.error(f"예측 생성 실패: {e}")
            return {"error": str(e)}
    
    def _calculate_trend_direction(self, scores: List[float]) -> str:
        """트렌드 방향 계산"""
        if len(scores) < 2:
            return "stable"
        
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 3:
            return "improving"
        elif second_avg < first_avg - 3:
            return "declining"
        else:
            return "stable"
    
    def _calculate_consistency(self, scores: List[float]) -> float:
        """일관성 점수 계산"""
        if len(scores) < 2:
            return 100.0
        
        # 표준편차 기반 일관성 계산
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # 표준편차가 작을수록 일관성이 높음
        consistency = max(0, 100 - (std_dev * 2))
        return consistency 