import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta
from async_request_timer import request_logger

logging.basicConfig(filename="app.log", level=logging.INFO)


class ApiPrivatBank:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def fetch_exchange_rate(self, date):
        url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logging.error(f"Error fetching exchange rate for date {date}: {e}")
            return None

    @request_logger
    async def get_exchange_rates(self, days):
        today = datetime.now().date()
        tasks = [
            self.fetch_exchange_rate((today - timedelta(days=i)).strftime("%d.%m.%Y"))
            for i in range(days)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exchange_rates = []
        for i, data in enumerate(results):
            date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
            if isinstance(data, dict) and "exchangeRate" in data:
                exchange_rate = {
                    date: {
                        "EUR": {"sale": None, "purchase": None},
                        "USD": {"sale": None, "purchase": None},
                    }
                }
                for rate in data["exchangeRate"]:
                    if rate["currency"] == "EUR":
                        exchange_rate[date]["EUR"]["sale"] = float(rate["saleRate"])
                        exchange_rate[date]["EUR"]["purchase"] = float(
                            rate["purchaseRate"]
                        )
                    elif rate["currency"] == "USD":
                        exchange_rate[date]["USD"]["sale"] = float(rate["saleRate"])
                        exchange_rate[date]["USD"]["purchase"] = float(
                            rate["purchaseRate"]
                        )
                exchange_rates.append(exchange_rate)
            else:
                logging.error(f"Failed to fetch exchange rate for date {date}: {data}")

        return exchange_rates

    async def close_session(self):
        await self.session.close()


async def main(days):
    exchange = ApiPrivatBank()
    exchange_rates = await exchange.get_exchange_rates(days)
    await exchange.close_session()
    if exchange_rates is not None:
        print(json.dumps(exchange_rates, indent=2))
    else:
        print("Failed to fetch exchange rates. Check the logs for details.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python main.py <number_of_days>")
        sys.exit(1)
    try:
        days = int(sys.argv[1])
        if days > 10:
            print("Error: You can only get exchange rates for up to 10 days.")
            sys.exit(1)
        asyncio.run(main(days))
    except ValueError:
        print("Error: Please provide a valid number of days.")
        sys.exit(1)
