# tests/trading/data_collection/test_controller.py
import pytest
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

from src.trading.data_collection.controller import main

@patch('src.trading.data_collection.controller.DataCollectionService')
@patch('src.trading.data_collection.controller.BackgroundScheduler')
@patch('time.sleep')
def test_컨트롤러_스케줄러_설정(mock_sleep, mock_scheduler, mock_service):
    """컨트롤러가 서비스와 스케줄러를 올바르게 초기화하고 실행하는지 테스트합니다."""
    # mock_sleep이 KeyboardInterrupt를 발생시키도록 설정
    mock_sleep.side_effect = KeyboardInterrupt

    # Mock 객체 설정
    mock_service_instance = mock_service.return_value
    mock_scheduler_instance = mock_scheduler.return_value

    # main 함수 실행
    main()

    # 검증
    mock_service.assert_called_once()
    mock_scheduler.assert_called_once_with(timezone=ZoneInfo("Asia/Seoul"))

    # add_job 호출 검증
    assert mock_scheduler_instance.add_job.call_count == 2
    
    # ticker_job 검증
    ticker_job_call = mock_scheduler_instance.add_job.call_args_list[0]
    assert ticker_job_call[0][0] == mock_service_instance.collect_ticker
    assert ticker_job_call[1]['trigger'] == 'interval'
    assert ticker_job_call[1]['seconds'] == 3

    # archive_5min_job 검증
    archive_job_call = mock_scheduler_instance.add_job.call_args_list[1]
    assert archive_job_call[0][0] == mock_service_instance.archive_5min
    assert archive_job_call[1]['trigger'] == 'cron'
    assert archive_job_call[1]['hour'] == 0
    assert archive_job_call[1]['minute'] == 0

    mock_scheduler_instance.start.assert_called_once()
    mock_scheduler_instance.shutdown.assert_called_once()
    mock_service_instance.close.assert_called_once()
