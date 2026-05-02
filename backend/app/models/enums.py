from enum import StrEnum


class AssetType(StrEnum):
    STOCK = "STOCK"
    FII = "FII"
    BDR = "BDR"
    ETF_RV = "ETF_RV"
    ETF_RF = "ETF_RF"
    SUBSCRICAO = "SUBSCRICAO"
    RF_POS = "RF_POS"
    RF_PRE = "RF_PRE"
