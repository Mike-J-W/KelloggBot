import requests
import functools
import os
import subprocess
import random
import sys
import time

import speech_recognition as sr
from faker import Faker
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from pdf2image import convert_from_path

from selenium.webdriver.common.action_chains import ActionChains

from webdriver_manager.chrome import ChromeDriverManager
os.environ['WDM_LOG_LEVEL'] = '0'

from constants.common import *
from constants.fileNames import *
from constants.classNames import *
from constants.elementIds import *
from constants.email import *
from constants.urls import *
from constants.xPaths import *

os.environ["PATH"] += ":/usr/local/bin" # Adds /usr/local/bin to my path which is where my ffmpeg is stored

fake = Faker()

# Change default in module for print to flush
# https://stackoverflow.com/questions/230751/how-can-i-flush-the-output-of-the-print-function-unbuffer-python-output#:~:text=Changing%20the%20default%20in%20one%20module%20to%20flush%3DTrue
print = functools.partial(print, flush=True)

r = sr.Recognizer()

def audioToText(mp3Path):
    # deletes old file
    try:
        os.remove(CAPTCHA_WAV_FILENAME)
    except FileNotFoundError:
        pass
    # convert wav to mp3                                                            
    subprocess.run(f"ffmpeg -i {mp3Path} {CAPTCHA_WAV_FILENAME}", shell=True, timeout=5)

    with sr.AudioFile(CAPTCHA_WAV_FILENAME) as source:
        audio_text = r.listen(source)
        try:
            text = r.recognize_google(audio_text)
            print('Converting audio transcripts into text ...')
            return(text)     
        except Exception as e:
            print(e)
            print('Sorry.. run again...')

def saveFile(content,filename):
    with open(filename, "wb") as handle:
        for data in content.iter_content():
            handle.write(data)
# END TEST

def solveCaptcha(driver):
    # Logic to click through the reCaptcha to the Audio Challenge, download the challenge mp3 file, run it through the audioToText function, and send answer
    googleClass = driver.find_elements_by_class_name(CAPTCHA_BOX)[0]
    time.sleep(2)
    outeriframe = googleClass.find_element_by_tag_name('iframe')
    time.sleep(1)
    outeriframe.click()
    time.sleep(2)
    allIframesLen = driver.find_elements_by_tag_name('iframe')
    time.sleep(1)
    audioBtnFound = False
    audioBtnIndex = -1
    for index in range(len(allIframesLen)):
        driver.switch_to.default_content()
        iframe = driver.find_elements_by_tag_name('iframe')[index]
        driver.switch_to.frame(iframe)
        driver.implicitly_wait(2)
        try:
            audioBtn = driver.find_element_by_id(RECAPTCHA_AUDIO_BUTTON) or driver.find_element_by_id(RECAPTCHA_ANCHOR)
            audioBtn.click()
            audioBtnFound = True
            audioBtnIndex = index
            break
        except Exception as e:
            pass
    if audioBtnFound:
        try:
            while True:
                href = driver.find_element_by_id(AUDIO_SOURCE).get_attribute('src')
                response = requests.get(href, stream=True)
                saveFile(response, CAPTCHA_MP3_FILENAME)
                response = audioToText(CAPTCHA_MP3_FILENAME)
                print(response)
                driver.switch_to.default_content()
                iframe = driver.find_elements_by_tag_name('iframe')[audioBtnIndex]
                driver.switch_to.frame(iframe)
                inputbtn = driver.find_element_by_id(AUDIO_RESPONSE)
                inputbtn.send_keys(response)
                inputbtn.send_keys(Keys.ENTER)
                time.sleep(2)
                errorMsg = driver.find_elements_by_class_name(AUDIO_ERROR_MESSAGE)[0]
                if errorMsg.text == "" or errorMsg.value_of_css_property('display') == 'none':
                    print("reCaptcha defeated!")
                    break
        except Exception as e:
            print(e)
            print('Oops, something happened. Check above this message for errors or check the chrome window to see if captcha locked you out...')
    else:
        print('Button not found. This should not happen.')

    time.sleep(2)
    driver.switch_to.default_content()

def start_driver():
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(FORM_URL)
    driver.implicitly_wait(10)
    time.sleep(2)
    return driver

def fill_out_rest_of_application(driver, position_id, fake_identity):
    if position_id == 'i21':
        # Confirm qualifications
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(POLICE_OFFICER_MIN_QUAL).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(NEXT_BUTTON).click()

        # Choose a Prospect Day
        day_id = random.choice(PROSPECT_DAYS)
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(day_id).click()
        print(f'--filled out officer info')
    elif position_id in ['i24', 'i27']:
        education = ''
        if position_id == 'i24':
            # Confirm residency and age
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
            driver.find_element_by_id(random.choices(CADET_RESIDENCY, CADET_RESIDENCY_WEIGHT)[0]).click()
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
            driver.find_element_by_id(AGE_CONFIRM).click()
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
            driver.find_element_by_xpath(NEXT_BUTTON).click()

            # Give education background
            dc_grad_id = random.choices(DC_GRAD, [3, 1])[0]
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
            driver.find_element_by_id(DC_RESIDENCY).click()

            if dc_grad_id == 'i5':
                education = random.choice(DC_SCHOOLS)
            if dc_grad_id == 'i8':
                education = random.choice(NON_DC_ED)
            print(f'--filled out non-hs cadet info')
        if position_id == 'i27': 
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
            driver.find_element_by_id(HS_CADET_CONFIRM).click()
