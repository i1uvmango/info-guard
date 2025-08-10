import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ..config.logging_config import get_logger, metrics_logger
    from ..models.multitask_credibility_model import MultiTaskCredibilityModel
    from .youtube_service import YouTubeService
except ImportError:
    from config.logging_config import get_logger, metrics_logger
    from models.multitask_credibility_model import MultiTaskCredibilityModel
    from services.youtube_service import YouTubeService

class AnalysisService:
    """
    종합 분석 서비스
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 멀티태스크 신뢰도 모델 초기화
        self.credibility_model = MultiTaskCredibilityModel()
        
        # YouTube 서비스 초기화
        self.youtube_service = YouTubeService()
        
        self.logger.info("AnalysisService 초기화 완료")
    
    def analyze_youtube_video(self, url: str) -> Dict[str, Any]:
        """
        YouTube 비디오를 종합적으로 분석합니다.
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"YouTube 비디오 분석 시작: {url}")
            
            # 1. YouTube 데이터 수집
            youtube_data = self.youtube_service.analyze_video(url)
            video_info = youtube_data['video_info']
            transcript_info = youtube_data['transcript_info']
            
            # 2. 분석할 텍스트 준비
            analysis_text = self._prepare_analysis_text(
                video_info.get('title', ''),
                video_info.get('description', ''),
                transcript_info.get('transcript_text', '')
            )
            
            # 3. 멀티태스크 모델로 분석
            analysis_results = self._run_ai_models(analysis_text, video_info)
            
            # 4. 종합 점수 계산
            overall_score = self._calculate_overall_score(analysis_results)
            
            # 5. 결과 통합
            processing_time = time.time() - start_time
            metrics_logger.log_analysis_time("analysis_service", processing_time)
            
            result = {
                'url': url,
                'video_id': video_info.get('video_id', ''),
                'video_title': video_info.get('title', ''),
                'channel_title': video_info.get('channel_title', ''),
                'overall_score': overall_score,
                'overall_grade': self._determine_overall_grade(overall_score),
                'analysis_results': analysis_results,
                'youtube_data': youtube_data,
                'processing_time': processing_time,
                'summary': self._generate_summary(analysis_results, overall_score)
            }
            
            self.logger.info(
                "YouTube 비디오 분석 완료",
                url=url,
                overall_score=overall_score,
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"YouTube 비디오 분석 실패: {url}, 오류: {str(e)}")
            metrics_logger.log_error("analysis_service", str(e))
            raise
    
    def analyze_text(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        텍스트를 종합적으로 분석합니다.
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info("텍스트 분석 시작")
            
            # 1. 텍스트 전처리
            processed_text = self._prepare_analysis_text(text, "", "")
            
            # 2. 멀티태스크 모델로 분석
            analysis_results = self._run_ai_models(processed_text, metadata or {})
            
            # 3. 종합 점수 계산
            overall_score = self._calculate_overall_score(analysis_results)
            
            # 4. 결과 통합
            processing_time = time.time() - start_time
            metrics_logger.log_analysis_time("analysis_service", processing_time)
            
            result = {
                'text': text[:200] + "..." if len(text) > 200 else text,
                'overall_score': overall_score,
                'overall_grade': self._determine_overall_grade(overall_score),
                'analysis_results': analysis_results,
                'processing_time': processing_time,
                'summary': self._generate_summary(analysis_results, overall_score)
            }
            
            self.logger.info(
                "텍스트 분석 완료",
                overall_score=overall_score,
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"텍스트 분석 실패: {str(e)}")
            metrics_logger.log_error("analysis_service", str(e))
            raise
    
    def _prepare_analysis_text(self, title: str, description: str, transcript: str) -> str:
        """
        분석할 텍스트를 준비합니다.
        """
        # 제목, 설명, 자막을 결합
        text_parts = []
        
        if title:
            text_parts.append(f"제목: {title}")
        
        if description:
            text_parts.append(f"설명: {description}")
        
        if transcript:
            text_parts.append(f"자막: {transcript}")
        
        combined_text = " ".join(text_parts)
        
        # 텍스트가 너무 길면 자르기
        if len(combined_text) > 1000:
            combined_text = combined_text[:1000] + "..."
        
        return combined_text
    
    def _run_ai_models(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        멀티태스크 모델로 분석을 실행합니다.
        """
        try:
            # 멀티태스크 모델로 분석
            analysis_result = self.credibility_model.predict_multiple_tasks(text)
            
            return {
                'credibility': {
                    'score': analysis_result['overall']['credibility_score'],
                    'grade': self._determine_grade(analysis_result['overall']['credibility_score']),
                    'details': analysis_result['overall']['analysis']
                },
                'harmlessness': {
                    'score': analysis_result['harmlessness']['safety_score'],
                    'grade': self._determine_grade(analysis_result['harmlessness']['safety_score']),
                    'details': {
                        'class': analysis_result['harmlessness']['predicted_class'],
                        'confidence': analysis_result['harmlessness']['confidence_score']
                    }
                },
                'honesty': {
                    'score': analysis_result['honesty']['confidence_score'],
                    'grade': self._determine_grade(analysis_result['honesty']['confidence_score']),
                    'details': {
                        'class': analysis_result['honesty']['predicted_class'],
                        'confidence': analysis_result['honesty']['confidence_score']
                    }
                },
                'helpfulness': {
                    'score': analysis_result['helpfulness']['confidence_score'],
                    'grade': self._determine_grade(analysis_result['helpfulness']['confidence_score']),
                    'details': {
                        'class': analysis_result['helpfulness']['predicted_class'],
                        'confidence': analysis_result['helpfulness']['confidence_score']
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"AI 모델 분석 실패: {str(e)}")
            return self._create_empty_result("multitask_credibility")
    
    def _create_empty_result(self, model_name: str) -> Dict[str, Any]:
        """
        빈 분석 결과를 생성합니다.
        """
        return {
            'credibility': {
                'score': 50.0,
                'grade': 'C',
                'details': {'error': f'{model_name} 분석 실패'}
            },
            'harmlessness': {
                'score': 50.0,
                'grade': 'C',
                'details': {'error': f'{model_name} 분석 실패'}
            },
            'honesty': {
                'score': 50.0,
                'grade': 'C',
                'details': {'error': f'{model_name} 분석 실패'}
            },
            'helpfulness': {
                'score': 50.0,
                'grade': 'C',
                'details': {'error': f'{model_name} 분석 실패'}
            }
        }
    
    def _calculate_overall_score(self, analysis_results: Dict[str, Any]) -> float:
        """
        종합 점수를 계산합니다.
        """
        try:
            credibility_score = analysis_results.get('credibility', {}).get('score', 50.0)
            harmlessness_score = analysis_results.get('harmlessness', {}).get('score', 50.0)
            honesty_score = analysis_results.get('honesty', {}).get('score', 50.0)
            helpfulness_score = analysis_results.get('helpfulness', {}).get('score', 50.0)
            
            # 가중 평균 계산 (신뢰도에 더 높은 가중치)
            overall_score = (
                credibility_score * 0.4 +
                harmlessness_score * 0.2 +
                honesty_score * 0.2 +
                helpfulness_score * 0.2
            )
            
            return round(overall_score, 2)
            
        except Exception as e:
            self.logger.error(f"종합 점수 계산 실패: {str(e)}")
            return 50.0
    
    def _determine_overall_grade(self, score: float) -> str:
        """
        점수에 따른 등급을 결정합니다.
        """
        if score >= 80:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 40:
            return 'C'
        elif score >= 20:
            return 'D'
        else:
            return 'F'
    
    def _determine_grade(self, score: float) -> str:
        """
        개별 점수에 따른 등급을 결정합니다.
        """
        if score >= 80:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 40:
            return 'C'
        elif score >= 20:
            return 'D'
        else:
            return 'F'
    
    def _generate_summary(self, analysis_results: Dict[str, Any], overall_score: float) -> str:
        """
        분석 결과 요약을 생성합니다.
        """
        try:
            credibility_grade = analysis_results.get('credibility', {}).get('grade', 'C')
            harmlessness_grade = analysis_results.get('harmlessness', {}).get('grade', 'C')
            honesty_grade = analysis_results.get('honesty', {}).get('grade', 'C')
            helpfulness_grade = analysis_results.get('helpfulness', {}).get('grade', 'C')
            
            summary = f"종합 신뢰도: {overall_score:.1f}점 ({self._determine_overall_grade(overall_score)}등급)\n"
            summary += f"무해성: {harmlessness_grade}등급\n"
            summary += f"정보정확성: {honesty_grade}등급\n"
            summary += f"도움적정성: {helpfulness_grade}등급"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"요약 생성 실패: {str(e)}")
            return "분석 결과 요약을 생성할 수 없습니다."
    
    def get_detailed_explanation(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """
        상세한 분석 설명을 제공합니다.
        """
        explanations = {}
        
        try:
            # 신뢰도 설명
            credibility_score = analysis_results.get('credibility', {}).get('score', 50.0)
            explanations['credibility'] = self._generate_credibility_explanation({
                'score': credibility_score,
                'grade': self._determine_grade(credibility_score)
            })
            
            # 무해성 설명
            harmlessness_score = analysis_results.get('harmlessness', {}).get('score', 50.0)
            explanations['harmlessness'] = f"무해성 점수: {harmlessness_score:.1f}점. "
            if harmlessness_score >= 80:
                explanations['harmlessness'] += "매우 안전한 콘텐츠입니다."
            elif harmlessness_score >= 60:
                explanations['harmlessness'] += "대체로 안전한 콘텐츠입니다."
            elif harmlessness_score >= 40:
                explanations['harmlessness'] += "주의가 필요한 콘텐츠입니다."
            else:
                explanations['harmlessness'] += "유해할 수 있는 콘텐츠입니다."
            
            # 정보정확성 설명
            honesty_score = analysis_results.get('honesty', {}).get('score', 50.0)
            explanations['honesty'] = f"정보정확성 점수: {honesty_score:.1f}점. "
            if honesty_score >= 80:
                explanations['honesty'] += "매우 정확한 정보를 제공합니다."
            elif honesty_score >= 60:
                explanations['honesty'] += "대체로 정확한 정보를 제공합니다."
            elif honesty_score >= 40:
                explanations['honesty'] += "정보의 정확성을 확인해야 합니다."
            else:
                explanations['honesty'] += "부정확한 정보가 포함될 수 있습니다."
            
            # 도움적정성 설명
            helpfulness_score = analysis_results.get('helpfulness', {}).get('score', 50.0)
            explanations['helpfulness'] = f"도움적정성 점수: {helpfulness_score:.1f}점. "
            if helpfulness_score >= 80:
                explanations['helpfulness'] += "매우 도움이 되는 콘텐츠입니다."
            elif helpfulness_score >= 60:
                explanations['helpfulness'] += "도움이 되는 콘텐츠입니다."
            elif helpfulness_score >= 40:
                explanations['helpfulness'] += "제한적인 도움을 제공합니다."
            else:
                explanations['helpfulness'] += "도움이 되지 않을 수 있습니다."
            
        except Exception as e:
            self.logger.error(f"상세 설명 생성 실패: {str(e)}")
            explanations = {
                'credibility': '분석 중 오류가 발생했습니다.',
                'harmlessness': '분석 중 오류가 발생했습니다.',
                'honesty': '분석 중 오류가 발생했습니다.',
                'helpfulness': '분석 중 오류가 발생했습니다.'
            }
        
        return explanations
    
    def _generate_credibility_explanation(self, credibility_result: Dict[str, Any]) -> str:
        """
        신뢰도 분석에 대한 상세 설명을 생성합니다.
        """
        score = credibility_result.get('score', 50.0)
        grade = credibility_result.get('grade', 'C')
        
        explanation = f"종합 신뢰도 점수: {score:.1f}점 ({grade}등급). "
        
        if score >= 80:
            explanation += "이 콘텐츠는 매우 높은 신뢰도를 가지고 있습니다. "
            explanation += "무해성, 정보정확성, 도움적정성 모든 측면에서 우수한 품질을 보입니다."
        elif score >= 60:
            explanation += "이 콘텐츠는 높은 신뢰도를 가지고 있습니다. "
            explanation += "대체로 안전하고 정확한 정보를 제공하며 도움이 됩니다."
        elif score >= 40:
            explanation += "이 콘텐츠는 중간 수준의 신뢰도를 가지고 있습니다. "
            explanation += "일부 측면에서 주의가 필요할 수 있습니다."
        elif score >= 20:
            explanation += "이 콘텐츠는 낮은 신뢰도를 가지고 있습니다. "
            explanation += "정보의 정확성과 안전성을 확인해야 합니다."
        else:
            explanation += "이 콘텐츠는 매우 낮은 신뢰도를 가지고 있습니다. "
            explanation += "신중하게 접근하는 것이 권장됩니다."
        
        return explanation
    
    def batch_analyze(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        여러 URL을 배치로 분석합니다.
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(self.analyze_youtube_video, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"배치 분석 실패: {url}, 오류: {str(e)}")
                    results.append({
                        'url': url,
                        'error': str(e),
                        'overall_score': 0,
                        'overall_grade': 'F'
                    })
        
        return results 