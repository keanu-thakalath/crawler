import os
import tempfile

import aiohttp
from pypdf import PdfReader


class PdfScraper:
    async def scrape_url(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                pdf_content = await response.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name

        try:
            reader = PdfReader(temp_file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        finally:
            os.unlink(temp_file_path)
