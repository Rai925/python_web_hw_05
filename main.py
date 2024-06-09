import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(filename="app.log", level=logging.INFO)


async def fetch_exchange_rate(session, date):
    url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
    try:
        async with session.get(url) as response:
            return await response.json()
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching exchange rate for date {date}: {e}")


async def get_exchange_rates(days):
    async with aiohttp.ClientSession() as session:
        today = datetime.now().date()
        tasks = [
            fetch_exchange_rate(
                session, (today - timedelta(days=i)).strftime("%d.%m.%Y")
            )
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


async def main(days):
    exchange_rates = await get_exchange_rates(days)
    print(json.dumps(exchange_rates, indent=2))


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
