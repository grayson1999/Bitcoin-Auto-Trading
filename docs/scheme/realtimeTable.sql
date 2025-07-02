-- 실시간 티커 데이터 저장용 테이블
CREATE TABLE tick_data (
    id                     BIGINT AUTO_INCREMENT PRIMARY KEY,
    market                 VARCHAR(20)  NOT NULL,
    trade_price            DOUBLE       NOT NULL,
    prev_closing_price     DOUBLE       NOT NULL,
    opening_price          DOUBLE       NOT NULL,
    high_price             DOUBLE       NOT NULL,
    low_price              DOUBLE       NOT NULL,
    change_type            VARCHAR(10)  NOT NULL,  -- "RISE", "FALL", "EVEN"
    change_rate            DOUBLE       NOT NULL,
    trade_volume           DOUBLE       NOT NULL,
    acc_trade_volume_24h   DOUBLE       NOT NULL,
    data_timestamp         BIGINT       NOT NULL,  -- API에서 주는 타임스탬프
    created_at             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_data_timestamp (data_timestamp)
);

-- 계좌 정보(비공개 데이터) 저장용 테이블
CREATE TABLE account_data (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    currency                VARCHAR(10)   NOT NULL,
    balance                 DOUBLE        NOT NULL,
    locked                  DOUBLE        NOT NULL,
    avg_buy_price           DOUBLE        NULL,
    data_timestamp          BIGINT        NOT NULL,
    created_at              DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_currency_timestamp (currency, data_timestamp)
);
