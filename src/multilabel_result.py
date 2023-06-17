import urllib.request
import pyautogui
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

class WebDriver(webdriver.Chrome):
    _attempts = 0
    _click_count = 0
    _clicked = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get("https://patrickhlauke.github.io/recaptcha/")
        self.fullscreen_window()
        self.find_element_by_css_selector('[title="reCAPTCHA"]').click()
        self.iframe = self.find_element_by_css_selector('[title="recaptcha challenge expires in two minutes"]')
        self.iframe = WebDriverWait(self, 10).until(EC.visibility_of(self.iframe))
        self.boxX = self.iframe.location["x"]
        self.boxY = self.iframe.location["y"] + 45
        self.switch_to.frame(self.iframe)
        self.verifyX, self.verifyY = self._find_coordinates_of_element(self.find_element_by_id("recaptcha-verify-button"))
        self.reloadX, self.reloadY = self._find_coordinates_of_element(self.find_element_by_id("recaptcha-reload-button"))
        self.reloadY += 10
        self.verifyY += 10
        self.initialize()
        self.table_coords = [self._find_coordinates_of_element(i) for i in self.find_elements_by_tag_name("td")]

    def initialize(self):
        """
        Finds a 3x3 box and downloads the original image
        """
        self._click_count = 0
        self._find_3x3_box()
        urllib.request.urlretrieve(self.find_element_by_class_name("rc-image-tile-33").get_attribute("src"), "../data/solver/captcha.jpeg")
        self.images = self._crop_image_and_convert(Image.open("../data/solver/captcha.jpeg"))

    def get_captcha_label(self, labels):
        label_text = self.find_element_by_tag_name("strong").text
        for i in labels:
            if label_text in i:
                return labels.index(i)

    def click_box(self, index):
        """
        Click the captcha grid box based on the index passed
        adds to click counter
        """
        self._click_count += 1
        self._click(*self.table_coords[index])
        self._clicked.append(index)
        
    def update_image(self):
        for index in self._clicked:
            img_element = self.find_elements_by_tag_name("td")[index].find_element_by_class_name("rc-image-tile-11")
            file_path = "../data/solver/captcha-tile-%d.jpeg" % index
            urllib.request.urlretrieve(img_element.get_attribute("src"), file_path)
            self.images[index] = self._process_image(Image.open(file_path))
        self._clicked = []

    def submit(self):
        """
        Click the verify button, then checks if the attempt was successful
        if unsuccessful reinitializes and returns None
        if successful, return the attempts count
        """
        self._attempts += 1
        self._click(self.verifyX, self.verifyY)
        sleep(3)

        if self._check_success() is True:
            return self._attempts
        else:
            if self._click_count < 3:
                self._reload()
                print("DEBUG RELOAD")
            self.initialize()
            return None
    
    def _find_3x3_box(self):
        """
        Loop until 3x3 CAPTCHA is found
        """
        # Check if there are any elements with rc-image-tile-33
        img_element = self._check_images()
        while img_element is None:
            self._reload()
            img_element = self._check_images()

    def _process_image(self, img):
        """
        Function to process images into a shape of (100, 100, 3)
        """
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img = img.resize((100, 100))
        return np.array(img)

    def _crop_image_and_convert(self, image):
        width, height = image.size
        grid_width = width // 3
        grid_height = height // 3
        cropped_images = np.zeros((0, 100, 100, 3), dtype=np.uint8)
        for i in range(3):
            for j in range(3):
                left = j * grid_width
                upper = i * grid_height
                right = (j + 1) * grid_width
                lower = (i + 1) * grid_height
                cropped = image.crop((left, upper, right, lower))
                cropped_images = np.concatenate((cropped_images, [self._process_image(cropped)]))
        return cropped_images

    def _click(self, x, y):
        pyautogui.moveTo(x, y, 0.5)
        pyautogui.click()

    def _reload(self):
        self._click(self.reloadX, self.reloadY)
        sleep(1)

    def _find_coordinates_of_element(self, element):
        """
        Used to find the coordinates of an element for pyautogui to click
        """
        x = self.boxX + element.size["width"] / 2 + element.location["x"]
        y = self.boxY + element.size["height"] / 2 + element.location["y"]
        return x, y
    
    def _check_images(self):
        images = self.find_elements_by_tag_name("img")
        for i in images:
            if i.get_attribute("class") == "rc-image-tile-33":
                return i
            
    def _check_success(self):
        self.switch_to.default_content()
        self.switch_to.frame(self.find_element_by_css_selector('[title="reCAPTCHA"]'))
        checker = self.find_elements_by_css_selector('[aria-checked="true"]')
        if len(checker) == 0:
            self.switch_to.default_content()
            self.switch_to.frame(self.find_element_by_css_selector('[title="recaptcha challenge expires in two minutes"]'))
            return False
        else:
            self.switch_to.default_content()
            return True
            
    def get_images(self):
        return self.images
    
    def get_click_count(self):
        return self._click_count
    
    def set_click_count(self, count):
        self._click_count = count
    
    def get_attempts(self):
        return self._attempts
    

            
    

