import torch 
import numpy as np 
from PIL import Image 
import groundingdino.datasets.transforms as T
from groundingdino.util.inference import load_model, predict
import re


class PerceptionModule:
    def __init__(self, config_path, weight_path , device="cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initializes VLM 
        """
        print(f"Grounding dino loaded with {device}")
        self.device = device
        self.model = load_model(config_path,weight_path).to(self.device)
        self.transform = T.Compose([
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _parse_prompt(self, command: str) -> tuple :
        """

        """

        command = command.lower()

        # Pattern 1: Action -> Target -> Preposition -> Destination
        # e.g., "pick up the red cube and drop it into the blue bowl"
        match1 = re.search(r'(?:pick up|grab|take)?\s*(?:the\s+)?(.*?)\s+(?:and\s+)?(?:drop it|place it|put it)?\s*(?:into|in|on)\s+(?:the\s+)?(.*)', command)
        
        # Pattern 2: Preposition -> Destination -> Action -> Target
        # e.g., "in the blue bowl keep the red cube"
        match2 = re.search(r'(?:in|into|on)\s+(?:the\s+)?(.*?)\s+(?:keep|put|place|drop)\s+(?:the\s+)?(.*)', command)

        if match2:
            return match2.group(2).strip(), match2.group(1).strip()
        elif match1:
            return match1.group(1).strip(), match1.group(2).strip()
        else:
            raise ValueError(f"Could not parse the command format: '{command}'")

    def _preprocess_image(self, rgb_image: np.ndarray):
        """

        """
        img_pil = Image.fromarray(rgb_image)
        image_tranformed, _ = self.transform(img_pil, None)
        return image_transformed
            

    def get_grasp_and_place_centroids(self,rgb_image: np.ndarray, command: str, box_threshold=0.3, text_threshold=0.25):
        """
        
        """
        target_obj, dest_obj = self._parse_prompt(command)

        dino_prompt = f"{target_obj} . {dest_obj}"

        image_tensor = self._preprocess_image(rgb_image)

        boxes , logits , phrases = predict(
            model=self.model,
            caption=dino_prompt,
            image=image_tensor,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
        )

        img_h , img_w ,_ = rgb_image.shape

        results = {"target": None, "destination": None}

        for box, phrase in zip(boxes, phrases):
            cx_norm, cy_norm , _ , _ = box.numpy()

            u = int(cx_norm * img_w)
            v = int(cy_norm * img_h)

            if target_obj in phrase:
                results["target"] = (u,v)
            elif dest_obj in phrase:
                results["destination"] = (u,v)

        return results

if __name__ == "__main__":
    CONFIG = "weights/GroundingDINO_SwinT_OGC.py" 
    WEIGHTS = "weights/groundingdino_swint_ogc.pth"
    
    perception = PerceptionModule(CONFIG, WEIGHTS)
    
    # Mock image (H, W, 3) 
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8) 

    print()
    print()
    
    # Test Normal Prompt
    prompt_1 = "Pick up the red cube and drop it into the blue bowl"
    print(f"Testing normal prompt: {perception._parse_prompt(prompt_1)}")
    
    # Test Inverted Prompt
    prompt_2 = "in the blue bowl keep the red cube"
    print(f"Testing inverted prompt: {perception._parse_prompt(prompt_2)}")