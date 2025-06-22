import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
from scipy import ndimage
from skimage import measure, morphology
from app.models.schemas import LandmarkPoint
import base64
from io import BytesIO
from PIL import Image

class ImageProcessor:
    def __init__(self):
        # We will use the landmarks provided, but a Haar Cascade can be a fallback
        # for validation purposes.
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def decode_base64_image(self, base64_str: str) -> np.ndarray:
        """Decode base64 string to a BGR numpy array for OpenCV"""
        try:
            # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            
            image_data = base64.b64decode(base64_str)
            image = Image.open(BytesIO(image_data))
            # Convert to numpy array and ensure it's in BGR format for OpenCV
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise ValueError(f"Invalid base64 image: {str(e)}")
    
    def detect_face_angle(self, landmarks: List[LandmarkPoint]) -> float:
        """Calculate face rotation angle from landmarks"""
        if len(landmarks) < 48: # Need at least eye landmarks
            return 0.0
        
        # Use eye landmarks for rotation calculation (assuming standard 68-point landmarks)
        # Points 36-41 are the left eye, 42-47 are the right eye.
        left_eye_points = np.array([[p.x, p.y] for p in landmarks[36:42]])
        right_eye_points = np.array([[p.x, p.y] for p in landmarks[42:48]])
        
        left_eye_center = np.mean(left_eye_points, axis=0)
        right_eye_center = np.mean(right_eye_points, axis=0)
        
        # Calculate angle
        dy = right_eye_center[1] - left_eye_center[1]
        dx = right_eye_center[0] - left_eye_center[0]
        angle = np.degrees(np.arctan2(dy, dx))
        
        return angle
    
    def rotate_image_and_landmarks(
        self, 
        image: np.ndarray, 
        landmarks: List[LandmarkPoint], 
        angle: float
    ) -> Tuple[np.ndarray, List[LandmarkPoint]]:
        """Rotate image and adjust landmarks accordingly"""
        if abs(angle) < 1.0:  # Skip rotation for small angles
            return image, landmarks
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotate image
        rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))
        
        # Rotate landmarks
        rotated_landmarks = []
        for landmark in landmarks:
            # Create a point vector [x, y, 1] for matrix multiplication
            point = np.array([landmark.x, landmark.y, 1])
            rotated_point = rotation_matrix @ point
            rotated_landmarks.append(
                LandmarkPoint(x=rotated_point[0], y=rotated_point[1])
            )
        
        return rotated_image, rotated_landmarks
    
    def crop_face_region(
        self, 
        image: np.ndarray, 
        landmarks: List[LandmarkPoint]
    ) -> Tuple[np.ndarray, List[LandmarkPoint]]:
        """Intelligently crop face region with proper padding"""
        if not landmarks:
            return image, landmarks
        
        # Get bounding box from landmarks
        xs = [p.x for p in landmarks]
        ys = [p.y for p in landmarks]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Add padding (e.g., 20% of face width/height)
        width = max_x - min_x
        height = max_y - min_y
        padding_x = width * 0.2
        padding_y = height * 0.2
        
        # Calculate crop boundaries, ensuring they are within image dimensions
        crop_x1 = max(0, int(min_x - padding_x))
        crop_y1 = max(0, int(min_y - padding_y))
        crop_x2 = min(image.shape[1], int(max_x + padding_x))
        crop_y2 = min(image.shape[0], int(max_y + padding_y))
        
        # Crop image
        cropped_image = image[crop_y1:crop_y2, crop_x1:crop_x2]
        
        # Adjust landmarks to be relative to the cropped image
        adjusted_landmarks = [
            LandmarkPoint(x=p.x - crop_x1, y=p.y - crop_y1)
            for p in landmarks
        ]
        
        return cropped_image, adjusted_landmarks
    
    def smooth_segmentation_mask(self, mask: np.ndarray) -> np.ndarray:
        """Apply smoothing to a binary segmentation mask"""
        # Morphological closing to fill small holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        closed_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Gaussian blur to smooth edges
        smoothed_mask = ndimage.gaussian_filter(closed_mask.astype(float), sigma=3.0)
        
        # Binarize the result to get a clean mask
        final_mask = (smoothed_mask > 0.5).astype(np.uint8)
        
        return final_mask
    
    def extract_contours_from_segmentation(
        self, 
        segmentation_map: np.ndarray
    ) -> Dict[str, List[List[Dict[str, float]]]]:
        """Extract smooth contours from the full segmentation map"""
        contours_dict = {}
        
        # Get unique region IDs (excluding background, assumed to be 0)
        unique_regions = np.unique(segmentation_map)
        unique_regions = unique_regions[unique_regions > 0]
        
        for region_id in unique_regions:
            # Create a binary mask for the current region
            region_mask = (segmentation_map == region_id).astype(np.uint8)
            
            # Smooth the individual region mask
            smoothed_mask = self.smooth_segmentation_mask(region_mask)
            
            # Find contours on the smoothed mask
            contours, _ = cv2.findContours(
                smoothed_mask, 
                cv2.RETR_EXTERNAL, # Get only external contours
                cv2.CHAIN_APPROX_SIMPLE # Compress contour points
            )
            
            region_contours = []
            for contour in contours:
                if cv2.contourArea(contour) < 20: # Filter out tiny noise contours
                    continue
                
                # Simplify the contour to reduce number of points
                epsilon = 0.005 * cv2.arcLength(contour, True)
                simplified_contour = cv2.approxPolyDP(contour, epsilon, True)
                
                # Convert to the required format (list of dicts)
                contour_points = [
                    {"x": float(point[0][0]), "y": float(point[0][1])}
                    for point in simplified_contour
                ]
                
                if len(contour_points) > 2:  # Only keep meaningful lines
                    region_contours.append(contour_points)
            
            if region_contours:
                contours_dict[str(region_id)] = region_contours
        
        return contours_dict
    
    def validate_face_detection(self, image: np.ndarray) -> bool:
        """Validate that the image contains a detectable face as a fallback"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0