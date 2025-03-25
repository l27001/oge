import os
import cv2
import numpy as np
from datetime import datetime
from flask import Flask, request, render_template, send_file, jsonify, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "bmp"}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/resize/<filename>", methods=["POST"])
def resize(filename):
    data = request.form
    try:
        width = int(data.get("width"))
        height = int(data.get("height"))
        scale = float(data.get("scale").replace(',', '.'))
        interpolation = data.get("interpolation")
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if(width < 1 or height < 1 or scale < 0 or scale > 4):
        return jsonify({"error": "Некорректные размеры"}), 400
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        h, w = img.shape[:2]
        
        if(width == w and height == h and scale == 1):
            return jsonify({"filename": f"{filename}", "filepath": filepath, "size": img.shape, "scale": scale})
        elif scale != 0:
            width = int(w * scale)
            height = int(h * scale)
        else:
            scale = 0

        # Автоматический выбор метода интерполяции
        if (interpolation == 'auto' and scale and scale > 1) or interpolation == 'cubic':
            interpolation = cv2.INTER_CUBIC
        elif (interpolation == 'auto' and scale and scale < 1) or interpolation == 'area':
            interpolation = cv2.INTER_AREA
        else:
            interpolation = cv2.INTER_LINEAR

        resized_img = cv2.resize(img, (width, height), interpolation=interpolation)
        resized_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"resized_{filename}")
        cv2.imwrite(resized_filepath, resized_img)
        
        return jsonify({"filename": f"resized_{filename}", "filepath": resized_filepath, "size": resized_img.shape, "scale": scale})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/crop/<filename>", methods=["POST"])
