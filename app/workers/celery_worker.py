import time
import cv2
from rich.console import Console

# 从中心位置导入celery_app实例
from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.image_processor import ImageProcessor
from app.services.svg_generator import SVGGenerator
from app.models.schemas import CropSubmitRequest

console = Console()

# 使用导入的celery_app实例来定义任务
@celery_app.task(bind=True)
def process_face_segmentation(self, job_data: dict):
    # ... 函数的其余部分保持不变 ...
    # (这里省略了您之前已经修复好的完整函数代码, 您无需修改函数内部)
    job_id = job_data.get('job_id')
    
    try:
        console.print(f"[bold yellow]▶️ Starting job {job_id}...[/bold yellow]")
        
        if not settings.LOAD_TEST_MODE:
            console.print(f"   - Simulating {settings.SIMULATION_DELAY}s delay for job {job_id}")
            time.sleep(settings.SIMULATION_DELAY)
        
        image_processor = ImageProcessor()
        svg_generator = SVGGenerator()
        
        request_data = CropSubmitRequest(**job_data['request'])
        
        console.print(f"   - Decoding images for job {job_id}")
        image = image_processor.decode_base64_image(request_data.image)
        segmentation_map = image_processor.decode_base64_image(request_data.segmentation_map)
        
        if len(segmentation_map.shape) == 3:
            segmentation_map_gray = cv2.cvtColor(segmentation_map, cv2.COLOR_BGR2GRAY)
        else:
            segmentation_map_gray = segmentation_map

        if not image_processor.validate_face_detection(image):
            raise ValueError("No face detected in the provided image.")
        
        console.print(f"   - Rotating image for job {job_id}")
        rotation_angle = image_processor.detect_face_angle(request_data.landmarks)
        rotated_image, rotated_landmarks = image_processor.rotate_image_and_landmarks(
            image, request_data.landmarks, rotation_angle
        )
        
        console.print(f"   - Cropping face region for job {job_id}")
        cropped_image, _ = image_processor.crop_face_region(
            rotated_image, rotated_landmarks
        )
        
        rotated_seg_map, _ = image_processor.rotate_image_and_landmarks(
            segmentation_map_gray, request_data.landmarks, rotation_angle
        )
        cropped_seg_map, _ = image_processor.crop_face_region(
            rotated_seg_map, rotated_landmarks
        )

        console.print(f"   - Extracting contours for job {job_id}")
        mask_contours = image_processor.extract_contours_from_segmentation(cropped_seg_map)
        
        console.print(f"   - Generating SVG for job {job_id}")
        svg_base64 = svg_generator.generate_svg(cropped_image.shape, mask_contours)
        
        result = {
            "svg": svg_base64,
            "mask_contours": mask_contours
        }
        
        console.print(f"[bold green]✅ Completed job {job_id}[/bold green]")
        
        return result
        
    except Exception as e:
        console.print(f"[bold red]❌ Error in job {job_id}: {str(e)}[/bold red]")
        raise