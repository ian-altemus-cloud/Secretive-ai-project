import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

# Hardcoded inputs for proof of concept
# These become dynamic inputs when wired into the agent
LOCATION = "santa_monica"
SERVICE = "Gel Manicure"
TARGET_DATE = "April 25"
TARGET_TIME = "2:00 PM"

LOCATION_URLS = {
    "santa_monica": "https://booking.secretivenailbar.com/webstoreNew/services/ecfa4e63-70e6-4055-a6a3-d265c336d152",
    "beverly_hills": "https://booking.secretivenailbar.com/webstoreNew/services/2c698217-4963-4b46-9c91-537bdb472ca5"
}

async def check_availability(location: str, service: str, target_date: str, target_time: str) -> dict:
    """
    Navigate to the booking site and check availability.
    Returns requested slot status plus two alts.
    """
    url = LOCATION_URLS.get(location)
    if not url:
        return {"error": f"Unknown location: {location}"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            print(f"Navigating to {url}", flush=True)
            await page.goto(url, wait_until="networkidle")
            print("Page loaded", flush=True)

            # Select the service by name
            print(f"Selecting service: {service}", flush=True)
            service_locator = page.locator(f"text={service}").first
            await service_locator.wait_for(state="visible", timeout=10000)

            # Click the parent link that contains the checkbox
            await page.locator(f"a:has-text('{service}')").first.click()
            print(f"Service selected: {service}", flush=True)
            await page.wait_for_timeout(5000)

            # Select the target date
            print(f"Selecting date: {target_date}", flush=True)
            day_number = target_date.split(" ")[1]
            await page.locator(f'[aria-label="Select day{day_number}"]').click()
            print(f"Date selected: {target_date}", flush=True)
            await page.wait_for_timeout(3000)

            # Read available time slots
            print("Reading available time slots", flush=True)
            await page.wait_for_selector('div[for="timeslot"]', timeout=10000)
            slot_elements = await page.locator('div[for="timeslot"]').all()

            available_slots = []
            for slot in slot_elements:
                time_text = await slot.inner_text()
                time_text = time_text.strip()
                if time_text:
                    available_slots.append(time_text)

            print(f"Available slots: {available_slots}", flush=True)

            # Check requested time and find alternatives
            requested = target_time.strip().upper()
            normalized_slots = [s.strip().upper() for s in available_slots]

            if requested in normalized_slots:
                status = "available"
                alternatives = [s for s in available_slots if s.strip().upper() != requested][:2]
            else:
                status = "unavailable"
                alternatives = available_slots[:2]

            return {
                "requested_time": target_time,
                "status": status,
                "alternatives": alternatives,
                "location": location,
                "service": service,
                "date": target_date
            }

        except Exception as e:
            print(f"Navigation error: {e}", flush=True)
            return {"error": str(e)}

        finally:
            await browser.close()

async def main():
    result = await check_availability(
        location=LOCATION,
        service=SERVICE,
        target_date=TARGET_DATE,
        target_time=TARGET_TIME
    )
    print(f"Result: {result}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())