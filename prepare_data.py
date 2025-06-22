import base64
import json

# --- 图像转Base64 ---
def image_to_base64(filepath: str) -> str:
    """读取图像文件并将其编码为base64字符串"""
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# --- 解析Landmarks文件 ---
def parse_landmarks(filepath: str) -> list:
    """读取landmarks文件并将其转换为所需的列表格式"""
    landmarks = []
    with open(filepath, "r") as f:
        for line in f:
            # 假设每行格式为 "x,y"
            parts = line.strip().split(',')
            if len(parts) == 2:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    landmarks.append({"x": x, "y": y})
                except ValueError:
                    print(f"Skipping invalid line: {line}")
    return landmarks

# --- 主逻辑 ---
if __name__ == "__main__":
    try:
        # 1. 编码图像文件
        original_image_b64 = image_to_base64("original_image.png")
        segmentation_map_b64 = image_to_base64("segmentation_map.png")
        
        # 2. 解析Landmarks (使用最终确认的正确文件名)
        landmarks_data = parse_landmarks("landmarks.txt") # <-- 已修正回 .txt
        
        # 3. 组合成最终的JSON payload
        payload = {
            "image": original_image_b64,
            "landmarks": landmarks_data,
            "segmentation_map": segmentation_map_b64
        }
        
        # 4. 将payload保存到一个文件中，方便curl调用
        with open("payload.json", "w") as f:
            json.dump(payload, f, indent=2)
            
        print("✅ 成功创建 payload.json 文件！")
        print("现在您可以使用 'curl' 命令来测试您的API了。")

    except FileNotFoundError as e:
        print(f"❌ 文件未找到错误: {e}")
        print("请确保 'original_image.png', 'segmentation_map.png', 和 'landmarks.txt' 这三个文件都在当前文件夹中。")
