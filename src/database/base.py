from sqlalchemy.ext.declarative import declarative_base

# 실시간 DB용 Base
BaseRealtime = declarative_base()

# 히스토리 DB용 Base
BaseHistory = declarative_base()