import os
import time
import subprocess
import shutil # shutil для більш надійного видалення файлів (вроде норм)
from plyer import notification


INPUT_DIR = r"D:\MangaUpscale\input"
OUTPUT_DIR = r"D:\MangaUpscale\output"
ESRGAN_PATH = r"D:\Real-ESRGAN-master"

def notify(title, message):
    notification.notify(title=title, message=message, timeout=5, app_name="MangaUpscaler")

def clean_input_directory():
    """Видаляє всі файли та підпапки з INPUT_DIR."""
    print("Очищення папки INPUT (необроблені файли)...")
    count = 0
    for item in os.listdir(INPUT_DIR):
        item_path = os.path.join(INPUT_DIR, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                count += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                count += 1
        except Exception as e:
            print(f'Не вдалося видалити {item_path}. Причина: {e}')
            
    if count > 0:
        print(f"Видалено {count} об'єктів у INPUT.")
    else:
        print("Папка INPUT чиста.")

def clean_output_directory():
    """Видаляє всі файли та підпапки з OUTPUT_DIR."""
    print("\n🧹 Очищення папки OUTPUT...")
    count = 0
    for item in os.listdir(OUTPUT_DIR):
        item_path = os.path.join(OUTPUT_DIR, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                count += 1
            elif os.path.isdir(item_path):
                # Використовуємо rmtree для видалення підпапок
                shutil.rmtree(item_path)
                count += 1
        except Exception as e:
            print(f'Не вдалося видалити {item_path}. Причина: {e}')
    
    if count > 0:
        print(f"Видалено {count} об'єктів. Папка OUTPUT чиста.")
    else:
        print("Папка OUTPUT вже чиста.")


def upscale_image(image_path):
    input_filename = os.path.basename(image_path)
    
    print(f"Upscaling: {input_filename}...")
    notify("Upscaling started", input_filename)

    cmd = [
        "python", os.path.join(ESRGAN_PATH, "inference_realesrgan.py"),
        "-n", "RealESRGAN_x2plus", # X2 МОДЕЛЬ
        "-i", image_path,
        "-o", OUTPUT_DIR, 
        "--ext", "png",  # Примусовий вихідний формат
        "-g", "0",
        "--tile", "400", # оптимізація для того щоб не перебільшити з використанням па'мяті відеокарти
        "--tile_pad", "10"
    ]

    try:
        files_before = set(os.listdir(OUTPUT_DIR))
        subprocess.run(cmd, check=True)
        files_after = set(os.listdir(OUTPUT_DIR))
        new_files = list(files_after - files_before)

        if new_files:
            actual_output_filename = new_files[0]
            actual_output_path = os.path.join(OUTPUT_DIR, actual_output_filename)
            
            print(f"Done: {actual_output_path}")
            notify("Upscale complete", actual_output_filename)
            
            os.startfile(actual_output_path)
            
            os.remove(image_path) 
            print(f"Cleaned up input file: {input_filename}")
        else:
            print("Done, but failed to locate the output file!")
            notify("Upscale complete", "File not found in output folder.")

    except subprocess.CalledProcessError as e:
        print(f"Error while upscaling {input_filename}: {e}")
        notify("Upscale error", input_filename)
    except Exception as e:
        print(f"An error occurred during processing: {e}")


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    seen = set()

    print("Watching for new images...")
    notify("MangaUpscaler", "Watching for new images...")
    
    # Ініціалізація: додаємо вже існуючі файли в "seen"
    for f in os.listdir(INPUT_DIR):
        path = os.path.join(INPUT_DIR, f)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
             seen.add(path)

    try:
        # ОСНОВНИЙ ЦИКЛ СПОСТЕРЕЖЕННЯ
        while True:
            
            # 1. Збираємо список усіх файлів у INPUT_DIR
            all_files = os.listdir(INPUT_DIR)
            
            # 2. Фільтруємо та відсортовуємо нові файли
            new_files_to_process = []
            
            for f in all_files:
                path = os.path.join(INPUT_DIR, f)
                
                # Умова: це зображення AND воно ще не було оброблене
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and path not in seen:
                    new_files_to_process.append(f)
            
            # 3. СОРТУВАННЯ: Сортуємо за алфавітом (що відповідає chapter_page_001, 002, ...)
            new_files_to_process.sort() 
            
            # 4. Обробка файлів по порядку
            for f in new_files_to_process:
                path = os.path.join(INPUT_DIR, f)
                
                seen.add(path) # Додаємо в seen перед обробкою
                upscale_image(path)
                    
            time.sleep(2)
            
    except KeyboardInterrupt:
    
        print("\nСкрипт зупинено користувачем.")
        clean_input_directory() 
        clean_output_directory() 
    finally:
        pass

if __name__ == "__main__":
    main()
