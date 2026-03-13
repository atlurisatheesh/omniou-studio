"use client";

import { useState, useEffect } from "react";
import {
  IndianRupee,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  Star,
  AlertCircle,
  Info,
} from "lucide-react";
import { api } from "@/lib/api";

interface MarketPrice {
  commodity: string;
  market_name: string;
  state: string;
  district: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  arrival_date: string;
  trend: string;
  trend_pct: number;
}

interface PriceData {
  commodity: string;
  msp: string;
  avg_price: number;
  prices: MarketPrice[];
  best_market: string;
  price_trend_7d: string;
  advisory: string;
}

interface Advisory {
  commodity: string;
  advisory: string;
  details: Record<string, unknown>;
}

interface CommodityInfo {
  key: string;
  name: string;
  msp: number | null;
  markets_count: number;
}

export default function MarketPricesPage() {
  const [commodities, setCommodities] = useState<CommodityInfo[]>([]);
  const [selected, setSelected] = useState("");
  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [advisory, setAdvisory] = useState<Advisory | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.market.commodities().then((r) => {
      setCommodities(r.commodities);
      if (r.commodities.length > 0) {
        loadPrices(r.commodities[0].key);
      }
    });
  }, []);

  const loadPrices = async (commodity: string) => {
    setSelected(commodity);
    setLoading(true);
    try {
      const [p, a] = await Promise.all([
        api.market.prices(commodity),
        api.market.advisory(commodity),
      ]);
      setPriceData(p);
      setAdvisory(a);
    } catch {
      setPriceData(null);
      setAdvisory(null);
    } finally {
      setLoading(false);
    }
  };

  const trendIcon = (t: string) => {
    if (t === "rising") return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (t === "falling") return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  return (
    <div className="animate-fade-in max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <IndianRupee className="w-8 h-8 text-purple-500" />
          Market Prices
        </h1>
        <p className="text-gray-500 mt-1">
          Live mandi prices, MSP comparison, and intelligent selling advisory
        </p>
      </div>

      {/* Commodity Selection */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          Select Commodity
        </label>
        <div className="flex flex-wrap gap-2">
          {commodities.map((c) => (
            <button
              key={c.key}
              onClick={() => loadPrices(c.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                selected === c.key
                  ? "bg-purple-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      )}

      {!loading && priceData && (
        <div className="space-y-6">
          {/* MSP & Best Market */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-purple-500 to-purple-700 rounded-xl p-6 text-white">
              <p className="text-purple-200 text-sm">
                Minimum Support Price (MSP)
              </p>
              <div className="text-4xl font-extrabold mt-1">
                {priceData.msp}
              </div>
              <p className="text-purple-200 text-sm mt-1 capitalize">
                {priceData.commodity}
              </p>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-green-700 rounded-xl p-6 text-white">
              <p className="text-green-200 text-sm flex items-center gap-1">
                <Star className="w-4 h-4" /> Best Market Today
              </p>
              <div className="text-3xl font-extrabold mt-1">
                {priceData.best_market}
              </div>
              <p className="text-green-200 text-sm mt-1">
                Avg ₹{priceData.avg_price?.toLocaleString("en-IN")}/qtl
              </p>
            </div>
          </div>

          {/* Market Prices Table */}
          <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-bold text-gray-900">Mandi Prices</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500">
                  <tr>
                    <th className="text-left px-6 py-3">Market</th>
                    <th className="text-left px-6 py-3">Min (₹/qtl)</th>
                    <th className="text-left px-6 py-3">Max (₹/qtl)</th>
                    <th className="text-left px-6 py-3">Modal (₹/qtl)</th>
                    <th className="text-left px-6 py-3">Trend</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {priceData.prices.map((p, idx) => {
                    const isBest = priceData.best_market.includes(p.market_name);
                    return (
                      <tr
                        key={`${p.market_name}-${idx}`}
                        className={`hover:bg-gray-50 ${
                          isBest ? "bg-green-50/50" : ""
                        }`}
                      >
                        <td className="px-6 py-3 font-medium text-gray-700">
                          {p.market_name}, {p.district}
                          {isBest && (
                            <Star className="w-3.5 h-3.5 text-amber-400 inline ml-1" />
                          )}
                        </td>
                        <td className="px-6 py-3">
                          ₹{p.min_price.toLocaleString("en-IN")}
                        </td>
                        <td className="px-6 py-3">
                          ₹{p.max_price.toLocaleString("en-IN")}
                        </td>
                        <td className="px-6 py-3 font-semibold">
                          ₹{p.modal_price.toLocaleString("en-IN")}
                        </td>
                        <td className="px-6 py-3">
                          <span className="flex items-center gap-1 capitalize">
                            {trendIcon(p.trend)} {p.trend} ({p.trend_pct > 0 ? "+" : ""}{p.trend_pct}%)
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Advisory */}
          {advisory && (
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Info className="w-5 h-5 text-blue-500" />
                Selling Advisory
              </h3>
              <div className="p-4 bg-blue-50 rounded-xl text-blue-800">
                <p className="font-medium">{advisory.advisory}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {!loading && !priceData && selected && (
        <div className="text-center py-12 text-gray-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-3" />
          <p>Could not load price data</p>
        </div>
      )}
    </div>
  );
}
