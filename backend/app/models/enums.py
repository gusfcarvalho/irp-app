from enum import StrEnum


class AssetType(StrEnum):
    STOCK = "STOCK"
    FII = "FII"
    BDR = "BDR"
    ETF_RV = "ETF_RV"
    ETF_RF = "ETF_RF"
    SUBSCRICAO = "SUBSCRICAO"
    RF_POS = "RF_POS"    # catch-all post-fixed
    RF_PRE = "RF_PRE"    # catch-all pre-fixed
    # Specific fixed-income sub-types (all taxed at source — same as RF_POS/RF_PRE)
    CDB = "CDB"
    LCI = "LCI"
    LCA = "LCA"
    LCF = "LCF"
    LIG = "LIG"
    CRI = "CRI"
    CRA = "CRA"
    DEB = "DEB"
    TD  = "TD"           # Tesouro Direto
