"""
tests/test_ui.py  —  FA23-BAI-030
Headless Selenium test against the provided index.html frontend.
Uses exact element IDs: text-input, submit-btn, result-output
"""

import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")


def test_frontend_sentiment():
    """Headless Chrome test: send text, click button, assert result-output is populated."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(BASE_URL)

        # Send text to the input field (ID: text-input)
        text_input = driver.find_element(By.ID, "text-input")
        text_input.clear()
        text_input.send_keys(
            "This app is incredibly intuitive and has made my daily workflow dramatically more efficient"
        )

        # Click the submit button (ID: submit-btn)
        submit_btn = driver.find_element(By.ID, "submit-btn")
        submit_btn.click()

        # Wait for result and assert it's non-empty (ID: result-output)
        wait = WebDriverWait(driver, 60)
        result_div = wait.until(
            EC.presence_of_element_located((By.ID, "result-output"))
        )
        wait.until(lambda d: d.find_element(By.ID, "result-output").text.strip() != "")

        result_text = result_div.text.strip()
        assert result_text != "", "result-output div is empty"
        assert any(
            keyword in result_text
            for keyword in ["POSITIVE", "NEGATIVE", "Confidence"]
        ), f"Unexpected result text: {result_text}"

    finally:
        driver.quit()