class Application():

    def __init__(self, model_path: str, count: int, mode: str):
        """
        Setup the application with 3 required parameters
        model_path: path to the Sequential keras model
        count: amount of tests to run
        mode: (multi/single) for the label types
        """
        self.model = tf.keras.models.load_model(model_path)
        self.result = []

        if mode == "multi":
            self.label_names = [
                'Bicycle', 'Bridge', 'Bus', 'Car', 'Crosswalk', 
                'Hydrant', 'Motorcycle', 'Stairs',
                'Traffic Light'
            ]
            self.captcha_labels = [
                ["bicycles", "bicycle", "bike"],
                ["bridges", "bridge"],
                ["buses", "bus"],
                ["cars", "car"],
                ["crosswalks", "crosswalk"],
                ["a fire hydrant", "fire hydrants"],
                ["motorcycles"],
                ["stairs"],
                ["traffic lights"]
            ]
        else:
            self.label_names = [
                'Bicycle', 'Bridge', 'Bus', 'Car', 'Chimney',
                'Crosswalk', 'Hydrant', 'Motorcycle', 'Other', 'Palm', 'Stair',
                'Traffic Light'
            ]
            self.captcha_labels = [
                ["bicycles", "bicycle", "bike"],
                ["bridges", "bridge"],
                ["buses", "bus"],
                ["cars", "car"],
                ["chimney"],
                ["crosswalks", "crosswalk"],
                ["a fire hydrant", "fire hydrants"],
                ["motorcycles"],
                ["UNDEFINED?"],
                ["tree", "palm tree"],
                ["stairs"],
                ["traffic lights"]
            ]
        
        while count:
            self._solve_captcha()
            count -= 1
        
    def _solve_captcha(self):
        """
        Main method to solve the captcha
        """
        driver = WebDriver("../driver/chromedriver.exe")

        # SOLVE HERE
        while True:
            predictions = self.model.predict(driver.get_images()) # type: ignore
            label_index = driver.get_captcha_label(self.captcha_labels)
            self._predict(driver, predictions, label_index)
            current_result = driver.submit()
            if current_result:
                break
            if driver.get_attempts() == 5:
                current_result = 0
                break
        self.result.append(current_result)
        driver.quit()

    def _predict(self, driver, predictions, label):
        """
        Checks for click count,
        Loop the prediction while clicks are not 0
        """
        while True:
            images = driver.get_images()
            index = 0
            for i in images:
                plt.imshow(i)
                plt.show()
                for j in predictions[index]:
                    print("%s: %.4f" % (self.label_names[np.where(predictions[index] == j)[0][0]], j))
                index += 1
            for i in predictions:
                # CONFIGURE DECODE THRESHOLD HERE
                if i[label] > 0.2:
                    driver.click_box(np.where(predictions == i)[0][0])
            if driver.get_click_count() > 0:
                sleep(5)
                driver.set_click_count(0)
                driver.update_image()
                predictions = self.model.predict(driver.get_images()) # type: ignore
            else:
                break

    def get_result(self):
        X = range(1, len(self.result) + 1)
        Y = self.result
        plt.bar(X, Y)
        plt.xlabel("Attempt")
        plt.ylabel("Verify Count")
        plt.title("RESULT")
        plt.show()

# MAIN DRIVER
if __name__ == "__main__":
    # TABLE RESULT WILL SHOW VERIFY ATTEMPTS IN EACH CAPTCHA ATTEMPT
    # 0 MEANS IT FAILED (VERIFY ATTEMPTS >= 5)
    app = Application("../data/solver/test.h5", 1, "multi")
    app.get_result()