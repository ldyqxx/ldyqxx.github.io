from datetime import date, timedelta
from math import sin
from random import Random
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Quant Forecast API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to the GitHub Pages URL in production.
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
    # Demo-only deterministic series. Replace this function with a trained model
    # and a licensed market-data provider before using this in production.
    seed = sum(ord(char) for char in symbol.upper())
    rng = Random(seed)
    today = date.today()
    current = round(60 + (seed % 300) + rng.random() * 30, 2)
    history = []
    for offset in range(29, -1, -1):
        value = current * (1 + 0.025 * sin(offset / 3) + rng.uniform(-0.012, 0.012))
        history.append(ForecastPoint(date=today - timedelta(days=offset), price=round(value, 2), kind="history"))
    predicted = round(current * (1 + 0.0018 * horizon_days + rng.uniform(-0.018, 0.018)), 2)
    forecast = [
        ForecastPoint(
            date=today + timedelta(days=offset),
            price=round(current + (predicted - current) * offset / horizon_days, 2),
            kind="forecast",
        )
        for offset in range(1, horizon_days + 1)
    ]
    return ForecastResponse(
        symbol=symbol.upper(),
        as_of=today,
        current_price=current,
        predicted_price=predicted,
        change_percent=round((predicted / current - 1) * 100, 2),
        confidence=round(0.62 + rng.random() * 0.2, 2),
        horizon_days=horizon_days,
        points=history + forecast,
        disclaimer="演示预测仅供研究，不构成投资建议；实际部署前请接入合规数据并完成回测。",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/forecast", response_model=ForecastResponse)
def forecast(
    symbol: str = Query(min_length=1, max_length=10, pattern=r"^[A-Za-z0-9.\-]+$"),
    horizon: int = Query(default=5, ge=1, le=30),
) -> ForecastResponse:
    return make_forecast(symbol, horizon)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "Quant Forecast API", "docs": "/docs"}
