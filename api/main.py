import os
from datetime import date, timedelta
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import yfinance as yf

app = FastAPI(title="Quant Forecast API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "https://ldyqxx.github.io").split(",")],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


class ForecastPoint(BaseModel):
    date: date
    price: float = Field(gt=0)
    kind: Literal["history", "forecast"]


class ForecastResponse(BaseModel):
    symbol: str
    as_of: date
    current_price: float
    predicted_price: float
    change_percent: float
    confidence: float
    horizon_days: int
    points: list[ForecastPoint]
    disclaimer: str


def make_forecast(symbol: str, horizon_days: int) -> ForecastResponse:
    """Build a baseline trend forecast from Yahoo Finance adjusted daily closes."""
    ticker = yf.Ticker(symbol)
    prices = ticker.history(period="3mo", interval="1d", auto_adjust=True, raise_errors=False)
    if prices.empty or "Close" not in prices:
        raise ValueError("未找到该股票代码的可用 Yahoo Finance 行情数据。")

    closes = [float(value) for value in prices["Close"].dropna().tail(30)]
    dates = [timestamp.date() for timestamp in prices.index[-len(closes):]]
    if len(closes) < 10:
        raise ValueError("可用历史行情不足，暂时无法生成预测。")

    current = round(closes[-1], 2)
    history = [
        ForecastPoint(date=price_date, price=round(price, 2), kind="history")
        for price_date, price in zip(dates, closes)
    ]
    x_mean = (len(closes) - 1) / 2
    y_mean = sum(closes) / len(closes)
    denominator = sum((index - x_mean) ** 2 for index in range(len(closes)))
    slope = sum((index - x_mean) * (price - y_mean) for index, price in enumerate(closes)) / denominator
    predicted = round(max(0.01, current + slope * horizon_days), 2)
    forecast_dates = []
    next_date = dates[-1]
    while len(forecast_dates) < horizon_days:
        next_date += timedelta(days=1)
        if next_date.weekday() < 5:
            forecast_dates.append(next_date)
    forecast = [
        ForecastPoint(
            date=forecast_date,
            price=round(current + (predicted - current) * offset / horizon_days, 2),
            kind="forecast",
        )
        for offset, forecast_date in enumerate(forecast_dates, start=1)
    ]
    return ForecastResponse(
        symbol=symbol.upper(),
        as_of=dates[-1],
        current_price=current,
        predicted_price=predicted,
        change_percent=round((predicted / current - 1) * 100, 2),
        confidence=0.0,
        horizon_days=horizon_days,
        points=history + forecast,
        disclaimer="价格来自 Yahoo Finance；预测为基于近期收盘价的线性趋势基线，仅供研究，不构成投资建议。",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/forecast", response_model=ForecastResponse)
def forecast(
    symbol: str = Query(min_length=1, max_length=10, pattern=r"^[A-Za-z0-9.\-]+$"),
    horizon: int = Query(default=5, ge=1, le=30),
) -> ForecastResponse:
    try:
        return make_forecast(symbol, horizon)
    except ValueError as error:
        return JSONResponse(status_code=404, content={"detail": str(error)})


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "Quant Forecast API", "docs": "/docs"}
