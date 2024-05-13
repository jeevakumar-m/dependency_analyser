from selenium import webdriver
from bs4 import BeautifulSoup
import re

from selenium.webdriver.common.by import By


class XpathUtil:
    "Class to generate the XPaths"

    def __init__(self):
        "Initialize the required variables"
        self.guessable_elements = ['input', 'button','a','p','link','li']
        self.known_attribute_list = ['id', 'name', 'placeholder', 'value', 'title', 'type', 'class']
        self.variable_names = []
        self.button_text_lists = []
        self.language_counter = 1

    def generate_xpath(self, soup):
        "Generate the XPath and assign the variable names"
        result_flag = False
        for guessable_element in self.guessable_elements:
            elements = soup.find_all(guessable_element)
            for element in elements:
                if guessable_element == 'input' and (not element.has_attr("type") or element['type'] != "hidden"):
                    for attr in self.known_attribute_list:
                        if element.has_attr(attr):
                            locator = self.guess_xpath(guessable_element, attr, element)
                            if len(driver.find_elements(By.XPATH,locator)) == 1:  # <-- Here is the correction
                                result_flag = True
                                variable_name = self.get_variable_names(element)
                                if variable_name and variable_name not in self.variable_names:
                                    self.variable_names.append(variable_name)
                                    print(f"{guessable_element}_{variable_name} = {locator}")
                                    break
                        elif guessable_element == 'button' and element.getText():
                            button_text = element.getText()
                            locator = self.guess_xpath_button(guessable_element, "text()", element.getText())
                            if len(driver.find_elements(By.XPATH,locator)) == 1:  # <-- Here is the correction
                                result_flag = True
                                if button_text.lower() not in self.button_text_lists:
                                    self.button_text_lists.append(button_text.lower())
                                    print(f"{guessable_element}_{button_text.strip()} = {locator}")
                                break
        return result_flag

    def get_variable_names(self, element):
        "Generate the variable names for the XPath"
        if element.has_attr('id') and len(element['id']) > 2 and not bool(re.search(r'\d', element['id'])) and (
                "input" not in element['id'].lower() and "button" not in element['id'].lower()):
            return element['id'].strip("_")
        elif element.has_attr('value') and element['value'] != '' and not bool(
                re.search(r'([\d]{1,}([/-]|\s|[.])?)+(\D+)?([/-]|\s|[.])?[[\d]{1,}',
                          element['value'])) and not bool(
                re.search(r'\d{1,2}[:]\d{1,2}\s+((am|AM|pm|PM)?)', element['value'])):
            if element.has_attr('type') and element['type'] in ('radio', 'submit', 'checkbox', 'search'):
                return f"{element['type']}_{element.getText().strip().strip('_.')}" if element.getText() else f"{element['type']}_{element['value'].strip('_.')}"
            else:
                return element['value'].strip("_.")
        elif element.has_attr('name') and len(element['name']) > 2:
            return element['name'].strip("_")
        elif element.has_attr('placeholder') and not bool(re.search(r'\d', element['placeholder'])):
            return element['placeholder']
        elif element.has_attr('title'):
            return element['title']
        elif element.has_attr('role') and element['role'] != "button":
            return element['role']
        return ''

    def guess_xpath(self, tag, attr, element):
        "Guess the XPath based on the tag, attr, element[attr]"
        if type(element[attr]) is list:
            element[attr] = ' '.join([i.encode('utf-8').decode('latin-1') for i in element[attr]])
        return f"//{tag}[@{attr}='{element[attr]}']"

    def guess_xpath_button(self, tag, attr, text):
        "Guess the XPath for button tag"
        return f"//{tag}[{attr}='{text}']"


if __name__ == "__main__":
    print("Start of script")

    # Initialize the XpathUtil object
    xpath_util = XpathUtil()

    # Get the URL and parse
    url = input("Enter URL: ")

    # Create a chrome session
    driver = webdriver.Chrome()
    driver.get(url)

    # Parsing the HTML page with BeautifulSoup
    page = driver.execute_script("return document.body.innerHTML").encode('utf-8').decode('latin-1')
    soup = BeautifulSoup(page, 'html.parser')

    # Execute generate_xpath
    if xpath_util.generate_xpath(soup) is False:
        print(f"No XPaths generated for the URL: {url}")

    driver.quit()