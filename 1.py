# There was little time to make the algorithm perfect, and not all the techniques that are in this file were included in the algorithm or perfectly configured.
import click


@click.command()
@click.option('--input')
@click.option('--output')
def main(input, output):

    import numpy as np
    import cv2
    image_file = input
    img = cv2.imread(image_file)

    inverted_image = cv2.bitwise_not(img)
    
    # Resizing image to improve quality of output
    img = cv2.resize(img, (0, 0), fx=4, fy=4)

    def grayscale(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray_image = grayscale(img)

    thresh, im_bw = cv2.threshold(gray_image, 150, 230, cv2.THRESH_BINARY)

    def noise_removal(image):
        kernel = np.ones((1, 1), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        kernel = np.ones((1, 1), np.uint8)
        image = cv2.erode(image, kernel, iterations=1)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        image = cv2.medianBlur(image, 3)
        return (image)

    no_noise = noise_removal(im_bw)

    # I didn't use these two functions because I didn't come up with a criterion for which one would be better for each drawing
    def thin_font(image):
        image = cv2.bitwise_not(image)
        kernel = np.ones((2, 2), np.uint8)
        image = cv2.erode(image, kernel, iterations=1)
        image = cv2.bitwise_not(image)
        return (image)

    def thick_font(image):     
        image = cv2.bitwise_not(image)
        kernel = np.ones((2, 2), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        image = cv2.bitwise_not(image)
        return (image)


    def getSkewAngle(cvImage) -> float:
        # Prep image, copy, convert to gray scale, blur, and threshold
        newImage = cvImage.copy()
        gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        thresh = cv2.threshold(blur, 0, 255,
                               cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Apply dilate to merge text into meaningful lines/paragraphs.
        # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
        # But use smaller kernel on Y axis to separate between different blocks of text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilate = cv2.dilate(thresh, kernel, iterations=2)

        # Тhis function corrects the text when the scanned document is not quite straight. I also didn't include it in the algorithm because it corrected one drawing and rotated the second 90 degrees. Needs modification.
        # Find all contours
        contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST,
                                               cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        for c in contours:
            rect = cv2.boundingRect(c)
            x, y, w, h = rect
            cv2.rectangle(newImage, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Find largest contour and surround in min area box
        largestContour = contours[0]
        print(len(contours))
        minAreaRect = cv2.minAreaRect(largestContour)
        cv2.imwrite("temp/boxes.jpg", newImage)
        # Determine the angle. Convert it to the value that was originally used to obtain skewed image
        angle = minAreaRect[-1]
        if angle < -45:
            angle = 90 + angle
        return -1.0 * angle

    # Rotate the image around its center
    def rotateImage(cvImage, angle: float):
        newImage = cvImage.copy()
        (h, w) = newImage.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        newImage = cv2.warpAffine(newImage,
                                  M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)
        return newImage

    # Deskew image
    def deskew(cvImage):
        angle = getSkewAngle(cvImage)
        return rotateImage(cvImage, -1.0 * angle)

    def remove_borders(image):
        contours, heiarchy = cv2.findContours(image, cv2.RETR_EXTERNAL,
                                              cv2.CHAIN_APPROX_SIMPLE)
        cntsSorted = sorted(contours, key=lambda x: cv2.contourArea(x))
        cnt = cntsSorted[-1]
        x, y, w, h = cv2.boundingRect(cnt)
        crop = image[y:y + h, x:x + w]
        return (crop)

    no_borders = remove_borders(no_noise)


    # This script removes the lines under the text
    # (1) Create long line kernel, and do morph-close-op
    kernel = np.ones((1, 40), np.uint8)
    morphed = cv2.morphologyEx(no_borders, cv2.MORPH_CLOSE, kernel)

    # (2) Invert the morphed image, and add to the source image:
    dst = cv2.add(no_borders, (255 - morphed))

    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # Adding custom options
    custom_config = r'--oem 3 --psm 6'
    
    # Here textblob can be used to correct text but results were not so good so I decided not to use it
    #from textblob import TextBlob
    #blob = TextBlob()

    my_file = open(output, "w+")
    my_file.write(pytesseract.image_to_string(dst, config=custom_config))
    my_file.close()


if __name__ == "__main__":
    main()