def crop(filename):
    data = request.form
    try:
        X = int(data.get("X"))
        Y = int(data.get("Y"))
        width = int(data.get("width"))
        height = int(data.get("height"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if(X < 0 or Y < 0):
        return jsonify({"error": "Некорректные координаты"}), 400
    if(height < 1 or width < 1):
        return jsonify({"error": "Некорректные размеры"}), 400
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        h, w = img.shape[:2]
        if(X > w or Y > h):
            return jsonify({"error": "Координаты больше размеров изображения"}), 400
        if(X+width > w or Y+height > h):
            return jsonify({"error": "Область вырезки больше размеров изображения"}), 400
        cropped_img = img[Y:Y+height, X:X+width]
        cropped_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"cropped_{filename}")
        cv2.imwrite(cropped_filepath, cropped_img)
        
        return jsonify({"filename": f"cropped_{filename}", "filepath": cropped_filepath, "size": cropped_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/mirror/<filename>", methods=["POST"])
def mirror(filename):
    data = request.form
    try:
        axis = int(data.get("axis"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if(axis < -1 or axis > 1):
        return jsonify({"error": "Некорректная ось"}), 400
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        mirrored_img = cv2.flip(img, axis)
        mirrored_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"mirrored_{filename}")
        cv2.imwrite(mirrored_filepath, mirrored_img)
        
        return jsonify({"filename": f"mirrored_{filename}", "filepath": mirrored_filepath, "size": mirrored_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route("/rotate/<filename>", methods=["POST"])
def rotate(filename):
    data = request.form
    try:
        center_x = int(data.get("center_x"))
        center_y = int(data.get("center_y"))
        angle = int(data.get("angle"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        (h, w) = img.shape[:2]
        if(center_x < 0 or center_x > w or center_y < 0 or center_y > h):
            return jsonify({"error": "Некорректный центр"}), 400
        # подготовим объект для поворота изображения на 180 относительно центра и запишем его в переменную prepObj
        prepObj = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)
        # повернем исходное изображение на abgle, результат запишем в переменную rotated_img
        rotated_img = cv2.warpAffine(img, prepObj, (w, h), flags=cv2.INTER_LINEAR)
        rotated_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"rotated_{filename}")
        cv2.imwrite(rotated_filepath, rotated_img)
        
        return jsonify({"filename": f"rotated_{filename}", "filepath": rotated_filepath, "size": rotated_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/contrast/<filename>", methods=["POST"])
def contast(filename):
    data = request.form
    try:
        contrast = float(data.get("contrast"))
        brightness = int(data.get("brightness"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        if(not (0.1 <= contrast <= 3)):
            return jsonify({"error": "Некорректный контраст"}), 400
        if(not (-100 <= brightness <= 100)):
            return jsonify({"error": "Некорректная яркость"}), 400
        adjusted_img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)
        adjusted_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"contrast_{filename}")
        cv2.imwrite(adjusted_filepath, adjusted_img)
        
        return jsonify({"filename": f"contrast_{filename}", "filepath": adjusted_filepath, "size": adjusted_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/color/<filename>", methods=["POST"])
def color(filename):
    data = request.form
    try:
        red = float(data.get("red"))
        green = float(data.get("green"))
        blue = float(data.get("blue"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        # if(not (0.5 <= red <= 2)):
        #     return jsonify({"error": "Некорректный уровень красного"}), 400
        # if(not (0.5 <= green <= 2)):
        #     return jsonify({"error": "Некорректный уровень зелёного"}), 400
        # if(not (0.5 <= blue <= 2)):
        #     return jsonify({"error": "Некорректный уровень синего"}), 400
        b_channel, g_channel, r_channel = cv2.split(img)
        b = np.clip(b_channel * blue, 0, 255).astype(np.uint8)
        g = np.clip(g_channel * green, 0, 255).astype(np.uint8)
        r = np.clip(r_channel * red, 0, 255).astype(np.uint8)
        color_img = cv2.merge((b, g, r))
        color_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"color_{filename}")
        cv2.imwrite(color_filepath, color_img)
        
        return jsonify({"filename": f"color_{filename}", "filepath": color_filepath, "size": color_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/gnoise/<filename>", methods=["POST"])
def gnoise(filename):
    data = request.form
    try:
        level = int(data.get("level"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        if(not (0 <= level <= 50)):
            return jsonify({"error": "Некорректный уровень шума"}), 400
        noise = np.random.normal(0, level, img.shape).astype(np.int16)
        noise_img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        noise_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"gnoise_{filename}")
        cv2.imwrite(noise_filepath, noise_img)
        return jsonify({"filename": f"gnoise_{filename}", "filepath": noise_filepath, "size": noise_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/snoise/<filename>", methods=["POST"])
def snoise(filename):
    data = request.form
    try:
        level = float(data.get("level"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    try:
        img = cv2.imread(filepath)
        if(not (0 <= level <= 0.5)):
            return jsonify({"error": "Некорректный уровень шума"}), 400
        noise_img = img.copy()
        total_pixels = img.size

        # Добавление соли (белых пикселей)
        num_salt = int(total_pixels * level)
        coords = [np.random.randint(0, i, num_salt) for i in img.shape[:2]]
        noise_img[coords[0], coords[1]] = 255

        # Добавление перца (черных пикселей)
        num_pepper = int(total_pixels * level)
        coords = [np.random.randint(0, i, num_pepper) for i in img.shape[:2]]
        noise_img[coords[0], coords[1]] = 0
        noise_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"snoise_{filename}")
        cv2.imwrite(noise_filepath, noise_img)
        return jsonify({"filename": f"snoise_{filename}", "filepath": noise_filepath, "size": noise_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/blur/<filename>", methods=["POST"])
def blur(filename):
    data = request.form
    try:
        blur = str(data.get("blur"))
        pixels = int(data.get("pixels"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    if(blur not in ["medium", "gauss", "median"]):
        return jsonify({"error": "Некорректный тип блюра"}), 400
    try:
        img = cv2.imread(filepath)
        if(pixels < 0):
            pixels = 0
        if(pixels % 2 != 1):
            return jsonify({"error": "Некорректное значение pixels"}), 400
        if(blur == "medium"):
            # 1️⃣ Среднее размытие (усреднение)
            blur_img = cv2.blur(img, (pixels, pixels))  # Ядро 5x5
        elif(blur == "gauss"):
            # 2️⃣ Гауссово размытие (сглаживает, но сохраняет детали)
            blur_img = cv2.GaussianBlur(img, (pixels, pixels), sigmaX=0)
        elif(blur == "median"):
            # 3️⃣ Медианное размытие (отлично удаляет шум «соль и перец»)
            blur_img = cv2.medianBlur(img, pixels)  # Размер ядра 5x5
        noise_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"blur_{filename}")
        cv2.imwrite(noise_filepath, blur_img)
        return jsonify({"filename": f"blur_{filename}", "filepath": noise_filepath, "size": blur_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify({"error": "Файл не выбран"}), 400
    
    file = request.files["file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        try:
            img = cv2.imread(filepath)
            if img is None:
                os.remove(filepath)
                return jsonify({"error": "Изображение повреждено"}), 400
        except Exception as e:
            os.remove(filepath)
            return jsonify({"error": str(e)}), 400
        
        return jsonify({"filename": filename, "filepath": filepath, "size": img.shape})
    else:
        return jsonify({"error": "Неподдерживаемый тип изображения"}), 400
    
@app.route("/colorspace/<filename>", methods=["POST"])
def colorspace(filename):
    data = request.form
    try:
        colorspace = str(data.get("colorspace")).upper()
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404

    try:
        img = cv2.imread(filepath)
        if colorspace == "GRAY":
            converted_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif colorspace == "HSV":
            converted_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        elif colorspace == "LAB":
            converted_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        else:
            return jsonify({"error": "Некорректное цветовое пространство"}), 400

        converted_filename = f"{colorspace.lower()}_{filename}"
        converted_filepath = os.path.join(app.config["UPLOAD_FOLDER"], converted_filename)
        cv2.imwrite(converted_filepath, converted_img)

        return jsonify({"filename": converted_filename, "filepath": converted_filepath, "size": converted_img.shape})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def hex2rgb(hex_value):
    h = hex_value.strip("#") 
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return rgb

def rgb2hsv(r, g, b):
    # Normalize R, G, B values
    r, g, b = r / 255.0, g / 255.0, b / 255.0
 
    # h, s, v = hue, saturation, value
    max_rgb = max(r, g, b)    
    min_rgb = min(r, g, b)   
    difference = max_rgb-min_rgb 
 
    # if max_rgb and max_rgb are equal then h = 0
    if max_rgb == min_rgb:
            h = 0
     
    # if max_rgb==r then h is computed as follows
    elif max_rgb == r:
            h = (60 * ((g - b) / difference) + 360) % 360
 
    # if max_rgb==g then compute h as follows
    elif max_rgb == g:
            h = (60 * ((b - r) / difference) + 120) % 360
 
    # if max_rgb=b then compute h
    elif max_rgb == b:
            h = (60 * ((r - g) / difference) + 240) % 360
 
    # if max_rgb==zero then s=0
    if max_rgb == 0:
            s = 0
    else:
            s = (difference / max_rgb) * 100
 
    # compute v
    v = max_rgb * 100
    # return rounded values of H, S and V
    return tuple(map(round, (h, s, v)))

@app.route("/find_object/<filename>", methods=["POST"])
def find_object(filename):
    data = request.form
    try:
        color_space = str(data.get("color_space")).upper()  # RGB или HSV
        color = hex2rgb(data.get("color"))
        up_hsv = [int(data.get("up_h")), int(data.get("up_s")), int(data.get("up_v"))]
        down_hsv = [int(data.get("down_h")), int(data.get("down_s")), int(data.get("down_v"))]
        tolerance = int(data.get("tolerance"))  # Допуск для поиска
        action = str(data.get("action")).lower()  # "box" или "crop"
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404

    try:
        img = cv2.imread(filepath)

        # Преобразование изображения в нужное цветовое пространство
        if color_space == "HSV":
            img_converted = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            if(not (0 <= up_hsv[0] < 180 and 0 <= down_hsv[0] < 180 and 0 <= up_hsv[1] <= 255 and 0 <= down_hsv[1] <= 255
                     and 0 <= up_hsv[2] <= 255) and 0 <= up_hsv[2] <= 255):
                return jsonify({"error": "Некорректные границы HSV"}), 400
            lower_bound = np.array(down_hsv)
            upper_bound = np.array(up_hsv)
        elif color_space == "RGB":
            img_converted = img
            if(not 0 > tolerance > 255):
                return jsonify({"error": "Допуск от 0 до 255"}), 400
            # Определение диапазона цвета с учетом допуска
            lower_bound = np.array([max(0, c - tolerance) for c in color[::-1]])
            upper_bound = np.array([min(255, c + tolerance) for c in color[::-1]])
        else:
            return jsonify({"error": "Некорректное цветовое пространство"}), 400

        # Создание маски для выделения объекта
        mask = cv2.inRange(img_converted, lower_bound, upper_bound)

        # Поиск контуров объекта
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return jsonify({"error": "Объект не найден"}), 404

        # Выбор самого большого контура
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        if action == "box":
            # Рисование ограничивающей рамки
            boxed_img = img.copy()
            cv2.rectangle(boxed_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            result_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"boxed_{filename}")
            cv2.imwrite(result_filepath, boxed_img)
            return jsonify({"filename": f"boxed_{filename}", "filepath": result_filepath, "coordinates": [x, y, w, h], "size": boxed_img.shape})
        elif action == "crop":
            # Обрезка изображения по найденным координатам
            cropped_img = img[y:y + h, x:x + w]
            result_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"cropped_{filename}")
            cv2.imwrite(result_filepath, cropped_img)
            return jsonify({"filename": f"cropped_{filename}", "filepath": result_filepath, "coordinates": [x, y, w, h], "size": cropped_img.shape})
        else:
            return jsonify({"error": "Некорректное действие"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/preview/<filename>")
def preview_image(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype="image/jpeg", max_age=0, last_modified=datetime.now().timestamp(), etag=None)
    return jsonify({"error": "Файл не найден"}), 404

@app.route("/save/<filename>", methods=['POST'])
def save(filename):
    data = request.form
    try:
        format = str(data.get("save"))
        quality = int(data.get("quality"))
    except Exception as e:
        print(e)
        return jsonify({"error": "Некорректные данные"}), 400
    if(format not in ['jpeg', 'png', 'tiff']):
        return jsonify({"error": "Некорректный формат"}), 400
    if(format == "jpeg" and not (30 <= quality <= 100)):
        return jsonify({"error": "Некорректное качество JPEG"}), 400
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден"}), 404
    img = cv2.imread(filepath)
    filename = '.'.join(filename.split('.')[:-1] + [format])
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"save_{filename}")
    params = []
    if(format == 'jpeg'):
        params += [cv2.IMWRITE_JPEG_QUALITY, quality]
    cv2.imwrite(filepath, img, params)
    return jsonify({"link": url_for('preview_image', filename=f"save_{filename}"), "name": filename})
    # return send_file(filepath)

if __name__ == "__main__":
    app.run(debug=True)
