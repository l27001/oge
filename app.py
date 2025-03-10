import os
import cv2
import numpy as np
from datetime import datetime
from flask import Flask, request, render_template, send_file, jsonify
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
        if(center_x < 1 or center_x > w or center_y < 1 or center_y > h):
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

@app.route("/preview/<filename>")
def preview_image(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype="image/jpeg", max_age=0, last_modified=datetime.now().timestamp(), etag=None)
    return jsonify({"error": "Файл не найден"}), 404

if __name__ == "__main__":
    app.run(debug=True)
