from pydantic import BaseModel
from typing import List, Optional


class StockSummaryResponseData(BaseModel):
    No: int
    IDStockSummary: int
    Date: str
    StockCode: str
    StockName: str
    Remarks: str
    Previous: Optional[float]
    OpenPrice: Optional[float]
    FirstTrade: Optional[float]
    High: Optional[float]
    Low: Optional[float]
    Close: Optional[float]
    Change: Optional[float]
    Volume: Optional[float]
    Value: Optional[float]
    Frequency: Optional[float]
    IndexIndividual: Optional[float]
    Offer: Optional[float]
    OfferVolume: Optional[float]
    Bid: Optional[float]
    BidVolume: Optional[float]
    ListedShares: Optional[float]
    TradebleShares: Optional[float]
    WeightForIndex: Optional[float]
    ForeignSell: Optional[float]
    ForeignBuy: Optional[float]
    DelistingDate: Optional[str]
    NonRegularVolume: Optional[float]
    NonRegularValue: Optional[float]
    NonRegularFrequency: Optional[float]
    persen: Optional[float]
    percentage: Optional[float]


class IndexSummaryResponseData(BaseModel):
    No: int
    IndexSummaryID: int
    Date: str
    IndexCode: str
    Previous: Optional[float]
    Highest: Optional[float]
    Lowest: Optional[float]
    Close: Optional[float]
    NumberOfStock: Optional[float]
    Change: Optional[float]
    Volume: Optional[float]
    Value: Optional[float]
    Frequency: Optional[float]
    MarketCapital: Optional[float]


class BaseSummaryResponse(BaseModel):
    draw: int
    recordsTotal: int
    recordsFiltered: int


class StockSummaryResponse(BaseSummaryResponse):
    data: List[StockSummaryResponseData]


class IndexSummaryResponse(BaseSummaryResponse):
    data: List[IndexSummaryResponseData]


class StockIndexResponseData(BaseModel):
    No: int
    StockUploaderID: int
    Date: str
    Group: str
    NoPengumuman: str
    TypeIndex: str
    Description: str
    Year: str
    AttachmentName: str
    AttachmentSize: str
    AttachmentUrl: str


class StockIndexResponse(BaseModel):
    SearchCriteria: object
    ResultCount: int
    Results: List[StockIndexResponseData]


class CurrencyExchangeRateResponse(BaseModel):
    amount: float
    base: str
    start_date: str
    end_date: str
    rates: dict[str, dict[str, float]]
