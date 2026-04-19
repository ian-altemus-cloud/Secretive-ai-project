import asyncio
from playwright.async_api import async_playwright
import os
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

def time_to_minutes(time_str: str) -> int:
    from datetime import datetime
    t = datetime.strptime(time_str.strip(), "%I:%M %p")
    return t.hour * 60 + t.minute

async def check_availability(location: str, service: str, target_date: str, target_time: str, attempt: int = 1, selectors: dict = None) -> dict:
    """
    Navigate to the booking site and check availability.
    Returns requested slot status plus two alts.
    Retries up to 3 times with exponential backoff.
    """
    max_attempts = 3
    url = LOCATION_URLS.get(location)

    if not url:
        return {"error": f"Unknown location: {location}"}

    # Use passed selectors or fall back to defaults
    default_selectors = {
        'service': "a:has-text('{service}')",
        'date': "[aria-label='Select day{day}']",
        'timeslot': 'div[for="timeslot"]',
        'calendar': '.datevalue.currmonth'
    }
    active_selectors = selectors if selectors else default_selectors

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            print(f"Navigating to {url} (attempt {attempt})", flush=True)
            await page.goto(url, wait_until="networkidle")
            print("Page loaded", flush=True)

            # Select the service by name
            print(f"Selecting service: {service}", flush=True)
            service_locator = page.locator(f"text={service}").first
            await service_locator.wait_for(state="visible", timeout=10000)
            await page.locator(active_selectors['service'].replace('{service}', service)).first.click()
            print(f"Service selected: {service}", flush=True)
            await page.wait_for_selector(active_selectors['calendar'], timeout=10000)

            # Select the target date
            print(f"Selecting date: {target_date}", flush=True)
            day_number = target_date.split(" ")[1]
            await page.locator(active_selectors['date'].replace('{day}', day_number)).click()
            print(f"Date selected: {target_date}", flush=True)
            await page.wait_for_timeout(3000)

            # Read available time slots
            print("Reading available time slots", flush=True)
            await page.wait_for_selector(active_selectors['timeslot'], timeout=10000)
            slot_elements = await page.locator(active_selectors['timeslot']).all()

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
                alternatives = sorted(
                    [s for s in available_slots if s.strip().upper() != requested],
                    key=lambda s: abs(time_to_minutes(s) - time_to_minutes(target_time)),
                )[:2]
            else:
                status = "unavailable"
                alternatives = sorted(
                    available_slots,
                    key=lambda s: abs(time_to_minutes(s) - time_to_minutes(target_time))
                )[:2]

            return {
                "requested_time": target_time,
                "status": status,
                "alternatives": alternatives,
                "location": location,
                "service": service,
                "date": target_date,
                "booking_url": url
            }

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}", flush=True)
            await browser.close()

            if attempt < max_attempts:
                wait = attempt * 2
                print(f"Retrying in {wait} seconds...", flush=True)
                await asyncio.sleep(wait)
                return await check_availability(location, service, target_date, target_time, attempt + 1)

            print("All attempts failed. Returning fallback.", flush=True)
            return {
                "error": "unavailable",
                "fallback_message": "Here is our direct booking link where you can view all available appointments.",
                "booking_url": LOCATION_URLS.get(location)
            }

        finally:
            try:
                await browser.close()
            except Exception:
                pass


async def main():
    result = await check_availability(
        location=LOCATION,
        service=SERVICE,
        target_date=TARGET_DATE,
        target_time=TARGET_TIME
    )
    print(f"Result: {result}", flush=True)

def run_agent(user_message: str, client_config: dict = None) -> str:
    """
    Run the availability agent loop.
    Takes a customer message, uses Claude tool use to determine
    if availability should be checked, runs Playwright if needed.
    and returns a natural language response.
    """
    import anthropic

    # Use selectors from client config if availabile, otherwise use defaults
    selectors = client_config.get('selectors') if client_config else None
    system_prompt_override = client_config.get('system_prompt') if client_config else None

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    tools = [
        {
            "name": "check_availability",
            "description": "Check appointment availability on the Secretive Nail Bar booking site. Use this when a customer wants to know if a specific service, location, date, and time is available.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The salon location. Must be one of: santa_monica, beverly_hills",
                        "enum": ["santa_monica", "beverly_hills"]
                    },
                    "service": {
                        "type": "string",
                        "description": "The service name exactly as it appears on the booking site. Example: Gel Manicure"
                    },
                    "target_date": {
                        "type": "string",
                        "description": "The requested date in format: Month Day. Example: April 25"
                    },
                    "target_time": {
                        "type": "string",
                        "description": "The requested time in format: H:MM AM/PM. Example: 2:00 PM"
                    }
                },
                "required": ["location", "service", "target_date", "target_time"]
            }
        }
    ]
    messages = [
        {"role": "user", "content": user_message},
    ]

    print("Sending message to Claude with tools", flush=True)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="You are Maya, a luxury nail salon concierge for Secretive Nail Bar. Respond in a warm, understated, confident tone. No emoji. No bold text. No exclamation overload. When availability is confirmed, deliver the result simply and include the booking link. End the message with a warm close. Do not ask follow up questions after providing the booking link. When the result contains a booking_url, share it naturally as a direct path to book without implying anything went wrong.",
        tools=tools,
        messages=messages
    )

    print(f"Claude response type: {response.stop_reason}", flush=True)

    #Claude wants to use a tool
    if response.stop_reason == "tool_use":
        tool_use_block = next(b for b in response.content if b.type == "tool_use")
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input

        print(f"Claude requesting tool: {tool_name}", flush=True)
        print(f"Tool arguments: {tool_input}", flush=True)

        #Run Playwright with Claudes extracted arguments
        tool_result = asyncio.run(check_availability(
            location=tool_input["location"],
            service=tool_input["service"],
            target_date=tool_input["target_date"],
            target_time=tool_input["target_time"],
            selectors=selectors
        ))

        print(f"Tool result: {tool_result}", flush=True)

        # Feed result back to Claude
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": str (tool_result)
                }
            ]
        })

        # Second Claude call with tool result
        final_response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system="You are Maya, a luxury nail salon concierge for Secretive Nail Bar. Respond in a warm, understated, confident tone. No emoji. No bold text. No exclamation overload. When availability is confirmed, deliver the result simply and include the booking link. End the message with a warm close. Do not ask follow up questions after providing the booking link. When the result contains a booking_url, share it naturally as a direct path to book without implying anything went wrong.",
            tools=tools,
            messages=messages
        )

        return final_response.content[0].text

    # Claude answered directly without needing a tool
    return response.content[0].text

if __name__ == "__main__":
    test_message = "Hi, I would like to book a Gel Manicure at your Santa Monica location on April 25th at 2:00 PM. Is that available?"
    print(f"Test message: {test_message}", flush=True)
    result = run_agent(test_message)
    print(f"Maya's response: {result}", flush=True)
