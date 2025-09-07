import cv2
import numpy as np

cap = cv2.VideoCapture(0)  # Use local webcam instead of IP camera
cap.set(3, 640)
cap.set(4, 480)
totalCount = 0

hsvVals = {'hmin': 0, 'smin': 0, 'vmin': 164, 'hmax': 179, 'smax': 111, 'vmax': 255}

def empty(a):
    pass

cv2.namedWindow("Setting")
cv2.resizeWindow("Setting", 640, 240)
cv2.createTrackbar("Threshold1", "Setting", 175, 255, empty)
cv2.createTrackbar("Threshold2", "Setting", 36, 255, empty)

def preProcess(img):
    imgPre = cv2.GaussianBlur(img, (151, 151), 3)
    threshold1 = cv2.getTrackbarPos("Threshold1", "Setting")
    threshold2 = cv2.getTrackbarPos("Threshold2", "Setting")
    imgPre = cv2.Canny(imgPre, threshold1, threshold2)
    kernel = np.ones((3, 3), np.uint8)
    imgPre = cv2.dilate(imgPre, kernel, iterations=1)
    imgPre = cv2.morphologyEx(imgPre, cv2.MORPH_CLOSE, kernel)
    return imgPre

def findContours(img, imgPre, minArea=20):
    contours, _ = cv2.findContours(imgPre, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    conFound = []
    imgContours = img.copy()
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > minArea:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            x, y, w, h = cv2.boundingRect(approx)
            
            conFound.append({'cnt': cnt, 'area': area, 'bbox': [x, y, w, h]})
            cv2.drawContours(imgContours, [cnt], -1, (0, 255, 0), 2)
            cv2.rectangle(imgContours, (x, y), (x + w, y + h), (255, 0, 0), 2)
    
    return imgContours, conFound

def updateColorMask(img, hsvVals):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([hsvVals['hmin'], hsvVals['smin'], hsvVals['vmin']])
    upper = np.array([hsvVals['hmax'], hsvVals['smax'], hsvVals['vmax']])
    mask = cv2.inRange(hsv, lower, upper)
    return mask

def putTextRect(img, text, pos, scale=3, thickness=3, colorT=(255, 255, 255), 
                colorR=(255, 0, 255), font=cv2.FONT_HERSHEY_PLAIN, 
                offset=10, border=None, colorB=(0, 255, 0)):
    ox, oy = pos
    (w, h), _ = cv2.getTextSize(text, font, scale, thickness)
    
    x1, y1, x2, y2 = ox - offset, oy + offset, ox + w + offset, oy - h - offset
    
    cv2.rectangle(img, (x1, y1), (x2, y2), colorR, cv2.FILLED)
    if border is not None:
        cv2.rectangle(img, (x1, y1), (x2, y2), colorB, border)
    cv2.putText(img, text, (ox, oy), font, scale, colorT, thickness)
    
    return img

def stackImages(scale, imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    
    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape[:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2:
                    imgArray[x][y] = cv2.cvtColor(imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank] * rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None, scale, scale)
            if len(imgArray[x].shape) == 2:
                imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor = np.hstack(imgArray)
        ver = hor
    return ver

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture image")
        break
        
    imgPre = preProcess(img)
    imgContours, conFound = findContours(img, imgPre, minArea=20)
    totalCount = 0
    
    if conFound:
        for count, contour in enumerate(conFound):
            peri = cv2.arcLength(contour['cnt'], True)
            approx = cv2.approxPolyDP(contour['cnt'], 0.02 * peri, True)

            if len(approx) > 5:
                area = contour['area']
                x, y, w, h = contour['bbox']
                imgCrop = img[y:y+h, x:x+w]
                mask = updateColorMask(img, hsvVals)
                whitePixels = cv2.countNonZero(mask)
                print(whitePixels)
                
                if area < 12830:
                    totalCount += 1
                elif 15940 < area < 20250:
                    totalCount += 20
                else:
                    totalCount += 5
                
                if 230000 < whitePixels < 260000:
                    totalCount += 50
                elif 260000 < whitePixels < 290000:
                    totalCount += 100

    imgStacked = stackImages(1, [[img, imgPre, imgContours]])
    imgStacked = putTextRect(imgStacked, f'Total: {totalCount}', (50, 50))
    cv2.imshow("Image", imgStacked)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()