#            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
#            driver.find_element_by_id(HS_TRANSPORTATION).click()
#            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
#            driver.find_element_by_id(HS_WIFI).click()
#            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
#            driver.find_element_by_id(HS_COMPUTER).click()
#            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
#            driver.find_element_by_xpath(PARENTS_INFO).send_keys(fake_identity['parent_info'])
#            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
#            driver.find_element_by_xpath(NEXT_BUTTON).click()
            education = random.choice(DC_SCHOOLS)

        print(education)
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(NEXT_BUTTON).click()

        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(DROPDOWN_MENU).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        options=driver.find_element_by_xpath(EDUCATION_LIST)
        elements = options.find_elements_by_tag_name('span')
        actions = ActionChains(driver)
        try:
            for e in elements:
                if e.text == education:
                    actions.move_to_element(e).perform()
                    e.click()
        except:
          elements[5].click()

        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(NEXT_BUTTON).click()

        # Additional Information
        day_id = random.choice(CADET_PROSPECT_DAYS)
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(day_id).click()
        source_id = random.choice(CADET_HEARD_ABOUT)
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(source_id).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(PARENTS_INFO).send_keys(fake_identity['parent_info'])
        print(f'--filled out cadet info')
    elif position_id == 'i30':
        # Confirm various statements
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(RESERVE_CONFIRM_1).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(RESERVE_CONFIRM_2).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(RESERVE_CONFIRM_3).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(RESERVE_CONFIRM_4).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(NEXT_BUTTON).click()

        # Confirm another statement
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(RESERVE_TRAIN_CONFIRM).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(NEXT_BUTTON).click()

        # Confirm another statement
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(POLICE_OFFICER_MIN_QUAL).click()
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_xpath(NEXT_BUTTON).click()

        # Choose a Prospect Day
        day_id = random.choice(PROSPECT_DAYS)
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        driver.find_element_by_id(day_id).click()

        print(f'--filled out reserve info')

    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
    driver.find_element_by_xpath(SUBMIT_BUTTON).click()
    time.sleep(5)

    print(f"successfully submitted the application")
    return

def fill_out_first_page(driver, fake_identity):
    driver.implicitly_wait(10)

    # fill out text fields
    text_fields = driver.find_elements_by_xpath(TEXT_FIELDS)
    email_field = driver.find_element_by_xpath(EMAIL_FIELD)
    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
    text_fields[0].send_keys(fake_identity['first_name'])
    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
    text_fields[1].send_keys(fake_identity['last_name'])
    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
    email_field.send_keys(fake_identity['email'])
    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
    text_fields[2].send_keys(fake_identity['phone'])

    # fill out radio button
    position_id = random.choices(POSITIONS, POSITION_WEIGHTS)[0]
    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
    driver.find_element_by_id(position_id).click()

    # go to next page
    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
    driver.find_element_by_xpath(NEXT_BUTTON).click()

    print(f"--filled out page 1")

    fill_out_rest_of_application(driver, position_id, fake_identity)
    return

def random_email(name=None):
    if name is None:
        name = fake.name()

    mailGens = [lambda fn, ln, *names: fn + ln,
                lambda fn, ln, *names: fn + "." + ln,
                lambda fn, ln, *names: fn + "_" + ln,
                lambda fn, ln, *names: fn[0] + "." + ln,
                lambda fn, ln, *names: fn[0] + "_" + ln,
                lambda fn, ln, *names: fn + ln + str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn + "." + ln + str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn + "_" + ln + str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn[0] + "." + ln + str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn[0] + "_" + ln + str(int(1 / random.random() ** 3)), ]

    emailChoices = [float(line[2]) for line in EMAIL_DATA]

    return random.choices(mailGens, MAIL_GENERATION_WEIGHTS)[0](*name.split(" ")).lower() + "@" + \
           random.choices(EMAIL_DATA, emailChoices)[0][1]

def random_phone():
    area_code = random.choice(PHONE_AREA_CODES)
    seven = random.randint(1000000, 9999999)
    return int(str(area_code) + str(seven))

def random_parent_info(last_name):
    parent_situation = random.choices([['M'], ['F'], ['M', 'F'], ['F', 'M'], ['M', 'M'], ['F', 'F']], [0.08, 0.22, 0.27, 0.27, 0.08, 0.08])[0]
    parent_info = []
    name_email_separator = random.choice([': ', ' - ', '-', ', ', ' '])
    parent_separator = random.choice(['; ', '. ', ' - ', ', ', ' '])
    for p in parent_situation:
        parent_name = ''
        if p == 'M':
            parent_name = fake.first_name_male()
        elif p == 'F':
            parent_name = fake.first_name_female()
        if random.randint(1, 5) == 1:
            last_name = fake.last_name()
        parent_full_name = parent_name+' '+last_name
        parent_email = random_email(parent_full_name)
        parent_info.append(parent_full_name+name_email_separator+parent_email)
    parent_content = parent_separator.join(parent_info)
    return parent_content

def main():
    submissions = 0
    while True:
        try:
            driver = start_driver()
        except Exception as e:
            print(f"FAILED TO START DRIVER: {e}")
            pass

        time.sleep(2)

        fake_first_name = fake.first_name()
        fake_last_name = fake.last_name()
        fake_email = random_email(fake_first_name+' '+fake_last_name)
        fake_phone = random_phone()
        fake_parent_info = random_parent_info(fake_last_name)

        fake_identity = {
            'first_name': fake_first_name,
            'last_name': fake_last_name,
            'email': fake_email,
            'phone': fake_phone,
            'parent_info': fake_parent_info
        }

        try:
            fill_out_first_page(driver, fake_identity)
        except Exception as e:
            print(f"FAILED TO FILL OUT APPLICATION AND SUBMIT: {e}")
            pass
            driver.close()
            continue

        driver.close()
        submissions += 1
        print(f'{submissions} completed submissions')
        time.sleep(random.randint(60, 3600))


if __name__ == '__main__':
    main()
    sys.exit()
